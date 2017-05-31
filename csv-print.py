##  Copyright (c) 2016 Upstream Research, Inc.  All Rights Reserved.  ##

help_text = (
    "CSV-PRINT tool version 20170220:20170518\n"
    "Prints a fixed-width representation of a CSV file\n"
    "Copyright (c) 2017 Upstream Research, Inc.  All Rights Reserved.\n"
    "\n"
    "csv-print [OPTIONS] [InputFile]\n"
    "\n"
    "OPTIONS\n"
    "    -H      Don't skip the header row when analyzing column width\n"
    "    -N {N}  Number of input rows to analyze for column widths (default=1)\n"
    "    -n {N}  Number of rows to print (default=all)\n"
    "    -o {F}  Output file name\n"
    "    --min-width {N}  Minimum column width (default=1)\n"
    "    --max-width {N}  Maximum column width (default=unbounded)\n"
    "    --widths  Comma-separated list of column widths\n"
    "\n"
)

import sys
import csv
import io

from csv_helpers import decode_delimiter_name, decode_charset_name, decode_newline

def main(arg_list, stdin, stdout, stderr):
    in_io = stdin
    out_io = stdout
    err_io = stderr
    show_help = False
    input_file_name = None
    output_file_name = None
    input_delimiter = ','
    output_delimiter = ' '
    # 'std' will be translated to the standard line break decided by csv_helpers.decode_newline
    input_row_terminator = 'std'
    output_row_terminator = 'std'
    input_charset_name = 'utf_8_sig'
    output_charset_name = 'utf_8'
    csv_cell_width_limit = 4*1024*1024  # python default is 131072 = 0x00020000
    column_name_list_string = None
    column_width_list_string = None
    analyze_row_count_string = None
    out_row_count_max_string = None
    column_width_min_string = None
    column_width_max_string = None
    analyze_row_count = 1
    out_row_count_max = None
    column_width_min = 1
    column_width_max = None
    truncation_symbol = "-"
    should_analyze_header_row = False
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
          or arg == "--analyze-row-count"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                analyze_row_count_string = arg
        elif (arg == "-n"
          or arg == "--out-row-count-max"
        ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                out_row_count_max_string = arg
        elif (arg == "--min-width"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                column_width_min_string = arg
        elif (arg == "--max-width"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                column_width_max_string = arg
        elif (arg == "--select"
          or arg == "--select-columns"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                column_name_list_string = arg
        elif (arg == "--column-widths"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                column_width_list_string = arg
        elif (arg == "--truncation-symbol"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                truncation_symbol = arg
        elif (arg == "-H"
            or arg == "--analyze-header"
        ):
            should_analyze_header_row = True
        elif (None != arg
          and 0 < len(arg)
          ):
            if (None == input_file_name):
                input_file_name = arg
        arg_index += 1
    
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
            if (None != out_row_count_max_string):
                if ("all" == out_row_count_max_string.lower()):
                    out_row_count_max = None
                else:
                    out_row_count_max = int(out_row_count_max_string)
            if (None != analyze_row_count_string):
                if ("all" == analyze_row_count_string.lower()):
                    analyze_row_count = None
                else:
                    analyze_row_count = int(analyze_row_count_string)
            # ensure the number of rows to analyze is not greater
            #  than the number of rows to output
            if (None != out_row_count_max
                and (None == analyze_row_count
                    or out_row_count_max < analyze_row_count
                )
            ):
                analyze_row_count = out_row_count_max
            if (None != column_width_min_string):
                column_width_min = int(column_width_min_string)
            if (None != column_width_max_string):
                if ("unbounded" == column_width_max_string.lower()
                    or "infinite" == column_width_max_string.lower()
                    or "inf" == column_width_max_string.lower()
                ):
                    column_width_max = None
                else:
                    column_width_max = int(column_width_max_string)
            column_name_list = None
            if (None != column_name_list_string):
                column_name_list = column_name_list_string.split(",")
            column_width_list = None
            if (None != column_width_list_string):
                column_width_list = []
                column_width_string_list = column_width_list_string.split(",")
                for column_width_string in column_width_string_list:
                    column_width = None
                    if (0 < len(column_width_string)):
                        column_width = int(column_width_string)
                    column_width_list.append(column_width)
            if (None != input_file_name):
                read_text_io_mode = 'rt'
                #in_newline_mode = ''  # don't translate newline chars
                in_newline_mode = input_row_terminator
                in_file = io.open(input_file_name, mode=read_text_io_mode, encoding=input_charset_name, newline=in_newline_mode)
                in_io = in_file
            if (None != output_file_name):
                write_text_io_mode = 'wt'
                out_newline_mode=''  # don't translate newline chars
                out_file = io.open(output_file_name, mode=write_text_io_mode, encoding=output_charset_name, newline=out_newline_mode)
                out_io = out_file
            in_csv = csv.reader(in_io, delimiter=input_delimiter, lineterminator=input_row_terminator)
            execute(
                in_csv
                ,out_io
                ,output_delimiter
                ,output_row_terminator
                ,truncation_symbol
                ,column_name_list
                ,column_width_list
                ,analyze_row_count
                ,out_row_count_max
                ,column_width_min
                ,column_width_max
                ,should_analyze_header_row
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
    ,out_io
    ,output_delimiter
    ,output_row_terminator
    ,truncation_symbol
    ,column_name_list
    ,column_width_fixed_list
    ,analyze_row_count
    ,out_row_count_max
    ,column_width_min
    ,column_width_max
    ,should_analyze_header_row
):
    end_row = None
    in_header_row = next(in_csv, end_row)
    out_header_row = None
    if (end_row != in_header_row):
        # [20170220 [db] This code for finding the column offsets comes from
        #  the csv-select tool, i thought it would be helpful to incorporate it here
        #  although i think it violates the "do one thing and do it well" rule]
        # default to inclusion of all input columns in the output
        if (None == column_name_list):
            column_name_list = list(in_header_row)
        # make a list of column offsets, and fixup the column names
        out_header_row = []
        column_position_map = []
        out_column_position = 0
        while (out_column_position < len(column_name_list)):
            out_column_name = column_name_list[out_column_position]
            out_column_name = out_column_name.strip()
            out_column_name_norm = out_column_name.lower()
            in_column_position = 0
            found_column_position = None
            while (in_column_position < len(in_header_row)
                and None == found_column_position
                ):
                in_column_name = in_header_row[in_column_position]
                in_column_name_norm = in_column_name.strip().lower()
                if (in_column_name_norm == out_column_name_norm):
                    found_column_position = in_column_position
                in_column_position += 1
            column_position_map.append(found_column_position)
            out_header_row.append(out_column_name)
            out_column_position += 1

        # figure out the row widths
        column_width_list = []
        row_count = 0
        in_row_list = []
        if (not should_analyze_header_row):
            # if we are not going to analyze the header row,
            #  then add it to our row list buffer now so it will get printed later.
            in_row_list.append(in_header_row)
        if (None == analyze_row_count 
            or 0 < analyze_row_count
        ):
            if (should_analyze_header_row):
                in_row = in_header_row
            else:
                in_row = next(in_csv, end_row)
            while (end_row != in_row
                and (None == analyze_row_count
                    or row_count < analyze_row_count
                )
            ):
                in_column_position = 0
                while (in_column_position < len(in_row)):
                    cell_value = in_row[in_column_position]
                    cell_width = len(cell_value)
                    if (in_column_position == len(column_width_list)):
                        column_width_list.append(column_width_min)
                    column_width = column_width_list[in_column_position]
                    column_width_fixed = None
                    if (None != column_width_fixed_list
                        and in_column_position < len(column_width_fixed_list)
                    ):
                        column_width_fixed = column_width_fixed_list[in_column_position]
                    if (None != column_width_fixed):
                        column_width = column_width_fixed
                    elif (column_width < cell_width):
                        if (column_width_max != None
                            and column_width_max < cell_width
                        ):
                            column_width = column_width_max
                        else:
                            column_width = cell_width
                    column_width_list[in_column_position] = column_width
                    in_column_position += 1
                in_row_list.append(in_row)
                row_count += 1
                if ((None == analyze_row_count 
                    or row_count < analyze_row_count
                )):
                    in_row = next(in_csv, end_row)

        # write the rows
        row_count = 0
        row_list_position = 0
        if (row_list_position < len(in_row_list)):
            in_row = in_row_list[row_list_position]
            row_list_position += 1
        else:
            in_row = next(in_csv, end_row)
        while (end_row != in_row
            and (None == out_row_count_max or row_count < out_row_count_max)
            ):
            out_row = []
            out_column_position = 0
            while (out_column_position < len(column_position_map)):
                in_column_position = column_position_map[out_column_position]
                cell_value = None
                if (None != in_column_position
                    and in_column_position < len(in_row)
                    ):
                    cell_value = in_row[in_column_position]
                column_width = None
                if (None != in_column_position
                    and in_column_position < len(column_width_list)
                    ):
                    column_width = column_width_list[in_column_position]
                if (None == column_width):
                    column_width = column_width_min
                out_cell_value = cell_value
                if (None == out_cell_value):
                    out_cell_value = ""
                if (column_width < len(out_cell_value)):
                    if (0 < column_width):
                        if (None == truncation_symbol):
                            out_cell_value = out_cell_value[0:column_width]
                        elif (len(truncation_symbol) <= column_width):
                            out_cell_value = out_cell_value[0:column_width-len(truncation_symbol)]
                            out_cell_value += truncation_symbol
                        elif (len(truncation_symbol) > column_width):
                            out_cell_value = truncation_symbol[0:column_width]
                    else:
                        out_cell_value = ""
                elif (column_width > len(out_cell_value)):
                    out_cell_value = out_cell_value.ljust(column_width)
                out_row.append(out_cell_value)
                out_column_position += 1
            out_line = output_delimiter.join(out_row) + output_row_terminator
            out_io.write(out_line)
            row_count += 1
            if (row_list_position < len(in_row_list)):
                in_row = in_row_list[row_list_position]
                row_list_position += 1
            else:
                in_row = next(in_csv, end_row)

if __name__ == "__main__":
    main(sys.argv, sys.stdin, sys.stdout, sys.stderr)
