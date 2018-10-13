##  Copyright (c) 2016-2017 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##

## #python-3.x
## python 2 does not work due mostly to issues with csv and io modules with unicode data

help_text = (
    "CSV-HEADMERGE tool version 20170609\n"
    "Merge multiple CSV header rows into one\n"
    "Copyright (c) 2016-2017 Upstream Research, Inc.  All Rights Reserved.\n"
    "\n"
    "csv-headmerge [OPTIONS] [InputFile]\n"
    "\n"
    "OPTIONS\n"
    "    -j {S}  Cell-join separator (default=space)\n"
    "    -K {N}  Number of rows to skip from the input (default=0)\n"
    "    -N {N}  Number of head rows to merge (default=2)\n"
    "    -o {F}  Output file name\n"
    "\n"
    "Attempts to merge head rows of a CSV file into one 'header' row.\n"
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
    csv_cell_width_limit = 4*1024*1024  # python default is 131072 = 0x00020000
    input_row_start_offset = 0
    input_row_count_max = None
    output_row_count_max = None
    input_head_row_count = 2
    output_cell_join_delimiter = ' '
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
                input_head_row_count = int(arg)
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
        elif (arg == "-j"
            or arg == "--join-delimtier"
        ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                output_cell_join_delimiter = arg
        elif (None != arg
          and 0 < len(arg)
          ):
            if (None == input_file_name):
                input_file_name = arg
        arg_index += 1
    
    if (1 > input_head_row_count):
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
        output_cell_join_delimiter = decode_delimiter_name(output_cell_join_delimiter)
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
                ,input_row_start_offset
                ,input_row_count_max
                ,output_row_count_max
                ,input_head_row_count
                ,output_cell_join_delimiter
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
    ,in_row_offset_start
    ,in_row_count_max
    ,out_row_count_max
    ,in_head_row_count_max
    ,out_cell_join_delimiter
):
    end_row = None
    
    in_row_count = 0
    out_row_count = 0
    out_header_row = []
    in_row = next(in_csv, end_row)
    # skip initial rows
    while (end_row != in_row
        and (None == in_row_count_max or in_row_count < in_row_count_max)
        and (in_row_offset_start > in_row_count)
    ):
        in_row_count += 1
        in_row = next(in_csv, end_row)
    
    in_head_row_count = 0
    while (end_row != in_row
        and (in_head_row_count < in_head_row_count_max)
    ):
        in_column_position = 0
        prev_nonempty_column_value = None
        while (in_column_position < len(in_row)):
            in_cell_value = in_row[in_column_position]
            if (None != in_cell_value):
                in_cell_value = in_cell_value.strip()

            out_column_name = None
            if (in_column_position < len(out_header_row)):
                out_column_name = out_header_row[in_column_position]
            
            # if the current cell is nonempty, 
            #  then remember it so we can fill across to merged columns
            # if the current cell is empty,
            #  then we should fill it in with the previous nonempty column
            #  only if no column name has come from a previous row
            if (None != in_cell_value
                and 0 < len(in_cell_value)
            ):
                prev_nonempty_column_value = in_cell_value
            elif (None == out_column_name
                or 0 == len(out_column_name)
            ):
                in_cell_value = prev_nonempty_column_value

            # if this column has no value already, then just add it
            # otherwise we must append the current cell value to it
            if (in_column_position >= len(out_header_row)):
                out_header_row.append(in_cell_value)
            else:
                out_cell_value = out_column_name
                if (None == out_cell_value
                    or 0 == len(out_cell_value)
                ):
                    out_cell_value = in_cell_value
                elif (None != in_cell_value
                    and 0 < len(in_cell_value)
                ):
                    out_cell_value += out_cell_join_delimiter + in_cell_value
                out_header_row[in_column_position] = out_cell_value
            in_column_position += 1
        in_head_row_count += 1
        in_row_count += 1
        in_row = next(in_csv, end_row)
    
    # write the merged header row
    if (0 < in_head_row_count):
        out_csv.writerow(out_header_row)
        out_row_count += 1

    # write the rest of the data without alteration
    while (end_row != in_row
        and (None == in_row_count_max or in_row_count < in_row_count_max)
        and (None == out_row_count_max or out_row_count < out_row_count_max)
    ):
        in_row_count += 1
        if (in_row_offset_start < in_row_count):
            out_row = in_row
            out_csv.writerow(out_row)
            out_row_count += 1
        in_row = next(in_csv, end_row)


def console_main():
    main(sys.argv, sys.stdin, sys.stdout, sys.stderr)

        
if __name__ == "__main__":
    console_main()
