# -*- coding: utf-8 -*-
"""
nsct
~~~~~~~~~~~~~~~~~~~

Specify and configure a network of domains, devices and servers.

:copyright: (c) 2018 by Neil Jarvis
:licence: MIT, see LICENCE for more details
"""
from __future__ import absolute_import, unicode_literals
import logging

# Generate your own AsciiArt at:
# patorjk.com/software/taag/#f=Calvin%20S&t=Network Specification and Configuration Tool
__banner__ = r"""
╔╗╔┌─┐┌┬┐┬ ┬┌─┐┬─┐┬┌─  ╔═╗┌─┐┌─┐┌─┐┬┌─┐┬┌─┐┌─┐┌┬┐┬┌─┐┌┐┌  ┌─┐┌┐┌┌┬┐  ╔═╗┌─┐┌┐┌┌─┐┬┌─┐┬ ┬┬─┐┌─┐┌┬┐┬┌─┐┌┐┌  ╔╦╗┌─┐┌─┐┬
║║║├┤  │ ││││ │├┬┘├┴┐  ╚═╗├─┘├┤ │  │├┤ ││  ├─┤ │ ││ ││││  ├─┤│││ ││  ║  │ ││││├┤ ││ ┬│ │├┬┘├─┤ │ ││ ││││   ║ │ ││ ││
╝╚╝└─┘ ┴ └┴┘└─┘┴└─┴ ┴  ╚═╝┴  └─┘└─┘┴└  ┴└─┘┴ ┴ ┴ ┴└─┘┘└┘  ┴ ┴┘└┘─┴┘  ╚═╝└─┘┘└┘└  ┴└─┘└─┘┴└─┴ ┴ ┴ ┴└─┘┘└┘   ╩ └─┘└─┘┴─┘
by Neil Jarvis
"""

__title__ = 'nsct'
__summary__ = 'Specify and configure a network of domains, devices and servers.'
__uri__ = 'https://github.com/njarvis/nsct'

__version__ = '0.0.1'

__author__ = 'Neil Jarvis'
__email__ = 'neil@jarvis.name'

__license__ = 'MIT'
__copyright__ = 'Copyright 2018 Neil Jarvis'

# the user should dictate what happens when a logging event occurs
logging.getLogger(__name__).addHandler(logging.NullHandler())
