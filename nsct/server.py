# -*- coding: utf-8 -*-
"""
:copyright: (c) 2018 by Neil Jarvis
:licence: MIT, see LICENCE for more details
"""
from __future__ import absolute_import, unicode_literals, print_function

import base64
import logging
import paramiko
from pathlib import Path

from nsct._compat import string_types, integer_types, iteritems, itervalues
from nsct.device import DeviceInterface
from nsct.error import DefinitionError
from nsct.support import supportedServices
from nsct.yaml import YAML_ipv4range, YAML_ipv4address, YAML_ipv6address

logger = logging.getLogger(__name__)


class ServerIpv4DHCP(object):
    def __init__(self, interface, addressRange, leasetime, domain):
        self._interface = interface
        self._addressRange = addressRange
        self._leasetime = leasetime
        self._domain = domain
        self._staticAllocations = {}

        self._domain.addDHCPService('ipv4', self)

    @property
    def addressRange(self):
        return self._addressRange

    def addStaticAllocation(self, mac, ipv4, host, domain):
        self._staticAllocations[mac] = (ipv4, host, domain)

    def compute(self):
        self._domain.reserveAddressRange('ipv4', self._addressRange)

    def generate(self, server):
        raise NotImplementedError('{0.__class__.__name__}:generate() method needs to be implemented'.format(self))

    def __repr__(self):
        return '{0.__class__.__name__}(addressRange={0._addressRange!s}, domain={0._domain!s}, ' \
            'static={0._staticAllocations!r})'.format(self)


class ServerIpv4DHCP_dnsmasq_openwrt(ServerIpv4DHCP):
    def generate(self, server):
        logger.info('Generating DNSMASQ(OpenWrt) config for IPv4 service on {}'.format(server))

        # Fetch DHCP config from server, modify and write back
        try:
            openwrtSSH = paramiko.SSHClient()
            openwrtSSH.get_host_keys().add(server.ssh.host, server.ssh.hostkeyType, paramiko.RSAKey(data=server.ssh.hostkeyValue))
            openwrtSSH.connect(server.ssh.host, port=server.ssh.port, username=server.ssh.user,
                               key_filename=server.ssh.identity, look_for_keys=False)

            try:
                def exec_command(cmd):
                    chan = openwrtSSH.get_transport().open_session()
                    chan.settimeout(None)
                    chan.exec_command(cmd)
                    rc = chan.recv_exit_status()
                    logger.debug('SSH cmd [{}] returned {}'.format(cmd, rc))

                logger.info('Deleting exising static IPv4 DHCP hosts on {}'.format(server))
                exec_command('/bin/ash -c "while uci -q delete dhcp.@host[0]; do :; done"')

                logger.info('Configuring IPv4 DHCP service on interface {} on {}'.format(self._interface, server))
                start = int(self._addressRange.range.first - self._domain.ipv4Subnet.first)
                limit = int(self._addressRange.range.last - self._addressRange.range.first)

                exec_command('uci set dhcp.{}.start={}'.format(self._interface, start))
                exec_command('uci set dhcp.{}.limit={}'.format(self._interface, limit))
                exec_command('uci set dhcp.{}.leasetime={}'.format(self._interface, self._leasetime))

                logger.info('Defining {} static IPv4 DHCP hosts on {}'.format(len(self._staticAllocations), server))
                for mac, (ipv4, host, domain) in iteritems(self._staticAllocations):
                    exec_command('uci add dhcp host')
                    exec_command('uci set dhcp.@host[-1].ip={}'.format(ipv4))
                    exec_command('uci set dhcp.@host[-1].mac={}'.format(mac))
                    exec_command('uci set dhcp.@host[-1].name={}'.format(host))
                exec_command('uci commit dhcp')

            except Exception as e:
                logger.error('Failed to configure IPv4 DHCP service on {}: {}'.format(server, e))
                exec_command('uci revert dhcp')
                raise
            else:
                logger.info('Restarting dnsmasq service on {}'.format(server))
                exec_command('/etc/init.d/dnsmasq restart')

        except Exception as e:
            raise

        finally:
            try:
                openwrtSSH.close()
            except Exception:
                pass


class ServerDNS(object):
    def __init__(self, domains):
        self._domains = domains

    def compute(self):
        pass

    def generate(self, server):
        raise NotImplementedError('{0.__class__.__name__}:generate() method needs to be implemented'.format(self))

    def __repr__(self):
        return '{0.__class__.__name__}()'.format(self)


class ServerDNS_dnsmasq_openwrt(ServerDNS):
    def generate(self, server):
        logger.info('Generating DNSMASQ(OpenWrt) config for DNS service on {}'.format(server))

        hosts = ['127.0.0.1\tlocalhost', '::1\tlocalhost ip6-localhost ip6-loopback',
                 'ff02::1\tip6-allnodes', 'ff02::2\tip6-allrouters']

        for domain in self._domains:
            for offset, deviceInterface in iteritems(domain._ipv4Allocations):
                if isinstance(deviceInterface, DeviceInterface):
                    a = domain._ipv4Subnet[offset]
                    hosts.append('{}\t{}.{}'.format(a, deviceInterface.hostname, domain))
            for offset, deviceInterface in iteritems(domain._ipv6Allocations):
                if isinstance(deviceInterface, DeviceInterface):
                    a = domain._ipv6Subnet[offset]
                    hosts.append('{}\t{}.{}'.format(a, deviceInterface.hostname, domain))
        try:
            openwrtSSH = paramiko.SSHClient()
            openwrtSSH.get_host_keys().add(server.ssh.host, server.ssh.hostkeyType, paramiko.RSAKey(data=server.ssh.hostkeyValue))
            openwrtSSH.connect(server.ssh.host, port=server.ssh.port, username=server.ssh.user,
                               key_filename=server.ssh.identity, look_for_keys=False)

            try:
                def exec_command(cmd):
                    chan = openwrtSSH.get_transport().open_session()
                    chan.settimeout(None)
                    chan.exec_command(cmd)
                    rc = chan.recv_exit_status()
                    logger.debug('SSH cmd [{}] returned {}'.format(cmd, rc))

                openwrtSFTP = paramiko.SFTPClient.from_transport(openwrtSSH.get_transport())

                logger.info('Creating {} entries in /etc/hosts {}'.format(len(hosts), server))
                with openwrtSFTP.open('/etc/hosts', 'w') as f:
                    f.write('\n'.join(hosts))
                    f.write('\n')
            except Exception as e:
                logger.error('Failed to configure /etc/hosts on {}: {}'.format(server, e))
                raise
            else:
                logger.info('Restarting IPv4 dnsmasq service on {}'.format(server))
                exec_command('/etc/init.d/dnsmasq restart')
            finally:
                try:
                    openwrtSFTP.close()
                except Exception:
                    pass

        except Exception as e:
            raise
        finally:
            try:
                openwrtSSH.close()
            except Exception:
                pass


class ServerEthers(object):
    def __init__(self, macs):
        self._macs = macs

    def compute(self):
        pass

    def generate(self, server):
        raise NotImplementedError('{0.__class__.__name__}:generate() method needs to be implemented'.format(self))

    def __repr__(self):
        return '{0.__class__.__name__}()'.format(self)


class ServerEthers_dnsmasq_openwrt(ServerEthers):
    def generate(self, server):
        logger.info('Generating DNSMASQ(OpenWrt) config for ethers service on {}'.format(server))

        try:
            openwrtSSH = paramiko.SSHClient()
            openwrtSSH.get_host_keys().add(server.ssh.host, server.ssh.hostkeyType, paramiko.RSAKey(data=server.ssh.hostkeyValue))
            openwrtSSH.connect(server.ssh.host, port=server.ssh.port, username=server.ssh.user,
                               key_filename=server.ssh.identity, look_for_keys=False)

            try:
                def exec_command(cmd):
                    chan = openwrtSSH.get_transport().open_session()
                    chan.settimeout(None)
                    chan.exec_command(cmd)
                    rc = chan.recv_exit_status()
                    logger.debug('SSH cmd [{}] returned {}'.format(cmd, rc))

                openwrtSFTP = paramiko.SFTPClient.from_transport(openwrtSSH.get_transport())

                logger.info('Creating {} entries in /etc/ethers on {}'.format(len(self._macs), server))
                with openwrtSFTP.open('/etc/ethers', 'w') as f:
                    for mac, deviceInterface in iteritems(self._macs):
                        f.write('{} {}\n'.format(mac, deviceInterface.hostname))
            except Exception as e:
                logger.error('Failed to configure /etc/ethers on {}: {}'.format(server, e))
                raise
            else:
                logger.info('Restarting IPv4 dnsmasq service on {}'.format(server))
                exec_command('/etc/init.d/dnsmasq restart')
            finally:
                try:
                    openwrtSFTP.close()
                except Exception:
                    pass

        except Exception as e:
            raise
        finally:
            try:
                openwrtSSH.close()
            except Exception:
                pass


class ServerSmokeping(object):
    def __init__(self, configName, domains):
        self._configName = configName
        self._domains = domains

    def compute(self):
        pass

    def generate(self, server):
        raise NotImplementedError('{0.__class__.__name__}:generate() method needs to be implemented'.format(self))

    def __repr__(self):
        return '{0.__class__.__name__}()'.format(self)


class ServerSmokeping_docker(ServerSmokeping):
    def generate(self, server):
        logger.info('Generating Docker config for smokeping service on {}'.format(server))

        try:
            openwrtSSH = paramiko.SSHClient()
            openwrtSSH.get_host_keys().add(server.ssh.host, server.ssh.hostkeyType, paramiko.RSAKey(data=server.ssh.hostkeyValue))
            openwrtSSH.connect(server.ssh.host, port=server.ssh.port, username=server.ssh.user,
                               key_filename=server.ssh.identity, look_for_keys=False)

            try:
                def exec_command(cmd):
                    chan = openwrtSSH.get_transport().open_session()
                    chan.settimeout(None)
                    chan.exec_command(cmd)
                    rc = chan.recv_exit_status()
                    logger.debug('SSH cmd [{}] returned {}'.format(cmd, rc))

                openwrtSFTP = paramiko.SFTPClient.from_transport(openwrtSSH.get_transport())

                logger.info('Creating {} on {}'.format(self._configName, server))
                with openwrtSFTP.open(self._configName, 'w') as f:
                    def _smokepingTarget(*args):
                        return '.'.join([str(a) for a in args]).replace('.', '_').replace('-', '_')

                    f.write('+ Devices\n\n')
                    f.write('menu = Devices\n')
                    f.write('title = Devices\n')
                    f.write('\n')

                    for domain in self._domains:
                        if len(domain._ipv4Allocations) == 0:
                            continue

                        f.write('++ {}\n\n'.format(_smokepingTarget(domain)))
                        f.write('menu = {}\n'.format(domain))
                        f.write('title = Domain {}\n'.format(domain))
                        f.write('host = {}\n'.format(' '.join(['/Devices/{}/{}'.
                                                               format(_smokepingTarget(domain),
                                                                      _smokepingTarget(h.hostname, domain))
                                                               for h in itervalues(domain._ipv4Allocations)
                                                               if isinstance(h, DeviceInterface)])))
                        f.write('\n')

                        for offset, deviceInterface in iteritems(domain._ipv4Allocations):
                            if isinstance(deviceInterface, DeviceInterface):
                                a = domain._ipv4Subnet[offset]
                                f.write('+++ {}\n\n'.format(_smokepingTarget(deviceInterface.hostname, domain)))
                                f.write('menu = {}\n'.format(deviceInterface.hostname))
                                f.write('title = {}.{}\n'.format(deviceInterface.hostname, domain))
                                f.write('host = {}\n'.format(a))
                                f.write('\n')
            except Exception as e:
                logger.error('Failed to configure {} on {}: {}'.format(self._configName, server, e))
                raise
            else:
                logger.info('Restarting smokeping service on {}'.format(server))
                exec_command('sudo systemctl restart docker-smokeping')
            finally:
                try:
                    openwrtSFTP.close()
                except Exception:
                    pass

        except Exception as e:
            raise
        finally:
            try:
                openwrtSSH.close()
            except Exception:
                pass


class ServerSSH(object):
    def __init__(self, host, port, user, identity, hostkeyType, hostkeyValue):
        self._host = host
        self._port = port
        self._user = user
        self._identity = identity
        self._hostkeyType = hostkeyType
        self._hostkeyValue = hostkeyValue

    @property
    def host(self):
        return str(self._host)

    @property
    def port(self):
        return self._port

    @property
    def user(self):
        return self._user

    @property
    def identity(self):
        return self._identity

    @property
    def hostkeyType(self):
        return self._hostkeyType

    @property
    def hostkeyValue(self):
        return base64.b64decode(self._hostkeyValue)


class Server(object):
    def __init__(self, name, fragment, definition, ssh, services):
        self._name = name
        self._fragment = fragment
        self._definition = definition
        self._ssh = ssh
        self._services = services

    @property
    def ssh(self):
        return self._ssh

    def __str__(self):
        return self._name

    def __repr__(self):
        return '{0.__class__.__name__}({0._name!r}, host={0._host!r}, sshUser={0._sshUser!r}, ' \
            'sshIdentity={0._sshIdentity!r}, services={0._services!r})'.format(self)

    def compute(self):
        for serviceType, service in iteritems(self._services):
            service.compute()

    def generate(self, action):
        if action in self._services:
            self._services[action].generate(self)

    @staticmethod
    def parse(name, fragment, definition):
        logger.debug('Parsing server at {!r}'.format(fragment))

        sshHost = fragment.getMappingValue('ssh.host', (YAML_ipv4address, YAML_ipv6address), required=True)
        sshPort = fragment.getMappingValue('ssh.port', integer_types, required=False, default=22)
        sshUser = fragment.getMappingValue('ssh.user', string_types, required=True)
        sshIdentity, sshIdentityFragment = fragment.getMappingValue('ssh.identity', string_types, required=True,
                                                                    returnValueFragment=True)
        sshIdentityPath = Path(sshIdentity).expanduser().resolve()
        try:
            if not sshIdentityPath.is_file():
                sshIdentityFragment.raiseError('ssh.identity \'{}\' (path {}) is not a file'.format(sshIdentity,
                                                                                                    sshIdentityPath))
            with sshIdentityPath.open():
                pass
        except DefinitionError:
            raise
        except Exception as e:
            sshIdentityFragment.raiseError('ssh.identity \'{}\' (path: {}) cannot be opened for reading: {}'.
                                           format(sshIdentity, sshIdentityPath, e))
        sshIdentity = str(sshIdentityPath)
        sshHostkey, sshHostkeyFragment = fragment.getMappingValue('ssh.host-key', string_types, required=True,
                                                                  returnValueFragment=True)
        sshHostkeyType, sshHostkeyValue = sshHostkey.split(' ', 1)

        services = dict()
        for serviceType in supportedServices.keys():
            service, serviceFragment = fragment.getMappingValue('services.%s' % serviceType, dict,
                                                                required=False, returnValueFragment=True)
            if service:
                serviceInstance = None
                serviceTypeType, serviceTypeTypeFragment = serviceFragment.getMappingValue('type', string_types,
                                                                                           required=True, returnValueFragment=True)
                if serviceTypeType not in supportedServices[serviceType]:
                    serviceTypeTypeFragment.raiseError('Unsupported service \'{}\' type \'{}\'.  Supported types: {}'.
                                                       format(serviceType, serviceTypeType,
                                                              ', '.join(supportedServices[serviceType])))
                if serviceType == 'ipv4-dhcp':
                    dhcpIpv4Interface = serviceFragment.getMappingValue('interface', string_types, required=True)
                    dhcpIpv4Leasetime = serviceFragment.getMappingValue('leasetime', string_types, required=False, default='12h')
                    dhcpIpv4Domain, dhcpIpv4DomainFragment = serviceFragment.getMappingValue('domain', string_types,
                                                                                             required=True,
                                                                                             returnValueFragment=True)
                    if dhcpIpv4Domain not in definition.domains:
                        dhcpIpv4DomainFragment.raiseError('domain \'{}\' is not a known domain'.format(dhcpIpv4Domain))
                    else:
                        dhcpIpv4Domain = definition.domains[dhcpIpv4Domain]

                    dhcpIpv4Range, dhcpIpv4RangeFragment = serviceFragment.getMappingValue('range', YAML_ipv4range,
                                                                                           required=True,
                                                                                           returnValueFragment=True)
                    if dhcpIpv4Domain.ipv4Subnet:
                        if dhcpIpv4Range.range.first not in dhcpIpv4Domain.ipv4Subnet:
                            dhcpIpv4RangeFragment.raiseError('Range start not inside domain\'s ipv4 subnet {}'.
                                                             format(dhcpIpv4Domain.ipv4Subnet))
                        if dhcpIpv4Range.range.last not in dhcpIpv4Domain.ipv4Subnet:
                            dhcpIpv4RangeFragment.raiseError('Range stop not inside domain\'s ipv4 subnet {}'.
                                                             format(dhcpIpv4Domain.ipv4Subnet))
                    else:
                        dhcpIpv4RangeFragment.raiseError('No ipv4 subnet defined in domain')

                    cls = globals()['ServerIpv4DHCP_{}'.format(serviceTypeType.replace('.', '_').replace('-', '_'))]
                    serviceInstance = cls(dhcpIpv4Interface, dhcpIpv4Range, dhcpIpv4Leasetime, dhcpIpv4Domain)

                if serviceType == 'dns':
                    dnsDomains, dnsDomainsFragment = serviceFragment.getMappingValue('domains', list,
                                                                                     required=True,
                                                                                     returnValueFragment=True)
                    dnsDomains = []
                    for i, dnsDomainFragment in dnsDomainsFragment.getElements():
                        dnsDomain = dnsDomainFragment.getValue(string_types, source='for {} dns domain')
                        if dnsDomain not in definition.domains:
                            dnsDomainFragment.raiseError('Unknown domain \'{}\''.format(dnsDomain))
                        dnsDomains.append(definition.domains[dnsDomain])

                    cls = globals()['ServerDNS_{}'.format(serviceTypeType.replace('.', '_').replace('-', '_'))]
                    serviceInstance = cls(dnsDomains)

                if serviceType == 'ethers':
                    cls = globals()['ServerEthers_{}'.format(serviceTypeType.replace('.', '_').replace('-', '_'))]
                    serviceInstance = cls(definition.macs)

                if serviceType == 'smokeping':
                    configName = serviceFragment.getMappingValue('config-name', string_types, required=True)
                    smokepingDomains, smokepingDomainsFragment = serviceFragment.getMappingValue('domains', list,
                                                                                     required=True,
                                                                                     returnValueFragment=True)
                    smokepingDomains = []
                    for i, smokepingDomainFragment in smokepingDomainsFragment.getElements():
                        smokepingDomain = smokepingDomainFragment.getValue(string_types, source='for {} smokeping domain')
                        if smokepingDomain not in definition.domains:
                            smokepingDomainFragment.raiseError('Unknown domain \'{}\''.format(smokepingDomain))
                        smokepingDomains.append(definition.domains[smokepingDomain])

                    cls = globals()['ServerSmokeping_{}'.format(serviceTypeType.replace('.', '_').replace('-', '_'))]
                    serviceInstance = cls(configName, smokepingDomains)

                # Record service
                if serviceInstance:
                    services[serviceType] = serviceInstance
                else:
                    logger.warning('Service {} does not have a valid service {}'.format(name, serviceType))

        return Server(name, fragment, definition,
                      ServerSSH(sshHost, sshPort, sshUser, sshIdentity, sshHostkeyType, sshHostkeyValue),
                      services)
