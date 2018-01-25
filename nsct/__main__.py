#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
nsct.__main__
~~~~~~~~~~~~~~~~~~~~~

The main entry point for the command line interface.

Invoke as ``nsct`` (if installed)
or ``python -m nsct`` (no install required).
"""
from __future__ import absolute_import, unicode_literals, print_function

from argparse import ArgumentParser, FileType
import logging
import os
from subprocess import run
import sys
from tempfile import TemporaryFile

from nsct import __version__, __summary__
from nsct.definition import Definition
from nsct.log import configure_stream, LEVELS
from nsct.support import supportedServices
from nsct.yaml import Fragment, Location, DefinitionError

logger = logging.getLogger(__name__)


def cli():
    """Add some useful functionality here or import from a submodule."""
    # configure root logger to print to STDERR
    try:
        configure_stream(level=LEVELS[int(os.environ.get('NSCT_LOG', '0'))])
    except ValueError:
        print('Error: NSCT_LOG value not an integer (choose from {!r})'.format(LEVELS), file=sys.stderr)
        sys.exit(1)
    except KeyError:
        print('Error: NSCT_LOG value out of range (choose from {!r})'.format(LEVELS), file=sys.stderr)
        sys.exit(1)

    # launch the command line interface
    logger.debug('Booting up command line interface')

    parser = ArgumentParser(prog='definition', description=__summary__)
    parser.add_argument('filename', metavar='<FILENAME>', type=FileType('r'), help='Name of YAML file containing definition')
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('--check', action='store_true', help='Read and check the YAML file')
    parser.add_argument('--diff', action='store_true', help='Read and re-generate YAML file, showing differences')
    parser.add_argument('--dump', metavar='<FILENAME>', type=FileType('w'), help='Read and dump the YAML file to <FILENAME>')
    parser.add_argument('--generate', choices=list(supportedServices.keys()) + ['all'], action='append')
    args = parser.parse_args()

    logger.debug('Running')

    try:
        fragment = Fragment(Location(args.filename.name))
        definition = Definition.parse(fragment)
        definition.compute()
    except DefinitionError as e:
        print(e, file=sys.stdout)
        sys.exit(1)
    else:
        if args.check:
            sys.exit(0)
        if args.diff:
            with TemporaryFile() as fp:
                fragment.dump(fp)
                fp.seek(0)
                cp = run(['diff', '-c', args.filename.name, '-'], input=fp.read())
                sys.exit(cp.returncode)
        if args.dump:
            fragment.dump(args.dump)
            sys.exit(0)

        if not args.generate:
            args.generate = ['all']

        if 'all' in args.generate:
            args.generate = list(supportedServices.keys())

        logger.debug('Generation phase: {}'.format(args.generate))

        for action in supportedServices:
            if action in args.generate:
                definition.generate(action)


if __name__ == '__main__':
    # exit using whatever exit code the CLI returned
    sys.exit(cli())
