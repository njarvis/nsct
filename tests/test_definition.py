# -*- coding: utf-8 -*-
"""
test_nsct
----------------------------------

Tests for `nsct` module.
"""
from functools import wraps
from inspect import getdoc
from os.path import dirname, realpath
import pytest

from nsct.yaml import Fragment, Location, DefinitionError
from nsct.definition import Definition


def yamlDoc(f):
    __f_name__ = f.__name__
    __f_doc__ = getdoc(f)
    assert __f_doc__ is not None, '@yamlDoc function must have YAML in document string'

    __f_doc__ = __f_doc__.strip().replace('%testdir%', dirname(realpath(__file__)))

    @wraps(f)
    def new_f(*args, **kwargs):
        kwargs['fname'] = __f_name__
        kwargs['fdoc'] = __f_doc__

        return f(*args, **kwargs)
    return new_f


class TestNsct(object):
    @classmethod
    def set_up(self):
        pass

    def _bad_definition(self, fname, fdoc, location, error):
        fragment = Fragment(Location(fname), ymlstr=fdoc)
        with pytest.raises(DefinitionError, match=r'{}:{}:{}: {}'.format(fname, location[0], location[1], error)):
            Definition.parse(fragment)

    def _good_definition(self, fname, fdoc):
        return Definition.parse(Fragment(Location(fname), ymlstr=fdoc))

    @yamlDoc
    def test_blank(self, fname=None, fdoc=None):
        """
        """
        self._bad_definition(fname, fdoc, (1, 1), 'Expecting dict at top level of definition')

    @yamlDoc
    def test_not_dict(self, fname=None, fdoc=None):
        """
- list
- not
- a dict
        """
        self._bad_definition(fname, fdoc, (1, 1), 'Expecting dict at top level of definition')

    @yamlDoc
    def test_no_nameserver(self, fname=None, fdoc=None):
        """
{}
        """
        self._bad_definition(fname, fdoc, (1, 1), 'Missing required key \'nameserver\'')

    @yamlDoc
    def test_bad_nameserver(self, fname=None, fdoc=None):
        """
nameserver: []
        """
        self._bad_definition(fname, fdoc, (1, 13),
                             r'\[nameserver\] Value of type .* for key nameserver is not of expected type str')

    @yamlDoc
    def test_emptyish(self, fname=None, fdoc=None):
        """
nameserver: test
domains: {}
devices: {}
servers: {}
        """
        definition = self._good_definition(fname, fdoc)
        assert len(definition.domains) == 0
        assert len(definition.devices) == 0
        assert len(definition.servers) == 0

        assert len(definition.macs) == 0

    @yamlDoc
    def test_empty(self, fname=None, fdoc=None):
        """
nameserver: test
        """
        definition = self._good_definition(fname, fdoc)
        assert len(definition.domains) == 0
        assert len(definition.devices) == 0
        assert len(definition.servers) == 0

        assert len(definition.macs) == 0

    @yamlDoc
    def test_good_domain(self, fname=None, fdoc=None):
        """
nameserver: test
domains:
  a.com:
    ipv4-subnet: !ipv4network 95.172.226.216/29
    ipv6-subnet: !ipv6network 2001:470:1f1d:cc9::/64
    records:
      a:
        all-0: !a 95.172.226.216
      aaaa:
        all-0: !aaaa '2001:470:1f1d:cc9::'
      mx:
        '@': !mx 0/a.com.
      cname:
        # Services
        a1: !cname a2.a.com.
      txt:
        _keybase: !txt 'keybase-site-verification=blah'
        """
        definition = self._good_definition(fname, fdoc)
        assert len(definition.domains) == 1
        assert len(definition.devices) == 0
        assert len(definition.servers) == 0

        assert len(definition.macs) == 0

    @yamlDoc
    def test_good_device(self, fname=None, fdoc=None):
        """
nameserver: test
domains:
  a.com:
    ipv4-subnet: !ipv4network 95.172.226.216/29
    ipv6-subnet: !ipv6network 2001:470:1f1d:cc9::/64
    records:
      a:
        all-0: !a 95.172.226.216
      aaaa:
        all-0: !aaaa '2001:470:1f1d:cc9::'
      mx:
        '@': !mx 0/a.com.
      cname:
        # Services
        a1: !cname a2.a.com.
      txt:
        _keybase: !txt 'keybase-site-verification=blah'
devices:
  dev1:
    lan:
      mac: !mac 00:01:02:03:04:05
      ipv4: !allocation a.com/1
      ipv6: !allocation a.com/1
        """
        definition = self._good_definition(fname, fdoc)
        assert len(definition.domains) == 1
        assert len(definition.devices) == 1
        assert len(definition.servers) == 0

        assert len(definition.macs) == 1

    @yamlDoc
    def test_good_server(self, fname=None, fdoc=None):
        """
nameserver: test
domains:
  a.com:
    ipv4-subnet: !ipv4network 95.172.226.216/29
    ipv6-subnet: !ipv6network 2001:470:1f1d:cc9::/64
    records:
      a:
        all-0: !a 95.172.226.216
      aaaa:
        all-0: !aaaa '2001:470:1f1d:cc9::'
      mx:
        '@': !mx 0/a.com.
      cname:
        # Services
        a1: !cname a2.a.com.
      txt:
        _keybase: !txt 'keybase-site-verification=blah'
devices:
  dev1:
    lan:
      mac: !mac 00:01:02:03:04:05
      ipv4: !allocation a.com/1
      ipv6: !allocation a.com/1
servers:
  test:
    ssh:
      host: !ipv4address 10.10.10.1
      user: user
      identity: %testdir%/test_id_rsa
      host-key: ssh-rsa AAAAxxx
        """
        definition = self._good_definition(fname, fdoc)
        assert len(definition.domains) == 1
        assert len(definition.devices) == 1
        assert len(definition.servers) == 1

        assert len(definition.macs) == 1

        # Make sure __repr__ and __str__ work
        str(definition)
        repr(definition)

    @classmethod
    def tear_down(self):
        pass
