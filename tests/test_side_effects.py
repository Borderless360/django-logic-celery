from django.test import TransactionTestCase
from django_logic import Process

from demo.models import Invoice
from django_logic_celery import InProgressTransition
from demo.tasks import *
from django_logic_celery.commands import complete_transition, fail_transition


class User:
    is_allowed = True


class ApplyTransitionTestCase(TransactionTestCase):
    def setUp(self) -> None:
        self.user = User()
        self.invoice = Invoice.objects.create(status='approved')

    def test_simple_transition(self):
        self.invoice.invoice_process.send_to_customer()
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'sent')
        self.assertTrue(self.invoice.customer_received)
