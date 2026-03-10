import logging

from celery import signature, group, chain, shared_task
from celery.result import AsyncResult
from django.apps import apps
from django.db import transaction
from django_logic.commands import SideEffects, Callbacks
from django_logic.state import State
from django_logic.logger import transition_logger as logger, TransitionEventType


def _find_transition_in_process(process, action_name):
    """Recursively search for transition by action_name in process and nested processes"""
    # Search in current process transitions
    for transition in process.transitions:
        if transition.action_name == action_name:
            return transition
    
    # Search in nested processes recursively
    for sub_process_class in process.nested_processes:
        sub_process = sub_process_class(state=process.state)
        result = _find_transition_in_process(sub_process, action_name)
        if result is not None:
            return result
    
    return None


def get_transition_from_process(instance, process_name, action_name):
    """Helper function to retrieve transition from process by action_name"""
    process = getattr(instance, process_name)
    transition = _find_transition_in_process(process, action_name)
    if transition is None:
        raise ValueError(f"Transition with action_name '{action_name}' not found in process '{process_name}'")
    return transition


@shared_task(acks_late=True)
def complete_transition(*args, **kwargs):
    """Completes transition """
    app_label = kwargs['app_label']
    model_name = kwargs['model_name']
    instance_id = kwargs['instance_id']
    action_name = kwargs['action_name']
    process_name = kwargs['process_name']

    app = apps.get_app_config(app_label)
    model = app.get_model(model_name)
    instance = model.objects.get(id=instance_id)
    state = getattr(instance, process_name).state
    transition = get_transition_from_process(instance, process_name, action_name)

    logging.info(f'{state.instance_key} complete transition task started')
    logger.info(f'{kwargs.get("tr_id")} complete transition task started')
    transition.complete_transition(state, **kwargs)
    logging.info(f'{state.instance_key} complete transition task finished')
    logger.info(f'{kwargs.get("tr_id")} complete transition task finished')


@shared_task(acks_late=True)
def fail_transition(task_id, *args, **kwargs):
    """
    Transition failure handler handles exceptions and runs fail_transition method of provided Transition.
    Make sure to catch all exceptions by this failure handler as otherwise
    it leads to the worker crash.
    """
    app_label = kwargs['app_label']
    model_name = kwargs['model_name']
    instance_id = kwargs['instance_id']
    action_name = kwargs['action_name']
    process_name = kwargs['process_name']

    try:
        app = apps.get_app_config(app_label)
        model = app.get_model(kwargs['model_name'])
        instance = model.objects.get(id=kwargs['instance_id'])
        state = getattr(instance, kwargs['process_name']).state
        transition = get_transition_from_process(instance, process_name, action_name)
        try:
            # If exception is raised in success callback, it will be passed through args
            error = args[0]
        except IndexError:
            task = AsyncResult(task_id)
            error = task.info
        logging.info(f"{state.instance_key} action '{transition.action_name}' failed with error {error}")
        logging.exception(error)
        logger.error(
            f'{kwargs.get("tr_id")} {TransitionEventType.FAIL.value}: {error}',
            exc_info=True, extra={'kwargs': kwargs}
        )
        transition.fail_transition(state, error, **kwargs)
    except Exception as error:
        logging.info(f'{app_label}-{model_name}-{action_name}-{instance_id}'
                      f'failure handler failed with error: {error}')
        logging.exception(error)
        logger.error(
            f'{kwargs.get("tr_id")} {app_label}-{model_name}-{action_name}-{instance_id} '
            f'failure handler failed with error: {error}',
            exc_info=True
        )


@shared_task(acks_late=True)
def run_side_effects_as_task(app_label, model_name, action_name, instance_id, process_name, **kwargs):
    """It runs all side-effects of provided transition under a single task"""
    app = apps.get_app_config(app_label)
    model = app.get_model(model_name)
    instance = model.objects.get(id=instance_id)
    state = getattr(instance, process_name).state
    transition = get_transition_from_process(instance, process_name, action_name)
    logging.info(f"{state.instance_key} side effects of '{transition.action_name}' started")
    logger.info(f'{kwargs.get("tr_id")} SideEffects {len(transition.side_effects.commands)}')

    try:
        for side_effect in transition.side_effects.commands:
            logger.info(f'{kwargs.get("tr_id")} {TransitionEventType.SIDE_EFFECT.value} {side_effect.__name__}')
            side_effect(instance)
    except Exception as error:
        logging.info(f"{state.instance_key} side effects of '{transition.action_name}' failed with error: {error}")
        logging.exception(error)
        logger.error(f'{kwargs.get("tr_id")} {error}', exc_info=True, extra={'kwargs': kwargs})
        transition.fail_transition(state, error, **kwargs)
    else:
        logging.info(f"{state.instance_key} side effects of '{transition.action_name}' succeeded")
        transition.complete_transition(state, **kwargs)


@shared_task(acks_late=True)
def run_callbacks_as_task(app_label, model_name, action_name, instance_id, process_name, **kwargs):
    """It runs all callbacks of provided transition under a single task"""
    try:
        app = apps.get_app_config(app_label)
        model = app.get_model(model_name)
        instance = model.objects.get(id=instance_id)
        state = getattr(instance, process_name).state
        transition = get_transition_from_process(instance, process_name, action_name)

        exception = kwargs.get('exception')
        commands = transition.callbacks.commands if not exception else transition.failure_callbacks.commands
        callback_kwargs = {} if not exception else {"exception": exception}
        logging.info(f"{state.instance_key} callbacks of '{transition.action_name}' started")
        logger.info(f'{kwargs.get("tr_id")} Callbacks {len(commands)}')
        command_name = None
        for callback in commands:
            command_name = callback.__name__
            logger.info(f'{kwargs.get("tr_id")} {TransitionEventType.CALLBACK.value} {command_name}')
            callback(instance, **callback_kwargs)
    except Exception as error:
        logging.info(f'{app_label}-{model_name}-{action_name}-{instance_id}'
                     f'callbacks failed with error: {error}')
        logging.exception(error)
        logger.error(
            f'{kwargs.get("tr_id")} {TransitionEventType.CALLBACK.value} {command_name}: {error}',
            exc_info=True, extra={'kwargs': kwargs}
        )


class CeleryCommandMixin:
    """Celery command mixin"""

    def execute(self, state: State, **kwargs):
        if not self.commands:
            return super().execute(state)

        task_kwargs = self.get_task_kwargs(state, **kwargs)
        self.queue_task(task_kwargs)
        logging.info(f'{self.__class__.__name__} has been added to queue with '
                     f'the following parameters {task_kwargs}')
        logger.info(
            f'{kwargs.get("tr_id")} {TransitionEventType.BACKGROUND_MODE.value} '
            f'{self.__class__.__name__} queued with {task_kwargs}'
        )

    def get_task_kwargs(self, state: State, **kwargs):
        task_kwargs = dict(
            app_label=state.instance._meta.app_label,
            model_name=state.instance._meta.model_name,
            instance_id=state.instance.pk,
            process_name=state.process_name,
            field_name=state.field_name,
            action_name=self._transition.action_name
        )
        
        # Only include serializable kwargs - convert objects to IDs where possible
        serializable_kwargs = {}
        for key, value in kwargs.items():
            if key == 'exception':
                serializable_kwargs[key] = value
                continue
            # Skip functions and other callables
            if callable(value) and not isinstance(value, type):
                continue
            # Convert user objects to user_id
            if key == 'user' and hasattr(value, 'pk'):
                serializable_kwargs['user_id'] = value.pk
                continue
            # Include only primitive serializable types
            if isinstance(value, (str, int, float, bool, type(None))):
                serializable_kwargs[key] = value
        
        task_kwargs.update(serializable_kwargs)

        return task_kwargs

    def queue_task(self, task_kwargs):
        return NotImplementedError


class SideEffectTasks(CeleryCommandMixin, SideEffects):
    """
    Celery side-effects creates a chain of celery tasks where every task is a command.
    In case of success it triggers complete_transition task
    In case of failure it triggers fail_transition task
    """

    def queue_task(self, task_kwargs):
        # Convert function objects to task names (strings)
        task_names = []
        for cmd in self.commands:
            if isinstance(cmd, str):
                task_names.append(cmd)
            elif hasattr(cmd, 'name'):
                # Celery task object
                task_names.append(cmd.name)
            elif callable(cmd):
                # Regular function - use its name (assumes it's registered as a Celery task)
                task_names.append(cmd.__name__)
            else:
                task_names.append(str(cmd))
        
        header = [signature(task_name, kwargs=task_kwargs) for task_name in task_names]
        header = chain(*header)
        body = complete_transition.s(**task_kwargs)
        tasks = chain(header | body).on_error(fail_transition.s(**task_kwargs))
        transaction.on_commit(tasks.delay)


class CallbacksTasks(CeleryCommandMixin, Callbacks):
    """Callbacks commands executed as a celery group of tasks"""

    def queue_task(self, task_kwargs):
        tasks = [signature(task_name, kwargs=task_kwargs) for task_name in self.commands]
        transaction.on_commit(group(tasks))


class SideEffectSingleTask(CeleryCommandMixin, SideEffects):
    """Side-effects commands executed as a single celery task"""

    def queue_task(self, task_kwargs):
        sig = run_side_effects_as_task.signature(kwargs=task_kwargs)
        transaction.on_commit(sig.delay)


class CallbacksSingleTask(CeleryCommandMixin, Callbacks):
    """Callbacks commands executed as a single celery task"""

    def queue_task(self, task_kwargs):
        sig = run_callbacks_as_task.signature(kwargs=task_kwargs)
        transaction.on_commit(sig.delay)
