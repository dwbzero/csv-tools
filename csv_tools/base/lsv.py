""" Provides a CSV interface for "line separated value" data. """

from contextlib import contextmanager

from .csv2 import csv_open

# ORIGIN wsv.py

LF = "\n"
CR = "\r"
CRLF = "\r\n"
SP = " "
ONELINE_SIGIL = "-"
MULTILINE_SIGIL = ">"
ONELINE_PREFIX = ONELINE_SIGIL + SP
MULTILINE_PREFIX = MULTILINE_SIGIL + SP
RECORD_SEP = "---"


class LsvValueError(ValueError):
    """ Raised when a LSV line cannot be parsed. """
    def __init__(self, message, line_num):
        self.line_num = line_num
        message = "line {0}: {1}".format(line_num, message)
        super(LsvValueError, self).__init__(message)


class LsvReader(object):
    """ Implements a CsvReader-compatible object on a Line Separated Value stream. """
    def __init__(self, in_io, lineterminator=None):
        self.in_iter = iter(in_io)
        self.lineterminator = lineterminator
        self.line_count = 0

    def __iter__(self):
        return self

    def __next__(self):
        # python3 __next__()
        return self.next()

    def next(self):
        """ Get the next item in the iteration. """
        # python2 next()
        endl = self.lineterminator or "\n"
        row = list()
        complete_row = None
        multiline_parts = None
        for line_str in self.in_iter:
            line_str = line_str.lstrip()
            if line_str.endswith(CRLF):
                line_str = line_str[:-len(CRLF)]
            elif line_str.endswith(LF):
                line_str = line_str[:-len(LF)]
            elif line_str.endswith(CR):
                line_str = line_str[:-len(CR)]
            if not line_str:
                if multiline_parts:
                    val_str = endl.join(multiline_parts)
                    multiline_parts = None
                    row.append(val_str)
                continue
            if line_str.startswith(RECORD_SEP):
                if multiline_parts:
                    val_str = endl.join(multiline_parts)
                    multiline_parts = None
                    row.append(val_str)
                complete_row = row
                break
            if line_str.startswith(ONELINE_SIGIL):
                if multiline_parts:
                    val_str = endl.join(multiline_parts)
                    multiline_parts = None
                    row.append(val_str)
                prefix_len = len(ONELINE_SIGIL)
                if line_str.startswith(ONELINE_PREFIX):
                    prefix_len = len(ONELINE_PREFIX)
                val_str = line_str[prefix_len:]
                row.append(val_str)
            elif line_str.startswith(MULTILINE_SIGIL):
                prefix_len = len(MULTILINE_SIGIL)
                if line_str.startswith(MULTILINE_PREFIX):
                    prefix_len = len(MULTILINE_PREFIX)
                val_str = line_str[prefix_len:]
                if multiline_parts is None:
                    multiline_parts = [val_str]
                else:
                    multiline_parts.append(val_str)
            elif multiline_parts:
                # TODO: consider just raising an exception here
                multiline_parts.append(line_str)
            else:
                # TODO: consider just raising an exception here
                row.append(line_str)
        if not complete_row and not row:
            raise StopIteration()
        elif complete_row:
            # This isn't really necessary, but for consistency:
            row = complete_row
        return row


class LsvWriter(object):
    """ Implements a CsvWriter-compatible object on a Line Separated Value stream. """
    def __init__(self, out_io, lineterminator=None):
        if not lineterminator:
            # let output stream translate linefeeds:
            lineterminator = "\n"
        self.out_io = out_io
        self.lineterminator = lineterminator

    def writerow(self, row):
        """ Write a row to the output stream. """
        endl = self.lineterminator
        out_io = self.out_io
        for cell_val in row:
            if cell_val is None:
                cell_val = ""
            else:
                cell_val = str(cell_val)
            if LF in cell_val:
                lines = cell_val.split(LF)
                for line_str in lines:
                    out_io.write(MULTILINE_PREFIX)
                    out_io.write(line_str)
                    out_io.write(endl)
                    out_io.write(endl)
            else:
                out_io.write(ONELINE_PREFIX)
                out_io.write(cell_val)
                out_io.write(endl)
        out_io.write(RECORD_SEP)
        out_io.write(endl)
        out_io.flush()


@contextmanager
def open_lsv_reader(
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

    in_csv = LsvReader(
        in_io,
        lineterminator=lineterminator,
        )
    # @contextmanager: enter: yield this object to the with statement:
    yield in_csv
    # @contextmanager: exit: after the yield close the stream:
    if in_file_io:
        in_file_io.close()


@contextmanager
def open_lsv_writer(
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
    out_csv = LsvWriter(
        out_io,
        lineterminator=lineterminator,
        )
    # @contextmanager: enter: yield this object to the with statement:
    yield out_csv
    # @contextmanager: exit: after the yield close the stream:
    if out_file_io:
        out_file_io.close()
