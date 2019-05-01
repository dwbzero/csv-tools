##  Copyright (c) 2016-2019 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##

## #python-3.x
## python 2 does not work due mostly to issues with csv and io modules with unicode data

help_text = (
    "CSV-REJOIN tool version 20190501\n"
    "Expand a CSV list embedded in a column of a CSV file like an outer join\n"
    "\n"
    "csv-rejoin [OPTIONS] Column [InputFile]\n"
    "\n"
    "OPTIONS\n"
    "    -o {F}  Output file name\n"
    "    -S {S}  Input file field delimiter (default ',')\n"
    "    -s {S}  Output file field delimiter (default ',')\n"
    "    -T {S}  Embedded list delimiter (default - same as out CSV delimiter)\n"
    "    --trim  Trim whitespace on the inner field values\n"
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
    exit_code = 0
    in_io = stdin
    out_io = stdout
    err_io = stderr
    show_help = False
    error_message = None
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
    source_column_name = None
    input_inner_delimiter = None
    should_trim_inner_values = False
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
        elif (arg == "-T"
          or arg == "--inner-separator-in"
          or arg == "---inner-delimiter-in"
          or arg == "--inner-separator"
          or arg == "---inner-delimiter"
          ):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                input_inner_delimiter = arg
        elif (arg == "--trim"):
            should_trim_inner_values = True
        elif (None != arg
          and 0 < len(arg)
          ):
            if (None == source_column_name):
                source_column_name = arg
            elif (None == input_file_name):
                input_file_name = arg
        arg_index += 1

    if (None == source_column_name):
        show_help = True
        exit_code = -2

    if (show_help):
        if (0 == exit_code):
            out_io.write(help_text)
        else:
            err_io.write(help_text)
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
        if (None == input_inner_delimiter):
            input_inner_delimiter = input_delimiter
        else:
            input_inner_delimiter = decode_delimiter_name(input_inner_delimiter)
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

            # We will parse the inner CSV records with a CSV reader
            #  that will read from a list that we will continue to push encoded rows onto
            in_inner_field_list = list()
            in_inner_csv = csv.reader(
                in_inner_field_list
                ,delimiter=input_inner_delimiter
            )

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
            exit_code = execute(
                in_csv
                ,out_csv
                ,in_inner_csv
                ,in_inner_field_list
                ,source_column_name
                ,should_trim_inner_values
                ,input_row_start_offset
                ,input_row_count_max
                ,output_row_count_max
                )
        except BrokenPipeError:
            # this error can occur when a process serving a stdio stream quits
            pass
        except UnicodeError as exc:
            error_message = str(exc)
            exit_code = -1
        finally:
            if (None != in_file):
                in_file.close()
                in_file = None
            if (None != out_file):
                out_file.close()
                out_file = None
    if (None != error_message):
        err_io.write("Error: {E}\n".format(E=error_message))

    return exit_code

def execute(
    in_csv
    ,out_csv
    ,in_inner_csv
    ,in_inner_field_list
    ,source_column_name
    ,should_trim_inner_values
    ,in_row_offset_start
    ,in_row_count_max
    ,out_row_count_max
):
    exit_code = 0
    end_row = None
    source_column_name_norm = normalize_column_name(source_column_name)
    in_source_column_position = None
    out_source_column_position = None

    in_header_row = next(in_csv, end_row)
    if (end_row != in_header_row):
        out_header_row = list()
        in_column_count = len(in_header_row)
        in_column_position = 0
        while (in_column_position < in_column_count):
            in_column_name = in_header_row[in_column_position]
            in_column_name_norm = normalize_column_name(in_column_name)
            if (in_column_name_norm == source_column_name_norm):
                if (None == in_source_column_position):
                    in_source_column_position = in_column_position
            out_header_row.append(in_column_name)
            in_column_position += 1
        out_source_column_position = in_source_column_position
        out_csv.writerow(out_header_row)
    
    in_row_count = 0
    out_row_count = 0
    in_row = next(in_csv, end_row)
    while (end_row != in_row
        and (None == in_row_count_max or in_row_count < in_row_count_max)
        and (None == out_row_count_max or out_row_count < out_row_count_max)
    ):
        in_row_count += 1
        if (in_row_offset_start < in_row_count):
            in_column_count = len(in_row)
            in_inner_row = end_row
            if (None != in_source_column_position
                and (0 <= in_source_column_position)
                and (in_column_count > in_source_column_position)
            ):
                in_inner_field = in_row[in_source_column_position]
                if (None != in_inner_field
                    and 0 < len(in_inner_field)
                ):
                    in_inner_field_list.append(in_inner_field)
                    in_inner_row = next(in_inner_csv, end_row)
            if (end_row == in_inner_row):
                # outer join on empty inner list:
                # just write the input row back out
                out_row = list(in_row)
                out_csv.writerow(out_row)
            else:
                for in_inner_value in in_inner_row:
                    out_row = list(in_row)
                    out_column_count = len(out_row)
                    if (None != out_source_column_position
                        and (0 <= out_source_column_position)
                        and (out_column_count > out_source_column_position)
                    ):
                        out_inner_value = in_inner_value
                        if (should_trim_inner_values
                            and None != out_inner_value
                            ):
                            out_inner_value = out_inner_value.strip()
                        if (0 == len(out_inner_value)):
                            out_inner_value = None
                        out_row[out_source_column_position] = out_inner_value
                    out_csv.writerow(out_row)
                    out_row_count += 1
        in_row = next(in_csv, end_row)
    return exit_code

def console_main():
    return main(sys.argv, sys.stdin, sys.stdout, sys.stderr)

        
if __name__ == "__main__":
    sys.exit(console_main())
