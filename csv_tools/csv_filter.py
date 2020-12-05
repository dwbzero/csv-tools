##  Copyright (c) 2017 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##

## #python-3.x
## python 2 does not work due mostly to issues with csv and io modules with unicode data

help_text = (
    "CSV-FILTER tool version 20170330\n"
    "Selects rows from a CSV file\n"
    "\n"
    "csv-filter [OPTIONS] FilterArguments... [InputFile]\n"
    "\n"
    "OPTIONS\n"
    "    -o {F}  Output file name\n"
    "\n"
    "The FilterArguments indicates which rows will be selected.\n"
    "\n"
    "The tool will recognize a filter argument sequence of the form:\n"
    "\n"
    "    {ColumnName} {OP} {Value}\n"
    "\n"
    "Arguments must be separated by whitespace.\n"
    "\n"
    "Valid operators ({OP}) are: '=', '!=', 'is', 'isnt'.\n"
    "'is'/'isnt' and '='/'!=' behave similarly, but 'is' will recognize \n"
    "a value of 'NULL' as a NULL value (and not the character string 'NULL').\n"
    "\n"
    "For example:\n"
    "\n"
    "    csv-filter COMPOUND = CHLORPYRIFOS  EPest.csv\n"
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
    filter_arg_list = list()
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
        elif (None != arg
          and 0 < len(arg)
        ):
            # [20170330 [db] This is sort of a hack to "parse" the filter expression
            #  based on the fact that we only currently support a Name=Value expression
            #  (which consists of 3 distinct tokens/arguments)]
            if (3 > len(filter_arg_list)):
                filter_arg_list.append(arg)
            elif (None == input_file_name):
                input_file_name = arg
        arg_index += 1

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
            execute(
                 in_csv
                ,out_csv
                ,filter_arg_list
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
    ,filter_arg_list
):
    end_row = None
    row_is_selected = None
    header_row = next(in_csv, end_row)
    if (None != header_row):
        row_is_selected = compile_filter_expression(
            filter_arg_list
            ,header_row
            )
    if (None != row_is_selected):
        out_csv.writerow(header_row)
        for in_row in in_csv:
            if (row_is_selected(in_row)):
                out_csv.writerow(in_row)


def normalize_column_name(in_column_name):
    out_column_name = in_column_name
    if (None != out_column_name):
        out_column_name = out_column_name.strip()
        out_column_name = out_column_name.lower()
    return out_column_name

def coalesce_cell_value(in_cell_value, default_cell_value):
    out_cell_value = in_cell_value
    if (None == out_cell_value):
        out_cell_value = default_cell_value
    elif (0 == len(out_cell_value)):
        out_cell_value = default_cell_value
    return out_cell_value

def compile_filter_expression(
    filter_arg_list
    ,header_row
):
    f_op_eq = '='
    f_op_not_eq = '!='
    f_op_is = 'is'
    f_op_is_not = 'isnt'

    column_name_list = list()
    column_position_lookup = dict()
    if (None != header_row):
        column_position = 0
        while (column_position < len(header_row)):
            column_name = header_row[column_position]
            column_name = normalize_column_name(column_name)
            column_name_list.append(column_name)
            column_position_lookup[column_name] = column_position
            column_position += 1

    f_column_name = None
    f_op = None
    f_column_value = None
    if 0 < len(filter_arg_list):
        f_column_name = filter_arg_list[0]
        f_column_name = normalize_column_name(f_column_name)
    if 1 < len(filter_arg_list):
        f_op = filter_arg_list[1]
        f_op = f_op.strip()
        f_op = f_op.lower()
    if 2 < len(filter_arg_list):
        f_column_value = filter_arg_list[2]
    
    if (None != f_column_value):
        if ("''" == f_column_value):
            f_column_value = ''
        elif (f_op in  {f_op_is,f_op_is_not}
            and "NULL" == f_column_value
        ):
            f_column_value = None

    f_value_predicate = None
    if (f_op_eq == f_op):
        f_value_predicate = lambda cell_value : (cell_value == f_column_value)
    elif (f_op_not_eq == f_op):
        f_value_predicate = lambda cell_value : (cell_value != f_column_value)
    elif (f_op_is == f_op):
        f_value_predicate = lambda cell_value : (f_column_value == coalesce_cell_value(cell_value, None))
    elif (f_op_is_not == f_op):
        f_value_predicate = lambda cell_value : (f_column_value != coalesce_cell_value(cell_value, None))

    f_column_position = column_position_lookup.get(f_column_name, None)

    def row_is_selected(in_row):
        cell_value = None
        if (f_column_position < len(in_row)):
            cell_value = in_row[f_column_position]
        return f_value_predicate(cell_value)

    f_row_predicate = None
    if (None != f_column_position
        and None != f_value_predicate
    ):
        f_row_predicate = row_is_selected
    
    return f_row_predicate



def console_main():
    main(sys.argv, sys.stdin, sys.stdout, sys.stderr)

        
if __name__ == "__main__":
    console_main()
