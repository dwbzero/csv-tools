##  Copyright (c) 2016-2017 Upstream Research, Inc.  All Rights Reserved.  ##

## #python-3.x
## python 2 does not work due mostly to issues with csv and io modules with unicode data

help_text = (
    "CSV-PREPEND tool version 20170918\n"
    "Insert a header row into a CSV stream\n"
    "Copyright (c) 2016-2017 Upstream Research, Inc.  All Rights Reserved.\n"
    "\n"
    "csv-prepend [OPTIONS] ColumnValueList [InputFile]\n"
    "\n"
    "OPTIONS\n"
    "    -E {E}  Input file text encoding (e.g. 'utf-8', 'windows-1252')\n"
    "    -e {E}  Output file text encoding (e.g. 'utf-8', 'windows-1252')\n"
    "    -K {N}  Number of rows to skip from the input (default=0)\n"
    "    -N {N}  Maximum number of rows to read (default=ALL)\n"
    "    -n {N}  Maximum number of rows to write (default=ALL)\n"
    "    -o {F}  Output file name\n"
    "    -S {S}  Input file field delimiter (default ',')\n"
    "    -s {S}  Output file field delimiter (default ',')\n"
    "\n"
    "ColumnValueList is a comma separated list of values to be inserted as \n"
    "the first row.\n"
    "It is possible to replace the header row using the -K option.\n"
)

import sys
import csv
import io

from csv_helpers import decode_delimiter_name, decode_charset_name, decode_newline

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
    csv_cell_width_limit = 4*1024*1024  # python default is 131072 = 0x00020000
    input_row_start_offset = 0
    input_row_count_max = None
    output_row_count_max = None
    head_row_str = None
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
        elif (arg == "-K"
            or arg == "--row-offset-in"
            or arg == "--offset"
            or arg == "--skip"
        ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                input_row_start_offset = int(arg)
        elif (arg == "-N"
            or arg == "--row-count-in"
        ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                if ('ALL' == arg.upper()):
                    input_row_count_max = None
                else:
                    input_row_count_max = int(arg)
        elif (arg == "-n"
            or arg == "--row-count-out"
        ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                if ('ALL' == arg.upper()):
                    output_row_count_max = None
                else:
                    output_row_count_max = int(arg)
        elif (None != arg
          and 0 < len(arg)
          ):
            if (None == head_row_str):
                head_row_str = arg
            elif (None == input_file_name):
                input_file_name = arg
        arg_index += 1

    head_row = None
    if (None != head_row_str):
        head_row = head_row_str.split(',')

    if (None == head_row):
        show_help = True

    if (show_help):
        out_io.write(help_text)
    else:
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
                ,out_csv
                ,input_row_terminator
                ,output_row_terminator
                ,input_row_start_offset
                ,input_row_count_max
                ,output_row_count_max
                ,head_row
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

def execute(
    in_csv
    ,out_csv
    ,input_row_terminator
    ,output_row_terminator
    ,in_row_offset_start
    ,in_row_count_max
    ,out_row_count_max
    ,new_head_row
):
    # first write the new row
    out_csv.writerow(new_head_row)    
    
    # then write the output using the csv-translate code
    # [20170918 [db] This is just a copy of the code from -csv-translate;
    #  it is a bit overkill to include all of this here]
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

if __name__ == "__main__":
    main(sys.argv, sys.stdin, sys.stdout, sys.stderr)
