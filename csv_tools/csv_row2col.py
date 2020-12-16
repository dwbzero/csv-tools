##  Copyright (c) 2017 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##

help_text = (
    "CSV-ROW2COL tool version 20170921:20201208\n"
    "Transpose named rows into columns\n"
    "\n"
    "csv-row2col [OPTIONS] EACH NameColumn GROUP BY GroupColumns [InputFile]\n"
    "csv-row2col [OPTIONS] EACH NameColumn EXPAND ExpansionColumns [InputFile]\n"
    "\n"
    "OPTIONS\n"
    "    -o {F}  Output file name\n"
    "    -u      Name first expansion column exactly as value of NameColumn.\n"
    "    --ignore-case   Ignore character case when comparing values\n"
    "\n"
    "GroupColumns and ExpansionColumns are each a comma-separated list of \n"
    "column names found in the input stream.\n"
    "\n"
    "If GroupColumns is not specified, then the GroupColumns will be \n"
    "all the non-expansion columns minus the NameColumn.\n"
    "Similarly, if ExpansionColumns is not specified, then they will be\n"
    "all the non-group columns minus the NameColumn.\n"
    "\n"
    "Rows are \"expanded\" by adding new columns which will contain\n"
    "the value of a \"named row\". For example, if the input columns are:\n"
    "\n"
    "    state_code,year,population\n"
    "\n"
    "and the values in the 'year' column are: 2000,2010,2020, then\n"
    "\n"
    "    csv-row2col EACH year GROUP BY state_code\n"
    "or\n"
    "    csv-row2col EACH YEAR EXPAND population\n"
    "\n"
    "will produce the following columns:\n"
    "\n"
    "    state_code,2000_population,2010_population,2020_population\n"
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
    output_row_count_max = None
    in_counter_column_name = None
    should_ignore_case = False
    in_name_column_name = None
    in_group_column_name_list_str = None
    in_expand_column_name_list_str = None
    in_expand_column_name_template_str = "{0}_{1}"
    should_not_suffix_first_expand_column = False
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
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                in_counter_column_name = arg
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
        elif (arg == "--ignore-case"):
            should_ignore_case = True
        elif (arg == "-u"):
            should_not_suffix_first_expand_column = True
        elif (arg == "--column-format"):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                in_expand_column_name_template_str = arg
        elif (None == in_name_column_name
            and (arg == "--each"
                or arg.upper() == "EACH"
            )
        ):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                in_name_column_name = arg
        elif (None == in_expand_column_name_list_str
            and (arg == "--expand"
                or arg.upper() == "EXPAND"
            )
        ):
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                in_expand_column_name_list_str = arg
        elif (None == in_group_column_name_list_str
            and (arg == "--group-by"
                or arg.upper() == "GROUP"
            )
        ):
            arg2 = arg
            arg_index += 1
            if (arg_index < arg_count):
                arg = arg_list[arg_index]
                if (arg2.upper() == "GROUP" 
                    and arg.upper() == "BY"
                ):
                    arg_index += 1
                    arg = None
                    if (arg_index < arg_count):
                        arg = arg_list[arg_index]
                in_group_column_name_list_str = arg
        elif (None != arg
          and 0 < len(arg)
        ):
            if (None == input_file_name):
                input_file_name = arg
        arg_index += 1

    in_group_column_name_list = None
    if (None != in_group_column_name_list_str):
        in_group_column_name_list = in_group_column_name_list_str.split(',')
    
    in_expand_column_name_list = None
    if (None != in_expand_column_name_list_str):
        in_expand_column_name_list = in_expand_column_name_list_str.split(',')

    # name column is required
    if (None == in_name_column_name):
        show_help = True

    # either group-by columns or expansion columns are required
    if (None == in_group_column_name_list
        and None == in_expand_column_name_list
    ):
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
            try:
                execute(
                  in_csv
                  ,out_csv
                  ,output_row_count_max
                  ,should_ignore_case
                  ,should_not_suffix_first_expand_column
                  ,in_expand_column_name_template_str
                  ,in_name_column_name
                  ,in_group_column_name_list
                  ,in_expand_column_name_list
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
    ,out_csv
    ,out_row_count_max
    ,should_ignore_case
    ,should_not_suffix_first_expand_column
    ,in_expand_column_name_template_str
    ,in_name_column_name
    ,in_group_column_name_list
    ,in_expand_column_name_list
    ):
    end_row = None
    end_cell = None
    name_dict = dict()
    group_row_dict = dict()
    in_column_name_list = None
    in_column_count = 0
    out_column_name_list = list()
    in_name_column_name_norm = normalize_column_name(in_name_column_name)
    in_name_column_position = None
    in_expand_column_position_list = list()
    in_group_column_position_list = list()
    in_row_position = 0
    in_row = end_row
    # find column offsets from header row
    in_header_row = next(in_csv, end_row)
    if (None != in_header_row):
        in_column_name_list = in_header_row
        in_column_count = len(in_column_name_list)
        in_column_name_norm_list = list(map(normalize_column_name, in_column_name_list))

        # if we don't know group or expansion columns, 
        #  then infer them based on what we do know
        if (None == in_group_column_name_list
            and None == in_expand_column_name_list
        ):
            in_group_column_name_list = []
        a_column_name_list = None
        b_column_name_list = None
        if (None == in_group_column_name_list):
            a_column_name_list = in_expand_column_name_list
            b_column_name_list = in_group_column_name_list
        elif (None == in_expand_column_name_list):
            a_column_name_list = in_group_column_name_list
            b_column_name_list = in_expand_column_name_list
        if (None != a_column_name_list
            and None == b_column_name_list
        ):
            b_column_name_list = []
            a_column_count = len(a_column_name_list)
            in_column_position = 0
            while (in_column_position < in_column_count):
                in_column_name = in_column_name_list[in_column_position]
                in_column_name_norm = in_column_name_norm_list[in_column_position]
                if (in_column_name_norm != in_name_column_name_norm):
                    a_column_position = 0
                    found_column_position = None
                    while (None == found_column_position
                        and a_column_position < a_column_count
                    ):
                        a_column_name = a_column_name_list[a_column_position]
                        a_column_name_norm = normalize_column_name(a_column_name)
                        if (a_column_name_norm == in_column_name_norm):
                            found_column_position = a_column_position
                        a_column_position += 1
                    if (None == found_column_position):
                        b_column_name_list.append(in_column_name)
                in_column_position += 1
        if (None == in_group_column_name_list):
            in_group_column_name_list = b_column_name_list
        elif (None == in_expand_column_name_list):
            in_expand_column_name_list = b_column_name_list

        # get positions for the group columns
        group_column_position = 0
        while (group_column_position < len(in_group_column_name_list)):
            group_column_name = in_group_column_name_list[group_column_position]
            group_column_name_norm = normalize_column_name(group_column_name)
            found_column_position = None
            in_column_position = 0
            while (None == found_column_position
                and in_column_position < in_column_count
                ):
                in_column_name_norm = in_column_name_norm_list[in_column_position]
                if (in_column_name_norm == group_column_name_norm):
                    found_column_position = in_column_position
                in_column_position += 1
            in_group_column_position_list.append(found_column_position)
            group_column_position += 1
        
        # get positions for the expansion columns
        expand_column_position = 0
        while (expand_column_position < len(in_expand_column_name_list)):
            expand_column_name = in_expand_column_name_list[expand_column_position]
            expand_column_name_norm = normalize_column_name(expand_column_name)
            found_column_position = None
            in_column_position = 0
            while (None == found_column_position
                and in_column_position < in_column_count
            ):
                in_column_name_norm = in_column_name_norm_list[in_column_position]
                if (in_column_name_norm == expand_column_name_norm):
                    found_column_position = in_column_position
                in_column_position += 1
            in_expand_column_position_list.append(found_column_position)
            expand_column_position += 1

        # find the position of the name column
        in_column_position = 0
        while (None == in_name_column_position
            and in_column_position < in_column_count
        ):
            in_column_name = in_column_name_list[in_column_position]
            in_column_name_norm = normalize_column_name(in_column_name)
            if (in_column_name_norm == in_name_column_name_norm):
                in_name_column_position = in_column_position
            in_column_position += 1

    # read over the whole dataset,
    # build a dictionary of the group rows,
    # a dictionary of the distinct values in the name column,
    # and keep track of the named values for each row
    if (0 < len(in_group_column_position_list)
        and 0 < len(in_expand_column_position_list)
        and None != in_name_column_position
        ):
        in_row = next(in_csv, end_row)
        while (end_row != in_row):
            in_name_value = None
            if (None != in_name_column_position
                and in_name_column_position < len(in_row)
            ):
                in_name_value = in_row[in_name_column_position]
            if (None == in_name_value):
                in_name_value = ""
            
            name_count = name_dict.get(in_name_value,0)
            name_count += 1
            name_dict[in_name_value] = name_count

            # collect the expansion column values for this row
            expand_column_position = 0
            expand_value_list = list()
            while (expand_column_position < len(in_expand_column_position_list)):
                in_column_position = in_expand_column_position_list[expand_column_position]
                cell_value = None
                if (None != in_column_position
                    and in_column_position < len(in_row)
                ):
                    cell_value = in_row[in_column_position]
                expand_value_list.append(cell_value)
                expand_column_position += 1

            # create a sub-row for the group column values in this row
            group_column_position = 0
            group_row = list()
            while (group_column_position < len(in_group_column_position_list)):
                in_column_position = in_group_column_position_list[group_column_position]
                cell_value = None
                if (None != in_column_position
                    and in_column_position < len(in_row)
                ):
                    cell_value = in_row[in_column_position]
                if (None != cell_value
                    and should_ignore_case
                    ):
                    cell_value = cell_value.upper()
                group_row.append(cell_value)
                group_column_position += 1

            group_row_key = tuple(group_row)
            group_row_attributes = group_row_dict.get(group_row_key, dict())
            group_row_attributes[in_name_value] = expand_value_list
            group_row_dict[group_row_key] = group_row_attributes

            in_row = next(in_csv, end_row)

    # create a sorted list of the values from the name column,
    # this will determine the ordering of the expanded columns
    name_value_list = list(name_dict.keys())
    name_value_list.sort()

    out_column_name_list = list(in_group_column_name_list)
    # make the output column list using the group columns as the base
    #  and by "multiplying" the name column values by the expansion column names
    for name_value in name_value_list:
        for pos, expand_column_name in enumerate(in_expand_column_name_list):
            out_column_name = None
            if pos == 0 and should_not_suffix_first_expand_column:
                out_column_name = name_value
            else:
                out_column_name = in_expand_column_name_template_str
                out_column_name = out_column_name.replace("{1}", expand_column_name)
                out_column_name = out_column_name.replace("{0}", name_value)
            out_column_name_list.append(out_column_name)

    # write a header row
    out_row = list(out_column_name_list)
    out_csv.writerow(out_row)

    # write out each of the group rows with expanded columns
    out_row_count = 0
    for group_row_key, group_row_attributes in group_row_dict.items():
        out_row = list(group_row_key)
        for name_value in name_value_list:
            expand_value_list = group_row_attributes.get(name_value,[])
            expand_column_position = 0
            while (expand_column_position < len(in_expand_column_position_list)):
                expand_value = None
                if (expand_column_position < len(expand_value_list)):
                    expand_value = expand_value_list[expand_column_position]
                out_row.append(expand_value)
                expand_column_position += 1
        if (None == out_row_count_max
            or out_row_count < out_row_count_max
        ):
            out_csv.writerow(out_row)
        out_row_count += 1


def console_main():
    main(sys.argv, sys.stdin, sys.stdout, sys.stderr)

        
if __name__ == "__main__":
    console_main()
