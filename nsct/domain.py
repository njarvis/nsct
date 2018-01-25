# -*- coding: utf-8 -*-
"""
:copyright: (c) 2018 by Neil Jarvis
:licence: MIT, see LICENCE for more details
"""
from __future__ import absolute_import, unicode_literals, print_function

from collections import OrderedDict, defaultdict
import logging

from nsct.support import supportedRecords
from nsct.yaml import (YAML_ipv4network, YAML_ipv6network, YAML_mx, YAML_a, YAML_aaaa, YAML_cname, YAML_txt)  # noqa

logger = logging.getLogger(__name__)


class Domain(object):
    def __init__(self, name, fragment, definition, ipv4Subnet, ipv6Subnet, records):
        self._name = name
        self._fragment = fragment
        self._globalDomain = False
        self._definition = definition

        self._ipv4Subnet = ipv4Subnet
        self._ipv4Allocations = dict()
        self._ipv6Subnet = ipv6Subnet
        self._ipv6Allocations = dict()
        self._records = records if records is not None else OrderedDict([(t, defaultdict(set)) for t in supportedRecords])

        self._ipv4DHCPServices = []
        self._ipv6DHCPServices = []

    @property
    def globalDomain(self):
        return self._globalDomain

    @globalDomain.setter
    def globalDomain(self, value):
        assert isinstance(value, bool)
        self._globalDomain = value

    @property
    def ipv4Subnet(self):
        return self._ipv4Subnet

    def addDHCPService(self, version, service):
        services = getattr(self, '_{}DHCPServices'.format(version))
        services.append(service)

    def reserveAddressRange(self, version, addressRange):
        logger.debug('Reserving {} DHCP address range {} in domain {}'.format(version, addressRange, self))

        subnet = getattr(self, '_{}Subnet'.format(version))
        allocations = getattr(self, '_{}Allocations'.format(version))
        record = 'a' if version == 'ipv4' else 'aaaa'

        for a in addressRange.range:
            offset = int(a - subnet.first)
            allocations[offset] = 'DHCP allocation range {}'.format(addressRange)
            self._records[record]['dhcp-{}.{}'.format(offset, self._name)] = a

    def allocate(self, fragment, version, allocation, deviceInterface):
        deviceInterfaceName = deviceInterface.hostname

        subnet = getattr(self, '_{}Subnet'.format(version))
        allocations = getattr(self, '_{}Allocations'.format(version))
        services = getattr(self, '_{}DHCPServices'.format(version))

        def _subnetAllocate(offset, unique=True):
            if not unique or offset not in allocations:
                try:
                    address = subnet[offset]
                except IndexError as e:
                    fragment.raiseError('Offset {} in {} subnet of domain {} is out of valid range 0..{}'.
                                        format(offset, version, self, len(subnet) - 1))
                else:
                    if unique:
                        allocations[offset] = deviceInterface
                    return address
            else:
                if isinstance(allocations[offset], str):
                    fragment.raiseError('Address {} in {} subnet of domain {} reserved for {!s}'.
                                        format(subnet[offset], version, self, allocations[offset]))
                else:
                    fragment.raiseError('Address {} in {} subnet of domain {} allocated to device interface {!s}'.
                                        format(subnet[offset], version, self, allocations[offset]))

        if allocation.isEUIStrategy:
            if version == 'ipv6':
                if self._ipv6Subnet:
                    if deviceInterface.mac:
                        eui = deviceInterface.mac.ipv6(self._ipv6Subnet.first)
                        offset = int(eui - self._ipv6Subnet.first)
                        address = _subnetAllocate(offset)
                    else:
                        fragment.raiseError('No MAC address defined on device interface {} to generate EUI ipv6 address'.
                                            format(deviceInterface))
                else:
                    fragment.raiseError('No ipv6 subnet defined on domain {}'.format(self))
            else:
                fragment.raiseError('Cannot allocate EUI address from an {} subnet'.format(version))
            dhcp = False
        elif allocation.isAliasStrategy:
            if subnet:
                address = _subnetAllocate(allocation.offset, unique=False)
            else:
                fragment.raiseError('No subnet defined on domain {}'.format(version, self))
            dhcp = False
        elif allocation.isOffsetStrategy:
            if subnet:
                address = _subnetAllocate(allocation.offset)
            else:
                fragment.raiseError('No {} subnet defined on domain {}'.format(version, self))
            dhcp = deviceInterface.mac is not None
        else:
            fragment.raiseError('Unknown allocation strategy type {}'.format(allocation.strategyType))

        if dhcp:
            for service in services:
                service.addStaticAllocation(deviceInterface.mac, address, deviceInterfaceName, self._name)

        if version == 'ipv4':
            recordType = 'a'
        else:
            recordType = 'aaaa'
        self._records[recordType][deviceInterfaceName].add(address)

        return address

    def __str__(self):
        return self._name

    def __repr__(self):
        return '{0.__class__.__name__}({0._name!r}, globalDomain={0._globalDomain!r}, ipv4Subnet={0._ipv4Subnet!r}, ' \
            'ipv6Subnet={0._ipv6Subnet!r}, records={0._records!r})'.format(self)

    def compute(self):
        pass

    @staticmethod
    def parse(name, fragment, definition):
        logger.debug('Parsing domain at {!r}'.format(fragment))

        ipv4Subnet = fragment.getMappingValue('ipv4-subnet', YAML_ipv4network, required=False)
        ipv6Subnet = fragment.getMappingValue('ipv6-subnet', YAML_ipv6network, required=False)

        records = OrderedDict([(t, defaultdict(set)) for t in supportedRecords])
        for recordType in records.keys():
            for recordName, recordFragment in fragment.getMappingItems('records.%s' % recordType,
                                                                       required=False):

                records[recordType][recordName].add(recordFragment.getValue(globals()['YAML_%s' % recordType],
                                                                            source='for %s record' % recordType))

        return Domain(name, fragment, definition, ipv4Subnet, ipv6Subnet, records)
