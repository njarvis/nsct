# -*- coding: utf-8 -*-
"""
:copyright: (c) 2018 by Neil Jarvis
:licence: MIT, see LICENCE for more details
"""
from __future__ import absolute_import, unicode_literals, print_function

import re
from ruamel.yaml import YAML, yaml_object
from ruamel.yaml.error import YAMLError, MarkedYAMLError
from netaddr import IPNetwork, IPAddress, IPRange, EUI, mac_unix_expanded

from nsct._compat import iteritems, string_types
from nsct.error import DefinitionError

yaml = YAML()
yaml.indent(sequence=4, offset=2)


class Scalar_mx(object):
    def __init__(self, priority, host):
        try:
            priority = int(priority)
        except Exception as e:
            raise TypeError('invalid MX priority: {}'.format(e))

        if not re.match(r'^(((?!-))(xn--)?[a-z0-9-_]{0,61}[a-z0-9]{1,1}\.)*(xn--)?'
                        '([a-z0-9\-]{1,61}|[a-z0-9-]{1,30}\.[a-z]{2,})(\.)?$', host):
            raise TypeError('invalid MX host')

        self._priority = priority
        self._host = host

    @property
    def priority(self):
        return self._priority

    @property
    def host(self):
        return self._host

    def __repr__(self):
        return '{}/{}'.format(self._priority, self._host)


class Scalar_cname(object):
    def __init__(self, host):
        if not isinstance(host, string_types):
            raise TypeError('invalid CNAME string')
        if not re.match(r'^(((?!-))(xn--)?[a-z0-9-_]{0,61}[a-z0-9]{1,1}\.)*(xn--)?'
                        '([a-z0-9\-]{1,61}|[a-z0-9-]{1,30}\.[a-z]{2,})(\.)?$', host):
            raise TypeError('invalid CNAME host')
        self._host = host

    @property
    def host(self):
        return self._host

    def __repr__(self):
        return self._host


class Scalar_txt(object):
    def __init__(self, txt):
        if not isinstance(txt, string_types):
            raise TypeError('invalid TXT string')
        self._txt = txt

    @property
    def txt(self):
        return self._txt

    def __repr__(self):
        return self._txt


class Scalar_ipv4range(object):
    def __init__(self, start, stop):
        try:
            start = IPAddress(start, version=4)
        except Exception as e:
            raise TypeError('IPv4 range start must be an IPv4 address: {}'.format(e))
        try:
            stop = IPAddress(stop, version=4)
        except Exception as e:
            raise TypeError('IPv4 range stop must be an IPv4 address: {}'.format(e))

        self._start = start
        self._stop = stop

        if start > stop:
            self._range = IPRange(stop, start)
        else:
            self._range = IPRange(start, stop)

    @property
    def range(self):
        return self._range

    def __repr__(self):
        return '{}-{}'.format(self._start, self._stop)


class Scalar_allocation(object):
    def __init__(self, domain, strategy):
        self._domain = domain
        self._strategy = strategy

        self._strategyType = None
        self._offset = None

        if strategy == 'EUI':
            self._strategyType = 'EUI'
        elif strategy.startswith('ALIAS/'):
            try:
                self._offset = int(strategy.split('/', 1)[1])
            except Exception as e:
                raise TypeError('Allocation strategy ALIAS requires an integer offset: {}'.format(e))
            else:
                self._strategyType = 'ALIAS'
        else:
            # Cope with optional OFFSET/n syntax
            if strategy.startswith('OFFSET/'):
                strategy = strategy.split('/', 1)[1]
            try:
                self._offset = int(strategy)
            except Exception as e:
                raise TypeError('Allocation strategy OFFSET requires an integer offset: {}'.format(e))
            else:
                self._strategyType = 'OFFSET'

    @property
    def domain(self):
        return self._domain

    @property
    def strategyType(self):
        return self._strategyType

    @property
    def isEUIStrategy(self):
        return self._strategyType == 'EUI'

    @property
    def isAliasStrategy(self):
        return self._strategyType == 'ALIAS'

    @property
    def isOffsetStrategy(self):
        return self._strategyType == 'OFFSET'

    @property
    def offset(self):
        assert self.isOffsetStrategy or self.isAliasStrategy
        return self._offset

    def __repr__(self):
        return '{}/{}'.format(self._domain, self._strategy)


class YAML_scalar(object):
    def __init__(self, value, style=None):
        self._value = value
        self._style = style

    @property
    def scalarValue(self):
        return self._value

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_scalar(cls.yaml_tag,
                                            str(node),
                                            style=node._style)

    def __repr__(self):
        try:
            return str(self._value)
        except Exception:
            return self.__class__.__name__ + '(<NOT-INTIALISED>)'


@yaml_object(yaml)
class YAML_mx(YAML_scalar):
    yaml_tag = u'!mx'

    def __init__(self, priority, host):
        super(YAML_mx, self).__init__(Scalar_mx(priority, host))

    @classmethod
    def from_yaml(cls, constructor, node):
        try:
            return cls(*node.value.split('/'))
        except Exception as e:
            raise MarkedYAMLError(None, None,
                                  "expected a MX scalar, found %s" % e, node.start_mark)


@yaml_object(yaml)
class YAML_cname(YAML_scalar):
    yaml_tag = u'!cname'

    def __init__(self, host):
        super(YAML_cname, self).__init__(Scalar_cname(host))

    @classmethod
    def from_yaml(cls, constructor, node):
        try:
            return cls(node.value)
        except Exception as e:
            raise MarkedYAMLError(None, None,
                                  "expected a CNAME scalar, found %s" % e, node.start_mark)


@yaml_object(yaml)
class YAML_txt(YAML_scalar):
    yaml_tag = u'!txt'

    def __init__(self, txt):
        super(YAML_txt, self).__init__(Scalar_txt(txt), style="'")

    @classmethod
    def from_yaml(cls, constructor, node):
        try:
            return cls(node.value)
        except Exception as e:
            raise MarkedYAMLError(None, None,
                                  "expected a TXT scalar, found %s" % e, node.start_mark)


@yaml_object(yaml)
class YAML_ipv4network(YAML_scalar):
    yaml_tag = u'!ipv4network'

    def __init__(self, network):
        super(YAML_ipv4network, self).__init__(IPNetwork(network, version=4))

    @classmethod
    def from_yaml(cls, constructor, node):
        try:
            return cls(node.value)
        except Exception as e:
            raise MarkedYAMLError(None, None,
                                  "expected an IPv4 network scalar, found %s" % e, node.start_mark)


@yaml_object(yaml)
class YAML_ipv6network(YAML_scalar):
    yaml_tag = u'!ipv6network'

    def __init__(self, network):
        super(YAML_ipv6network, self).__init__(IPNetwork(network, version=6))

    @classmethod
    def from_yaml(cls, constructor, node):
        try:
            return cls(node.value)
        except Exception as e:
            raise MarkedYAMLError(None, None,
                                  "expected an IPv6 network scalar, found %s" % e, node.start_mark)


@yaml_object(yaml)
class YAML_ipv4address(YAML_scalar):
    yaml_tag = u'!ipv4address'

    def __init__(self, address):
        super(YAML_ipv4address, self).__init__(IPAddress(address, version=4))

    @classmethod
    def from_yaml(cls, constructor, node):
        try:
            return cls(node.value)
        except Exception as e:
            raise MarkedYAMLError(None, None,
                                  "expected an IPv4 address scalar, found %s" % e, node.start_mark)


@yaml_object(yaml)
class YAML_ipv6address(YAML_scalar):
    yaml_tag = u'!ipv6address'

    def __init__(self, address):
        super(YAML_ipv6address, self).__init__(IPAddress(address, version=6))

    @classmethod
    def from_yaml(cls, constructor, node):
        try:
            return cls(node.value)
        except Exception as e:
            raise MarkedYAMLError(None, None,
                                  "expected an IPv6 address scalar, found %s" % e, node.start_mark)


@yaml_object(yaml)
class YAML_a(YAML_ipv4address):
    yaml_tag = u'!a'


@yaml_object(yaml)
class YAML_aaaa(YAML_ipv6address):
    yaml_tag = u'!aaaa'


@yaml_object(yaml)
class YAML_mac(YAML_scalar):
    yaml_tag = u'!mac'

    def __init__(self, mac):
        super(YAML_mac, self).__init__(EUI(mac, dialect=mac_unix_expanded))

    @classmethod
    def from_yaml(cls, constructor, node):
        try:
            return cls(node.value)
        except Exception as e:
            raise MarkedYAMLError(None, None,
                                  "expected a MAC address scalar, found %s" % e, node.start_mark)


@yaml_object(yaml)
class YAML_ipv4range(YAML_scalar):
    yaml_tag = u'!ipv4range'

    def __init__(self, start, stop):
        super(YAML_ipv4range, self).__init__(Scalar_ipv4range(start, stop))

    @classmethod
    def from_yaml(cls, constructor, node):
        try:
            return cls(*node.value.split('-'))
        except Exception as e:
            raise MarkedYAMLError(None, None,
                                  "expected an IPv4 address range scalar, found %s" % e, node.start_mark)


@yaml_object(yaml)
class YAML_allocation(YAML_scalar):
    yaml_tag = u'!allocation'

    def __init__(self, domain, strategy):
        super(YAML_allocation, self).__init__(Scalar_allocation(domain, strategy))

    @classmethod
    def from_yaml(cls, constructor, node):
        try:
            return cls(*node.value.split('/', 1))
        except Exception as e:
            raise MarkedYAMLError(None, None,
                                  "expected an allocation scalar, found %s" % e, node.start_mark)


class Location(object):
    def __init__(self, filename, lc=None, section=None):
        assert isinstance(filename, str)
        assert lc is None or isinstance(lc, tuple)
        assert section is None or isinstance(section, list)

        self._filename = filename
        self._lc = lc if lc else (0, 0)
        self._section = section if section else []

    @property
    def filename(self):
        return self._filename

    def subLocation(self, lc, section):
        if isinstance(section, list):
            subSection = self._section + section
        else:
            subSection = self._section + [section]
        return Location(self._filename, lc, subSection)

    def _where(self):
        (line, col) = self._lc
        section = '|'.join(self._section).replace('|[', '[')
        return (line + 1, col + 1, section)

    def __str__(self):
        return '{._filename}'.format(self)

    def __repr__(self):
        line, col, section = self._where()
        if section == '':
            return '{._filename}:{}:{}:'.format(self, line, col)
        else:
            return '{._filename}:{}:{}: [{}]'.format(self, line, col, section)


class Fragment(object):
    def __init__(self, location, **kwargs):
        assert isinstance(location, Location)
        self._location = location
        if 'yml' in kwargs:
            self._yml = kwargs['yml']
        else:
            try:
                if 'ymlstr' in kwargs and kwargs['ymlstr'] is not None:
                    self._yml = yaml.load(kwargs['ymlstr'])
                else:
                    try:
                        with open(self._location.filename, 'r') as s:
                            self._yml = yaml.load(s)
                    except YAMLError:
                        raise
                    except Exception as e:
                        raise DefinitionError('DefinitionError: {}:0:0: {}'.format(self._location.filename, e))
            except YAMLError as e:
                raise DefinitionError('DefinitionError: {}:{}:{}: {}'.format(self._location.filename,
                                                                             e.problem_mark.line + 1,
                                                                             e.problem_mark.column + 1,
                                                                             e.problem))

    def subLocation(self, subLc, subSection):
        return self._location.subLocation(subLc, subSection)

    def dump(self, s):
        yaml.dump(self._yml, s)

    def ymlIsInstance(self, types):
        return isinstance(self._yml, types)

    def raiseError(self, msg):
        raise DefinitionError('DefinitionError: {!r} {}'.format(self, msg))

    def getValue(self, expectedType, source=None):
        if not isinstance(self._yml, expectedType):
            if isinstance(expectedType, (list, tuple)):
                expectedTypeNames = [n.__name__ for n in expectedType]
            else:
                expectedTypeNames = [expectedType.__name__]
            self.raiseError('Value of type {} {}is not of expected type{} {}.'.
                            format(type(self._yml).__name__,
                                   source + ' ' if source else '',
                                   '' if len(expectedTypeNames) == 1 else 's',
                                   ' or '.join(expectedTypeNames)))

        if hasattr(self._yml, 'scalarValue'):
            return self._yml.scalarValue
        else:
            return self._yml

    def getMappingValue(self, key, expectedType, required=True, default=None, returnValueFragment=False):
        assert isinstance(self._yml, dict)

        if '.' in key:
            _k, _rk = key.split('.', 1)
            _d, _f = self.getMappingValue(_k, dict, required=required, default={}, returnValueFragment=True)

            if not _d and not required:
                return (default, None)

            return _f.getMappingValue(_rk, expectedType, required=required, default=default,
                                      returnValueFragment=returnValueFragment)

        if key in self._yml:
            valueYml = self._yml[key]
            valueFragment = Fragment(self.subLocation(self._yml.lc.value(key), key), yml=valueYml)
            value = valueFragment.getValue(expectedType, source='for key {}'.format(key))

            if returnValueFragment:
                return (value, valueFragment)
            else:
                return value
        else:
            if required:
                self.raiseError('Missing required key \'{}\''.format(key))
            else:
                if returnValueFragment:
                    return (default, None)
                else:
                    return default

    def getElements(self, key=[]):
        assert isinstance(self._yml, list)
        return [(i, Fragment(self.subLocation(self._yml.lc.item(i),
                                              key + ['[{}]'.format(i + 1)]),
                             yml=v))
                for i, v in enumerate(self._yml)]

    def getItems(self, key=[]):
        assert isinstance(self._yml, dict)
        return [(str(k), Fragment(self.subLocation(self._yml.lc.value(k),
                                                   key + [str(k)]),
                                  yml=v))
                for k, v in iteritems(self._yml)]

    def getMappingItems(self, key, required=True):
        _rk = key
        _f = self

        while _rk is not None:
            if '.' in _rk:
                _k, _rk = _rk.split('.', 1)
            else:
                _k = _rk
                _rk = None

            _d, _f = _f.getMappingValue(_k, dict, required=required, default={}, returnValueFragment=True)

            # Short cut
            if not _d and not required:
                return []

        return _f.getItems()

    def __str__(self):
        return self._location.__str__()

    def __repr__(self):
        return self._location.__repr__()
