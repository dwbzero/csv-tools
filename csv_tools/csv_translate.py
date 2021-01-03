##  Copyright (c) 2016-2020 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##
""" Translate delimited text encodings.

    Defines a csv processor class which can be used as a base class
    for other csv processors.
    See the csv_count module for an example of how to derive from this class.
"""

# This module serves as a basis for the other CSV modules.
# Eventually, some of this code may need to be refactored
#  into a more basic class.

import errno
import os
import sys

# This conditional statement allows you to start csv_translate in several ways:
#  directly: > python csv_translate.py
#  indirectly when used by another script: > python csv_count.py
#  indirectly when used as a submodule: > python csvf.py translate
if __name__ in ("__main__", "csv_translate"):
    from base.pyver import irange
    from base import csv2
else: # if __name__ == "csvtools.csv_translate":
    from .base.pyver import irange
    from .base import csv2

lookup_delimiter = csv2.lookup_delimiter
lookup_charset = csv2.lookup_charset
lookup_newline = csv2.lookup_newline
lookup_quote_symbol = csv2.lookup_quote_symbol
open_csv_reader = csv2.open_csv_reader
open_csv_writer = csv2.open_csv_writer


HELP_TEXT = """{program_name} tool version 20160916:20200516
Translates delimited text encodings

{program_name} [OPTIONS] [InputFile]

OPTIONS
    -b {N}  Set output buffer size bytes
    -B {N}  Set input buffer size in bytes
    -E {E}  Input file text encoding (e.g. 'utf-8', 'windows-1252')
    -e {E}  Output file text encoding (e.g. 'utf-8', 'windows-1252')
    -K {N}  Number of rows to skip from the input (default=0)
    -l      Flush buffer after each line written
    -L      Read data in line-buffer mode
    -N {N}  Maximum number of rows to read (default=ALL)
    -n {N}  Maximum number of rows to write (default=ALL)
    -o {F}  Output file name
    -Q {S}  Input file quote symbol (default='\"')
    -q {S}  Output file quote symbol (default='\"')
    -S {S}  Input file field delimiter (default=',')
    -s {S}  Output file field delimiter (default=',')
    -W {S}  Input line terminator (default='std')
    -w {S}  Output line terminator (default='std')

Text encoding names are determined by the Python 'codecs' module,
but a few common names like 'utf-8' and 'windows-1252' are recoginized.
See <https://docs.python.org/3/library/codecs.html#standard-encodings>.

A Field delimiter must be a single character or a delimiter name.
Valid delimiter names are: 'comma', 'tab', 'space', 'semicolon'.
The escape sequence '\\t' is also recognized.

A quote symbol must be a single character or a quote symbol name.
Valid quote symbol names are: 'apos', 'quot', 'single-quote', 'double-quote'.

A line terminator may be a character sequence or a line terminator name.
Valid line terminator names are: 'CR', 'LF', 'CRLF', '\\r', '\\n', '\\r\\n',
as well as 'sys', 'std', 'mac', 'unix', 'dos'.
'sys' will use whatever newline convention applies to the OS platform.
'std' will let this tool to decide what to use.
"""



class CsvTranslateProcessor(object):
    """ Implements a CSV format translator.

        This class is meant to be used as a base class for more specialized
        csv processing tools.
    """
    program_name = "{csv_processor}"
    DEFAULT_BUFFERING = -1
    LINE_BUFFERING = 1
    exit_code = 0
    help_text = HELP_TEXT
    should_print_help = False
    #error_message = None
    in_file_name = None
    out_file_name = None
    in_buffering = DEFAULT_BUFFERING
    out_buffering = DEFAULT_BUFFERING
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

    def __init__(self):
        pass

    def parse_next_input_stream_arg(self, arg_obj, arg, arg_iter):
        """ Parse the next argument flag from an argument iterator.
        """
        succeeded = True
        if arg in ("-B", "--buffer-size-in"):
            arg_obj.in_buffering = int(next(arg_iter))
        elif arg in ("-E", "--encoding-in", "--charset-in"):
            arg_obj.in_charset_name = next(arg_iter)
        elif arg in ("-L", "--line-buffering-in"):
            arg_obj.in_buffering = self.LINE_BUFFERING
        elif arg in ("-K", "--row-offset-in", "--offset", "--skip"):
            arg_obj.in_row_offset_start = int(next(arg_iter))
        elif arg in ("-N", "--row-count-in"):
            arg = next(arg_iter)
            row_count = None
            if arg.upper() != 'ALL':
                row_count = int(arg)
            arg_obj.in_row_count_max = row_count
        elif arg in ("-Q", "--quote-in"):
            arg_obj.in_quote_symbol = next(arg_iter)
        elif arg in ("-S", "--separator-in", "--delimiter-in"):
            arg_obj.in_delimiter = next(arg_iter)
        elif arg in ("-W", "--terminator-in", "--newline-in", "--endline-in"):
            arg_obj.in_row_terminator = next(arg_iter)
        elif arg in ("--charset-in-error-mode",):
            arg_obj.in_charset_error_mode = next(arg_iter)
        elif arg in ("--cell-width-limit",):
            arg_obj.csv_cell_width_limit = int(next(arg_iter))
        else:
            succeeded = False
        return succeeded

    def parse_next_output_stream_arg(self, arg_obj, arg, arg_iter):
        """ Parse the next argument flag from an argument iterator.
        """
        succeeded = True
        if arg in ("-o", "--output"):
            arg_obj.out_file_name = next(arg_iter)
        elif arg in ("-b", "--buffer-size-out"):
            arg_obj.out_buffering = int(next(arg_iter))
        elif arg in ("-e", "--encoding-out", "--charset-out"):
            arg_obj.out_charset_name = next(arg_iter)
        elif arg in ("-l", "--line-buffering-out"):
            arg_obj.out_buffering = self.LINE_BUFFERING
        elif arg in ("-n", "--row-count-out"):
            arg = next(arg_iter)
            row_count = None
            if arg.upper() != 'ALL':
                row_count = int(arg)
            arg_obj.out_row_count_max = row_count
        elif arg in ("-q", "--quote-out"):
            arg_obj.out_quote_symbol = next(arg_iter)
        elif arg in ("-s", "--separator-out", "--delimiter-out"):
            arg_obj.out_delimiter = next(arg_iter)
        elif arg in ("-w", "--terminator-out", "--newline-out", "--endline-out"):
            arg_obj.out_row_terminator = next(arg_iter)
        elif arg in ("--charset-out-error-mode",):
            arg_obj.out_charset_error_mode = next(arg_iter)
        else:
            succeeded = False
        return succeeded


    def parse_next_arg(self, arg_obj, arg, arg_iter):
        """ Parse the next argument flag from an argument iterator.

            Returns True if the argument was parsed:
            the parser should then get the next arg from arg_iter
            and keep parsing.
            Returns False if the argument was not parsed:
            the parser should try to parse the current argument
            according to any other parsing rules it may have.
        """
        succeeded = True
        if arg in ("--help", "-?"):
            arg_obj.should_print_help = True
        elif self.parse_next_input_stream_arg(arg_obj, arg, arg_iter):
            pass
        elif self.parse_next_output_stream_arg(arg_obj, arg, arg_iter):
            pass
        elif arg in ("--charset-error_mode",):
            error_mode = next(arg_iter)
            arg_obj.in_charset_error_mode = error_mode
            arg_obj.out_charset_error_mode = error_mode
        elif arg.startswith("-"):
            succeeded = False
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
            if arg_obj.parse_next_arg(arg_obj, arg, arg_iter):
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

    def open_writer(self, arg_obj, file_name, out_io, err_io):
        """ Open a CSV writer using commandline argument options. """
        return open_csv_writer(
                out_io,
                file_name,
                encoding=arg_obj.out_charset_name,
                errors=arg_obj.out_charset_error_mode,
                delimiter=arg_obj.out_delimiter,
                lineterminator=arg_obj.out_row_terminator,
                quotechar=arg_obj.out_quote_symbol,
                )

    def open_reader(self, arg_obj, file_name, in_io, err_io):
        """ Open a CSV reader using commandline argument options. """
        return open_csv_reader(
                in_io,
                file_name,
                encoding=arg_obj.in_charset_name,
                errors=arg_obj.in_charset_error_mode,
                delimiter=arg_obj.in_delimiter,
                lineterminator=arg_obj.in_row_terminator,
                quotechar=arg_obj.in_quote_symbol,
                csv_cell_width_limit=arg_obj.csv_cell_width_limit,
                )

    def main(self, argv, stdin, stdout, stderr):
        """ Implements main entry point function. """
        exe = self
        exit_code = 0
        error_message = None
        try:
            arg_obj = exe.parse_args(argv)
            if arg_obj.should_print_help:
                exe.print_help(stdout)
            else:
                exit_code = exe.execute(arg_obj, stdin, stdout, stderr)
        except IOError as exc:
            if exc.errno == errno.EPIPE:
                # (also BrokenPipeError python 3)
                # can occur when a process serving a stdio stream quits
                pass
            elif exc.errno == errno.ENOENT:
                # (also FileNotFoundError python 3)
                error_message = "File '{FileName}' not found.".format(FileName=exc.filename)
            else:
                raise
        except UnicodeError as exc:
            error_message = str(exc)
        if error_message:
            stderr.write("Error: {E}\n".format(E=error_message))
            exit_code = 1
        return exit_code

    def execute(self, arg_obj, in_io, out_io, err_io):
        """ Execute the csv processing operation. """
        exit_code = 0
        exe = self
        with exe.open_reader(arg_obj, arg_obj.in_file_name, in_io, err_io) as in_csv:
            with exe.open_writer(arg_obj, arg_obj.out_file_name, out_io, err_io) as out_csv:
                for row in exe.process(in_csv):
                    out_csv.writerow(row)
        return exit_code

    def process(self, rows):
        """ Return a generator that will process the input rows. """
        arg_obj = self
        #in_row_terminator = arg_obj.in_row_terminator
        out_row_terminator = arg_obj.out_row_terminator
        in_row_offset_start = arg_obj.in_row_offset_start
        in_row_count_max = arg_obj.in_row_count_max
        out_row_count_max = arg_obj.out_row_count_max

        cr_newline = '\r'
        lf_newline = '\n'
        crlf_newline = '\r\n'
        out_newline = out_row_terminator

        in_row_count = 0
        out_row_count = 0
        for in_row in rows:
            if in_row_count_max is not None and in_row_count_max <= in_row_count:
                break
            elif out_row_count_max is not None and out_row_count_max <= out_row_count:
                break
            in_row_count += 1
            if in_row_count <= in_row_offset_start:
                continue
            out_row = list(in_row)
            column_count = len(out_row)
            for column_position in irange(column_count):
                cell_value = out_row[column_position]
                # fix newline characters in the data
                # (some tools - like postgres - can't handle mixed newline chars)
                if cell_value is not None:
                    # replace crlf with lf, then we will replace lf's with the output newline,
                    #  this prevents us from turning a crlf into a double newline
                    cell_value = cell_value.replace(crlf_newline, lf_newline)
                    cell_value = cell_value.replace(cr_newline, lf_newline)
                    cell_value = cell_value.replace(lf_newline, out_newline)
                    out_row[column_position] = cell_value
            yield out_row
            out_row_count += 1


def main(argv, stdin, stdout, stderr):
    """ Main entry point for program. """
    exe = CsvTranslateProcessor()
    return exe.main(argv, stdin, stdout, stderr)


def console_main():
    """ Main entry point when invoked from executable wrapper. """
    return main(sys.argv, sys.stdin, sys.stdout, sys.stderr)


if __name__ == "__main__":
    sys.exit(console_main())
