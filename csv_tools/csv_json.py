##  Copyright (c) 2016 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##

## #python-3.x
## python 2 does not work due mostly to issue with csv and io modules with unicode data

help_text = (
    "CSV-JSON tool version 20170215\n"
    "Translates between CSV and JSON\n"
    "\n"
    "csv-json [OPTIONS] PropertyList [InputFile]\n"
    "\n"
    "OPTIONS\n"
    "    -!      Reverse mode (from JSON to CSV)\n"
    "    -E {E}  Input file text encoding (e.g. 'utf-8', 'windows-1252')\n"
    "    -e {E}  Output file text encoding (e.g. 'utf-8', 'windows-1252')\n"
    "    -o {F}  Output file name\n"
    "\n"
    "Translates from CSV to JSON.\n"
    "Use the -! option to translate (in reverse) from JSON to CSV.\n"
    "\n"
    "Input JSON must be a JSON array of objects.\n"
    "The properties of the objects will become the fields of the CSV document.\n"
    "The behavior for complex property values is undefined.\n"
    "\n"
    "PropertyList is a comma-delimited list of property (or column) names.\n"
    "By default, properties are assumed to be string/text datatype.\n"
    "To define a property of non-string type, append the datatype name\n"
    "to the property name after a colon symbol.\n"
    "Valid property datatype names are: \n"
    "    'string', 'integer', 'real', 'boolean'\n"
)

import sys
import io
# [20170215 [db] note that python 2.x csv module does not support unicode, which makes for some problems]
import csv
import json

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
    should_reverse_execution = False
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
    property_list_string = None
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
          or arg == "--json-to-csv"
          or arg == "--from-json"
        ):
            should_reverse_execution = True
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
            if (None == property_list_string):
                property_list_string = arg
            elif (None == input_file_name):
                input_file_name = arg
        arg_index += 1

    # parse property list
    property_name_list = None
    property_type_list = None
    if (None == property_list_string):
        show_help = True
    else:
        property_name_list = []
        property_type_list = []
        property_delimiter = ','
        property_type_delimiter = ':'
        property_spec_list = property_list_string.split(property_delimiter)
        for property_spec in property_spec_list:
            property_spec_component_list = property_spec.split(property_type_delimiter)
            property_name = property_spec_component_list[0]
            property_type_name = None
            if (1 < len(property_spec_component_list)):
                property_type_name = property_spec_component_list[1]
            property_name_list.append(property_name)
            property_type_list.append(property_type_name)

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

            if (should_reverse_execution):
                out_csv = csv.writer(out_io, delimiter=output_delimiter, lineterminator=output_row_terminator)
                execute_json_to_csv(
                      in_io
                    , out_csv
                    , property_name_list
                    , property_type_list
                    )
            else:
                in_csv = csv.reader(in_io, delimiter=input_delimiter, lineterminator=input_row_terminator)
                execute_csv_to_json(
                      in_csv
                    , out_io
                    , property_name_list
                    , property_type_list
                    )
        except BrokenPipeError:
            pass
        finally:
            if (None != in_file):
                in_file.close()
            if (None != out_file):
                out_file.close()

def execute_json_to_csv(
      in_io
    , out_csv
    , property_name_list
    , property_type_list
    ):
    # builtin json module has to load the whole json document into memory
    in_json_text = in_io.read()
    in_json_array = json.loads(in_json_text)

    property_count = len(property_name_list)
    # write header row
    header_row = []
    property_position = 0
    while property_position < property_count:
        property_name = property_name_list[property_position]
        header_row.append(property_name)
        property_position += 1
    out_csv.writerow(header_row)

    for json_object in in_json_array:
        out_row = []
        property_position = 0
        while property_position < property_count:
            property_name = property_name_list[property_position]
            property_value = None
            if (None != json_object):
                property_value = json_object.get(property_name, property_value)
            if (None != property_value):
                property_value = property_value
            out_row.append(property_value)
            property_position += 1
        out_csv.writerow(out_row)


def execute_csv_to_json(
      in_csv
    , out_io
    , property_name_list
    , property_type_list
    ):
    end_row = None

    # read header and remember column positions
    column_count = 0
    column_name_list = []
    column_position_lookup = {}
    in_row = next(in_csv, end_row)
    if (end_row != in_row):
        column_name_list = list(in_row)
        column_position = 0
        column_count = len(column_name_list)
        while column_position < column_count:
            column_name = column_name_list[column_position]
            column_name = normalize_column_name(column_name)
            column_position_lookup[column_name] = column_position
            column_position += 1
        in_row = next(in_csv, end_row)

    property_count = len(property_name_list)
    row_count = 0
    out_io.write("[")  ## write_start_array
    while (end_row != in_row):
        out_row_object = {}
        property_position = 0
        while (property_position < property_count):
            property_name = property_name_list[property_position]
            property_type_name = None
            if (property_position < len(property_type_list)):
                property_type_name = property_type_list[property_position]
            column_name = normalize_column_name(property_name)
            column_position = column_position_lookup.get(column_name, None)
            property_value = None
            if (None != column_position
              and column_position < len(in_row)
            ):
                property_value = in_row[column_position]
            if (None != property_value):
                if ('integer' == property_type_name
                  or 'int' == property_type_name
                ):
                    try:
                        property_value = int(property_value)
                    except ValueError:
                        pass
                elif ('real' == property_type_name
                    or 'float' == property_type_name
                  ):
                    try:
                        property_value = float(property_value)
                    except ValueError:
                        pass
                elif ('boolean' == property_type_name
                  or 'bool' == property_type_name
                ):
                    try:
                        property_value = bool(prroperty_value)
                    except ValueError:
                        pass
                out_row_object[property_name] = property_value
            property_position += 1
        out_row_json_text = json.dumps(out_row_object)
        if 0 < row_count:
            out_io.write(",")
        out_io.write("\n")
        out_io.write(out_row_json_text)
        row_count += 1
        in_row = next(in_csv, end_row)
    out_io.write("\n]\n")  ## write_end_array

def normalize_column_name(in_column_name):
    norm_column_name = in_column_name
    if (None != norm_column_name):
        norm_column_name = norm_column_name.strip()
        norm_column_name = norm_column_name.lower()
        norm_column_name = norm_column_name.replace(' ', '_')
        norm_column_name = norm_column_name.replace('-', '_')
        norm_column_name = norm_column_name.replace('.', '_')
    return norm_column_name


def console_main():
    main(sys.argv, sys.stdin, sys.stdout, sys.stderr)

        
if __name__ == "__main__":
    console_main()
