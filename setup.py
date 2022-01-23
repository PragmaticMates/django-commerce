#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='django-commerce',
    version='0.2.2',
    description='Basic e-shop app for Django',
    long_description=open('README.md').read(),
    author='Pragmatic Mates',
    author_email='info@pragmaticmates.com',
    maintainer='Pragmatic Mates',
    maintainer_email='info@pragmaticmates.com',
    url='https://github.com/PragmaticMates/django-commerce',
    packages=find_packages(),
    # [
    #     'commerce',
    #     'commerce.migrations',
    #     'commerce.gateways.globalpayments',
    #     'commerce.gateways.globalpayments.migrations',
    #     'commerce.gateways.wiretransfer',
    # ],
    include_package_data=True,
    install_requires=('django', 'django-invoicing'),
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Operating System :: OS Independent',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Framework :: Django',
        'License :: OSI Approved :: BSD License',
        'Development Status :: 3 - Alpha'
    ],
    license='BSD License',
    keywords="django e-shop product order shipping",
)
