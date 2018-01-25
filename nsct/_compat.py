# -*- coding: utf-8 -*-
"""
nsct._compat
~~~~~~~~~~~~~~~~~~~~

Python 2.7.x, 3.2+ compatability module.
"""
from __future__ import absolute_import, unicode_literals
import operator
import sys

is_py2 = sys.version_info[0] == 2


if not is_py2:
    # Python 3
    # strings and ints
    text_type = str
    string_types = (str,)
    integer_types = (int,)

    # lazy iterators
    zip = zip
    range = range
    iteritems = operator.methodcaller('items')
    iterkeys = operator.methodcaller('keys')
    itervalues = operator.methodcaller('values')

    import io
    StringIO = io.StringIO
else:
    # Python 2

    # strings and ints
    text_type = unicode  # noqa
    string_types = (str, unicode)  # noqa
    integer_types = (int, long)  # noqa

    # lazy iterators
    range = xrange  # noqa
    from itertools import izip as zip  # noqa
    iteritems = operator.methodcaller('iteritems')
    iterkeys = operator.methodcaller('iterkeys')
    itervalues = operator.methodcaller('itervalues')

    from StringIO import StringIO as _StringIO
    StringIO = _StringIO
