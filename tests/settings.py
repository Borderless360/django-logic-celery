import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'django_logic_celery'

PROJECT_APPS = [
    'django_logic',
    'django_logic_celery',
    'demo',
    'tests',
]

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
] + PROJECT_APPS


MIDDLEWARE = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
CELERY_BROKER_URL = 'amqp://guest:guest@127.0.0.1:5672//'
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_ACCEPT_CONTENT = ['json', 'pickle', 'application/x-python-serialize']
CELERY_TASK_ALWAYS_EAGER = True
CELERY_ALWAYS_EAGER = True
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'django_logic',
    }
}
#
# MIGRATION_MODULES = {
#     'auth': None,
#     'contenttypes': None,
# }