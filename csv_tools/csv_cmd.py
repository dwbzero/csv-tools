""" Top-level command driver module to execute csv subprograms. 

    Implemented as a module so that it can be wrapped in an executable.
"""


import os
import sys

HELP_TEXT = """{program_name} tool version 20200516
Manipulate CSV I/O streams.

{program_name} Command args...

COMMANDS:

    help <CMD> : show help for CMD
    append     : Append CSV files with common column schema.
    col2row    : Transpose subset of CSV columns into rows.
    columns    : Transpose CSV rows and columns.  Print CSV column names.
    count      : Count rows, columns, and cells in a csv document.
    distinct   : Aggregate distinct column values of a CSV stream.
    filter     : Basic row exclusion by a simple expression.
    headmerge  : Merge multi-line headers into a single header row.
    join       : Joinn CSV documents by common column values.
    json       : Convert between a simple JSON document and CSV.
    prepend    : Insert rows at start of CSV stream.
    print      : Print CSV in fixed-width columns.
    rejoin     : Expand value lists embedded in a CSV columns into rows.
    row2col    : Aggregate and transpose CSV rows into columns.
    rowcalc    : Execute a custom python script on each row of a CSV stream.
    rownum     : Add a row count column to a CSV stream.
    select     : Select/Project and rename a subset of CSV columns.
    sort       : Sort CSV rows in memory.
    tail       : Omit all except the final rows of a CSV stream.
    translate  : Translate between CSV encodings. Skip and omit tail rows.
"""


def main(argv, in_io, out_io, err_io):
    """ Main entry point function. """
    endl = '\n'
    exit_code = 0
    arg_iter = iter(argv)
    program_path = next(arg_iter)
    program_name = os.path.basename(program_path)
    should_show_help = False
    err_str = None
    cmd_name = None
    cmd_args = None
    for arg in arg_iter:
        if arg is None:
            pass
        elif cmd_name:
            cmd_args.append(arg)
        elif arg in ("-?", "--help"):
            should_show_help = True
        elif arg.startswith("-"):
            err_str = "Unknown option: " + arg
        else:
            cmd_name = arg
            cmd_args = [cmd_name]
    if not cmd_name:
        should_show_help = True
    elif cmd_name == "help":
        if len(cmd_args) < 2:
            should_show_help = True
        else:
            # User typed "help <command>",
            #  change this to "<command> --help":
            cmd_name = cmd_args[1]
            cmd_args[0] = cmd_name
            cmd_args[1] = "--help"
    cmd_main = None
    if should_show_help:
        # We will print help leter:
        pass
    elif err_str:
        # We will print the error later:
        pass
    elif cmd_name == "append":
        from .csv_append import main as cmd_main
    elif cmd_name == "col2row":
        from .csv_col2row import main as cmd_main
    elif cmd_name == "columns":
        from .csv_columns import main as cmd_main
    elif cmd_name == "count":
        from .csv_count import main as cmd_main
    elif cmd_name == "distinct":
        from .csv_distinct import main as cmd_main
    elif cmd_name == "filter":
        from .csv_filter import main as cmd_main
    elif cmd_name == "headmerge":
        from .csv_headmerge import main as cmd_main
    elif cmd_name == "join":
        from .csv_join import main as cmd_main
    elif cmd_name == "json":
        from .csv_json import main as cmd_main
    elif cmd_name == "prepend":
        from .csv_prepend import main as cmd_main
    elif cmd_name == "print":
        from .csv_print import main as cmd_main
    elif cmd_name == "rejoin":
        from .csv_rejoin import main as cmd_main
    elif cmd_name == "row2col":
        from .csv_row2col import main as cmd_main
    elif cmd_name == "rownum":
        from .csv_rownum import main as cmd_main
    elif cmd_name == "select":
        from .csv_select import main as cmd_main
    elif cmd_name == "sort":
        from .csv_sort import main as cmd_main
    elif cmd_name == "tail":
        from .csv_tail import main as cmd_main
    elif cmd_name == "translate":
        from .csv_translate import main as cmd_main
    else:
        err_str = "Unknown command: " + cmd_name

    if should_show_help:
        help_text = HELP_TEXT.replace("{program_name}", program_name)
        out_io.write(help_text)
    if err_str:
        err_io.write(err_str)
        err_io.write(endl)
        exit_code = 2
    elif cmd_main:
        assert cmd_args is not None
        cmd_args[0] = "{0} {1}".format(program_name, cmd_name)
        exit_code = cmd_main(cmd_args, in_io, out_io, err_io)

    return exit_code


def console_main():
    """ Main entry point when invoked from an executable wrapper. """
    return main(sys.argv, sys.stdin, sys.stdout, sys.stderr)

        
if __name__ == "__main__":
    sys.exit(console_main())
