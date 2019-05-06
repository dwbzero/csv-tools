##  Copyright (c) 2016-2019 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##

help_text = (
    "CSV-ROWCALC tool version 20170217:20190506\n"
    "Executes a custom python script on each row of a CSV file\n"
    "Copyright (c) 2017-2019 Upstream Research, Inc.  All Rights Reserved.\n"
    "\n"
    "csv-rowcalc [OPTIONS] ScriptFile [CsvInputFile]\n"
    "\n"
    "OPTIONS\n"
    "    -a {S}  Comma separated list of additional columns to add to output\n"
    "    -F {F}  Additional script file to include (option can be used multiple times)\n"
    "    -K {N}  Number of non-header rows to skip (default=0)\n"
    "    -n {N}  Number of non-header rows to process from input (default=all)\n"
    "    -N {N}  Number of non-header rows to write to output (default=all)\n"
    "    -o {F}  Output file name\n"
    "    -X      Interpret the ScriptFile parameter as a Python statement (not a file name)\n"
    "    --row-var    {S}   Name of row map variable (default='row')\n"
    "    --state-var  {S}   Name of state map variable (default='state')\n"
    "\n"
    "ScriptFile should be a Python script.  It will be executed once per row\n"
    "in a context with some predefined variables, including one called 'row'\n"
    "which is a Python map (dict) of column names to cell values.\n"
    "Cell values may be altered by setting the values into the row map.\n"
    "A row may be deleted from the output by setting the row variable to None.\n"
    "\n"
    "For example, to left-pad the column 'GEOID' with upto 5 zeros, the script might be:\n"
    "\n"
    "    row['GEOID'] = row['GEOID'].rjust(5,'0')\n"
    "\n"
    "The script will also be given a 'state' map, which is preserved from row to row.\n"
    "This allows the script to accumulate state information as it gets executed.\n"
    "\n"
    "For example, to make a 'row_offset' column, the script could be:\n"
    "\n"
    "    row_offset         = state.get('row_count', 0)\n"
    "    row['row_offset']  = row_offset\n"
    "    state['row_count'] = row_offset + 1\n"
)

import sys
import csv
import io
import ast

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
    include_script_file_name_list = []
    script_file_name = None
    script_content = None
    script_arg_is_code = False
    extra_column_names_string = None
    row_var_name = 'row'
    row_offset_var_name = 'row_offset'
    state_var_name = 'state'
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
        elif (arg == "--row-var"):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                row_var_name = arg
        elif (arg == "--state-var"):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                state_var_name = arg
        elif (arg == "-a"
          or arg == "--append-columns"
        ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                extra_column_names_string = arg
        elif (arg == "-X"
          or arg == "--statement"
        ):
            script_arg_is_code = True
        elif (arg == "-F"
          or arg == "--include"
        ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                include_script_file_name_list.append(arg)
        elif (None != arg
          and 0 < len(arg)
          ):
            if (None == script_file_name):
                script_file_name = arg
            elif (None == input_file_name):
                input_file_name = arg
        arg_index += 1
    
    if (None == script_file_name):
        show_help = True
    elif (script_arg_is_code):
        # script must end with a newline character or python compiler will complain
        script_content = script_file_name + '\n'
        script_file_name = None

    if (show_help):
        out_io.write(help_text)
    else:
        # combine the include scripts first
        # [20170531 [db] I tried to compile these separately
        #   so that the include file line numbers would be preserved properly,
        #   but I failed to find a way to execute the combined code,
        #   so I fell back to simply concating all the code together and compiling it once.]
        include_script_content = None
        for include_script_file_name in include_script_file_name_list:
            include_script_file_content = read_file_content(include_script_file_name)
            if (None == include_script_content):
                include_script_content = include_script_file_content
            elif (None != include_script_file_content):
                include_script_content += "\n" + include_script_file_content

        if (None != script_file_name
            and None == script_content
        ):
            script_content = read_file_content(script_file_name)
        
        if (None == script_content):
            script_content = include_script_content
        elif (None != include_script_content):
            script_content = include_script_content + "\n" + script_content
        script_compiled_code = compile_script_content(script_content, script_file_name)

        extra_column_name_list = []
        if (None != extra_column_names_string):
            extra_column_name_list = extra_column_names_string.split(",")

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
            if (None != script_compiled_code):
                execute(
                    in_csv
                    ,out_csv
                    ,input_row_start_offset
                    ,input_row_count_max
                    ,output_row_count_max
                    ,script_compiled_code
                    ,extra_column_name_list
                    ,row_var_name
                    ,state_var_name
                    ,row_offset_var_name
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
    ,in_row_start_offset
    ,in_row_count_max
    ,out_row_count_max
    ,script_compiled_code
    ,extra_column_name_list
    ,row_var_name
    ,state_var_name
    ,row_offset_var_name
):
    end_row = None
    in_header_row = next(in_csv, end_row)
    out_header_row = None
    if (end_row != in_header_row):
        out_header_row = list(in_header_row)
        if (None != extra_column_name_list):
            out_header_row = out_header_row + extra_column_name_list
        out_csv.writerow(out_header_row)

    in_row_count = 0

    # skip rows before in_row_start_offset
    in_row = next(in_csv, end_row)
    while (end_row != in_row
        and in_row_count < in_row_start_offset
        and (None == in_row_count_max or in_row_count < in_row_count_max)
    ):
        in_row_count += 1
        in_row = next(in_csv, end_row)

    out_row_count = 0
    state_dict = dict()
    while (end_row != in_row
        and (None == in_row_count_max or in_row_count < in_row_count_max)
        and (None == out_row_count_max or out_row_count < out_row_count_max)
        ):
        # make a dictionary for the row
        # we don't use a csv.DictReader since we want more flexiblity here
        row_dict = dict()
        column_position = 0
        while (column_position < len(in_row)
            and column_position < len(in_header_row)
        ):
            column_name = in_header_row[column_position]
            row_dict[column_name] = in_row[column_position]
            column_position += 1
        # add default values for missing and extra columns
        default_cell_value = None
        while (column_position < len(out_header_row)):
            column_name = out_header_row[column_position]
            row_dict[column_name] = default_cell_value
            column_position += 1

        script_variables = dict()
        script_variables[row_var_name] = row_dict
        script_variables[state_var_name] = state_dict
        script_variables[row_offset_var_name] = in_row_count
        exec(script_compiled_code, script_variables)

        # check if the row variable has been set to None
        row_dict = script_variables[row_var_name]
        if (None != row_dict):
            out_row = list()
            column_position = 0
            while (column_position < len(out_header_row)):
                column_name = out_header_row[column_position]
                cell_value = row_dict.get(column_name, default_cell_value)
                out_row.append(cell_value)
                column_position += 1
            out_csv.writerow(out_row)
            out_row_count += 1

        in_row_count += 1
        in_row = next(in_csv, end_row)

def read_file_content(in_file_name):
    read_text_io_mode = 'rt'
    newline_mode = None  # universal newlines required for scripts
    charset_name = 'utf_8'
    file_content = None
    in_file = None
    try:
        in_file = io.open(
            in_file_name
            ,mode=read_text_io_mode
            ,encoding=charset_name
            ,newline=newline_mode
            )
        file_content = in_file.read()
    finally:
        if (None != in_file):
            in_file.close()
            in_file = None
    return file_content

def compile_script_content(
    script_content
    ,script_file_name
    ):
    default_script_source_name = '<string>'
    script_compile_mode = 'exec'
    script_compiled_code = None
    script_source_name = default_script_source_name
    if (None != script_file_name):
        script_source_name = script_file_name
    if (None != script_content):
        script_compiled_code = compile(
            script_content
            ,script_source_name
            ,script_compile_mode
        )
    return script_compiled_code

# Notice this is the exact same code as the compile_script_content() function
def parse_script_ast_from_string(
    script_content
    ,script_file_name
    ):
    default_script_source_name = '<string>'
    script_compile_mode = 'exec'
    script_compiled_code = None
    script_source_name = default_script_source_name
    if (None != script_file_name):
        script_source_name = script_file_name
    if (None != script_content):
        script_compiled_code = ast.parse(
            script_content
            ,script_source_name
            ,script_compile_mode
        )
    return script_compiled_code
    


def console_main():
    main(sys.argv, sys.stdin, sys.stdout, sys.stderr)

        
if __name__ == "__main__":
    console_main()
