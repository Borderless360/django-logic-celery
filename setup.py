import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="django-logic-celery",
    version="0.0.4",
    author="Emil Balashov",
    author_email="emil@borderless360.com",
    description="Django Logic Celery - background transitions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Borderless360/django-logic-celery",
    keywords="django",
    packages=setuptools.find_packages(),
    include_package_data=True,
    zip_safe=False,
    license='MIT License',
    platforms=['any'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Framework :: Django",
        "Framework :: Django :: 2.0",
        "Framework :: Django :: 2.1",
        "Framework :: Django :: 2.2",
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.6',
)