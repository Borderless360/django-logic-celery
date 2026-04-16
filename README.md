![django-logic-celery](https://user-images.githubusercontent.com/6745569/87846587-7e57f580-c903-11ea-8ef7-b3ca129c92b1.png)

> **⚠️ Deprecation Notice**
>
> This package is **deprecated** and will not receive further updates.
>
> Starting with [`django-logic`](https://github.com/Borderless360/django-logic) **v0.3.0**, Celery support is built directly into the core package via `BackgroundTransition` and `BackgroundAction` — with full DB-backed durability, automatic retry, and queue routing.
>
> **Migration path:**
> 1. Upgrade to `django-logic >= 0.3.0`
> 2. Replace `CeleryTransition` with `BackgroundTransition`
> 3. Replace `CeleryAction` with `BackgroundAction`
> 4. Remove `django-logic-celery` from your dependencies
>
> See the [django-logic documentation](https://github.com/Borderless360/django-logic) for the new API.

---

[![Build Status](https://travis-ci.org/Borderless360/django-logic-celery.svg?branch=master)](https://travis-ci.org/Borderless360/django-logic-celery)[![Coverage Status](https://coveralls.io/repos/github/Borderless360/django-logic-celery/badge.svg?branch=master)](https://coveralls.io/github/Borderless360/django-logic-celery?branch=master)

The main idea of [Django Logic](https://github.com/Borderless360/django-logic) is to allow developers implementing
business logic via pure functions. Django-Logic-Celery takes care of the connection
between the pure functions and the business requirements, based on a state of the model object.
Please, make sure to make yourself familiar with [Django Logic](https://github.com/Borderless360/django-logic) first,
as it implements the core functionality and the very package is the only extension allowing using Celery tasks.


## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install Django-Logic-Celery.

```bash
pip install django-logic-celery
```

## Contributing

This package is deprecated. Please contribute to [django-logic](https://github.com/Borderless360/django-logic) instead.

## License
[MIT](https://choosealicense.com/licenses/mit/)

## Project status
**Deprecated** — superseded by `django-logic >= 0.3.0`.
