##  Copyright (c) 2016 Upstream Research, Inc.  All Rights Reserved.  ##
""" Module containing helper methods used in csv_tools commandline programs. """

#   _csv_helpers is deprecated

# The following functions were originally defined in _csv_helpers,
#   but have since been moved.
from .base.csv2 import (
    lookup_delimiter as decode_delimiter_name,
    lookup_charset as decode_charset_name,
    lookup_newline as decode_newline,
    lookup_quote_symbol as decode_quote_symbol_name,
    normalize_column_name,
    )
