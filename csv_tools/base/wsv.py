""" Provides a CSV interface for sh-style whitespace separated values. """

from contextlib import contextmanager
from subprocess import list2cmdline
from shlex import split as cmdline2list

from .csv2 import csv_open


class WsvValueError(ValueError):
    """ Raised when a WSV line cannot be parsed. """
    def __init__(self, message, line_num):
        self.line_num = line_num
        message = "line {0}: {1}".format(line_num, message)
        super(WsvValueError, self).__init__(message)

class WsvReader(object):
    """ Implements a CsvReader-compatible object on a Whitespace Separated Value stream. """
    def __init__(self, in_io, lineterminator=None):
        self.in_iter = iter(in_io)
        self.lineterminator = lineterminator
        self.line_count = 0

    def __iter__(self):
        return self

    def __next__(self):
        # python3
        return self.next()

    def next(self):
        """ Get the next item in the iteration. """
        # python2
        lineterminator = self.lineterminator
        line_str = next(self.in_iter)
        self.line_count += 1
        if lineterminator and line_str.endswith(lineterminator):
            line_str = line_str[:-len(lineterminator)]
        try:
            row = cmdline2list(line_str)
        except ValueError as ex:
            raise WsvValueError(str(ex), self.line_count)
        return row


class WsvWriter(object):
    """ Implements a CsvWriter-compatible object on a Whitespace Separated Value stream. """
    def __init__(self, out_io, lineterminator=None):
        if not lineterminator:
            # let output stream translate linefeeds:
            lineterminator = "\n"
        self.out_io = out_io
        self.lineterminator = lineterminator

    def writerow(self, row):
        """ Write a row to the output stream. """
        out_io = self.out_io
        line_str = list2cmdline(row)
        out_io.write(line_str)
        out_io.write(self.lineterminator)


@contextmanager
def open_wsv_reader(
        in_io,
        file_name,
        encoding=None,
        errors=None,
        lineterminator=None,
        buffering=None,
        ):
    """ High-level function to open a CSV reader.
    
        If file_name is None, then in_io will be used.
    """
    DEFAULT_BUFFERING = -1
    encoding = encoding or 'utf_8_sig'
    # 'strict' | 'ignore' | 'replace' | 'backslashreplace'
    errors = errors or 'strict'
    buffering = buffering if buffering is not None else DEFAULT_BUFFERING

    read_text_io_mode = 'r'
    in_file_id = file_name
    should_close_in_file = True
    if not in_file_id:
        in_file_id = in_io.fileno()
        should_close_in_file = False
    in_io = csv_open(
        in_file_id,
        mode=read_text_io_mode,
        encoding=encoding,
        errors=errors,
        buffering=buffering,
        closefd=should_close_in_file,
        )
    in_file_io = None
    if should_close_in_file:
        in_file_io = in_io

    in_csv = WsvReader(
        in_io,
        lineterminator=lineterminator,
        )
    # @contextmanager: enter: yield this object to the with statement:
    yield in_csv
    # @contextmanager: exit: after the yield close the stream:
    if in_file_io:
        in_file_io.close()


@contextmanager
def open_wsv_writer(
        out_io,
        file_name,
        encoding=None,
        errors=None,
        lineterminator=None,
        buffering=None,
        ):
    """ Basic function to open a CSV writer with various options. 
    
        If file_name is None, then out_io will be used as the underlying stream.
    """
    DEFAULT_BUFFERING = -1
    encoding = encoding or 'utf_8'
    # 'strict' | 'ignore' | 'replace' | 'backslashreplace'
    errors = errors or 'strict'
    buffering = buffering if buffering is not None else DEFAULT_BUFFERING

    write_text_io_mode = 'w'
    out_file_id = file_name
    should_close_out_file = True
    if not out_file_id:
        out_file_id = out_io.fileno()
        should_close_out_file = False
    out_io = csv_open(
        out_file_id,
        mode=write_text_io_mode,
        encoding=encoding,
        errors=errors,
        buffering=buffering,
        closefd=should_close_out_file,
        )
    out_file_io = None
    if should_close_out_file:
        out_file_io = out_io
    out_csv = WsvWriter(
        out_io,
        lineterminator=lineterminator,
        )
    # @contextmanager: enter: yield this object to the with statement:
    yield out_csv
    # @contextmanager: exit: after the yield close the stream:
    if out_file_io:
        out_file_io.close()
