##  Copyright (c) 2016-2017 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##

## #python-3.x
## python 2 does not work due mostly to issues with csv and io modules with unicode data

help_text = (
    "CSV-APPEND tool version 20170602:20200715\n"
    "Appends a CSV file to a CSV stream with matching columns.\n"
    "\n"
    "csv-append [OPTIONS] AppendFile1\n"
    "csv-append [OPTIONS] InputFile AppendFile1 [AppendFile2...]\n"
    "\n"
    "OPTIONS\n"
    "    -F {S}  Name of column where file name should be saved.\n"
    "    -o {F}  Output file name.\n"
    "\n"
    "Appends the non-header rows of one or more CSV files to the end\n"
    "of a CSV input stream, cells in the append files are matched to the\n"
    "appropriate column of the input stream by matching column names.\n"
    "\n"
    "If more than one file name is specified, then the CSV input stream will\n"
    "be read from the first file, otherwise it will be read from STDIN.\n"
    "If the first file is named '-', then it will be read from STDIN anyway.\n"
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
    stdio_file_name = '-'
    show_help = False
    input_file_name = None
    input_file_name_list = []
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
    per_file_row_count_max = None
    input_file_column_name = None
    err_msg = None
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
        elif (arg == "-F"
          or arg == "--file-column"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                input_file_column_name = arg
        elif (arg == "-m"
          or arg == "--rows-per-file"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                per_file_row_count_max = int(arg)
        elif (arg.startswith("-") and arg != "-"):
            err_msg = "unknown option: " + arg
        elif (None != arg
          and 0 < len(arg)
          ):
            input_file_name_list.append(arg)
        arg_index += 1
    
    if (0 >= len(input_file_name_list)):
        show_help = True

    if (err_msg is not None):
        err_io.write(err_msg)
        err_io.write("\n")
    if (show_help):
        out_io.write(help_text)
    elif (err_msg is None):
        # if only one input file is provided, then use STDIN,
        # if multiple input files are specified, then the main file will be the first one.
        # if the name of the first file is '-' then read the main file from STDIN
        if (1 < len(input_file_name_list)):
            file_name = input_file_name_list[0]
            if (stdio_file_name != file_name):
                input_file_name = file_name
            del input_file_name_list[0]

        input_charset_name = decode_charset_name(input_charset_name)
        output_charset_name = decode_charset_name(output_charset_name)
        input_row_terminator = decode_newline(input_row_terminator)
        output_row_terminator = decode_newline(output_row_terminator)
        input_delimiter = decode_delimiter_name(input_delimiter)
        output_delimiter = decode_delimiter_name(output_delimiter) 
        in_file = None
        in_append_file = None
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

            open_csv_input_file = lambda file_name: io.open(
                 file_name
                ,mode=read_text_io_mode
                ,encoding=input_charset_name
                ,newline=in_newline_mode
                ,errors=input_charset_error_mode
                )
            create_csv_reader = lambda input_file: csv.reader(
                input_file
                ,delimiter=input_delimiter
                ,lineterminator=input_row_terminator
                )

            execute(
                in_csv
                ,out_csv
                ,input_file_name_list
                ,open_csv_input_file
                ,create_csv_reader
                ,output_row_count_max
                ,input_file_name
                ,input_file_column_name
                ,per_file_row_count_max
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
    ,in_append_file_name_list
    ,open_csv_input_file
    ,create_csv_reader
    ,out_row_count_max
    ,in_file_name
    ,input_file_column_name
    ,per_file_row_count_max
):
    end_row = None
    in_row_count = 0
    out_row_count = 0
    out_column_name_list = []
    

    # copy all input rows from the main stream directly to the output stream
    # find the "file name" column, if it exists
    input_file_column_position = -1
    in_header_row = next(in_csv, end_row)
    if (end_row != in_header_row):
        out_header_row = list()
        if input_file_column_name is not None:
            input_file_column_name_norm = normalize_column_name(input_file_column_name)
            in_column_count = len(in_header_row)
            in_column_position = 0
            input_file_column_position = -1
            while (0 > input_file_column_position
                and in_column_position < in_column_count
            ):
                in_column_name = in_header_row[in_column_position]
                in_column_name_norm = normalize_column_name(in_column_name)
                if in_column_name_norm == input_file_column_name_norm:
                    input_file_column_position = in_column_position
                in_column_position += 1
            if (0 > input_file_column_position):
                out_header_row.append(input_file_column_name)
                input_file_column_position = 0
        out_header_row.extend(in_header_row)
        out_column_name_list = out_header_row
        out_csv.writerow(out_header_row)
        in_row = next(in_csv, end_row)
    # dump input file to output stream,
    #  add file name column if available:
    file_row_count = 0
    while (end_row != in_row
        and (out_row_count_max is None or out_row_count_max > out_row_count)
        and (per_file_row_count_max is None or per_file_row_count_max > file_row_count)
    ):
        in_row_count += 1
        if (0 > input_file_column_position):
            out_row = in_row
        else:
            out_row = list()
            out_row.append(in_file_name)
            out_row.extend(in_row)
        out_csv.writerow(out_row)
        out_row_count += 1
        file_row_count += 1
        in_row = next(in_csv, end_row)
    
    # process each append_file:
    in_file_count = len(in_append_file_name_list)
    in_file_position = 0
    while (in_file_count > in_file_position
        and (out_row_count_max is None or out_row_count_max > out_row_count)
    ):
        in_append_file_name = in_append_file_name_list[in_file_position]
        in_append_file = None
        file_row_count = 0
        try:
            in_append_file = open_csv_input_file(in_append_file_name)
            in_append_csv = create_csv_reader(in_append_file)
            # read header row of append file, 
            # find the column offsets for columns that match the output header row
            out_append_column_position_list = []
            in_header_row = next(in_append_csv, end_row)
            if (end_row != in_header_row):
                out_column_position = 0
                while (out_column_position < len(out_column_name_list)):
                    out_column_name = out_column_name_list[out_column_position]
                    out_column_name_norm = normalize_column_name(out_column_name)
                    found_in_column_position = -1
                    in_column_position = 0
                    while (0 > found_in_column_position
                        and in_column_position < len(in_header_row)
                    ):
                        in_column_name = in_header_row[in_column_position]
                        in_column_name_norm = normalize_column_name(in_column_name)
                        if (None != in_column_name_norm
                            and in_column_name_norm == out_column_name_norm
                        ):
                            found_in_column_position = in_column_position
                        in_column_position += 1
                    out_append_column_position_list.append(found_in_column_position)
                    out_column_position += 1
            # append the rows after the header
            in_row = end_row
            if (end_row != in_header_row):
                in_row = next(in_append_csv, end_row)
            while (in_row != end_row
                and (out_row_count_max is None or out_row_count_max > out_row_count)
                and (per_file_row_count_max is None or per_file_row_count_max > file_row_count)
            ):
                in_row_count += 1
                out_row = []
                out_column_count = len(out_column_name_list)
                out_column_position = 0
                while (out_column_position < out_column_count):
                    in_column_position = out_append_column_position_list[out_column_position]
                    out_cell_value = None
                    if (0 <= input_file_column_position
                        and input_file_column_position == out_column_position
                    ):
                        out_cell_value = in_append_file_name
                    if (0 <= in_column_position
                        and in_column_position < len(in_row)
                    ):
                        out_cell_value = in_row[in_column_position]
                    out_row.append(out_cell_value)
                    out_column_position += 1
                out_csv.writerow(out_row)
                file_row_count += 1
                out_row_count += 1
                in_row = next(in_append_csv, end_row)
        except BrokenPipeError:
            pass
        finally:
            if (None != in_append_file):
                in_append_file.close()
                in_append_file = None
        in_file_position += 1

    
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
