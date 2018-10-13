##  Copyright (c) 2016-2017 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##

## #python-3.x
## python 2 does not work due mostly to issues with csv and io modules with unicode data

help_text = (
    "CSV-COL2ROW tool version 20170920\n"
    "Transposes a subset of named CSV columns into rows\n"
    "Copyright (c) 2016-2017 Upstream Research, Inc.  All Rights Reserved.\n"
    "\n"
    "csv-col2row [OPTIONS] OutNameColumn OutValueColumn InColumnList [InputFile]\n"
    "\n"
    "OPTIONS\n"
    "    -N {N}  Number of rows to read from input (default=ALL)\n"
    "    -n {N}  Number of rows to write to output (default=ALL)\n"
    "    -o {F}  Output file name\n"
    "\n"
    "InColumnList is a comma-separated list of column names from the input stream.\n"
    "A new CSV stream will be output that will have all the columns from the input\n"
    "except for the columns from InColumnList.  It will also add two new columns\n"
    "for the OutNameColumn and OutValueColumn arguments.\n"
    "For each row of the input, a new row will be created for each column from\n"
    "InColumnList, the column name will be put into OutNameColumn and\n"
    "the column's value will be put into OutValueColumn in the output stream.\n"
    "\n"
    "A range of columns can be specified by using '*' as a column name,\n"
    "for example:  Pop10,Pop11,Pop12,Pop13\n"
    "is equivalent to: Pop10,*,Pop13\n"
)

import sys
import csv
import io

from ._csv_helpers import (
    decode_delimiter_name
    ,decode_charset_name
    ,decode_newline
    ,normalize_column_name
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
    output_name_column_name = None
    output_value_column_name = None
    input_column_name_list_str = None
    input_column_name_list = None
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
            if (None == output_name_column_name):
                output_name_column_name = arg
            elif (None == output_value_column_name):
                output_value_column_name = arg
            elif (None == input_column_name_list_str):
                input_column_name_list_str = arg
            elif (None == input_file_name):
                input_file_name = arg
        arg_index += 1

    if (None != input_column_name_list_str):
        input_column_name_list = input_column_name_list_str.split(',')
    if (None == input_column_name_list):
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
                ,output_name_column_name
                ,output_value_column_name
                ,input_column_name_list
                ,input_row_start_offset
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
    ,out_name_column_name
    ,out_value_column_name
    ,selected_column_name_list
    ,in_row_start_position
    ,in_row_count_max
    ,out_row_count_max
):
    selected_range_column_name_symbol = '*'
    end_row = None

    out_header_row = None
    column_action_copy = 'c'
    column_action_mkrow = 'r'
    in_column_action_list = []
    in_header_row = next(in_csv, end_row)
    if (None != in_header_row):
        # make a list of normalized column names from the input stream
        in_column_name_norm_list = []
        in_column_position = 0
        while (in_column_position < len(in_header_row)):
            in_column_name = in_header_row[in_column_position]
            in_column_name_norm = normalize_column_name(in_column_name)
            in_column_name_norm_list.append(in_column_name_norm)
            in_column_position += 1
        
        # make a list of normalized selected column names that will be transposed into rows;
        # this is a bit messy since we allow a special "range selection" symbol
        # which we need to expand into actual column names
        in_column_position = 0
        selected_column_position = 0
        selected_column_name_norm_list = []
        selected_column_name_norm = None
        while (selected_column_position < len(selected_column_name_list)):
            selected_column_name = selected_column_name_list[selected_column_position]
            selected_column_name_norm = None
            next_selected_column_name_norm = None
            if (selected_range_column_name_symbol == selected_column_name):
                if (selected_column_position+1 < len(selected_column_name_list)):
                    next_selected_column_name = selected_column_name_list[selected_column_position+1]
                    next_selected_column_name_norm = normalize_column_name(next_selected_column_name)
            else:
                selected_column_name_norm = normalize_column_name(selected_column_name)
            
            if (None != selected_column_name_norm):
                in_column_position = 0
                found_column_position = None
                while (in_column_position < len(in_column_name_norm_list)
                    and None == found_column_position
                ):
                    in_column_name_norm = in_column_name_norm_list[in_column_position]
                    if (selected_column_name_norm == in_column_name_norm):
                        found_column_position = in_column_position
                        selected_column_name_norm_list.append(in_column_name_norm)
                    in_column_position += 1
            else:
                found_column_position = None
                while (in_column_position < len(in_column_name_norm_list)
                    and None == found_column_position
                ):
                    in_column_name_norm = in_column_name_norm_list[in_column_position]
                    if (next_selected_column_name_norm == in_column_name_norm):
                        found_column_position = in_column_position
                    else:
                        selected_column_name_norm_list.append(in_column_name_norm)
                    in_column_position += 1
            selected_column_position += 1
            # end while
        # make a parallel list of "actions" for each of the input columns;
        # this will tell us if the column should be copied to the output directly,
        # or if the column needs to be expanded into a new row
        in_column_position = 0
        while (in_column_position < len(in_column_name_norm_list)):
            in_column_name_norm = in_column_name_norm_list[in_column_position]
            found_column_position = None
            selected_column_position = 0
            while (selected_column_position < len(selected_column_name_norm_list)
                and None == found_column_position
            ):
                selected_column_name_norm = selected_column_name_norm_list[selected_column_position]
                if (selected_column_name_norm == in_column_name_norm):
                    found_column_position = selected_column_position
                selected_column_position += 1
            if (None == found_column_position):
                in_column_action_list.append(column_action_copy)
            else:
                in_column_action_list.append(column_action_mkrow)
            in_column_position += 1
        # make a header row for the output
        out_header_row = []
        in_column_position = 0
        while (in_column_position < len(in_header_row)):
            in_column_name = in_header_row[in_column_position]
            in_column_action = in_column_action_list[in_column_position]
            if (column_action_copy == in_column_action):
                out_header_row.append(in_column_name)
            in_column_position += 1
        out_header_row.append(out_name_column_name)
        out_header_row.append(out_value_column_name)

        out_csv.writerow(out_header_row)

    in_row_count = 0
    out_row_count = 0
    in_row = next(in_csv, end_row)
    while (end_row != in_row
        and (None == in_row_count_max or in_row_count < in_row_count_max)
        and (None == out_row_count_max or out_row_count < out_row_count_max)
    ):
        # build up a base row of all column values that will be copied directly
        out_row_base = []
        in_column_position = 0
        while (in_column_position < len(in_column_action_list)):
            in_column_value = None
            if (in_column_position < len(in_row)):
                in_column_value = in_row[in_column_position]
            in_column_action = in_column_action_list[in_column_position]
            if (column_action_copy == in_column_action):
                out_row_base.append(in_column_value)
            in_column_position += 1
        
        # for each selected column, create a new row from the base
        in_column_position = 0
        while (in_column_position < len(in_column_action_list)
            and in_column_position < len(in_header_row)
            and (None == out_row_count_max or out_row_count < out_row_count_max) 
            and in_row_start_position <= in_row_count
            ):
            in_column_name = in_header_row[in_column_position]
            in_column_value = None
            if (in_column_position < len(in_row)):
                in_column_value = in_row[in_column_position]
            in_column_action = in_column_action_list[in_column_position]
            if (column_action_mkrow == in_column_action):
                out_row = list(out_row_base)
                out_row.append(in_column_name)
                out_row.append(in_column_value)
                out_csv.writerow(out_row)
                out_row_count += 1
            in_column_position += 1

        in_row_count += 1
        in_row = next(in_csv, end_row)



def console_main():
    main(sys.argv, sys.stdin, sys.stdout, sys.stderr)

        
if __name__ == "__main__":
    console_main()
