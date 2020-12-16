##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##
""" Write a file/directory listing in CSV format. """

# 20201207 (db) ORIGIN csv_translate.py
# 20201207 (db) TODO refactor this file and csv_translate.py to better share code.

from contextlib import contextmanager
import errno
import os
import sys
import time

from .base.pyver import irange
from .base import csv2
from .base.csv2 import (
    lookup_delimiter,
    lookup_charset,
    lookup_newline,
    lookup_quote_symbol,
    )

HELP_TEXT = """{program_name} tool version 20201207
Write a file/directory listing in CSV-format.

{program_name} [OPTIONS] [Files]

OPTIONS
    -e {E}        Output file text encoding (e.g. 'utf-8', 'windows-1252')
    -h,--header   Print a header row.
    -o {F}        Output file name

"""

class CsvDirectoryListWriter(object):
    """ Writes a directory/file listing. """
    program_name = "{csv_processor}"
    exit_code = 0
    help_text = HELP_TEXT
    should_print_help = False
    #arg_error_message = None
    out_file_name = None
    out_delimiter = ','
    out_quote_symbol = '"'
    out_row_terminator = 'std'
    out_charset_name = 'utf_8'
    out_charset_error_mode = 'strict'  # 'strict' | 'ignore' | 'replace' | 'backslashreplace'
    csv_cell_width_limit = 4*1024*1024  # python default is 131072 = 0x00020000
    out_row_count_max = None
    should_print_header_row = False
    should_not_read_subdirs = False
    should_follow_symlinks = False
    in_paths = None

    def __init__(self):
        pass

    def parse_next_arg(self, arg, arg_iter):
        """ Parse the next argument flag from an argument iterator.

            Returns True if the argument was parsed:
            the parser should then get the next arg from arg_iter
            and keep parsing.
            Returns False if the argument was not parsed:
            the parser should try to parse the current argument
            according to any other parsing rules it may have.
        """
        succeeded = True
        arg_obj = self
        if arg in ("--help", "-?"):
            arg_obj.should_print_help = True
        elif arg in ("-o", "--output"):
            arg_obj.out_file_name = next(arg_iter)
        elif arg in ("-e", "--encoding-out", "--charset-out"):
            arg_obj.out_charset_name = next(arg_iter)
        elif arg in ("--charset-out-error-mode",):
            arg_obj.out_charset_error_mode = next(arg_iter)
        elif arg in ("--charset-error_mode",):
            error_mode = next(arg_iter)
            arg_obj.in_charset_error_mode = error_mode
            arg_obj.out_charset_error_mode = error_mode
        elif arg in ("-s", "--separator-out", "--delimiter-out"):
            arg_obj.out_delimiter = next(arg_iter)
        elif arg in ("-q", "--quote-out"):
            arg_obj.out_quote_symbol = next(arg_iter)
        elif arg in ("-w", "--terminator-out", "--newline-out", "--endline-out"):
            arg_obj.out_row_terminator = next(arg_iter)
        elif arg in ("--cell-width-limit",):
            arg_obj.csv_cell_width_limit = int(next(arg_iter))
        elif arg in ("-n", "--row-count-out"):
            arg = next(arg_iter)
            row_count = None
            if arg.upper() != 'ALL':
                row_count = int(arg)
            arg_obj.out_row_count_max = row_count
        elif arg in ("-h", "--header"):
            arg_obj.should_print_header_row = True
        elif arg in ("-d", "--directories"):
            arg_obj.should_not_read_subdirs = True
        elif arg.startswith("-"):
            succeeded = False
        elif arg_obj.in_paths is None:
            arg_obj.in_paths = [arg]
        else:
            arg_obj.in_paths.append(arg)
        return succeeded

    def parse_args(self, argv):
        """ Parse a list of commandline arguments into attributes of this object. """
        # [20160916 [db] I avoided using argparse
        #  in order to retain some flexibility for command syntax]
        arg_obj = self
        arg_iter = iter(argv)
        program_path = next(arg_iter)
        arg_obj.program_name = os.path.basename(program_path)
        for arg in arg_iter:
            if arg_obj.parse_next_arg(arg, arg_iter):
                pass
            else:
                raise LookupError("Unknown argument: " + arg)
        arg_obj.out_charset_name = lookup_charset(arg_obj.out_charset_name)
        arg_obj.out_row_terminator = lookup_newline(arg_obj.out_row_terminator)
        arg_obj.out_delimiter = lookup_delimiter(arg_obj.out_delimiter)
        arg_obj.out_quote_symbol = lookup_quote_symbol(arg_obj.out_quote_symbol)
        
        if not arg_obj.in_paths:
            # default to current directory
            arg_obj.in_paths = ["."]

        return arg_obj

    def print_help(self, out_io):
        """ Print command help information to a stream. """
        help_text = self.help_text.replace("{program_name}", self.program_name)
        out_io.write(help_text)

    @contextmanager
    def open_writer(self, file_name, out_io, err_io):
        """ Open an output CSV writer. """
        arg_obj = self
        out_file_name = file_name
        out_charset_name = arg_obj.out_charset_name
        out_charset_error_mode = arg_obj.out_charset_error_mode
        out_delimiter = arg_obj.out_delimiter
        out_row_terminator = arg_obj.out_row_terminator
        out_quote_symbol = arg_obj.out_quote_symbol
        out_file = None
        write_text_io_mode = 'w'
        out_file_id = out_file_name
        should_close_out_file = True
        if not out_file_id:
            out_file_id = out_io.fileno()
            should_close_out_file = False
        out_io = csv2.csv_open(
            out_file_id,
            mode=write_text_io_mode,
            encoding=out_charset_name,
            errors=out_charset_error_mode,
            closefd=should_close_out_file,
            )
        if should_close_out_file:
            out_file = out_io
        out_csv = csv2.CsvWriter(
            out_io,
            delimiter=out_delimiter,
            lineterminator=out_row_terminator,
            quotechar=out_quote_symbol,
            )
        # @contextmanager: enter: yield this object to the with statement:
        yield out_csv
        # @contextmanager: exit: after the yield close the stream:
        if should_close_out_file and out_file:
            out_file.close()

    def main(self, argv, in_io, out_io, err_io):
        """ Implements main entry point function. """
        exe = self
        exit_code = 0
        error_message = None
        try:
            arg_obj = exe.parse_args(argv)
            if arg_obj.should_print_help:
                exe.print_help(out_io)
            else:
                exit_code = exe.execute(arg_obj, in_io, out_io, err_io)
        except IOError as exc:
            if exc.errno == errno.EPIPE:
                # (also BrokenPipeError python 3)
                # can occur when a process serving a stdio stream quits
                pass
            elif exc.errno == errno.ENOENT:
                # (also FileNotFoundError python 3)
                error_message = "File '{FileName}' not found.".format(FileName=exc.filename)
                exit_code = 1
            else:
                raise
        except UnicodeError as exc:
            error_message = str(exc)
            exit_code = 1
            raise
        if error_message:
            err_io.write("Error: {E}\n".format(E=error_message))
            exit_code = 1
        return exit_code

    def execute(self, arg_obj, in_io, out_io, err_io):
        """ Execute the csv processing operation. """
        exit_code = 0
        exe = self
        with exe.open_writer(arg_obj.out_file_name, out_io, err_io) as out_csv:
            for row in exe.readrows(err_io):
                out_csv.writerow(row)
        return exit_code

    def readrows(self, err_io):
        """ Return a generator that will yield rows. """
        arg_obj = self
        out_row_count_max = arg_obj.out_row_count_max
        in_paths = arg_obj.in_paths
        should_print_header_row = arg_obj.should_print_header_row
        should_not_read_subdirs = arg_obj.should_not_read_subdirs
        should_follow_symlinks = arg_obj.should_follow_symlinks
        should_assume_utc = False
        dt_format = "%Y-%m-%dT%H:%M:%S"
        
        to_st_time = time.localtime
        if should_assume_utc:
            to_st_time = time.gmtime
        
        fspaths = in_paths
        if not should_not_read_subdirs:
            fspaths = []
            for fspath in in_paths:
                if fspath == os.path.curdir:
                    fspaths.extend(os.listdir(fspath))
                elif os.path.isdir(fspath):
                    fspaths.extend((
                        os.path.join(fspath, f)
                        for f in os.listdir(fspath)))
                else:
                    fspaths.append(fspath)

        if should_print_header_row:
            header_row = [
                "path",
                "dir",
                "name",
                "type",
                "size",
                "created",
                "modified",
                ]
            yield header_row

        out_row_count = 0
        for fspath in fspaths:
            if out_row_count_max is not None and out_row_count_max <= out_row_count:
                break
            # TODO use stats.st_mode to determine file node type:
            fs_node_type = "?"
            if os.path.isfile(fspath):
                fs_node_type = ""
            elif os.path.isdir(fspath):
                fs_node_type = "d"
            elif os.path.islink(fspath):
                fs_node_type = "l"
            #stats = os.stat(fspath, follow_symlinks=should_follow_symlinks)
            stats = os.stat(fspath)
            parent_path, fsname = os.path.split(fspath)
            st_created = to_st_time(stats.st_ctime)
            st_modified = to_st_time(stats.st_mtime)
            out_row = [
                fspath,
                parent_path,
                fsname,
                fs_node_type,
                str(stats.st_size),
                time.strftime(dt_format, st_created),
                time.strftime(dt_format, st_modified),
                ]
            yield out_row
            out_row_count += 1


def main(argv, in_io, out_io, err_io):
    """ Main entry point for program. """
    exe = CsvDirectoryListWriter()
    return exe.main(argv, in_io, out_io, err_io)


def console_main():
    """ Main entry point when invoked from executable wrapper. """
    return main(sys.argv, sys.stdin, sys.stdout, sys.stderr)


if __name__ == "__main__":
    sys.exit(console_main())
