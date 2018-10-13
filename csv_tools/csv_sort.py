##  Copyright (c) 2016-2017 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##

## #python-3.x
## python 2 does not work due mostly to issues with csv and io modules with unicode data

help_text = (
    "CSV-SORT tool version 20170919\n"
    "Sort rows in a CSV file\n"
    "Copyright (c) 2016-2017 Upstream Research, Inc.  All Rights Reserved.\n"
    "\n"
    "csv-sort [OPTIONS] ColumnList [InputFile]\n"
    "\n"
    "OPTIONS\n"
    "    -N {N}  Maximum number of rows to sort at a time (default=ALL)\n"
    "    -n {N}  Maximum number of rows to write (default=ALL)\n"
    "    -o {F}  Output file name\n"
    "\n"
    "ColumnList is a comma-separated list of column names to be used\n"
    "as sort keys.\n"
    "\n"
    "Rows are sorted in memory.\n"
    "Memory usage can be controlled (somewhat) with the -N option.\n"
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
    in_key_column_name_list_str = None
    in_key_column_name_list = None
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
            if (None == in_key_column_name_list_str):
                in_key_column_name_list_str = arg
            elif (None == input_file_name):
                input_file_name = arg
        arg_index += 1

    if (None != in_key_column_name_list_str):
        in_key_column_name_list = in_key_column_name_list_str.split(',')

    if (None == in_key_column_name_list):
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
                ,in_key_column_name_list
                ,input_row_count_max
                ,output_row_count_max
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
    ,in_key_column_name_list
    ,in_row_count_max
    ,out_row_count_max
):
    end_row = None
    
    in_header_row = next(in_csv, end_row)
    # make a list with a slot for each sort key column name
    in_key_column_position_list = []
    in_key_column_count = len(in_key_column_name_list)
    in_key_column_position = 0
    while (in_key_column_position < in_key_column_count):
        in_key_column_position_list.append(None)
        in_key_column_position += 1
    
    # find the positions of the key columns within the csv file
    if (None != in_header_row):
        in_column_position = 0
        in_column_count = len(in_header_row)
        while (in_column_position < in_column_count):
            in_column_name = in_header_row[in_column_position]
            in_column_name_norm = normalize_column_name(in_column_name)
            in_key_column_position = 0
            found_key_column_position = None
            while (None == found_key_column_position
                and in_key_column_position < in_key_column_count
            ):
                in_key_column_name = in_key_column_name_list[in_key_column_position]
                in_key_column_name_norm = normalize_column_name(in_key_column_name)
                if (in_key_column_name_norm == in_column_name_norm):
                    found_key_column_position = in_key_column_position
                in_key_column_position += 1
            if (None != found_key_column_position):
                in_key_column_position_list[found_key_column_position] = in_column_position
            in_column_position += 1

    # define a row key "generator" function which can in-turn be used to define a row key tuple.
    # instead of using this "yield expression" mechanism,
    #  we could have created a list of the key values
    #  but it seemed like better practice to use a light-weight iterator
    #  instead of a throw-away list
    def get_row_key_iter(in_row):
        key_pos = 0
        col_pos = None
        while (key_pos < len(in_key_column_position_list)):
            col_pos = in_key_column_position_list[key_pos]
            col_value = None
            if (None != col_pos
                and 0 <= col_pos
                and col_pos < len(in_row)
            ):
                col_value = in_row[col_pos]
            yield col_value
            key_pos += 1

    # define a key extraction function
    #  which can extract a hashable key object from a csv row
    def get_row_key(in_row):
        return tuple(get_row_key_iter(in_row))

    out_row_count = 0
    in_row = next(in_csv, end_row)
    while (end_row != in_row
        and (None == out_row_count_max or out_row_count < out_row_count_max)
    ):
        in_row_count = 0
        in_row_list = list()
        while (end_row != in_row
            and (None == in_row_count_max or in_row_count < in_row_count_max)
        ):
            in_row_list.append(in_row)
            in_row_count += 1
            in_row = next(in_csv, end_row)
        
        in_row_list.sort(key=get_row_key)
        out_row_iter = iter(in_row_list)
        out_row = next(out_row_iter, end_row)
        while (end_row != out_row
            and (None == out_row_count_max or out_row_count < out_row_count_max)
        ):
            out_csv.writerow(out_row)
            out_row_count += 1
            out_row = next(out_row_iter, end_row)

def normalize_column_name(column_name):
    norm_column_name = column_name
    if (None != norm_column_name):
        norm_column_name = norm_column_name.strip()
        norm_column_name = norm_column_name.lower()
    return norm_column_name



def console_main():
    main(sys.argv, sys.stdin, sys.stdout, sys.stderr)

        
if __name__ == "__main__":
    console_main()
