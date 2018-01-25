# -*- coding: utf-8 -*-
"""
:copyright: (c) 2018 by Neil Jarvis
:licence: MIT, see LICENCE for more details
"""
from __future__ import absolute_import, unicode_literals, print_function


def nth(number):
    if str(number)[-1] == '1':
        return number + 'st'
    elif str(number)[-1] == '2':
        return number + 'nd'
    elif str(number)[-1] == '3':
        return number + '3rd'
    else:
        return number + 'th'
