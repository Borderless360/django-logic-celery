from django_logic import Transition

from django_logic_celery import SideEffectTasks, CallbacksTasks


class InProgressTransition(Transition):
    side_effects = SideEffectTasks()
    failure_callbacks = CallbacksTasks()


class CeleryCallbackTransition(Transition):
    callbacks = CallbacksTasks()


class CeleryTransition(Transition):
    side_effects = SideEffectTasks()
    callbacks = CallbacksTasks()
    failure_callbacks = CallbacksTasks()

