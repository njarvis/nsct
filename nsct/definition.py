# -*- coding: utf-8 -*-
"""
:copyright: (c) 2018 by Neil Jarvis
:licence: MIT, see LICENCE for more details
"""
from __future__ import absolute_import, unicode_literals, print_function

import logging

from nsct._compat import string_types, iteritems
from nsct.domain import Domain
from nsct.device import Device
from nsct.server import Server

logger = logging.getLogger(__name__)


class Definition(object):
    def __init__(self, nameserver):
        self._nameserver = nameserver
        self._domains = {}
        self._devices = {}
        self._servers = {}

        self._macs = {}  # Derived from devices

    @property
    def domains(self):
        return self._domains

    @property
    def devices(self):
        return self._devices

    @property
    def servers(self):
        return self._servers

    @property
    def macs(self):
        return self._macs

    def addDomain(self, name, domain):
        if len(self._domains) == 0:
            # First domain - this is the global domain by convention
            domain.globalDomain = True

        self._domains[name] = domain

    def addDevice(self, name, device):
        self._devices[name] = device

    def addServer(self, name, server):
        self._servers[name] = server

    def __repr__(self):
        return '{0.__class__.__name__}(nameserver={0._nameserver!r}, domains={0._domains!r}, ' \
            'devices={0._devices!r}, macs={0._macs!r})'.format(self)

    def compute(self):
        logger.info('Computing final definition state')

        for serverName, server in iteritems(self._servers):
            server.compute()

        for deviceName, device in iteritems(self._devices):
            device.compute()

        for domainName, domain in iteritems(self._domains):
            domain.compute()

    def generate(self, action):
        logger.info('Generating for action: {}'.format(action))

        for serverName, server in iteritems(self._servers):
            server.generate(action)

    @staticmethod
    def parse(fragment):
        logger.info('Starting parse of {}'.format(fragment))

        if not fragment.ymlIsInstance(dict):
            fragment.raiseError('Expecting dict at top level of definition')

        definition = Definition(fragment.getMappingValue('nameserver', string_types, required=True))

        #
        # Parse domains
        #
        for domainName, domainFragment in fragment.getMappingItems('domains', required=False):
            definition.addDomain(domainName, Domain.parse(domainName, domainFragment, definition))

        #
        # Parse devices
        #
        for deviceName, deviceFragment in fragment.getMappingItems('devices', required=False):
            definition.addDevice(deviceName, Device.parse(deviceName, deviceFragment, definition))

        #
        # Parse servers
        #
        for serverName, serverFragment in fragment.getMappingItems('servers', required=False):
            definition.addServer(serverName, Server.parse(serverName, serverFragment, definition))

        logger.info('Completed parse of {}'.format(fragment))

        return definition
