##  Copyright (c) 2016 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##

help_text = (
    "CSV-SELECT tool version 20170220:20170531\n"
    "Selects a subset of columns from a CSV file\n"
    "Copyright (c) 2017 Upstream Research, Inc.  All Rights Reserved.\n"
    "\n"
    "csv-select [OPTIONS] Columns [InputFile]\n"
    "\n"
    "OPTIONS\n"
    "    -o {F}  Output file name\n"
    "    -X      Exclude the named columns instead of including them\n"
    "\n"
    "The Columns argument is a comma-separated list of columns to select\n"
    "from the input stream.\n"
    "\n"
    "RENAMING COLUMNS: Columns can (optionally) be renamed in the output \n"
    "by specifying an alias name followed by an equal sign '=', \n"
    "followed by the column name in the column name list.\n"
    "\n"
    "FIXED VALUE COLUMNS: New columns can be added to the output\n"
    "by specifyint a column name that does not exist in the input.\n"
    "The default value for new columns can be assigned by specifying\n"
    "the column name followed by a double equal sign '==', \n"
    "followed by the value that should be assigned to that column in every row.\n"
    "\n"
    "For example:\n"
    "\n"
    "  csv-select tract_id=GEOID,population,score==1.00  hazard_data.csv\n"
    "\n"
    "will rename 'GEOID' to 'tract_id', will not rename 'population',\n"
    "and will create a column named 'score' with the fixed value '1.00'\n"
    "(assuming a 'score' column does not exist in the input file).\n"
    "\n"
    "Columns will be written in the order specified, thus they may be reordered.\n"
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
    column_name_list_string = None
    should_exclude_columns = False
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
        elif (arg == "-X"
            or arg == "--exclude"
        ):
            should_exclude_columns = True
        elif (None != arg
          and 0 < len(arg)
          ):
            if (None == column_name_list_string):
                column_name_list_string = arg
            elif (None == input_file_name):
                input_file_name = arg
        arg_index += 1
    
    if (None == column_name_list_string):
        show_help = True

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
            inclusion_column_name_list = None
            alias_column_name_list = None
            const_column_value_list = None
            exclusion_column_name_list = None
            if (None != column_name_list_string):
                column_name_list = column_name_list_string.split(",")
                if (should_exclude_columns):
                    exclusion_column_name_list = column_name_list
                else:
                    alias_separator = '='
                    const_separator = '=='
                    inclusion_column_name_list = []
                    alias_column_name_list = []
                    const_column_value_list = []
                    for column_name_expr in column_name_list:
                        in_column_name = column_name_expr
                        out_column_name = column_name_expr
                        out_column_value_str = None
                        alias_separator_position = -1
                        const_separator_position = column_name_expr.find(const_separator)
                        if (0 <= const_separator_position
                            and const_separator_position < len(in_column_name)
                        ):
                            out_column_name = column_name_expr[0:const_separator_position]
                            out_column_value_str = column_name_expr[const_separator_position+len(const_separator):]
                        else:
                            alias_separator_position = column_name_expr.find(alias_separator)
                        if (0 <= alias_separator_position 
                            and alias_separator_position < len(in_column_name)
                        ):
                            out_column_name = column_name_expr[0:alias_separator_position]
                            in_column_name = column_name_expr[alias_separator_position+len(alias_separator):]
                        inclusion_column_name_list.append(in_column_name)
                        alias_column_name_list.append(out_column_name)
                        const_column_value_list.append(out_column_value_str)

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

            in_csv = csv.reader(in_io, delimiter=input_delimiter, lineterminator=input_row_terminator)
            out_csv = csv.writer(out_io, delimiter=output_delimiter, lineterminator=output_row_terminator)
            if (None != inclusion_column_name_list
                or None != exclusion_column_name_list
            ):
                execute(
                    in_csv
                    ,out_csv
                    ,inclusion_column_name_list
                    ,alias_column_name_list
                    ,const_column_value_list
                    ,exclusion_column_name_list
                    )
        except BrokenPipeError:
            pass
        finally:
            if (None != in_file):
                in_file.close()
            if (None != out_file):
                out_file.close()

def execute(
    in_csv
    ,out_csv
    ,inclusion_column_name_list
    ,alias_column_name_list
    ,const_column_value_list
    ,exclusion_column_name_list
):
    end_row = None
    in_header_row = next(in_csv, end_row)
    out_header_row = None
    if (end_row != in_header_row):
        # make a list of the column names we will actually use
        column_name_list = []
        out_column_name_list = []
        default_column_value_list = []

        src_column_name_list = in_header_row
        if (None != inclusion_column_name_list):
            src_column_name_list = inclusion_column_name_list
        
        column_position = 0
        while (column_position < len(src_column_name_list)):
            column_name = src_column_name_list[column_position]
            out_column_name = column_name
            if (None != alias_column_name_list
                and column_position < len(alias_column_name_list)
                ):
                out_column_name = alias_column_name_list[column_position]
            default_column_value = None
            if (None != const_column_value_list
                and column_position < len(const_column_value_list)
                ):
                default_column_value = const_column_value_list[column_position]
            column_name_list.append(column_name)
            out_column_name_list.append(out_column_name)
            default_column_value_list.append(default_column_value)
            column_position += 1
        
        # exclude columns if necessary
        if (None != exclusion_column_name_list):
            ex_column_position = 0
            while (ex_column_position < len(exclusion_column_name_list)):
                ex_column_name = exclusion_column_name_list[ex_column_position]
                ex_column_name_norm = normalize_column_name(ex_column_name)
                found_column_position = len(column_name_list)
                column_position = 0
                while (found_column_position >= len(column_name_list)
                    and column_position < len(column_name_list)
                ):
                    column_name = column_name_list[column_position]
                    column_name_norm = normalize_column_name(column_name)
                    if (column_name_norm == ex_column_name_norm):
                        found_column_position = column_position
                    column_position += 1
                if (found_column_position < len(column_name_list)):
                    del column_name_list[found_column_position]
                if (found_column_position < len(out_column_name_list)):
                    del out_column_name_list[found_column_position]
                if (found_column_position < len(default_column_value_list)):
                    del default_column_value_list[found_column_position]
                ex_column_position += 1

        # make a list of column offsets
        out_header_row = []
        column_position_map = []
        column_position = 0
        while (column_position < len(column_name_list)
            and column_position < len(out_column_name_list)
            ):
            column_name = column_name_list[column_position]
            out_column_name = out_column_name_list[column_position]
            column_name_norm = normalize_column_name(column_name)
            in_column_position = 0
            found_column_position = None
            while (in_column_position < len(in_header_row)
                and None == found_column_position
                ):
                in_column_name = in_header_row[in_column_position]
                in_column_name_norm = normalize_column_name(in_column_name)
                if (in_column_name_norm == column_name_norm):
                    found_column_position = in_column_position
                in_column_position += 1
            column_position_map.append(found_column_position)
            out_header_row.append(out_column_name)
            column_position += 1
        out_csv.writerow(out_header_row)

        # write the rows
        row_count = 0
        in_row = next(in_csv, end_row)
        while (end_row != in_row):
            out_row = []
            out_column_position = 0
            while (out_column_position < len(column_position_map)):
                in_column_position = column_position_map[out_column_position]
                cell_value = None
                if (out_column_position < len(default_column_value_list)):
                    cell_value = default_column_value_list[out_column_position]
                if (None != in_column_position
                    and in_column_position < len(in_row)
                    ):
                    cell_value = in_row[in_column_position]
                out_row.append(cell_value)
                out_column_position += 1
            out_csv.writerow(out_row)
            row_count += 1
            in_row = next(in_csv, end_row)

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
