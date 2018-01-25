# -*- coding: utf-8 -*-
"""
:copyright: (c) 2018 by Neil Jarvis
:licence: MIT, see LICENCE for more details
"""
from __future__ import absolute_import, unicode_literals, print_function

from collections import OrderedDict
import logging

from nsct._compat import iteritems
from nsct.yaml import YAML_allocation, YAML_mac
from nsct.util import nth

logger = logging.getLogger(__name__)


class DeviceInterface(object):
    def __init__(self, name, fragment, definition, device, mac=None):
        self._name = name
        self._fragment = fragment
        self._primary = False
        self._definition = definition
        self._device = device
        self._mac = mac
        self._ipv4 = []
        self._ipv6 = []

    @property
    def primary(self):
        return self._primary

    @primary.setter
    def primary(self, value):
        assert isinstance(value, bool)
        self._primary = value

    @property
    def mac(self):
        return self._mac

    @property
    def device(self):
        return self._device

    def addAllocation(self, version, allocation, allocationFragment):
        if version == 'ipv4':
            self._ipv4.append((allocation, allocationFragment))
        elif version == 'ipv6':
            self._ipv6.append((allocation, allocationFragment))

    @property
    def hostname(self, sep='-'):
        if self._primary:
            return str(self._device)
        else:
            return str(self._device) + sep + self._name

    def __str__(self):
        return str(self._device) + '/' + self._name

    def __repr__(self):
        return '{0.__class__.__name__}({0._name!r}, primary={0._primary!r}, ' \
            'mac={0._mac!r}, ipv4={0._ipv4!r}, ipv6={0._ipv6!r})'.format(self)

    def compute(self):
        for (allocation, allocationFragment) in self._ipv4:
            address = self._definition.domains[allocation.domain].allocate(allocationFragment, 'ipv4', allocation, self)
            logger.debug('Allocated ipv4 addresses {} for {} from {}'.format(address, self, allocation.domain))

        for (allocation, allocationFragment) in self._ipv6:
            address = self._definition.domains[allocation.domain].allocate(allocationFragment, 'ipv6', allocation, self)
            logger.debug('Allocated ipv6 addresses {} for {} from {}'.format(address, self, allocation.domain))

    @staticmethod
    def parse(name, fragment, definition, device, primary):
        logger.debug('Parsing device at {!r}'.format(fragment))

        def _parseAllocations(version, deviceInterface):
            a, f = fragment.getMappingValue(version, (YAML_allocation, list), required=False, returnValueFragment=True)
            if a is not None:
                if isinstance(a, list):
                    es = f.getElements()
                else:
                    es = [(0, f)]

                for i, f in es:
                    a = f.getValue(YAML_allocation, source='for {} allocation'.format(version))
                    if a.domain not in definition.domains:
                        f.raiseError('Unknown domain \'{}\' in {} allocation'.format(a.domain, nth(i + 1)))
                    else:
                        deviceInterface.addAllocation(version, a, f)

        mac, macFragment = fragment.getMappingValue('mac', YAML_mac, required=False, returnValueFragment=True)
        deviceInterface = DeviceInterface(name, fragment, definition, device, mac)
        deviceInterface.primary = primary

        if mac:
            if mac not in definition.macs:
                definition.macs[mac] = deviceInterface
            else:
                macFragment.raiseError('MAC address {} already defined for device interface {}'.format(mac, definition.macs[mac]))

        _parseAllocations('ipv4', deviceInterface)
        _parseAllocations('ipv6', deviceInterface)

        return deviceInterface


class Device(object):
    def __init__(self, name, fragment, definition):
        self._name = name
        self._fragment = fragment
        self._definition = definition
        self._interfaces = OrderedDict()

    def addInterface(self, name, deviceInterface):
        self._interfaces[name] = deviceInterface

    def __str__(self):
        return self._name

    def __repr__(self):
        return '{0.__class__.__name__}({0._name!r}, interfaces={0._interfaces!r})'.format(self)

    def compute(self):
        for deviceInterfaceName, deviceInterface in iteritems(self._interfaces):
            deviceInterface.compute()

    @staticmethod
    def parse(name, fragment, definition):
        device = Device(name, fragment, definition)

        primary = True
        for interfaceName, interfaceFragment in fragment.getItems():
            device.addInterface(interfaceName, DeviceInterface.parse(interfaceName, interfaceFragment, definition, device, primary))
            primary = False

        return device
