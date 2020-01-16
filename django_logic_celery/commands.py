from celery import signature, group, chain, shared_task
from celery.result import AsyncResult
from django.apps import apps
from django.db import transaction
from django_logic.commands import SideEffects, Callbacks


class TransitionTaskFailed(Exception):
    pass


@shared_task(acks_late=True)
def complete_transition(*args, **kwargs):
    app = apps.get_app_config(kwargs['app_label'])
    model = app.get_model(kwargs['model_name'])
    instance = model.objects.get(id=kwargs['instance_id'])
    transition = kwargs['transition']
    field_name = kwargs.pop('field_name')

    transition.complete_transition(instance, field_name, **kwargs)


@shared_task(acks_late=True)
def fail_transition(task_id, *args, **kwargs):
    try:
        transition = kwargs['transition']
        try:
            # Exception passed through args
            exc = args[0]
        except IndexError:
            task = AsyncResult(task_id)
            exc = task.info

        app = apps.get_app_config(kwargs['app_label'])
        model = app.get_model(kwargs['model_name'])
        instance = model.objects.get(id=kwargs['instance_id'])
        field_name = kwargs.pop('field_name')
        transition.fail_transition(instance, field_name, **kwargs)
    except Exception:
        # TODO: add logger
        print('Exception')


@shared_task(acks_late=True)
def run_side_effects_as_task(**kwargs):
    app = apps.get_app_config(kwargs['app_label'])
    model = app.get_model(kwargs['model_name'])
    instance = model.objects.get(id=kwargs['instance_id'])
    field_name = kwargs.pop('field_name')
    transition = kwargs['transition']
    try:
        for side_effect in transition.side_effects.commands:
            side_effect(instance)
    except Exception:
        transition.fail_transition(instance, field_name, **kwargs)

    transition.complete_transition(instance, field_name, **kwargs)


@shared_task(acks_late=True)
def run_callbacks_as_task(**kwargs):
    app = apps.get_app_config(kwargs['app_label'])
    model = app.get_model(kwargs['model_name'])
    instance = model.objects.get(id=kwargs['instance_id'])
    transition = kwargs['transition']

    for callback in transition.callbacks.commands:
        callback(instance)


class CeleryTaskMixin:
    def execute(self, instance: any, field_name: str, **kwargs):
        if not self.commands:
            return super().execute(instance, field_name)

        task_kwargs = self.get_task_kwargs(instance, field_name)
        self.queue_task(task_kwargs)

    def get_task_kwargs(self, instance: any, field_name: str, **kwargs):
        return dict(
            app_label=instance._meta.app_label,
            model_name=instance._meta.model_name,
            instance_id=instance.pk,
            field_name=field_name
        )

    def queue_task(self, task_kwargs):
        return NotImplementedError


class SideEffectTasks(CeleryTaskMixin, SideEffects):
    def queue_task(self, task_kwargs):
        header = [signature(task_name, kwargs=task_kwargs) for task_name in self.commands]
        header = chain(*header)
        task_kwargs.update(dict(transition=self._transition))
        body = complete_transition.s(**task_kwargs)
        tasks = chain(header | body).on_error(fail_transition.s(**task_kwargs))
        transaction.on_commit(tasks.delay)


class CallbacksTasks(CeleryTaskMixin, Callbacks):
    def queue_task(self, task_kwargs):
        tasks = [signature(task_name, kwargs=task_kwargs) for task_name in self.commands]
        transaction.on_commit(group(tasks))


class SideEffectSingleTask(CeleryTaskMixin, SideEffects):
    def get_task_kwargs(self, instance: any, field_name: str, **kwargs):
        task_kwargs = super().get_task_kwargs(instance, field_name, **kwargs)
        task_kwargs['transition'] = self._transition
        return task_kwargs

    def queue_task(self, task_kwargs):
        sig = run_side_effects_as_task.signature(kwargs=task_kwargs)
        transaction.on_commit(sig.delay)


class CallbacksSingleTask(CeleryTaskMixin, Callbacks):
    def get_task_kwargs(self, instance: any, field_name: str, **kwargs):
        task_kwargs = super().get_task_kwargs(instance, field_name, **kwargs)
        task_kwargs['transition'] = self._transition
        return task_kwargs

    def queue_task(self, task_kwargs):
        sig = run_callbacks_as_task.signature(kwargs=task_kwargs)
        transaction.on_commit(sig.delay)
