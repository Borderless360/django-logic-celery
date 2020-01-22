from django_logic import Process, Transition

from django_logic_celery import SideEffectTasks, CallbacksTasks, CallbacksSingleTask, SideEffectSingleTask
from demo import tasks


class CeleryTransition(Transition):
    side_effects_class = SideEffectTasks
    callbacks_class = CallbacksTasks
    failure_callbacks_class = CallbacksTasks

class CelerySingleTaskTransition(Transition):
    side_effects_class = SideEffectSingleTask
    callbacks_class = CallbacksSingleTask
    failure_callbacks_class = CallbacksSingleTask


class InvoiceProcess(Process):
    process_name = 'invoice_process'

    states = (
        ('draft', 'Draft'),
        ('paid', 'Paid'),
        ('void', 'Void'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )

    transitions = [
        Transition(
            action_name='approve',
            sources=['draft'],
            target='approved'
        ),
        CeleryTransition(
            action_name='send_to_customer',
            sources=['approved'],
            side_effects=['demo.tasks.send_to_a_customer'],
            target='sent'
        ),
        Transition(
            action_name='void',
            sources=['draft', 'paid'],
            target='voided'
        ),
        CeleryTransition(
            action_name='demo',
            sources=['draft'],
            target='sent',
            in_progress_state='in_progress',
            side_effects=['demo.tasks.demo_task_1', 'demo.tasks.demo_task_2', 'demo.tasks.demo_task_3'],
            callbacks=['demo.tasks.demo_task_4', 'demo.tasks.demo_task_5']
        ),
        CelerySingleTaskTransition(
            action_name='demo_single',
            sources=['draft'],
            target='sent',
            in_progress_state='in_progress',
            side_effects=[tasks.demo_task_1, tasks.demo_task_2, tasks.demo_task_3],
            callbacks=[tasks.demo_task_4, tasks.demo_task_5]
        ),
        CeleryTransition(
            action_name='failing_transition',
            sources=['draft'],
            target='sent',
            in_progress_state='in_progress',
            failed_state='failed',
            side_effects=['demo.tasks.demo_task_1', 'demo.tasks.demo_task_exception', 'demo.tasks.demo_task_2'],
            failure_callbacks=['demo.tasks.demo_task_3', 'demo.tasks.demo_task_4']
        ),
        CelerySingleTaskTransition(
            action_name='failing_transition_single',
            sources=['draft'],
            target='sent',
            in_progress_state='in_progress',
            failed_state='failed',
            side_effects=[tasks.demo_task_1, tasks.demo_task_exception, tasks.demo_task_2],
            failure_callbacks=[tasks.demo_task_3, tasks.demo_task_4]
        )

    ]
