##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##
""" Join multiple CSV files, merging corresponding columns.
"""

# 20201207 (db) ORIGIN csv_translate.py
# 20201207 (db) TODO refactor this file and csv_translate.py to better share code.

from contextlib import contextmanager
import errno
from itertools import chain
import os
import sys

from .base.pyver import irange
from .base import csv2
from .base.csv2 import (
    lookup_delimiter,
    lookup_charset,
    lookup_newline,
    lookup_quote_symbol,
    )

HELP_TEXT = """{program_name} tool version 20201207
Join multiple files, merging corresponding columns.

{program_name} [OPTIONS] FileNameColumn [InputFile]

OPTIONS
    -M {N}  Read N files to compute output header row (default=1).
    -N {N}  Read N rows from the input file.
    -n {N}  Write N rows of output.
    -o {F}  Output file name

Read a CSV containing file names in a designated FileNameColumn.
Reads each file item listed in the input CSV,
joins the columns of the file item row to every row in the file itself.
If a column exists in both the file item row and the file data,
then the file data will take precedent.

The input file should have the same encoding as the files that it references.
"""

class CsvFileJoinProcessor(object):
    """ Implements a CSV format translator.

        This class is meant to be used as a base class for more specialized
        csv processing tools.
    """
    program_name = "{csv_processor}"
    exit_code = 0
    help_text = HELP_TEXT
    should_print_help = False
    #error_message = None
    in_file_name = None
    out_file_name = None
    in_delimiter = ','
    in_quote_symbol = '"'
    out_delimiter = ','
    out_quote_symbol = '"'
    in_row_terminator = 'std'
    out_row_terminator = 'std'
    in_charset_name = 'utf_8_sig'
    out_charset_name = 'utf_8'
    out_charset_error_mode = 'strict'  # 'strict' | 'ignore' | 'replace' | 'backslashreplace'
    in_charset_error_mode = 'strict'  # 'strict' | 'ignore' | 'replace' | 'backslashreplace'
    csv_cell_width_limit = 4*1024*1024  # python default is 131072 = 0x00020000
    in_row_offset_start = 0
    in_row_count_max = None
    out_row_count_max = None
    file_path_column = None
    in_header_count_max = 1

    def __init__(self):
        pass

    def parse_next_arg(self, arg, arg_iter):
        """ Parse the next argument flag from an argument iterator.

            Returns True if the argument was parsed:
            the parser should then get the next arg from arg_iter
            and keep parsing.
            Returns False if the argument was not parsed:
            the parser should try to parse the current argument
            according to any other parsing rules it may have.
        """
        succeeded = True
        arg_obj = self
        if arg in ("--help", "-?"):
            arg_obj.should_print_help = True
        elif arg in ("-o", "--output"):
            arg_obj.out_file_name = next(arg_iter)
        elif arg in ("-E", "--encoding-in", "--charset-in"):
            arg_obj.in_charset_name = next(arg_iter)
        elif arg in ("-e", "--encoding-out", "--charset-out"):
            arg_obj.out_charset_name = next(arg_iter)
        elif arg in ("--charset-in-error-mode",):
            arg_obj.in_charset_error_mode = next(arg_iter)
        elif arg in ("--charset-out-error-mode",):
            arg_obj.out_charset_error_mode = next(arg_iter)
        elif arg in ("--charset-error_mode",):
            error_mode = next(arg_iter)
            arg_obj.in_charset_error_mode = error_mode
            arg_obj.out_charset_error_mode = error_mode
        elif arg in ("-S", "--separator-in", "--delimiter-in"):
            arg_obj.in_delimiter = next(arg_iter)
        elif arg in ("-s", "--separator-out", "--delimiter-out"):
            arg_obj.out_delimiter = next(arg_iter)
        elif arg in ("-Q", "--quote-in"):
            arg_obj.in_quote_symbol = next(arg_iter)
        elif arg in ("-q", "--quote-out"):
            arg_obj.out_quote_symbol = next(arg_iter)
        elif arg in ("-W", "--terminator-in", "--newline-in", "--endline-in"):
            arg_obj.in_row_terminator = next(arg_iter)
        elif arg in ("-w", "--terminator-out", "--newline-out", "--endline-out"):
            arg_obj.out_row_terminator = next(arg_iter)
        elif arg in ("--cell-width-limit",):
            arg_obj.csv_cell_width_limit = int(next(arg_iter))
        elif arg in ("-K", "--row-offset-in", "--offset", "--skip"):
            arg_obj.in_row_offset_start = int(next(arg_iter))
        elif arg in ("-N", "--row-count-in"):
            arg = next(arg_iter)
            row_count = None
            if arg.upper() != 'ALL':
                row_count = int(arg)
            arg_obj.in_row_count_max = row_count
        elif arg in ("-n", "--row-count-out"):
            arg = next(arg_iter)
            row_count = None
            if arg.upper() != 'ALL':
                row_count = int(arg)
            arg_obj.out_row_count_max = row_count
        elif arg in ("-M", "--header-files"):
            arg = next(arg_iter)
            row_count = None
            if arg.upper() != 'ALL':
                row_count = int(arg)
            arg_obj.in_header_count_max = row_count
        elif arg.startswith("-"):
            succeeded = False
        elif arg_obj.file_path_column is None:
            arg_obj.file_path_column = arg
        elif arg_obj.in_file_name is None:
            arg_obj.in_file_name = arg
        else:
            succeeded = False
        return succeeded

    def parse_args(self, argv):
        """ Parse a list of commandline arguments into attributes of this object. """
        # [20160916 [db] I avoided using argparse
        #  in order to retain some flexibility for command syntax]
        arg_obj = self
        arg_iter = iter(argv)
        program_path = next(arg_iter)
        arg_obj.program_name = os.path.basename(program_path)
        for arg in arg_iter:
            if arg_obj.parse_next_arg(arg, arg_iter):
                pass
            else:
                raise LookupError("Unknown argument: " + arg)
        arg_obj.in_charset_name = lookup_charset(arg_obj.in_charset_name)
        arg_obj.out_charset_name = lookup_charset(arg_obj.out_charset_name)
        arg_obj.in_row_terminator = lookup_newline(arg_obj.in_row_terminator)
        arg_obj.out_row_terminator = lookup_newline(arg_obj.out_row_terminator)
        arg_obj.in_delimiter = lookup_delimiter(arg_obj.in_delimiter)
        arg_obj.out_delimiter = lookup_delimiter(arg_obj.out_delimiter)
        arg_obj.in_quote_symbol = lookup_quote_symbol(arg_obj.in_quote_symbol)
        arg_obj.out_quote_symbol = lookup_quote_symbol(arg_obj.out_quote_symbol)

        return arg_obj

    def print_help(self, out_io):
        """ Print command help information to a stream. """
        help_text = self.help_text.replace("{program_name}", self.program_name)
        out_io.write(help_text)

    @contextmanager
    def open_writer(self, file_name, out_io, err_io):
        """ Open an output CSV writer. """
        arg_obj = self
        out_file_name = file_name
        out_charset_name = arg_obj.out_charset_name
        out_charset_error_mode = arg_obj.out_charset_error_mode
        out_delimiter = arg_obj.out_delimiter
        out_row_terminator = arg_obj.out_row_terminator
        out_quote_symbol = arg_obj.out_quote_symbol
        out_file = None
        write_text_io_mode = 'w'
        out_file_id = out_file_name
        should_close_out_file = True
        if not out_file_id:
            out_file_id = out_io.fileno()
            should_close_out_file = False
        out_io = csv2.csv_open(
            out_file_id,
            mode=write_text_io_mode,
            encoding=out_charset_name,
            errors=out_charset_error_mode,
            closefd=should_close_out_file,
            )
        if should_close_out_file:
            out_file = out_io
        out_csv = csv2.CsvWriter(
            out_io,
            delimiter=out_delimiter,
            lineterminator=out_row_terminator,
            quotechar=out_quote_symbol,
            )
        # @contextmanager: enter: yield this object to the with statement:
        yield out_csv
        # @contextmanager: exit: after the yield close the stream:
        if should_close_out_file and out_file:
            out_file.close()

    @contextmanager
    def open_reader(self, file_name, in_io, err_io):
        """ Open an input CSV reader, and return an iterator that can read rows. """
        # set global CSV column width
        arg_obj = self
        csv_cell_width_limit = arg_obj.csv_cell_width_limit
        in_file_name = file_name
        in_charset_name = arg_obj.in_charset_name
        in_charset_error_mode = arg_obj.in_charset_error_mode
        in_delimiter = arg_obj.in_delimiter
        in_row_terminator = arg_obj.in_row_terminator
        in_quote_symbol = arg_obj.in_quote_symbol

        if csv_cell_width_limit:
            csv2.set_global_csv_field_size_limit(csv_cell_width_limit)

        in_file = None
        read_text_io_mode = 'r'
        in_file_id = in_file_name
        should_close_in_file = True
        if not in_file_id:
            in_file_id = in_io.fileno()
            should_close_in_file = False
        in_io = csv2.csv_open(
            in_file_id,
            mode=read_text_io_mode,
            encoding=in_charset_name,
            errors=in_charset_error_mode,
            closefd=should_close_in_file,
            )
        if should_close_in_file:
            in_file = in_io

        in_csv = csv2.CsvReader(
            in_io,
            delimiter=in_delimiter,
            lineterminator=in_row_terminator,
            quotechar=in_quote_symbol,
            )
        # @contextmanager: enter: yield this object to the with statement:
        yield in_csv
        # @contextmanager: exit: after the yield close the stream:
        if should_close_in_file and in_file:
            in_file.close()

    def main(self, argv, in_io, out_io, err_io):
        """ Implements main entry point function. """
        exe = self
        exit_code = 0
        error_message = None
        try:
            arg_obj = exe.parse_args(argv)
            if arg_obj.should_print_help:
                exe.print_help(out_io)
            else:
                exit_code = exe.execute(arg_obj, in_io, out_io, err_io)
        except IOError as exc:
            if exc.errno == errno.EPIPE:
                # (also BrokenPipeError python 3)
                # can occur when a process serving a stdio stream quits
                pass
            elif exc.errno == errno.ENOENT:
                # (also FileNotFoundError python 3)
                error_message = "File '{FileName}' not found.".format(FileName=exc.filename)
                exit_code = 1
            else:
                raise
        except UnicodeError as exc:
            error_message = str(exc)
            exit_code = 1
            raise
        if error_message:
            err_io.write("Error: {E}\n".format(E=error_message))
            exit_code = 1
        return exit_code

    def execute(self, arg_obj, in_io, out_io, err_io):
        """ Execute the csv processing operation. """
        exit_code = 0
        exe = self
        with exe.open_reader(arg_obj.in_file_name, in_io, err_io) as in_csv:
            with exe.open_writer(arg_obj.out_file_name, out_io, err_io) as out_csv:
                for row in exe.process(in_csv, err_io):
                    out_csv.writerow(row)
        return exit_code

    def process(self, rows, err_io):
        """ Return a generator that will process the input rows. """
        in_io = None
        arg_obj = self
        in_row_offset_start = arg_obj.in_row_offset_start
        in_row_count_max = arg_obj.in_row_count_max
        out_row_count_max = arg_obj.out_row_count_max
        in_header_count_max = arg_obj.in_header_count_max
        file_path_column_name = arg_obj.file_path_column
        
        def normalize_column_name(name):
            return name

        row_iter = iter(rows)
        flist_header_row = next(row_iter, None)
        column_set = set()
        header_row = list()
        if flist_header_row:
            header_row.extend(flist_header_row)
            column_set.update((
                normalize_column_name(column_name)
                for column_name in flist_header_row))
        
        file_path_column_position = None
        for pos, column_name in enumerate(header_row):
            if normalize_column_name(column_name) == file_path_column_name:
                file_path_column_position = pos
        
        if file_path_column_position is None:
            return
        
        # Read headers from each file:
        buf_rows = []
        in_header_count = 0
        for in_row in row_iter:
            buf_rows.append(in_row)
            if in_header_count_max is not None and in_header_count_max <= in_header_count:
                break
            in_header_count += 1
            file_path = in_row[file_path_column_position]
            file_header_row = None
            with self.open_reader(file_path, in_io, err_io) as file_rows:
                file_row_iter = iter(file_rows)
                file_header_row = next(file_row_iter, None)
            if not file_header_row:
                continue
            for column_name in file_header_row:
                norm_column_name = normalize_column_name(column_name)
                if norm_column_name not in column_set:
                    header_row.append(column_name)
                    column_set.add(norm_column_name)
        
        yield header_row
        
        # Read file data and join:
        in_row_count = 0
        out_row_count = 0
        for in_row in chain(buf_rows, row_iter):
            if in_row_count_max is not None and in_row_count_max <= in_row_count:
                break
            elif out_row_count_max is not None and out_row_count_max <= out_row_count:
                break
            in_row_count += 1
            if in_row_count <= in_row_offset_start:
                continue
            file_path = in_row[file_path_column_position]
            with self.open_reader(file_path, in_io, err_io) as file_rows:
                file_row_iter = iter(file_rows)
                file_header_row = next(file_row_iter, None)
                if not file_header_row:
                    continue
                src_pos_list = len(header_row) * [None]
                for src_pos, src_column_name in enumerate(file_header_row):
                    src_column_name_norm = normalize_column_name(src_column_name)
                    for dest_pos, dest_column_name in enumerate(header_row):
                        dest_column_name_norm = normalize_column_name(dest_column_name)
                        if dest_column_name_norm == src_column_name_norm:
                            src_pos_list[dest_pos] = src_pos
                            break
                for file_row in file_row_iter:
                    if out_row_count_max is not None and out_row_count_max <= out_row_count:
                        break
                    out_row = list(in_row)
                    dest_pos = len(out_row)
                    while dest_pos < len(header_row):
                        out_row.append(None)
                        dest_pos += 1
                    dest_pos = 0
                    while dest_pos < len(header_row):
                        src_pos = src_pos_list[dest_pos]
                        if src_pos is not None and src_pos < len(file_row):
                            out_row[dest_pos] = file_row[src_pos]
                        dest_pos += 1
                    yield out_row
                    out_row_count += 1


def main(argv, in_io, out_io, err_io):
    """ Main entry point for program. """
    exe = CsvFileJoinProcessor()
    return exe.main(argv, in_io, out_io, err_io)


def console_main():
    """ Main entry point when invoked from executable wrapper. """
    return main(sys.argv, sys.stdin, sys.stdout, sys.stderr)


if __name__ == "__main__":
    sys.exit(console_main())
