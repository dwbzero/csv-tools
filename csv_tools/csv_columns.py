##  Copyright (c) 2016 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##

help_text = (
    "CSV-COLUMNS tool version 20160919:20170215\n"
    "Print column names and transpose delimited text encodings\n"
    "Copyright (c) 2016 Upstream Research, Inc.  All Rights Reserved.\n"
    "\n"
    "csv-columns [OPTIONS] [InputFile]\n"
    "\n"
    "OPTIONS\n"
    "    -E {E}  Input file text encoding (default=utf-8)\n"
    "    -e {E}  Output file text encoding (default=utf-8)\n"
    "    -K {N}  Number of rows to skip over (default=0)\n"
    "    -N {N}  Number of rows to transpose, or 'all' (default=1)\n"
    "    -o {F}  Output file name\n"
    "    -S {S}  Input file field delimiter\n"
    "    -s {S}  Output file field delimiter\n"
)

import sys
import csv
import io

from ._csv_helpers import (
    decode_delimiter_name
    ,decode_charset_name
    ,decode_newline
    )

def main(arg_list, stdin, stdout, stderr):
    in_io = stdin
    out_io = stdout
    err_io = stderr
    show_help = False
    input_file_name = None
    output_file_name = None
    input_delimiter = ','
    output_delimiter = ','
    # 'std' will be translated to the standard line break decided by csv_helpers.decode_newline
    input_row_terminator = 'std'
    output_row_terminator = 'std'
    input_charset_name = 'utf_8_sig'
    output_charset_name = 'utf_8'
    output_charset_error_mode = 'strict'  # 'strict' | 'ignore' | 'replace' | 'backslashreplace'
    input_charset_error_mode = 'strict'  # 'strict' | 'ignore' | 'replace' | 'backslashreplace'
    input_row_start = 0
    input_row_count_max = 1
    csv_cell_width_limit = 4*1024*1024  # python default is 131072 = 0x00020000
    # [20160916 [db] I avoided using argparse in order to retain some flexibility for command syntax]
    arg_count = len(arg_list)
    arg_index = 1
    while (arg_index < arg_count):
        arg = arg_list[arg_index]
        if (arg == "--help" 
          or arg == "-?"
          ):
            show_help = True
        elif (arg == "-K"
          or arg == "--row-start"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                input_row_start = int(arg)
        elif (arg == "-N"
          or arg == "--rows-in"
          or arg == "--columns-out"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                if (arg == "all"
                  or arg == "ALL"
                  ):
                    input_row_count_max = None
                else:
                    input_row_count_max = int(arg)
        elif (arg == "-o"
          or arg == "--output"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                output_file_name = arg
        elif (arg == "-E"
          or arg == "--charset-in"
          or arg == "--encoding-in"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                input_charset_name = arg
        elif (arg == "-e"
          or arg == "--charset-out"
          or arg == "--encoding-out"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                output_charset_name = arg
        elif (arg == "--charset-in-error-mode"
        ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                input_charset_error_mode = arg
        elif (arg == "--charset-out-error-mode"
        ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                output_charset_error_mode = arg
        elif (arg == "--charset-error-mode"
        ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                input_charset_error_mode = arg
                output_charset_error_mode = arg
        elif (arg == "-S"
          or arg == "--separator-in"
          or arg == "--delimiter-in"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                input_delimiter = arg
        elif (arg == "-s"
          or arg == "--separator-out"
          or arg == "--delimiter-out"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                output_delimiter = arg
        elif (arg == "-W"
          or arg == "--terminator-in"
          or arg == "--newline-in"
          or arg == "--endline-in"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                input_row_terminator = arg
        elif (arg == "-w"
          or arg == "--terminator-out"
          or arg == "--newline-out"
          or arg == "--endline-out"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                output_row_terminator = arg
        elif (arg == "--cell-width-limit"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                csv_cell_width_limit = int(arg)
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
                )
            out_csv = csv.writer(
                out_io
                ,delimiter=output_delimiter
                ,lineterminator=output_row_terminator
                )

            execute(
                in_csv
                , out_csv
                , input_delimiter
                , output_delimiter
                , input_row_start
                , input_row_count_max
                )
        except BrokenPipeError:
            pass
        finally:
            if (None != in_file):
                in_file.close()
                in_file = None
            if (None != out_file):
                out_file.close()
                out_file = None


def execute(in_csv, out_csv, input_delimiter, output_delimiter, in_row_offset_start, in_row_count_max):
    end_row = None
    end_cell = None
    buf_rows = []
    in_column_count_max = 0
    in_column_count = 0
    in_row_offset_max = in_row_count_max
    if (None != in_row_offset_max):
        in_row_offset_max += in_row_offset_start
    in_row_offset = 0
    in_row_count = 0
    in_row = next(in_csv, end_row)
    while (end_row != in_row
      and (None == in_row_offset_max  or  in_row_offset_max > in_row_offset)
      ):
        in_column_count = len(in_row)
        if (in_column_count_max < in_column_count):
            in_column_count_max = in_column_count
        if (in_row_offset_start <= in_row_offset):
            buf_rows.append(in_row)
            in_row_count += 1
        in_row_offset += 1
        in_row = next(in_csv, end_row)
    in_row_count_max = in_row_count
    in_column_count = 0
    while (in_column_count_max > in_column_count):
        out_row = []
        in_row_count = 0
        while (in_row_count_max > in_row_count):
            in_row = buf_rows[in_row_count]
            out_cell = ""
            if (len(in_row) > in_column_count):
                out_cell = in_row[in_column_count]
            out_row.append(out_cell)
            in_row_count += 1
        out_csv.writerow(out_row)
        in_column_count += 1



def console_main():
    main(sys.argv, sys.stdin, sys.stdout, sys.stderr)

        
if __name__ == "__main__":
    console_main()
