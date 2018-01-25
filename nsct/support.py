# -*- coding: utf-8 -*-
"""
:copyright: (c) 2018 by Neil Jarvis
:licence: MIT, see LICENCE for more details
"""
from __future__ import absolute_import, unicode_literals, print_function

supportedRecords = ['mx', 'cname', 'txt', 'a', 'aaaa']
supportedServices = {'ipv4-dhcp': ['dnsmasq.openwrt'],
                     'dns': ['dnsmasq.openwrt'],
                     'ethers': ['dnsmasq.openwrt'],
                     'smokeping': ['docker']}
