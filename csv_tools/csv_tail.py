##  Copyright (c) 2016-2017 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##

## #python-3.x
## python 2 does not work due mostly to issues with csv and io modules with unicode data

help_text = (
    "CSV-TAIL tool version 20170609:20170920\n"
    "Filter the last rows of a CSV stream\n"
    "\n"
    "csv-tail [OPTIONS] [InputFile]\n"
    "\n"
    "OPTIONS\n"
    "    -!      Reverse mode; write everything except the tail\n"
    "    -h      Always write the header row from the input\n"
    "    -K {N}  Number of rows to skip from the input (default=0)\n"
    "    -N {N}  Maximum number of input rows to read (default=ALL)\n"
    "    -n {N}  Maximum number of tail rows to write (default=1)\n"
    "    -o {F}  Output file name\n"
    "\n"
    "By default tail rows are written to the output stream.\n"
    "If the -! option is used, everything except the tail rows will be written.\n"
    "\n"
    "Tail rows will be stored in memory before being printed,\n"
    "thus this tool will use more memory when more tail rows are filtered.\n"
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
    tail_row_count = 1
    reverse_mode_enabled = False
    header_enabled = False
    # [20160916 [db] I avoided using argparse in order to retain some flexibility for command syntax]
    arg_count = len(arg_list)
    arg_index = 1
    while (arg_index < arg_count):
        arg = arg_list[arg_index]
        if (arg == "--help" 
          or arg == "-?"
          ):
            show_help = True
        elif (arg == "-!"
          or arg == "--crop"
          ):
            reverse_mode_enabled = True
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
            or arg == "--tail-row-count"
        ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                tail_row_count = int(arg)
        elif (arg == "-h"
            or arg == "--header-out"
        ):
            header_enabled = True
        elif (None != arg
          and 0 < len(arg)
          ):
            if (None == input_file_name):
                input_file_name = arg
        arg_index += 1

    if (None == tail_row_count
        or 0 > tail_row_count
    ):
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
                ,input_row_start_offset
                ,input_row_count_max
                ,output_row_count_max
                ,tail_row_count
                ,reverse_mode_enabled
                ,header_enabled
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
    ,tail_row_count_max
    ,reverse_mode_enabled
    ,should_write_header_row
):
    end_row = None
    
    should_write_head_rows = False
    should_write_tail_rows = True
    if (reverse_mode_enabled):
        should_write_head_rows = True
        should_write_tail_rows = False
    
    out_header_row = None
    if (should_write_header_row):
        in_header_row = next(in_csv, end_row)
        if (end_row != in_header_row):
            out_header_row = list(in_header_row)
        if (None != out_header_row):
            out_csv.writerow(out_header_row)

    tail_row_circ_list = []
    tail_row_circ_list_position = 0
    in_row_count = 0
    out_row_count = 0
    in_row = next(in_csv, end_row)
    while (end_row != in_row
        and (None == in_row_count_max or in_row_count < in_row_count_max)
        and (None == out_row_count_max or out_row_count < out_row_count_max)
    ):
        in_row_count += 1
        if (in_row_offset_start < in_row_count):
            out_row = end_row
            if (tail_row_count_max > len(tail_row_circ_list)):
                tail_row_circ_list.append(in_row)
            elif (tail_row_count_max == len(tail_row_circ_list)
                and tail_row_circ_list_position < len(tail_row_circ_list)
                ):
                # take the oldest row out of the queue,
                #  replace it with the current input row
                #  and move our old-row position to the next slot
                out_row = tail_row_circ_list[tail_row_circ_list_position]
                tail_row_circ_list[tail_row_circ_list_position] = in_row
                tail_row_circ_list_position += 1
                if (tail_row_count_max <= tail_row_circ_list_position):
                    tail_row_circ_list_position -= tail_row_count_max
            if (end_row != out_row
                and should_write_head_rows
             ):
                out_csv.writerow(out_row)
                out_row_count += 1
        in_row = next(in_csv, end_row)
    if (should_write_tail_rows):
        tail_row_count = len(tail_row_circ_list)
        tail_row_position = 0
        while (tail_row_position < tail_row_count
            and (None == out_row_count_max or out_row_count < out_row_count_max)
        ):
            out_row = tail_row_circ_list[tail_row_circ_list_position]
            tail_row_circ_list_position += 1
            if (tail_row_count <= tail_row_circ_list_position):
                tail_row_circ_list_position -= tail_row_count
            out_csv.writerow(out_row)
            out_row_count += 1
            tail_row_position += 1


def console_main():
    main(sys.argv, sys.stdin, sys.stdout, sys.stderr)

        
if __name__ == "__main__":
    console_main()
