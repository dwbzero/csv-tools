##  Copyright (c) 2016-2020 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##

import sys

if __name__ == "__main__":
    from csv_translate import CsvTranslateProcessor
else:
    from .csv_translate import CsvTranslateProcessor


HELP_TEXT = """{program_name} tool version 20170602:20201225
Counts CSV rows and cells

{program_name} [OPTIONS] [InputFile]

OPTIONS
    -E {E}  Input file text encoding (e.g. 'utf-8', 'windows-1252')
    -S {S}  Input file field delimiter (default ',')
    -W {S}  Input line terminator (default '\\r\\n')
    -h,--header   print a header row containing counter names
    --cells       print cell count
    --columns     print column count (of first row only)
    --rows        print row count (includes header row)

By default, prints rows, columns, cells, and file name as a CSV row.
"""

class CsvCountProcessor(CsvTranslateProcessor):
    """ Reads CSV files and counts rows and cells (like wc) """
    # (20200418 (db) This class is sort of an experiment:
    #  Notice that it derives from CsvTranslateProcessor.
    #  This allows it to re-use much of CsvTranslateProcessor's behavior,
    #   including commandline processing and file handling.)
    should_print_header_row = False
    should_print_custom_count = False
    should_print_row_count = None
    should_print_cell_count = None
    should_print_column_count = None
    help_text = HELP_TEXT

    def parse_next_arg(self, arg_obj, arg, arg_iter):
        """ Override to parse custom args. """
        succeeded = True
        if arg in ("-h", "--header", "--header-out"):
            arg_obj.should_print_header_row = True
        elif arg in ("--rows",):
            arg_obj.should_print_custom_count = True
            arg_obj.should_print_row_count = True
        elif arg in ("--columns",):
            arg_obj.should_print_custom_count = True
            arg_obj.should_print_column_count = True
        elif arg in ("--cells",):
            arg_obj.should_print_custom_count = True
            arg_obj.should_print_cell_count = True
        else:
            succeeded = super(CsvCountProcessor, self).parse_next_arg(arg_obj, arg, arg_iter)
        return succeeded

    def parse_args(self, argv):
        """ Override to evaluate custom args. """
        arg_obj = super(CsvCountProcessor, self).parse_args(argv)
        if arg_obj.should_print_custom_count:
            if arg_obj.should_print_row_count is None:
                arg_obj.should_print_row_count = False
            if arg_obj.should_print_column_count is None:
                arg_obj.should_print_column_count = False
            if arg_obj.should_print_cell_count is None:
                arg_obj.should_print_cell_count = False
        else:
            arg_obj.should_print_row_count = True
            arg_obj.should_print_column_count = True
            arg_obj.should_print_cell_count = True
        return arg_obj

    def process(self, rows):
        """ Read rows and count them. """
        arg_obj = self
        in_file_name = arg_obj.in_file_name
        should_print_header_row = arg_obj.should_print_header_row
        should_print_row_count = arg_obj.should_print_row_count
        should_print_column_count = arg_obj.should_print_column_count
        should_print_cell_count = arg_obj.should_print_cell_count
        
        in_column_count = 0
        in_cell_count = 0
        in_row_count = 0
        for in_row in rows:
            if in_row_count < 1:
                in_column_count = len(in_row)
                # Don't read the rest of the rows if we don't need to:
                if not should_print_row_count and not should_print_cell_count:
                    break
            in_cell_count += len(in_row)
            in_row_count += 1
        
        out_header_row = []
        out_row = []
        if should_print_row_count:
            out_header_row.append("rows")
            out_row.append(str(in_row_count))
        if should_print_column_count:
            out_header_row.append("columns")
            out_row.append(str(in_column_count))
        if should_print_cell_count:
            out_header_row.append("cells")
            out_row.append(str(in_cell_count))
        if in_file_name is not None:
            out_header_row.append("file_name")
            out_row.append(in_file_name)

        if should_print_header_row:
            yield out_header_row
        yield out_row


def main(argv, in_io, out_io, err_io):
    exe = CsvCountProcessor()
    return exe.main(argv, in_io, out_io, err_io)


def console_main():
    main(sys.argv, sys.stdin, sys.stdout, sys.stderr)

        
if __name__ == "__main__":
    sys.exit(console_main())
