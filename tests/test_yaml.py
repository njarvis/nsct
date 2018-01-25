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

from nsct._compat import StringIO
from nsct.yaml import Fragment, Location, DefinitionError
from nsct.yaml import YAML_mx, YAML_cname, YAML_a, YAML_aaaa, YAML_txt
from nsct.yaml import YAML_ipv4network, YAML_ipv6network, YAML_ipv4address, YAML_ipv6address
from nsct.yaml import YAML_ipv4range, YAML_allocation, YAML_mac


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

    @classmethod
    def tear_down(self):
        pass

    def _bad_yaml(self, fname, fdoc, location, error):
        with pytest.raises(DefinitionError, match=r'{}:{}:{}: {}'.format(fname, location[0], location[1], error)):
            Fragment(Location(fname), ymlstr=fdoc)

    def _good_yaml(self, fname, fdoc):
        f = Fragment(Location(fname), ymlstr=fdoc)
        if fdoc:
            d = StringIO()
            f.dump(d)

            d = d.getvalue().strip()
            if d.endswith('...'):
                d = d[:-3].strip()

            assert d == fdoc.strip()

        return f

    def test_yaml_good_file(self):
        self._good_yaml('/dev/null', None)

    def test_yaml_bad_file_1(self):
        self._bad_yaml('non-existant-file', None, (0, 0), '.* No such file or directory')

    @yamlDoc
    def test_yaml_good_ipv4network(self, fname=None, fdoc=None):
        """
!ipv4network 95.172.226.216/32
        """
        f = self._good_yaml(fname, fdoc)
        assert f.ymlIsInstance(YAML_ipv4network)
        ipv4network = f.getValue(YAML_ipv4network)
        assert str(ipv4network) == '95.172.226.216/32'

    @yamlDoc
    def test_yaml_bad_ipv4network_1(self, fname=None, fdoc=None):
        """
!ipv4network 95.172.226.216/33
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv4 network scalar, found ')

    @yamlDoc
    def test_yaml_bad_ipv4network_2(self, fname=None, fdoc=None):
        """
!ipv4network string
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv4 network scalar, found ')

    @yamlDoc
    def test_yaml_bad_ipv4network_3(self, fname=None, fdoc=None):
        """
!ipv4network [ 1, 2 ]
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv4 network scalar, found ')

    @yamlDoc
    def test_yaml_good_ipv6network(self, fname=None, fdoc=None):
        """
!ipv6network 2001:470:1f1d:cc9::/60
        """
        f = self._good_yaml(fname, fdoc)
        assert f.ymlIsInstance(YAML_ipv6network)
        ipv6network = f.getValue(YAML_ipv6network)
        assert str(ipv6network) == '2001:470:1f1d:cc9::/60'

    @yamlDoc
    def test_yaml_bad_ipv6network_1(self, fname=None, fdoc=None):
        """
!ipv6network 2001:470:1f1d:cc9::/200
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv6 network scalar, found ')

    @yamlDoc
    def test_yaml_bad_ipv6network_2(self, fname=None, fdoc=None):
        """
!ipv6network string
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv6 network scalar, found ')

    @yamlDoc
    def test_yaml_bad_ipv6network_3(self, fname=None, fdoc=None):
        """
!ipv6network [ 1, 2 ]
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv6 network scalar, found ')

    @yamlDoc
    def test_yaml_good_ipv4address(self, fname=None, fdoc=None):
        """
!ipv4address 95.172.226.216
        """
        f = self._good_yaml(fname, fdoc)
        assert f.ymlIsInstance(YAML_ipv4address)
        ipv4address = f.getValue(YAML_ipv4address)
        assert str(ipv4address) == '95.172.226.216'

    @yamlDoc
    def test_yaml_bad_ipv4address_1(self, fname=None, fdoc=None):
        """
!ipv4address fe80::0
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv4 address scalar, found ')

    @yamlDoc
    def test_yaml_bad_ipv4address_2(self, fname=None, fdoc=None):
        """
!ipv4address string
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv4 address scalar, found ')

    @yamlDoc
    def test_yaml_bad_ipv4address_3(self, fname=None, fdoc=None):
        """
!ipv4address [ 1, 2 ]
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv4 address scalar, found ')

    @yamlDoc
    def test_yaml_good_a(self, fname=None, fdoc=None):
        """
!a 95.172.226.216
        """
        f = self._good_yaml(fname, fdoc)
        assert f.ymlIsInstance(YAML_a)
        a = f.getValue(YAML_a)
        assert str(a) == '95.172.226.216'

    @yamlDoc
    def test_yaml_bad_a_1(self, fname=None, fdoc=None):
        """
!a fe80::0
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv4 address scalar, found ')

    @yamlDoc
    def test_yaml_bad_a_2(self, fname=None, fdoc=None):
        """
!a string
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv4 address scalar, found ')

    @yamlDoc
    def test_yaml_bad_a_3(self, fname=None, fdoc=None):
        """
!a [ 1, 2 ]
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv4 address scalar, found ')

    @yamlDoc
    def test_yaml_good_ipv6address(self, fname=None, fdoc=None):
        """
!ipv6address '2001:470:1f1d:cc9::'
        """
        f = self._good_yaml(fname, fdoc)
        assert f.ymlIsInstance(YAML_ipv6address)
        ipv6address = f.getValue(YAML_ipv6address)
        assert str(ipv6address) == '2001:470:1f1d:cc9::'

    @yamlDoc
    def test_yaml_bad_ipv6address_1(self, fname=None, fdoc=None):
        """
!ipv6address 1.2.3.4
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv6 address scalar, found ')

    @yamlDoc
    def test_yaml_bad_ipv6address_2(self, fname=None, fdoc=None):
        """
!ipv6address string
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv6 address scalar, found ')

    @yamlDoc
    def test_yaml_bad_ipv6address_3(self, fname=None, fdoc=None):
        """
!ipv6address [ 1, 2 ]
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv6 address scalar, found ')

    @yamlDoc
    def test_yaml_good_aaaa(self, fname=None, fdoc=None):
        """
!aaaa '2001:470:1f1d:cc9::'
        """
        f = self._good_yaml(fname, fdoc)
        assert f.ymlIsInstance(YAML_aaaa)
        aaaa = f.getValue(YAML_aaaa)
        assert str(aaaa) == '2001:470:1f1d:cc9::'

    @yamlDoc
    def test_yaml_bad_aaaa_1(self, fname=None, fdoc=None):
        """
!aaaa 1.2.3.4
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv6 address scalar, found ')

    @yamlDoc
    def test_yaml_bad_aaaa_2(self, fname=None, fdoc=None):
        """
!aaaa string
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv6 address scalar, found ')

    @yamlDoc
    def test_yaml_bad_aaaa_3(self, fname=None, fdoc=None):
        """
!aaaa [ 1, 2 ]
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv6 address scalar, found ')

    @yamlDoc
    def test_yaml_good_mx(self, fname=None, fdoc=None):
        """
!mx 0/a.com
        """
        f = self._good_yaml(fname, fdoc)
        assert f.ymlIsInstance(YAML_mx)
        mx = f.getValue(YAML_mx)
        assert mx.priority == 0
        assert mx.host == 'a.com'

    @yamlDoc
    def test_yaml_bad_mx_1(self, fname=None, fdoc=None):
        """
!mx no-slash
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected a MX scalar, found ')

    @yamlDoc
    def test_yaml_bad_mx_2(self, fname=None, fdoc=None):
        """
!mx not-an-int/host
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected a MX scalar, found ')

    @yamlDoc
    def test_yaml_bad_mx_3(self, fname=None, fdoc=None):
        """
!mx 0/not a valid hostname
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected a MX scalar, found ')

    @yamlDoc
    def test_yaml_bad_mx_4(self, fname=None, fdoc=None):
        """
!mx [ 1, 2 ]
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected a MX scalar, found ')

    @yamlDoc
    def test_yaml_good_cname(self, fname=None, fdoc=None):
        """
!cname a.com
        """
        f = self._good_yaml(fname, fdoc)
        assert f.ymlIsInstance(YAML_cname)
        cname = f.getValue(YAML_cname)
        assert cname.host == 'a.com'

    @yamlDoc
    def test_yaml_bad_cname_1(self, fname=None, fdoc=None):
        """
!cname [ 1, 2 ]
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected a CNAME scalar, found ')

    @yamlDoc
    def test_yaml_bad_cname_2(self, fname=None, fdoc=None):
        """
!cname not a valid host name
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected a CNAME scalar, found ')

    @yamlDoc
    def test_yaml_good_txt(self, fname=None, fdoc=None):
        """
!txt 'hello there'
        """
        f = self._good_yaml(fname, fdoc)
        assert f.ymlIsInstance(YAML_txt)
        txt = f.getValue(YAML_txt)
        assert txt.txt == 'hello there'

    @yamlDoc
    def test_yaml_bad_txt_1(self, fname=None, fdoc=None):
        """
!txt [ 1, 2 ]
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected a TXT scalar, found ')

    @yamlDoc
    def test_yaml_good_mac(self, fname=None, fdoc=None):
        """
!mac 00:01:02:03:04:05
        """
        f = self._good_yaml(fname, fdoc)
        assert f.ymlIsInstance(YAML_mac)
        mac = f.getValue(YAML_mac)
        assert str(mac) == '00:01:02:03:04:05'

    @yamlDoc
    def test_yaml_bad_mac_1(self, fname=None, fdoc=None):
        """
!mac [ 1, 2 ]
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected a MAC address scalar, found ')

    @yamlDoc
    def test_yaml_bad_mac_2(self, fname=None, fdoc=None):
        """
!mac 00:01
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected a MAC address scalar, found ')

    @yamlDoc
    def test_yaml_good_ipv4range_1(self, fname=None, fdoc=None):
        """
!ipv4range 95.172.226.216-95.172.226.217
        """
        f = self._good_yaml(fname, fdoc)
        assert f.ymlIsInstance(YAML_ipv4range)
        ipv4range = f.getValue(YAML_ipv4range)
        assert str(ipv4range.range) == '95.172.226.216-95.172.226.217'

    @yamlDoc
    def test_yaml_good_ipv4range_2(self, fname=None, fdoc=None):
        """
!ipv4range 95.172.226.217-95.172.226.216
        """
        f = self._good_yaml(fname, fdoc)
        assert f.ymlIsInstance(YAML_ipv4range)
        ipv4range = f.getValue(YAML_ipv4range)
        assert str(ipv4range.range) == '95.172.226.216-95.172.226.217'

    @yamlDoc
    def test_yaml_bad_ipv4range_1a(self, fname=None, fdoc=None):
        """
!ipv4range fe80::0-fe80::1
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv4 address range scalar, found ')

    @yamlDoc
    def test_yaml_bad_ipv4range_1b(self, fname=None, fdoc=None):
        """
!ipv4range 1.2.3.4-fe80::1
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv4 address range scalar, found ')

    @yamlDoc
    def test_yaml_bad_ipv4range_2(self, fname=None, fdoc=None):
        """
!ipv4range string
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv4 address range scalar, found ')

    @yamlDoc
    def test_yaml_bad_ipv4range_3(self, fname=None, fdoc=None):
        """
!ipv4range [ 1, 2 ]
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv4 address range scalar, found ')

    @yamlDoc
    def test_yaml_bad_ipv4range_4(self, fname=None, fdoc=None):
        """
!ipv4range
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an IPv4 address range scalar, found ')

    @yamlDoc
    def test_yaml_good_allocation_1(self, fname=None, fdoc=None):
        """
!allocation domain/1
        """
        f = self._good_yaml(fname, fdoc)
        assert f.ymlIsInstance(YAML_allocation)
        allocation = f.getValue(YAML_allocation)
        assert allocation.domain == 'domain'
        assert allocation.strategyType == 'OFFSET'
        assert allocation.isOffsetStrategy
        assert allocation.offset == 1

    @yamlDoc
    def test_yaml_good_allocation_2(self, fname=None, fdoc=None):
        """
!allocation domain/OFFSET/1
        """
        f = self._good_yaml(fname, fdoc)
        assert f.ymlIsInstance(YAML_allocation)
        allocation = f.getValue(YAML_allocation)
        assert allocation.domain == 'domain'
        assert allocation.strategyType == 'OFFSET'
        assert allocation.isOffsetStrategy
        assert allocation.offset == 1

    @yamlDoc
    def test_yaml_good_allocation_3(self, fname=None, fdoc=None):
        """
!allocation domain/EUI
        """
        f = self._good_yaml(fname, fdoc)
        assert f.ymlIsInstance(YAML_allocation)
        allocation = f.getValue(YAML_allocation)
        assert allocation.domain == 'domain'
        assert allocation.strategyType == 'EUI'
        assert allocation.isEUIStrategy

    @yamlDoc
    def test_yaml_good_allocation_4(self, fname=None, fdoc=None):
        """
!allocation domain/ALIAS/2
        """
        f = self._good_yaml(fname, fdoc)
        assert f.ymlIsInstance(YAML_allocation)
        allocation = f.getValue(YAML_allocation)
        assert allocation.domain == 'domain'
        assert allocation.strategyType == 'ALIAS'
        assert allocation.isAliasStrategy
        assert allocation.offset == 2

    @yamlDoc
    def test_yaml_bad_allocation_1(self, fname=None, fdoc=None):
        """
!allocation fe80::0-fe80::1
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an allocation scalar, found ')

    @yamlDoc
    def test_yaml_bad_allocation_2(self, fname=None, fdoc=None):
        """
!allocation string
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an allocation scalar, found ')

    @yamlDoc
    def test_yaml_bad_allocation_3(self, fname=None, fdoc=None):
        """
!allocation [ 1, 2 ]
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an allocation scalar, found ')

    @yamlDoc
    def test_yaml_bad_allocation_4(self, fname=None, fdoc=None):
        """
!allocation
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an allocation scalar, found ')

    @yamlDoc
    def test_yaml_bad_allocation_5(self, fname=None, fdoc=None):
        """
!allocation domain/not-an-integer
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an allocation scalar, found ')

    @yamlDoc
    def test_yaml_bad_allocation_6(self, fname=None, fdoc=None):
        """
!allocation domain/ALIAS/not-an-integer
        """
        self._bad_yaml(fname, fdoc, (1, 1), 'expected an allocation scalar, found ')
