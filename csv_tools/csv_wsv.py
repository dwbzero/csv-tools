## ORIGIN csv_count.py

import sys

if __name__ in ("__main__", "csv_wsv"):
    from csv_translate import CsvTranslateProcessor
    from base import wsv
else:
    from .csv_translate import CsvTranslateProcessor
    from .base import wsv

open_wsv_reader = wsv.open_wsv_reader
open_wsv_writer = wsv.open_wsv_writer


HELP_TEXT = """{program_name} tool version 20201227
Translate CSV to sh-compatible "Whitespace Separated Value" format.

{program_name} [OPTIONS] [InputFile]

OPTIONS
    -!,--decode   Invert process; translate WSV to CSV
    -e {E}        Output file text encoding (e.g. 'utf-8', 'windows-1252')
    -E {E}        Input file text encoding (e.g. 'utf-8', 'windows-1252')

Whitespace separated text can contain any number of whitespace characters
between datum values.  This makes it a somewhat convenient format
for editing tabular data in a regular text editor.

Since this WSV format is shell-compatibile, backslash characters
in a double-quoted item must be escaped with another backslash (e.g. '\\').
Backslashes do not need to be escaped in single-quoted items.
Double-quote characters in a double-quoted item
must be escaped with a backslash (e.g. '\"').
"""


class WsvTranslateProcessor(CsvTranslateProcessor):
    """ Translate between CSV and WSV. """
    WSV_FORMAT = "WSV"
    CSV_FORMAT = "CSV"
    help_text = HELP_TEXT
    in_format = CSV_FORMAT
    out_format = WSV_FORMAT

    def parse_next_arg(self, arg_obj, arg, arg_iter):
        """ Override to parse custom args. """
        succeeded = True
        if arg in ("-!", "--decode", "--from-wsv", "--to-csv"):
            arg_obj.in_format = self.WSV_FORMAT
            arg_obj.out_format = self.CSV_FORMAT
        else:
            succeeded = super(WsvTranslateProcessor, self).parse_next_arg(arg_obj, arg, arg_iter)
        return succeeded

    def open_writer(self, arg_obj, file_name, out_io, err_io):
        """ Open a CSV or WSV writer using commandline argument options. """
        if arg_obj.out_format == self.WSV_FORMAT:
            out_csv = open_wsv_writer(
                    out_io,
                    file_name,
                    encoding=arg_obj.out_charset_name,
                    errors=arg_obj.out_charset_error_mode,
                    lineterminator=arg_obj.out_row_terminator,
                    )
        else:
            out_csv = super(WsvTranslateProcessor, self).open_writer(
                    arg_obj,
                    file_name,
                    out_io,
                    err_io,
                    )
        return out_csv

    def open_reader(self, arg_obj, file_name, in_io, err_io):
        """ Open an CSV or WSV reader using commandline argument options. """
        if arg_obj.in_format == self.WSV_FORMAT:
            in_csv = open_wsv_reader(
                    in_io,
                    file_name,
                    encoding=arg_obj.in_charset_name,
                    errors=arg_obj.in_charset_error_mode,
                    lineterminator=arg_obj.in_row_terminator,
                    )
        else:
            in_csv = super(WsvTranslateProcessor, self).open_reader(
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
    exe = WsvTranslateProcessor()
    return exe.main(argv, in_io, out_io, err_io)


def console_main():
    main(sys.argv, sys.stdin, sys.stdout, sys.stderr)

        
if __name__ == "__main__":
    sys.exit(console_main())
