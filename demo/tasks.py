from celery import shared_task
from demo.exceptions import DemoException

@shared_task(acks_late=True)
def send_to_a_customer(*args, **kwargs):
    """
    It sends an invoice to the customer
    """
    from demo.models import Invoice
    invoice = Invoice.objects.get(pk=kwargs['instance_id']) if 'instance_id' in kwargs else args[0]
    invoice.customer_received = True
    invoice.save(update_fields=['customer_received'])


@shared_task(acks_late=True)
def demo_task_1(*args, **kwargs):
    from demo.models import Invoice
    invoice = Invoice.objects.get(pk=kwargs['instance_id']) if 'instance_id' in kwargs else args[0]
    invoice.debug("demo_task_1", *args, **kwargs)


@shared_task(acks_late=True)
def demo_task_2(*args, **kwargs):
    from demo.models import Invoice
    invoice = Invoice.objects.get(pk=kwargs['instance_id']) if 'instance_id' in kwargs else args[0]
    invoice.debug("demo_task_2", *args, **kwargs)


@shared_task(acks_late=True)
def demo_task_3(*args, **kwargs):
    from demo.models import Invoice
    invoice = Invoice.objects.get(pk=kwargs['instance_id']) if 'instance_id' in kwargs else args[0]
    invoice.debug("demo_task_3", *args, **kwargs)


@shared_task(acks_late=True)
def demo_task_4(*args, **kwargs):
    from demo.models import Invoice
    invoice = Invoice.objects.get(pk=kwargs['instance_id']) if 'instance_id' in kwargs else args[0]
    invoice.debug("demo_task_4", *args, **kwargs)


@shared_task(acks_late=True)
def demo_task_5(*args, **kwargs):
    from demo.models import Invoice
    invoice = Invoice.objects.get(pk=kwargs['instance_id']) if 'instance_id' in kwargs else args[0]
    invoice.debug("demo_task_5", *args, **kwargs)


@shared_task(acks_late=True)
def demo_task_exception(*args, **kwargs):
    from demo.models import Invoice
    invoice = Invoice.objects.get(pk=kwargs['instance_id']) if 'instance_id' in kwargs else args[0]
    print('EXCEPTION TASK', invoice.status, args, kwargs)
    raise DemoException()
