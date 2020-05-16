""" CSV wrapper objects. """

import codecs
import csv
import io
import os

from .pyver import PY3


DEFAULT_CHARSET = "utf-8"
CSV_CHARSET = "utf-8"


def set_global_csv_field_size_limit(limit):
    """ Wrapper function. """
    csv.field_size_limit(limit)


def csv_open(file_name, mode, **kwargs):
    """ Wrapper function for opening a file for use by CSV reader/writer.
    
        Returns a file IO object; not a CSV object.
        
        Attempts to handle mode and encoding options on the file object
        so that they will be compatible with a CSV reader or writer.
        It is intended to be a drop-in replacement for open() or io.open(),
        with the exception that
        the newline option should not be specified when using this function.
    """
    if mode is None:
        mode = "r"
    if mode not in ("r", "w"):
        raise LookupError("mode must be 'r' or 'w'")
    if "newline" in kwargs:
        raise AttributeError("newline parameter is not allowed for CSV")
    # NOTE:
    #   Python 3 says to ensure newline=""
    #   Python 2 says to ensure file is open in binary mode,
    #    but if we open in binary mode, we cannot easily honor the encoding.
    #    Trying to open in binary mode and wrap it with a codec reader/writer
    #     doesn't seem to work.
    #    It appears that Python3 can reopen the STDOUT stream,
    #     but Python2 cannot.  The result is that newlines cannot be 
    #     controlled when writing to stdout in Python2.
    kwargs = dict(kwargs) # copy
    if True:
        kwargs["newline"] = ""
        return io.open(file_name, mode, **kwargs)
    else:
        # The purpose of all this python2 code
        #  is to try and handle newlines correctly,
        #  but it doesn't seem to work any better than
        #  if we just executed the PY3 case above:
        encoding = None
        errors = None
        if "encoding" in kwargs:
            encoding = kwargs["encoding"]
            del kwargs["encoding"]
        if "errors" in kwargs:
            errors = kwargs["errors"]
            del kwargs["errors"]
        if not encoding:
            encoding = CSV_CHARSET
        if mode == "r":
            CodecStream = codecs.getreader(encoding)
        elif mode == "w":
            CodecStream = codecs.getwriter(encoding)
        mode = mode + "b"
        file_io = io.open(file_name, mode, **kwargs)        
        if errors:
            file_io = CodecStream(file_io, errors)
        else:
            file_io = CodecStream(file_io)
        return file_io


def lookup_delimiter(delimiter_name):
    """ Maps a delimiter name (e.g. "tab") to a delimter value (e.g. "\t")
    
        This is mostly useful for tabs since Windows commandline
         makes it nearly impossible to specify a tab without an alias name.
    """
    delimiter = delimiter_name
    if delimiter_name is not None:
        delimiter_name = delimiter_name.lower()
    if not delimiter_name:
        pass
    elif delimiter_name in ("tab", "\\t"):
        delimiter = "\t"
    elif delimiter_name in ("space", "sp"):
        delimiter = " "
    elif delimiter_name in ("comma",):
        delimiter = ","
    elif delimiter_name in ("pipe", "vbar", "verticalbar"):
        delimiter = "|"
    elif delimiter_name in ("semicolon",):
        delimiter = ";"
    return delimiter


def lookup_charset(in_charset_name):
    """ Provides some additional aliases for text encoding names. """
    out_charset_name = in_charset_name
    if out_charset_name is not None:
        out_charset_name = out_charset_name.lower()
        out_charset_name = out_charset_name.replace("-", "_")
        if out_charset_name == "windows-1252":
            out_charset_name = "cp1252"
    return out_charset_name


def lookup_newline(in_newline_name):
    """ Provides commandline-friendly aliases for newline character names. """
    out_newline = in_newline_name
    if out_newline is not None:
        out_newline = out_newline.lower()
        out_newline = out_newline.replace("\\r", "\r")
        out_newline = out_newline.replace("\\n", "\n")
        out_newline = out_newline.replace("\\r\\n", "\r\n")
        if out_newline == "sys":
            out_newline = os.linesep
        elif out_newline == "std":
            # 'std' newline convention is the "standard" for this toolset;
            #  LF was chosen to try and accommodate some pipe scenarios,
            #  but this might change.
            #  The RFC-4180 recommendation is to use \r\n.
            out_newline = "\n"
            #out_newline = os.linesep
        elif out_newline in (
                "cr",
                "macintosh",
                "mac",
                "\\r",
                ):
            out_newline = "\r"
        elif out_newline in (
                "lf",
                "unix",
                "posix",
                "\\n",
                ):
            out_newline = "\n"
        elif out_newline in (
                "crlf",
                "windows",
                "win",
                "dos",
                "\\r\\n",
                ):
            out_newline = "\r\n"
    return out_newline


def lookup_quote_symbol(quote_symbol_name):
    ''' Provides some commandline friendly aliases for quote symbols
    '''
    quote_symbol = quote_symbol_name
    if quote_symbol_name is not None:
        quote_symbol_name = quote_symbol_name.lower()
    if not quote_symbol_name:
        pass
    elif quote_symbol_name in (
            "quot",
            "dquote",
            "double_quote",
            "double-quote",
            ):
        quote_symbol = "\""
    elif quote_symbol_name in (
            "apos",
            "squote",
            "single_quote",
            "single-quote",
            ):
        quote_symbol = "'"

    return quote_symbol


def normalize_column_name(column_name):
    """ puts a CSV column name into a "normalized" form for comparison. """
    norm_column_name = column_name
    if norm_column_name is not None:
        norm_column_name = norm_column_name.strip()
        norm_column_name = norm_column_name.lower()
    return norm_column_name


class CsvRecoder:
    """ Wraps an iterator of unicode to re-encode it for use with csv module. """
    encoding = CSV_CHARSET  # target encoding
    
    def __init__(
            self,
            in_iter,
            encoding,  # source encoding
            ):
        if not encoding:
            self.in_iter = in_iter
        else:
            decoder = codecs.getreader(encoding)
            self.in_iter = decoder(in_iter)

    def __iter__(self):
        return self

    def next(self):
        line_ustr = self.in_iter.next()
        return line_ustr.encode(self.encoding)

    def decode(self, s):
        return s.decode(self.encoding)



class UnicodeCsvReader:
    """ Wraps a csv.reader with a text encoder. """
    def __init__(
            self,
            in_io,
            **kwargs):
        encoding = None
        self.recoder = CsvRecoder(in_io, encoding)
        self.reader = csv.reader(self.recoder, **kwargs)

    def next(self):
        row = self.reader.next()
        return [self.recoder.decode(cell) for cell in row]

    def __iter__(self):
        return self


class UnicodeCsvWriter:
    """ Wraps a csv.writer to write to a unicode stream. """

    def __init__(
            self,
            out_io,
            **kwargs):
        from cStringIO import StringIO
        self.buf_io = StringIO()
        self.writer = csv.writer(self.buf_io, **kwargs)
        self.out_io = out_io

    def writerow(self, row):
        self.writer.writerow([cell_ustr.encode(CSV_CHARSET) for cell_ustr in row])
        row_str = self.buf_io.getvalue()
        self.buf_io.truncate(0)
        row_ustr = row_str.decode(CSV_CHARSET)
        self.out_io.write(row_ustr)
 
    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


if PY3:
    CsvReader = csv.reader
    CsvWriter = csv.writer
else:
    CsvReader = UnicodeCsvReader
    CsvWriter = UnicodeCsvWriter

