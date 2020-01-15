from django_logic import Transition

from django_logic_celery import SideEffectTasks, CallbacksTasks


class InProgressTransition(Transition):
    side_effects_class = SideEffectTasks


class CeleryCallbackTransition(Transition):
    callbacks_class = CallbacksTasks


class CeleryTransition(Transition):
    side_effects_class = SideEffectTasks
    callbacks_class = CallbacksTasks
