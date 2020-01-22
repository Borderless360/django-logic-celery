from django.test import TransactionTestCase

from unittest.mock import patch
from demo.process import InvoiceProcess
from demo.models import Invoice
from demo.tasks import *


class InvoiceProcessTestCase(TransactionTestCase):
    def setUp(self):
        self.process_class = InvoiceProcess

    def test_process_class_method(self):
        self.assertEqual(self.process_class.process_name, 'invoice_process')

    def test_invoice_process(self):
        invoice = Invoice.objects.create(status='draft')
        invoice.invoice_process.approve()
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'approved')

    def test_invoice_save(self):
        invoice = Invoice.objects.create(status='draft')
        invoice.status = 'paid'
        invoice.save()
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'draft')
        invoice.invoice_process.approve()
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'approved')

    @patch('demo.models.Invoice.debug')
    def test_invoice_callbacks(self, debug_method):
        invoice = Invoice.objects.create(status='draft')
        invoice.invoice_process.demo(foo='bar')
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'sent')
        self.assertEqual(debug_method.call_count, 5)
        expected_side_effects_kwargs = {
            'app_label': 'demo',
            'model_name': 'invoice',
            'instance_id': invoice.id,
            'process_name': 'invoice_process',
            'field_name': 'status',
            'transition': InvoiceProcess.transitions[3]
        }
        expected_callbacks_kwargs = {
            'app_label': 'demo',
            'model_name': 'invoice',
            'instance_id': invoice.id,
            'process_name': 'invoice_process',
            'field_name': 'status',
        }
        self.assertEqual(list(debug_method.call_args_list[0]), [('demo_task_1',), expected_side_effects_kwargs])
        self.assertEqual(list(debug_method.call_args_list[1]), [('demo_task_2', None), expected_side_effects_kwargs])
        self.assertEqual(list(debug_method.call_args_list[2]), [('demo_task_3', None), expected_side_effects_kwargs])
        self.assertEqual(list(debug_method.call_args_list[3]), [('demo_task_4',), expected_callbacks_kwargs])
        self.assertEqual(list(debug_method.call_args_list[4]), [('demo_task_5',), expected_callbacks_kwargs])

    @patch('demo.models.Invoice.debug')
    def test_invoice_single_task_callbacks(self, debug_method):
        invoice = Invoice.objects.create(status='draft')
        invoice.invoice_process.demo_single(foo='bar')
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'sent')
        self.assertEqual(debug_method.call_count, 5)
        self.assertEqual(list(debug_method.call_args_list[0]), [('demo_task_1', invoice), {}])
        self.assertEqual(list(debug_method.call_args_list[1]), [('demo_task_2', invoice), {}])
        self.assertEqual(list(debug_method.call_args_list[2]), [('demo_task_3', invoice), {}])
        self.assertEqual(list(debug_method.call_args_list[3]), [('demo_task_4', invoice), {}])
        self.assertEqual(list(debug_method.call_args_list[4]), [('demo_task_5', invoice), {}])

    @patch('demo.models.Invoice.debug')
    def test_invoice_failure_callbacks(self, debug_method):
        invoice = Invoice.objects.create(status='draft')
        with self.assertRaises(Exception) as ctx:
            invoice.invoice_process.failing_transition(foo='bar')
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'failed')
        self.assertEqual(debug_method.call_count, 3)
        expected_side_effects_kwargs = {
            'app_label': 'demo',
            'model_name': 'invoice',
            'instance_id': invoice.id,
            'process_name': 'invoice_process',
            'field_name': 'status',
            'transition': InvoiceProcess.transitions[5]
        }
        expected_callbacks_kwargs = {
            'app_label': 'demo',
            'model_name': 'invoice',
            'instance_id': invoice.id,
            'process_name': 'invoice_process',
            'field_name': 'status',
            'exception': ctx.exception,
        }
        self.assertEqual(list(debug_method.call_args_list[0]), [('demo_task_1',), expected_side_effects_kwargs])
        self.assertEqual(list(debug_method.call_args_list[1]), [('demo_task_3',), expected_callbacks_kwargs])
        self.assertEqual(list(debug_method.call_args_list[2]), [('demo_task_4',), expected_callbacks_kwargs])

    @patch('demo.models.Invoice.debug')
    def test_invoice_failure_callbacks_single(self, debug_method):
        invoice = Invoice.objects.create(status='draft')
        invoice.invoice_process.failing_transition_single(foo='bar')
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'failed')
        self.assertEqual(debug_method.call_count, 3)
        self.assertEqual(list(debug_method.call_args_list[0]), [('demo_task_1', invoice), {}])
        self.assertEqual(debug_method.call_args_list[1][0], ('demo_task_3', invoice))
        self.assertEqual(list(debug_method.call_args_list[1][1].keys()), ['exception'])
        self.assertEqual(debug_method.call_args_list[2][0], ('demo_task_4', invoice))
        self.assertEqual(list(debug_method.call_args_list[2][1].keys()), ['exception'])