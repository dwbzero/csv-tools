##  Copyright (c) 2016-2019 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##

## #python-3.x
## python 2 does not work due mostly to issues with csv and io modules with unicode data

## This file contains a nearly complete commandline tool implementation.
##  It makes use of a small submodule '_csvhelpers' which provides 
##   some basic functions to establish consistency among other, related commandline tools.
## This file is organized into a sequence of sections
##   1. Commandline help text
##   2. Module Imports
##   3. main() function implementation
##   3.1.  Commandline argument parsing loop
##   3.2.  Commandline argument validation and processing
##   3.3.  Command initialization (i.e. opening CSV streams, etc.) and invocation.
##   4. execute() function implementation (i.e. Command implementation)
##      ** execute() is where the real work happens **
##   5. helper functions (if any)
##   6. main() entry point invocation

help_text = """CSV-TRANSLATE tool version 20160916:20190529
Translates delimited text encodings

csv-translate [OPTIONS] [InputFile]

OPTIONS
    -E {E}  Input file text encoding (e.g. 'utf-8', 'windows-1252')
    -e {E}  Output file text encoding (e.g. 'utf-8', 'windows-1252')
    -K {N}  Number of rows to skip from the input (default=0)
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

import sys
import csv
import io

from ._csv_helpers import (
    decode_delimiter_name
    ,decode_charset_name
    ,decode_newline
    ,decode_quote_symbol_name
    )


def main(arg_list, stdin, stdout, stderr):
    exit_code = 0
    in_io = stdin
    out_io = stdout
    err_io = stderr
    show_help = False
    error_message = None
    input_file_name = None
    output_file_name = None
    input_delimiter = ','
    input_quote_symbol = '"'
    output_delimiter = ','
    output_quote_symbol = '"'
    # 'std' will be translated to the standard line break decided by csv_helpers.decode_newline
    input_row_terminator = 'std'
    output_row_terminator = 'std'
    input_charset_name = 'utf_8_sig'
    output_charset_name = 'utf_8'
    output_charset_error_mode = 'strict'  # 'strict' | 'ignore' | 'replace' | 'backslashreplace'
    input_charset_error_mode = 'strict'  # 'strict' | 'ignore' | 'replace' | 'backslashreplace'
    csv_cell_width_limit = 4*1024*1024  # python default is 131072 = 0x00020000
    input_row_start_offset = 0
    input_row_count_max = None
    output_row_count_max = None
    # [20160916 [db] I avoided using argparse in order to retain some flexibility for command syntax]
    arg_count = len(arg_list)
    arg_index = 1
    while (arg_index < arg_count):
        arg = arg_list[arg_index]
        if (arg == "--help" 
          or arg == "-?"
          ):
            show_help = True
        elif (arg == "-o"
          or arg == "--output"
          ):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                output_file_name = arg
        elif (arg == "-E"
          or arg == "--charset-in"
          or arg == "--encoding-in"
          ):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                input_charset_name = arg
        elif (arg == "-e"
          or arg == "--charset-out"
          or arg == "--encoding-out"
          ):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                output_charset_name = arg
        elif (arg == "--charset-in-error-mode"
        ):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                input_charset_error_mode = arg
        elif (arg == "--charset-out-error-mode"
        ):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                output_charset_error_mode = arg
        elif (arg == "--charset-error-mode"
        ):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                input_charset_error_mode = arg
                output_charset_error_mode = arg
        elif (arg == "-S"
          or arg == "--separator-in"
          or arg == "--delimiter-in"
          ):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                input_delimiter = arg
        elif (arg == "-s"
          or arg == "--separator-out"
          or arg == "--delimiter-out"
          ):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                output_delimiter = arg
        elif (arg == "-Q"
          or arg == "--quote-in"
          ):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                input_quote_symbol = arg
        elif (arg == "-q"
          or arg == "--quote-out"
          ):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                output_quote_symbol = arg
        elif (arg == "-W"
          or arg == "--terminator-in"
          or arg == "--newline-in"
          or arg == "--endline-in"
          ):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                input_row_terminator = arg
        elif (arg == "-w"
          or arg == "--terminator-out"
          or arg == "--newline-out"
          or arg == "--endline-out"
          ):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                output_row_terminator = arg
        elif (arg == "--cell-width-limit"
          ):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                csv_cell_width_limit = int(arg)
        elif (arg == "-K"
            or arg == "--row-offset-in"
            or arg == "--offset"
            or arg == "--skip"
        ):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                input_row_start_offset = int(arg)
        elif (arg == "-N"
            or arg == "--row-count-in"
        ):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                if ('ALL' == arg.upper()):
                    input_row_count_max = None
                else:
                    input_row_count_max = int(arg)
        elif (arg == "-n"
            or arg == "--row-count-out"
        ):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                if ('ALL' == arg.upper()):
                    output_row_count_max = None
                else:
                    output_row_count_max = int(arg)
        elif (None != arg
          and 0 < len(arg)
          ):
            if (None == input_file_name):
                input_file_name = arg
        arg_index += 1

    if (show_help):
        out_io.write(help_text)
    else:
        # set global CSV column width
        if (None != csv_cell_width_limit):
            csv.field_size_limit(csv_cell_width_limit)

        input_charset_name = decode_charset_name(input_charset_name)
        output_charset_name = decode_charset_name(output_charset_name)
        input_row_terminator = decode_newline(input_row_terminator)
        output_row_terminator = decode_newline(output_row_terminator)
        input_delimiter = decode_delimiter_name(input_delimiter)
        output_delimiter = decode_delimiter_name(output_delimiter)
        input_quote_symbol = decode_quote_symbol_name(input_quote_symbol)
        output_quote_symbol = decode_quote_symbol_name(output_quote_symbol)
        in_file = None
        out_file = None
        try:
            read_text_io_mode = 'rt'
            #in_newline_mode = ''  # don't translate newline chars
            in_newline_mode = input_row_terminator
            in_file_id = input_file_name
            should_close_in_file = True
            if (None == in_file_id):
                in_file_id = in_io.fileno()
                should_close_in_file = False
            in_io = io.open(
                 in_file_id
                ,mode=read_text_io_mode
                ,encoding=input_charset_name
                ,newline=in_newline_mode
                ,errors=input_charset_error_mode
                ,closefd=should_close_in_file
                )
            if (should_close_in_file):
                in_file = in_io

            write_text_io_mode = 'wt'
            out_newline_mode=''  # don't translate newline chars
            #out_newline_mode = output_row_terminator
            out_file_id = output_file_name
            should_close_out_file = True
            if (None == out_file_id):
                out_file_id = out_io.fileno()
                should_close_out_file = False
            out_io = io.open(
                 out_file_id
                ,mode=write_text_io_mode
                ,encoding=output_charset_name
                ,newline=out_newline_mode
                ,errors=output_charset_error_mode
                ,closefd=should_close_out_file
                )
            if (should_close_out_file):
                out_file = out_io

            in_csv = csv.reader(
                in_io
                ,delimiter=input_delimiter
                ,lineterminator=input_row_terminator
                ,quotechar=input_quote_symbol
                )
            out_csv = csv.writer(
                out_io
                ,delimiter=output_delimiter
                ,lineterminator=output_row_terminator
                ,quotechar=output_quote_symbol
                )
            exit_code = execute(
                in_csv
                ,out_csv
                ,input_row_terminator
                ,output_row_terminator
                ,input_row_start_offset
                ,input_row_count_max
                ,output_row_count_max
                )
        except BrokenPipeError:
            # this error can occur when a process serving a stdio stream quits
            pass
        except FileNotFoundError as exc:
            error_message = "File '{FileName}' not found.".format(FileName=exc.filename)
            exit_code = -1
        except UnicodeError as exc:
            error_message = str(exc)
            exit_code = -1
        finally:
            if (None != in_file):
                in_file.close()
                in_file = None
            if (None != out_file):
                out_file.close()
                out_file = None
    if (None != error_message):
        err_io.write("Error: {E}\n".format(E=error_message))

    return exit_code

def execute(
    in_csv
    ,out_csv
    ,input_row_terminator
    ,output_row_terminator
    ,in_row_offset_start
    ,in_row_count_max
    ,out_row_count_max
):
    exit_code = 0
    end_row = None
    cr_newline = '\r'
    lf_newline = '\n'
    crlf_newline = '\r\n'
    out_newline = output_row_terminator
    
    in_row_count = 0
    out_row_count = 0
    in_row = next(in_csv, end_row)
    while (end_row != in_row
        and (None == in_row_count_max or in_row_count < in_row_count_max)
        and (None == out_row_count_max or out_row_count < out_row_count_max)
    ):
        in_row_count += 1
        if (in_row_offset_start < in_row_count):
            out_row = list(in_row)
            column_count = len(out_row)
            column_position = 0
            while (column_position < column_count):
                cell_value = out_row[column_position]
                # fix newline characters in the data
                # (some tools - like postgres - can't handle mixed newline chars)
                if (None != cell_value):
                    # replace crlf with lf, then we will replace lf's with the output newline,
                    #  this prevents us from turning a crlf into a double newline
                    cell_value = cell_value.replace(crlf_newline, lf_newline)
                    cell_value = cell_value.replace(cr_newline, lf_newline)
                    cell_value = cell_value.replace(lf_newline, out_newline)
                    out_row[column_position] = cell_value
                column_position += 1
            out_csv.writerow(out_row)
            out_row_count += 1
        in_row = next(in_csv, end_row)
    return exit_code

# console_main() is the main entry point when invoked from an executable wrapper.
def console_main():
    return main(sys.argv, sys.stdin, sys.stdout, sys.stderr)

        
if __name__ == "__main__":
    sys.exit(console_main())
