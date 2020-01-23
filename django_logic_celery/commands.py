import logging

from celery import signature, group, chain, shared_task
from celery.result import AsyncResult
from django.apps import apps
from django.db import transaction
from django_logic.commands import SideEffects, Callbacks
from django_logic.state import State


@shared_task(acks_late=True)
def complete_transition(*args, **kwargs):
    """Completes transition """
    app_label = kwargs['app_label']
    model_name = kwargs['model_name']
    instance_id = kwargs['instance_id']
    transition = kwargs['transition']
    process_name = kwargs['process_name']

    app = apps.get_app_config(app_label)
    model = app.get_model(model_name)
    instance = model.objects.get(id=instance_id)
    state = getattr(instance, process_name).state

    logging.info(f'{state.instance_key} complete transition task started')
    transition.complete_transition(state, **kwargs)
    logging.info(f'{state.instance_key} complete transition task finished')


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
    transition = kwargs['transition']

    try:
        app = apps.get_app_config(app_label)
        model = app.get_model(kwargs['model_name'])
        instance = model.objects.get(id=kwargs['instance_id'])
        state = getattr(instance, kwargs['process_name']).state
        try:
            # If exception is raised in success callback, it will be passed through args
            error = args[0]
        except IndexError:
            task = AsyncResult(task_id)
            error = task.info
        logging.error(f'{state.instance_key} failed with error {error}')
        transition.fail_transition(state, error, **kwargs)
    except Exception as error:
        logging.error(f'{app_label}-{model_name}-{transition.action_name}-{instance_id}'
                      f'failed with error: {error}')


@shared_task(acks_late=True)
def run_side_effects_as_task(app_label, model_name, transition, instance_id, process_name, **kwargs):
    """It runs all side-effects of provided transition under a single task"""
    app = apps.get_app_config(app_label)
    model = app.get_model(model_name)
    instance = model.objects.get(id=instance_id)
    state = getattr(instance, process_name).state
    logging.info(f"{state.instance_key} single task's side-effects of "
                 f"'{transition.action_name}' action started")

    try:
        for side_effect in transition.side_effects.commands:
            side_effect(instance)
    except Exception as error:
        logging.error(f"{state.instance_key} single task's side-effects of "
                      f"'{transition.action_name}' action "
                      f"failed with error: {error}")
        transition.fail_transition(state, error, **kwargs)
    else:
        logging.info(f"{state.instance_key} side-effects of "
                     f"'{transition.action_name}' action succeed")
        transition.complete_transition(state, **kwargs)


@shared_task(acks_late=True)
def run_callbacks_as_task(app_label, model_name, transition, instance_id, process_name, **kwargs):
    """It runs all callbacks of provided transition under a single task"""
    app = apps.get_app_config(app_label)
    model = app.get_model(model_name)
    instance = model.objects.get(id=instance_id)
    exception = kwargs.get('exception')
    commands = transition.callbacks.commands if not exception else transition.failure_callbacks.commands
    callback_kwargs = {} if not exception else {"exception": exception}
    for callback in commands:
        callback(instance, **callback_kwargs)


class CeleryCommandMixin:
    """Celery command mixin"""

    def execute(self, state: State, **kwargs):
        if not self.commands:
            return super().execute(state)

        task_kwargs = self.get_task_kwargs(state, **kwargs)
        self.queue_task(task_kwargs)
        logging.info(f'{self.__class__.__name__} has been added to queue with '
                     f'the following parameters {task_kwargs}')

    def get_task_kwargs(self, state: State, **kwargs):
        task_kwargs = dict(
            app_label=state.instance._meta.app_label,
            model_name=state.instance._meta.model_name,
            instance_id=state.instance.pk,
            process_name=state.process_name,
            field_name=state.field_name
        )
        if 'exception' in kwargs:
            task_kwargs['exception'] = kwargs['exception']

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
        header = [signature(task_name, kwargs=task_kwargs) for task_name in self.commands]
        header = chain(*header)
        task_kwargs.update(dict(transition=self._transition))
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

    def get_task_kwargs(self, state: State, **kwargs):
        task_kwargs = super().get_task_kwargs(state, **kwargs)
        task_kwargs['transition'] = self._transition
        return task_kwargs

    def queue_task(self, task_kwargs):
        sig = run_side_effects_as_task.signature(kwargs=task_kwargs)
        transaction.on_commit(sig.delay)


class CallbacksSingleTask(CeleryCommandMixin, Callbacks):
    """Callbacks commands executed as a single celery task"""

    def get_task_kwargs(self, state: State, **kwargs):
        task_kwargs = super().get_task_kwargs(state, **kwargs)
        task_kwargs['transition'] = self._transition
        return task_kwargs

    def queue_task(self, task_kwargs):
        sig = run_callbacks_as_task.signature(kwargs=task_kwargs)
        transaction.on_commit(sig.delay)
