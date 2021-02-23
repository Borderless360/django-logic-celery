from django_logic import Transition, Action

from django_logic_celery import SideEffectTasks, CallbacksTasks, SideEffectSingleTask


class InProgressTransition(Transition):
    side_effects_class = SideEffectTasks


class CeleryCallbackTransition(Transition):
    callbacks_class = CallbacksTasks


class CeleryTransition(Transition):
    side_effects_class = SideEffectTasks
    callbacks_class = CallbacksTasks


class CelerySingleTaskTransition(Transition):
    side_effects_class = SideEffectSingleTask


class InProgressAction(Action):
    side_effects_class = SideEffectTasks


class CeleryCallbackAction(Action):
    callbacks_class = CallbacksTasks


class CeleryAction(Action):
    side_effects_class = SideEffectTasks
    callbacks_class = CallbacksTasks


class CelerySingleTaskAction(Action):
    side_effects_class = SideEffectSingleTask
