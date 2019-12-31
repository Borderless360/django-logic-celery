from django.test import TestCase
from django_logic import Process, Transition

from demo.models import Invoice
from django_logic_celery import SideEffectTasks


class User:
    is_allowed = True


class InProgressTransition(Transition):
    side_effects = SideEffectTasks()


class ApplyTransitionTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User()
        self.invoice = Invoice.objects.create(status='draft')

    def test_simple_transition(self):
        class TestProcess(Process):
            transitions = [
                InProgressTransition('cancel',
                                     sources=['draft', ],
                                     target='cancelled',
                                     in_progress_state='cancelling',
                                     side_effects='demo.tasks.send_to_a_customer')
            ]

        process = TestProcess(instance=self.invoice, field_name='status')
        process.cancel()
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'cancelling')
