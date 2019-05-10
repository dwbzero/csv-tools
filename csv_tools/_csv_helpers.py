##  Copyright (c) 2016 Upstream Research, Inc.  All Rights Reserved.  ##

import os

def decode_delimiter_name(delimiter_name):
    ''' Maps a delimiter name (e.g. "tab") to a delimter value (e.g. "\t")
        This is mostly useful for tabs since Windows commandline makes it near impossible to specify without an alias name
    '''
    delimiter = delimiter_name
    if (None == delimiter_name):
        pass
    elif ("tab" == delimiter_name.lower()
      or "\\t" == delimiter_name.lower()
      ):
        delimiter = "\t"
    elif ("space" == delimiter_name.lower()
      or "sp" == delimiter_name.lower()
      ):
        delimiter = " "
    elif ("comma" == delimiter_name.lower()):
        delimiter = ","
    elif ("pipe" == delimiter_name.lower()
      or "vbar" == delimiter_name.lower()
      or "verticalbar" == delimiter_name.lower()
      ):
        delimiter = "|"
    elif ("semicolon" == delimiter_name.lower()):
        delimiter = ";"
    return delimiter

def decode_charset_name(in_charset_name):
    ''' Provides some additional aliases for text encoding names
    '''
    out_charset_name = in_charset_name
    if (None != out_charset_name):
        out_charset_name = out_charset_name.lower()
        out_charset_name = out_charset_name.replace("-", "_")
        if ("windows-1252" == out_charset_name):
            out_charset_name = "cp1252"
    return out_charset_name

def decode_newline(in_newline_name):
    ''' Provides a commandline-friendly alias for newline character names 
    '''
    out_newline = in_newline_name
    if (None != out_newline):
        out_newline = out_newline.lower()
        out_newline = out_newline.replace("\\r", "\r")
        out_newline = out_newline.replace("\\n", "\n")
        out_newline = out_newline.replace("\\r\\n", "\r\n")
        if ("sys" == out_newline):
            out_newline = os.linesep
        elif ("std" == out_newline):
            out_newline = "\n"
            #out_newline = os.linesep
        elif ("cr" == out_newline
          or "macintosh" == out_newline
          or "mac" == out_newline
        ):
            out_newline = "\r"
        elif ("lf" == out_newline
          or "unix" == out_newline
        ):
            out_newline = "\n"
        elif ("crlf" == out_newline
          or "windows" == out_newline
          or "win" == out_newline
          or "dos" == out_newline
        ):
            out_newline = "\r\n"
    return out_newline

def decode_quote_symbol_name(quote_symbol_name):
    ''' Provides some commandline friendly aliases for quote symbols
    '''
    quote_symbol = quote_symbol_name
    if (None == quote_symbol_name):
        pass
    elif ("quot" == quote_symbol_name.lower()
      or "dquote" == quote_symbol_name.lower()
      or "double_quote" == quote_symbol_name.lower()
      or "double-quote" == quote_symbol_name.lower()
      ):
        quote_symbol = "\""
    elif ("apos" == quote_symbol_name.lower()
      or "squote" == quote_symbol_name.lower()
      or "single_quote" == quote_symbol_name.lower()
      or "single-quote" == quote_symbol_name.lower()
      ):
        quote_symbol = "'"

    return quote_symbol

def normalize_column_name(column_name):
    ''' puts a CSV column name into a "normalized" form
        which is supposed to make it easier for comparison
    '''
    norm_column_name = column_name
    if (None != norm_column_name):
        norm_column_name = norm_column_name.strip()
        norm_column_name = norm_column_name.lower()
    return norm_column_name
