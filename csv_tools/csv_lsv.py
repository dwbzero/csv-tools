## ORIGIN csv_wsv.py

import sys

if __name__ in ("__main__", "csv_lsv"):
    from csv_translate import CsvTranslateProcessor
    from base import lsv
else:
    from .csv_translate import CsvTranslateProcessor
    from .base import lsv

open_lsv_reader = lsv.open_lsv_reader
open_lsv_writer = lsv.open_lsv_writer


HELP_TEXT = """{program_name} tool version 20201227
Translate CSV to "Line Separated Value" format.

{program_name} [OPTIONS] [InputFile]

OPTIONS
    -!,--decode   Invert process; translate LSV to CSV
    -e {E}        Output file text encoding (e.g. 'utf-8', 'windows-1252')
    -E {E}        Input file text encoding (e.g. 'utf-8', 'windows-1252')

The Line Separated Value format separates each datum by a line.
Records are separated by the symbol: "---".
Lines must be prefixed by a one-line "-" or multi-line ">" prefix symbol.
In a multi-line datum, each line must be prefixed by ">", 
the end of the datum will be the start of a one-line datum,
a record separator, or an empty line.

Typical example:

    - Washington
    - King County
    - Seattle
    ---
    - Washington
    - Pierce County
    - Tacoma
    ---

Translates to the CSV representation:

    Washington,King County,Seattle
    Washington,Pierce County,Tacoma
"""


class LsvTranslateProcessor(CsvTranslateProcessor):
    """ Translate between CSV and LSV. """
    LSV_FORMAT = "LSV"
    CSV_FORMAT = "CSV"
    help_text = HELP_TEXT
    in_format = CSV_FORMAT
    out_format = LSV_FORMAT

    def parse_next_arg(self, arg_obj, arg, arg_iter):
        """ Override to parse custom args. """
        succeeded = True
        if arg in ("-!", "--decode", "--from-lsv", "--to-csv"):
            arg_obj.in_format = self.LSV_FORMAT
            arg_obj.out_format = self.CSV_FORMAT
        else:
            succeeded = super(LsvTranslateProcessor, self).parse_next_arg(arg_obj, arg, arg_iter)
        return succeeded

    def open_writer(self, arg_obj, file_name, out_io, err_io):
        """ Open a CSV or LSV writer using commandline argument options. """
        if arg_obj.out_format == self.LSV_FORMAT:
            out_csv = open_lsv_writer(
                    out_io,
                    file_name,
                    encoding=arg_obj.out_charset_name,
                    errors=arg_obj.out_charset_error_mode,
                    lineterminator=arg_obj.out_row_terminator,
                    )
        else:
            out_csv = super(LsvTranslateProcessor, self).open_writer(
                    arg_obj,
                    file_name,
                    out_io,
                    err_io,
                    )
        return out_csv

    def open_reader(self, arg_obj, file_name, in_io, err_io):
        """ Open an CSV or LSV reader using commandline argument options. """
        if arg_obj.in_format == self.LSV_FORMAT:
            in_csv = open_lsv_reader(
                    in_io,
                    file_name,
                    encoding=arg_obj.in_charset_name,
                    errors=arg_obj.in_charset_error_mode,
                    lineterminator=arg_obj.in_row_terminator,
                    )
        else:
            in_csv = super(LsvTranslateProcessor, self).open_reader(
                    arg_obj,
                    file_name,
                    in_io,
                    err_io,
                    )
        return in_csv

    def execute(self, arg_obj, in_io, out_io, err_io):
        """ Execute the csv processing operation. """
        exit_code = 0
        exe = self
        with exe.open_reader(arg_obj, arg_obj.in_file_name, in_io, err_io) as in_csv:
            with exe.open_writer(arg_obj, arg_obj.out_file_name, out_io, err_io) as out_csv:
                for row in exe.process(in_csv):
                    out_csv.writerow(row)
        return exit_code


def main(argv, in_io, out_io, err_io):
    exe = LsvTranslateProcessor()
    return exe.main(argv, in_io, out_io, err_io)


def console_main():
    main(sys.argv, sys.stdin, sys.stdout, sys.stderr)

        
if __name__ == "__main__":
    sys.exit(console_main())
