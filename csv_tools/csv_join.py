##  Copyright (c) 2016 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##

## #python-3.x
## python 2 does not work due mostly to issues with csv and io modules with unicode data

## 20170524 ORIGIN csv-translate.py

help_text = (
    "CSV-JOIN tool version 20170524\n"
    "Joins two CSV files on common column values\n"
    "\n"
    "csv-join [OPTIONS] {INNER|OUTER} File2 Columns2 '=' Columns1 [File1]\n"
    "\n"
    "OPTIONS\n"
    "    -o {F}  Output file name\n"
    "    --column-prefix {S}  Prefix for column names from File2\n"
    "    --include-join-keys  Include columns from Column2 in the output\n"
    "\n"
    "Joins rows from File1 (or STDIN) to rows in File2 by matching column values\n"
    "for equality.  \n"
    "\n"
    "Columns1 and Columns2 are comma-separated lists of column names.\n"
    "\n"
    "File2 will be read entirely into memory and rows will be indexed.\n"
    "When a row is read from File1, corresponding rows from File2 will be\n"
    "looked-up and appended to the row from File1.\n"
    "If the INNER option is used, and if no corresponding rows are found in File2\n"
    "then the row from File1 will not be written to the output.\n"
    "If the OUTER option is used, and if no corresponding rows are found in File2\n"
    "then the row will be written to the output with an empty value for each column\n"
    "that would come from File2.\n"
    "\n"
    "By default, the join key columns from File2 will not be written to the output\n"
    "since they are redundant.\n"
    "\n"
    "Example:\n"
    "    csv-join INNER oil_wells.csv state,well_id = state,site_id  production.csv\n"
    "\n"
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
    output_charset_error_mode = 'strict'
    input_charset_error_mode = 'strict'
    csv_cell_width_limit = 4*1024*1024  # python default is 131072 = 0x00020000
    join_type_name = None
    join_operator_symbol = None
    join_table_file_name = None
    join_table_column_list_string = None
    input_column_list_string = None
    join_table_column_prefix = ''
    should_exclude_join_columns = True
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
        elif (arg == "--column-prefix"
        ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                join_table_column_prefix = arg
        elif (arg == "--include-join-keys"
            or arg == "--include-join-key"
        ):
            should_exclude_join_columns = False
        elif (None != arg
          and 0 < len(arg)
          ):
            if (None == join_type_name):
                join_type_name = arg
            elif (None == join_table_file_name):
                join_table_file_name = arg
            elif (None == join_table_column_list_string):
                join_table_column_list_string = arg
            elif (None == join_operator_symbol):
                join_operator_symbol = arg
            elif (None == input_column_list_string):
                input_column_list_string = arg
            elif (None == input_file_name):
                input_file_name = arg
        arg_index += 1

    if (None == join_table_column_list_string):
        show_help = True

    if (None == join_type_name):
        show_help = True
    else: 
        join_type_name = join_type_name.upper()
    
    if (not (join_type_name in {'INNER','OUTER'})):
        show_help = True

    if (show_help):
        out_io.write(help_text)
    else:
        column_name_separator = ','
        if (None == input_column_list_string):
            input_column_list_string = join_table_column_list_string
        
        join_table_column_name_list = None
        if (None != join_table_column_list_string):
            join_table_column_name_list = join_table_column_list_string.split(column_name_separator)
        
        input_column_name_list = None
        if (None != input_column_list_string):
            input_column_name_list = input_column_list_string.split(column_name_separator)

        input_charset_name = decode_charset_name(input_charset_name)
        output_charset_name = decode_charset_name(output_charset_name)
        input_row_terminator = decode_newline(input_row_terminator)
        output_row_terminator = decode_newline(output_row_terminator)
        input_delimiter = decode_delimiter_name(input_delimiter)
        output_delimiter = decode_delimiter_name(output_delimiter) 
        in_file = None
        out_file = None
        join_file = None
        try:
            read_text_io_mode = 'rt'
            #in_newline_mode = ''  # don't translate newline chars
            in_newline_mode = input_row_terminator
            in_file_id = input_file_name
            in_close_file = True
            if (None == in_file_id):
                in_file_id = in_io.fileno()
                in_close_file = False
            in_io = io.open(
                 in_file_id
                ,mode=read_text_io_mode
                ,encoding=input_charset_name
                ,newline=in_newline_mode
                ,errors=input_charset_error_mode
                ,closefd=in_close_file
                )
            if (in_close_file):
                in_file = in_io

            write_text_io_mode = 'wt'
            out_newline_mode=''  # don't translate newline chars
            #out_newline_mode = output_row_terminator
            out_file_id = output_file_name
            out_close_file = True
            if (None == out_file_id):
                out_file_id = out_io.fileno()
                out_close_file = False
            out_io = io.open(
                 out_file_id
                ,mode=write_text_io_mode
                ,encoding=output_charset_name
                ,newline=out_newline_mode
                ,errors=output_charset_error_mode
                ,closefd=out_close_file
                )
            if (out_close_file):
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

            join_file = io.open(
                 join_table_file_name
                ,mode=read_text_io_mode
                ,encoding=input_charset_name
                ,newline=in_newline_mode
                ,errors=input_charset_error_mode
                )
            join_csv = csv.reader(
                join_file
                ,delimiter=input_delimiter
                ,lineterminator=input_row_terminator
                )

            # execute() will close join_file,
            # but if an exception is raised, 
            # we won't know if join_file is closed, 
            # so we will end up trying to close it again
            execute(
                 in_csv
                ,out_csv
                ,join_file
                ,join_csv
                ,join_type_name
                ,join_operator_symbol
                ,join_table_column_prefix
                ,join_table_column_name_list
                ,input_column_name_list
                ,should_exclude_join_columns
                )
            # set join_file to None since execute() will have closed it
            join_file = None
        except BrokenPipeError:
            pass
        finally:
            if (None != in_file):
                in_file.close()
                in_file = None
            if (None != out_file):
                out_file.close()
                out_file = None
            if (None != join_file):
                join_file.close()
                join_file = None

def execute(
    in_csv
    ,out_csv
    ,join_file
    ,join_csv
    ,join_type_name
    ,join_operator_symbol
    ,join_column_name_prefix
    ,join_key_column_name_list
    ,in_key_column_name_list
    ,should_exclude_join_columns
):
    end_row = None

    outer_join_type = 0
    inner_join_type = 1
    join_type = outer_join_type
    if (None != join_type_name):
        if ('OUTER' == join_type_name.upper()):
            join_type = outer_join_type
        elif ('INNER' == join_type_name.upper()):
            join_type = inner_join_type

    # read join_table into a dictionary
    join_dict = dict()
    join_in_column_name_list = None
    join_norm_column_name_list = None
    join_out_column_name_list = None
    join_out_column_position_list = None
    join_key_column_position_list = None
    header_row = next(join_csv,None)
    if (None != header_row):
        join_in_column_name_list = list(header_row) # copy
        join_norm_column_name_list = []
        join_column_position = 0
        while (join_column_position < len(join_in_column_name_list)):
            column_name = join_in_column_name_list[join_column_position]
            norm_column_name = normalize_column_name(column_name)
            join_norm_column_name_list.append(norm_column_name)
            join_column_position += 1

        join_key_column_position_list = []
        join_column_position = 0
        while (join_column_position < len(join_key_column_name_list)):
            key_column_name = join_key_column_name_list[join_column_position]
            key_column_name = normalize_column_name(key_column_name)
            found_column_position = -1
            in_column_position = 0
            while (0 > found_column_position
                and in_column_position < len(join_norm_column_name_list)
            ):
                norm_column_name = join_norm_column_name_list[in_column_position]
                if (norm_column_name == key_column_name):
                    found_column_position = in_column_position
                in_column_position += 1
            join_key_column_position_list.append(found_column_position)
            join_column_position += 1

        join_out_column_name_list = []
        join_out_column_position_list = []
        join_column_position = 0
        while (join_column_position < len(join_in_column_name_list)):
            column_name = join_in_column_name_list[join_column_position]
            out_column_name = column_name
            if (None != join_column_name_prefix):
                out_column_name = join_column_name_prefix + column_name
            if (should_exclude_join_columns):
                found_join_key_position = -1
                join_key_position = 0
                while (0 > found_join_key_position
                    and join_key_position < len(join_key_column_position_list)
                ):
                    column_position = join_key_column_position_list[join_key_position]
                    if (join_column_position == column_position):
                        found_join_key_position = join_key_position
                    join_key_position += 1
                if (0 <= found_join_key_position):
                    out_column_name = None
            if (None != out_column_name):
                join_out_column_name_list.append(out_column_name)
                join_out_column_position_list.append(join_column_position)
            join_column_position += 1
        
    if (None != join_key_column_position_list):
        in_row = next(join_csv,None)
        while (None != in_row):
            row_key_list = []
            for key_column_position in join_key_column_position_list:
                key_value = None
                if (0 <= key_column_position
                    and key_column_position < len(in_row)
                ):
                    key_value = in_row[key_column_position]
                row_key_list.append(key_value)
            row_key = tuple(row_key_list)
            join_row_list = join_dict.get(row_key,[])
            join_row_list.append(in_row)
            join_dict[row_key] = join_row_list
            in_row = next(join_csv,None)
    # close join_file so that we don't keep it open the whole time we are reading the input table
    if (None != join_file):
        join_file.close()
    

    # start processing the input,
    # first build a key column position list
    # [20170524 [db] This code is copy-pasted from the code above,
    #  it could be centralized into some awkward functions]
    in_column_name_list = None
    norm_column_name_list = None
    out_column_name_list = None
    key_column_position_list = None
    header_row = next(in_csv,None)
    if (None != header_row):
        in_column_name_list = list(header_row) # copy
        norm_column_name_list = []
        out_column_name_list = []
        for column_name in in_column_name_list:
            norm_column_name = normalize_column_name(column_name)
            norm_column_name_list.append(norm_column_name)
            out_column_name = column_name
            out_column_name_list.append(out_column_name)

        key_column_position_list = []
        column_position = 0
        while (column_position < len(in_key_column_name_list)):
            key_column_name = in_key_column_name_list[column_position]
            key_column_name = normalize_column_name(key_column_name)
            found_column_position = -1
            in_column_position = 0
            while (0 > found_column_position
                and in_column_position < len(norm_column_name_list)
            ):
                norm_column_name = norm_column_name_list[in_column_position]
                if (norm_column_name == key_column_name):
                    found_column_position = in_column_position
                in_column_position += 1
            key_column_position_list.append(found_column_position)
            column_position += 1

    # write header row
    if (None != out_column_name_list):
        if (None != join_out_column_name_list):
            out_column_name_list += join_out_column_name_list
        out_csv.writerow(out_column_name_list)

    # process incoming rows
    in_row = next(in_csv,None)
    while (None != in_row):
        out_row = None
        row_key_list = []
        for key_column_position in key_column_position_list:
            key_value = None
            if (0 <= key_column_position
                and key_column_position < len(in_row)
            ):
                key_value = in_row[key_column_position]
            row_key_list.append(key_value)
        row_key = tuple(row_key_list)
        join_row_list = join_dict.get(row_key,[])
        if (0 == len(join_row_list)):
            if (outer_join_type == join_type):
                join_row = []
                for column_name in join_out_column_name_list:
                    cell_value = None
                    join_row.append(cell_value)
                join_row_list = [join_row]
            elif (inner_join_type == join_type):
                pass
        for join_row in join_row_list:
            out_row = list(in_row)
            for column_position in join_out_column_position_list:
                if (0 <= column_position):
                    cell_value = None
                    if (column_position < len(join_row)):
                        cell_value = join_row[column_position]
                    out_row.append(cell_value)
            out_csv.writerow(out_row)        
        in_row = next(in_csv,None)


def normalize_column_name(in_column_name):
    out_column_name = in_column_name
    if (None != out_column_name):
        out_column_name = out_column_name.strip()
        out_column_name = out_column_name.lower()
    return out_column_name



def console_main():
    main(sys.argv, sys.stdin, sys.stdout, sys.stderr)

        
if __name__ == "__main__":
    console_main()
