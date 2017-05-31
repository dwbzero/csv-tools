##  Copyright (c) 2016 Upstream Research, Inc.  All Rights Reserved.  ##

help_text = (
    "CSV-DISTINCT tool version 20160927:20170512\n"
    "Find distinct cell values in a column of a CSV file\n"
    "Copyright (c) 2016 Upstream Research, Inc.  All Rights Reserved.\n"
    "\n"
    "csv-distinct [OPTIONS] SourceColumns [InputFile]\n"
    "\n"
    "OPTIONS\n"
    "    -F {F}  Column/Field name for counter column\n"
    "    -o {F}  Output file name\n"
    "    --ignore-case   Ignore character case when comparing values\n"
    "\n"
    "SourceColumns is a comma-separated list of column names found in the input stream.\n"
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
    output_delimiter = ','
    # 'std' will be translated to the standard line break decided by csv_helpers.decode_newline
    input_row_terminator = 'std'
    output_row_terminator = 'std'
    input_charset_name = 'utf_8_sig'
    output_charset_name = 'utf_8'
    csv_cell_width_limit = 4*1024*1024  # python default is 131072 = 0x00020000
    in_source_column_name_list_string = None
    in_counter_column_name = None
    should_ignore_case = False
    # [20160916 [db] I avoided using argparse in order to retain some flexibility for command syntax]
    arg_count = len(arg_list)
    arg_index = 1
    while (arg_index < arg_count):
        arg = arg_list[arg_index]
        if (arg == "--help" 
          or arg == "-?"
          ):
            show_help = True
        elif (arg == "-F"
          or arg == "--counter-field"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                in_counter_column_name = arg
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
        elif (arg == "--ignore-case"):
            should_ignore_case = True
        elif (None != arg
          and 0 < len(arg)
          ):
            if (None == in_source_column_name_list_string):
                in_source_column_name_list_string = arg
            elif (None == input_file_name):
                input_file_name = arg
        arg_index += 1

    if (None == in_source_column_name_list_string):
        show_help = True

    if (show_help):
        out_io.write(help_text)
    else:
        in_source_column_name_list = []
        if (None != in_source_column_name_list_string):
            in_source_column_name_list = in_source_column_name_list_string.split(',')
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
            out_csv = csv.writer(out_io, delimiter=output_delimiter, lineterminator=output_row_terminator)
            try:
                execute(
                  in_csv, 
                  out_csv, 
                  input_delimiter, 
                  output_delimiter,
                  in_source_column_name_list,
                  in_counter_column_name 
                  ,should_ignore_case
                  )
            except BrokenPipeError:
                # ignore BrokenPipeError; it is raised when a downstream process exits early (head.exe does this)
                pass
            except IOError:
                # ignore IOError; it is raised when a downstream process exits early (head.exe does this)
                pass
        finally:
            if (None != in_file):
                in_file.close()
            if (None != out_file):
                out_file.close()

def execute(
    in_csv
    , out_csv
    , input_delimiter
    , output_delimiter
    , in_source_column_name_list
    , in_counter_column_name
    , should_ignore_case
    ):
    end_row = None
    end_cell = None
    distinct_row_counters = dict()
    out_column_name_list = list()
    in_source_column_position_list = list()
    in_source_column_position = None
    in_row_position = 0
    in_row = end_row
    # find column offset from header row
    in_header_row = next(in_csv, end_row)
    if (None != in_header_row):
        out_column_position = 0
        while (out_column_position < len(in_source_column_name_list)):
            out_column_name = in_source_column_name_list[out_column_position]
            out_column_name_norm = out_column_name.strip().lower()
            found_column_position = len(in_header_row)
            in_column_position = 0
            while (found_column_position >= len(in_header_row)
                and in_column_position < len(in_header_row)
                ):
                in_column_name = in_header_row[in_column_position]
                in_column_name_norm = in_column_name.strip().lower()
                if (in_column_name_norm == out_column_name_norm):
                    found_column_position = in_column_position
                in_column_position += 1
            if (found_column_position < len(in_header_row)):
                in_source_column_position_list.append(found_column_position)
                out_column_name_list.append(out_column_name)
            out_column_position += 1
    
    # look for distinct rows
    if (0 < len(out_column_name_list)
        and len(out_column_name_list) == len(in_source_column_position_list)
        ):
        in_row = next(in_csv, end_row)
        while (end_row != in_row):
            out_column_position = 0
            out_row = list()
            while (out_column_position < len(out_column_name_list)):
                in_source_column_position = in_source_column_position_list[out_column_position]
                cell_value = None
                if (in_source_column_position < len(in_row)):
                    cell_value = in_row[in_source_column_position]
                if (None != cell_value
                    and should_ignore_case
                    ):
                    cell_value = cell_value.upper()
                out_row.append(cell_value)
                out_column_position += 1

            distinct_row_key = tuple(out_row)
            distinct_row_count = distinct_row_counters.get(distinct_row_key, 0)
            distinct_row_count += 1
            distinct_row_counters[distinct_row_key] = distinct_row_count 
            in_row = next(in_csv, end_row)

    # write a header row
    out_row = list(out_column_name_list)
    if (None != in_counter_column_name):
        out_row.append(in_counter_column_name)
    out_csv.writerow(out_row)

    # construct a new mutable list of the keys so that we can sort it
    distinct_row_list = list(distinct_row_counters.keys())
    distinct_row_list.sort()
    for distinct_row in distinct_row_list:
        out_row = list(distinct_row)
        if (None != in_counter_column_name):
            distinct_row_count = distinct_row_counters[distinct_row]
            out_row.append(distinct_row_count)
        out_csv.writerow(out_row)

if __name__ == "__main__":
    main(sys.argv, sys.stdin, sys.stdout, sys.stderr)
