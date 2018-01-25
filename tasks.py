#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from invoke import task
from invoke.util import log


@task
def clean(ctx):
    """clean - remove build artifacts."""
    ctx.run('rm -rf build/')
    ctx.run('rm -rf dist/')
    ctx.run('rm -rf htmlcov/')
    ctx.run('rm -rf cov_annotate/')
    ctx.run('rm -rf nsct.egg-info')
    ctx.run('find . -name *.pyc -delete')
    ctx.run('find . -name *.pyo -delete')
    ctx.run('find . -name __pycache__ -delete')

    log.info('cleaned up')


@task
def test(ctx):
    """test - run the test runner."""
    ctx.run('py.test --flakes --cov-report term-missing --cov-report annotate:cov_annotate --cov nsct tests/', pty=True)


@task
def lint(ctx):
    """lint - check style with flake8."""
    ctx.run('flake8 nsct tests')


@task(clean)
def publish(ctx):
    """publish - package and upload a release to the cheeseshop."""
    ctx.run('python setup.py sdist upload', pty=True)
    ctx.run('python setup.py bdist_wheel upload', pty=True)

    log.info('published new release')
