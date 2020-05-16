""" Module to centralize detection of python language version. """

import sys

# A pair (M,m) that can be easily compared.
PYVER = (sys.version_info[0], sys.version_info[1])


if PYVER < (3,0):

    PY3 = False
    RSTR_CHARSET = "utf-8"
    irange = xrange
    ustr = unicode
    def rstr(s):
        """ Convert unicode to "raw" string. """
        if isinstance(s, unicode):
            return s.encode(RSTR_CHARSET)
        return s

else:
    PY3 = True
    irange = range
    ustr = str
    rstr = str
