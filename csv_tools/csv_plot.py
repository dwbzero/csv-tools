""" Plot numeric data from stdio as text to stdout. """

import os
import sys
if __name__ == "__main__":
    from csv_translate import CsvTranslateProcessor
else:
    from .csv_translate import CsvTranslateProcessor


HELP_TEXT = """{program_name} tool version 20201201
print a graph of numeric data from a CSV stream onto stdout.

{program_name} [OPTIONS] Range [InputFile]

OPTIONS
    -g,--width <N>    : number of character columns per line of plot.
    -K,--skip <N>     : ignore the first N rows from the input stream.
    -k,--step <N>     : skip N-1 rows between each input row.
    --label-width <N> : use first column as label with character width N.
    -s,--symbols <S>  : sequence of characters to use as plot markers.
    -m,--channels <N> : plot numbers in N separate channel columns.

Tries to interpret cell values from a CSV as numbers
and plots cell values for each input row to a line in the output stream.

Input values will be plotted proportional to an input RANGE,
which is specified as an expression in one of the following forms:
    N     : The range will be [0,N]
    N+M   : The range will be [N,N+M]
    N+/-M : The range will be [N-M,N+M]

Two plot modes are supported: HORIZONTAL and CHANNEL mode.

HORIZONTAL mode plots all numeric values in the same row to an output position
proportional to the cell value within the input RANGE.  Cells from the 
same input column will be assigned the same SYMBOL in the output.
This is the default mode.

CHANNEL mode plots all numeric values from the same input column in
the same output column.  The plot symbol is chosen from the SYMBOL sequence
by its position proportional to the input RANGE.
This mode is invoked by the --channels option.

The SYMBOL sequence is a sequence of characters such as ".+xX#".
"""

def terminal_size(ios=None):
    """ Get (width,height) of controlling console.
    
        Returns (None,None) if there is no controlling console.
    """
    # https://stackoverflow.com/questions/566746/how-to-get-linux-console-window-width-in-python
    # . Perhaps the 0 should be replaced with fcntl.ioctl(sys.stdin.fileno(), ...
    # . I think you should use stdout or stderr instead of stdin, though. 
    #   stdin might very well be a pipe. 
    #   You might also want to add a line such as 
    #       if not os.isatty(0): return float("inf")
    import fcntl
    import termios
    import struct
    if ios is None:
        ios = sys.stdout
    fileno = ios.fileno()
    # _, _ = wp, hp should contain pixel width and height, but don't.
    if not os.isatty(fileno):
        return (None, None)
    h, w, _, _ = struct.unpack('HHHH',
        fcntl.ioctl(fileno, termios.TIOCGWINSZ,
            struct.pack('HHHH', 0, 0, 0, 0)
            )
        )
    return (w, h)


def parse_range_expr(range_expr):
    """ Parse a range expression into a (min,max) pair """
    not_found = -1
    min_val = None
    max_val = None
    if range_expr is None:
        return (min_val, max_val)
    sep = "+/-"
    pos = range_expr.find(sep)
    if pos >= 0:
        mid_str = range_expr[:pos]
        ext_str = range_expr[pos+len(sep):]
        mid_val = 0.0
        if mid_str:
            mid_val = float(mid_str)
        ext_val = float(ext_str)
        min_val = mid_val - ext_val
        max_val = mid_val + ext_val
        return (min_val, max_val)
    sep = "+"
    pos = range_expr.find(sep)
    if pos >= 0:
        min_str = range_expr[:pos]
        max_str = range_expr[pos+len(sep):]
        min_val = 0.0
        if min_str:
            min_val = float(min_str)
        max_val = float(max_str)
        return (min_val, max_val)
    min_val = 0.0
    max_val = float(range_expr)
    return (min_val, max_val)


class CsvPlotter(CsvTranslateProcessor):
    """ Plot numeric data from a CSV file to a character output stream. """
    COL_COUNT_DEFAULT = 80
    MISSING_OPTION_FSTRING = "Missing argument for option {0}"
    POS_MARKS = ".+xX#"
    NEG_MARKS = "@Oo. +xX#"
    help_text = HELP_TEXT
    err_msg = None
    init_count = 0
    step_size = 1
    col_count = None
    out_chan_count = None
    label_len = None
    range_expr = None
    range_min = None
    range_max = None
    marks = None
    bg_char = ' '

    def parse_next_arg(self, arg_obj, arg, arg_iter):
        """ Override to parse custom args. """
        MISSING_OPTION_FSTRING = self.MISSING_OPTION_FSTRING
        err_msg = None
        succeeded = True
        if arg in ("-g", "--width"):
            flag = arg
            arg = next(arg_iter, None)
            if arg is None:
                err_msg = MISSING_OPTION_FSTRING.format(flag)
            else:
                arg_obj.col_count = int(arg)
        elif arg in ("-K", "--skip"):
            flag = arg
            arg = next(arg_iter, None)
            if arg is None:
                err_msg = MISSING_OPTION_FSTRING.format(flag)
            else:
                arg_obj.init_count = int(arg)
        elif arg in ("-k", "--step"):
            flag = arg
            arg = next(arg_iter, None)
            if arg is None:
                err_msg = MISSING_OPTION_FSTRING.format(flag)
            else:
                arg_obj.step_size= int(arg)
        elif arg in ("--label-width",):
            flag = arg
            arg = next(arg_iter, None)
            if arg is None:
                err_msg = MISSING_OPTION_FSTRING.format(flag)
            else:
                arg_obj.label_len = int(arg)
        elif arg in ("-R", "--range"):
            flag = arg
            arg = next(arg_iter, None)
            if arg is None:
                err_msg = MISSING_OPTION_FSTRING.format(flag)
            else:
                arg_obj.range_expr = arg
        elif arg in ("-s", "--symbols"):
            flag = arg
            arg = next(arg_iter, None)
            if arg is None:
                err_msg = MISSING_OPTION_FSTRING.format(flag)
            else:
                arg_obj.marks = arg
        elif arg in ("-m","--channels"):
            flag = arg
            arg = next(arg_iter, None)
            if arg is None:
                err_msg = MISSING_OPTION_FSTRING.format(flag)
            else:
                arg_obj.out_chan_count = int(arg)
        elif arg.startswith("-"):
            succeeded = False
        elif arg_obj.range_expr is None:
            arg_obj.range_expr = arg
        else:
            succeeded = False
        if not succeeded:
            succeeded = super(CsvPlotter, self).parse_next_arg(arg_obj, arg, arg_iter)
        if err_msg and not arg_obj.err_msg:
            arg_obj.err_msg = err_msg
            succeeded = False
        return succeeded

    def parse_args(self, argv):
        """ Override to evaluate custom args. """
        arg_obj = super(CsvPlotter, self).parse_args(argv)
        err_msg = arg_obj.err_msg
        range_expr = arg_obj.range_expr
        col_count = arg_obj.col_count
        if not err_msg and not range_expr:
            err_msg = "Missing range expression"
        if not err_msg and range_expr:
            try:
                arg_obj.range_min, arg_obj.range_max = parse_range_expr(range_expr)
            except ValueError:
                err_msg = "Invalid range expression: {0}".format(range_expr)
        if not err_msg and col_count is not None and col_count < 1:
            err_msg = "Invalid column count: {0}".format(col_count)
        if err_msg:
            arg_obj.err_msg = err_msg
        return arg_obj

    def execute(self, arg_obj, in_io, out_io, err_io):
        """ Execute the csv processing operation. """
        endl = '\n'
        exit_code = 0
        exe = self
        err_msg = arg_obj.err_msg
        col_count = arg_obj.col_count
        if err_msg is None and col_count is None:
            # Detecting the column count this way only works if stdout is not redirected.
            col_count, _ = terminal_size(out_io)
            if col_count is None:
                col_count = self.COL_COUNT_DEFAULT
            arg_obj.col_count = col_count
        if err_msg:
            err_io.write(err_msg)
            err_io.write(endl)
            exit_code = 1
        else:
            endl = arg_obj.out_row_terminator
            with exe.open_reader(arg_obj, arg_obj.in_file_name, in_io, err_io) as in_csv:
                for line_str in exe.plot(in_csv):
                    out_io.write(line_str)
                    out_io.write(endl)
                    out_io.flush()
        return exit_code

    def plot(self, rows):
        """ Read rows and plot them. """
        arg_obj = self
        bg_char = arg_obj.bg_char
        range_min = arg_obj.range_min
        range_max = arg_obj.range_max
        label_len = arg_obj.label_len
        init_count = arg_obj.init_count
        step_size = arg_obj.step_size
        out_chan_count = arg_obj.out_chan_count
        marks = arg_obj.marks
        col_count = arg_obj.col_count
        if marks is None:
            marks = self.POS_MARKS
        min_val = range_min
        max_val = range_max
        lmargin = 0
        if label_len is not None:
            lmargin = label_len
        if lmargin > col_count:
            lmargin = 0
        plot_width = col_count - lmargin
        out_chan_width = None
        if out_chan_count:
            out_chan_width = plot_width // out_chan_count
        line_count = 0
        step_count = 0
        for row in rows:
            line_count += 1
            if init_count > line_count:
                continue
            step_count += 1
            if step_count < step_size:
                continue
            step_count = 0
            cell_iter = iter(row)
            label = ''
            if label_len is not None:
                label = next(cell_iter, None)
            if label_len is None:
                pass
            elif not label:
                label = lmargin * [bg_char]
            elif len(label) < lmargin:
                # pad the label
                label = label.ljust(lmargin, bg_char)
            elif len(label) > col_count:
                # truncate the label
                label = label[:col_count]
            line_marks = list(label)
            if len(line_marks) < col_count:
                line_marks.extend((col_count - len(line_marks)) * [bg_char])
            assert len(line_marks) == col_count
            nums = []
            for cell_str in cell_iter:
                try:
                    num = float(cell_str)
                except ValueError:
                    num = None
                if max_val is None:
                    max_val = num
                if min_val is None:
                    min_val = num
                if range_max is not None and num is not None and num > range_max:
                    num = range_max
                if range_min is not None and num is not None and num < range_min:
                    num = range_min
                if num is not None and max_val < num:
                    max_val = num
                if num is not None and min_val > num:
                    min_val = num
                nums.append(num)
            if min_val is not None and min_val == max_val:
                min_val -= 1.0
                max_val += 1.0
            if out_chan_count:
                assert out_chan_count > 0
                assert out_chan_width > 0
                mark_count = len(marks)
                for pos in range(lmargin, col_count):
                    chan_num = (pos - lmargin) // out_chan_width
                    num = None
                    if chan_num < len(nums) and chan_num < out_chan_count:
                        num = nums[chan_num]
                    if num is None:
                        ch = ' '
                    else:
                        mark_pos = int((num - min_val) / (max_val - min_val) * float(mark_count - 1))
                        ch = marks[mark_pos]
                    line_marks[pos] = ch
            else:
                for i, num in enumerate(nums):
                    if num is None:
                        continue
                    assert num >= min_val
                    assert num <= max_val
                    pos = lmargin
                    pos += int((num - min_val) / (max_val - min_val) * float(plot_width - 1))
                    assert pos >= 0
                    assert pos < col_count
                    mark_pos = i % len(marks)
                    line_marks[pos] = marks[mark_pos]
            out_line = "".join(line_marks)
            yield out_line


def main(argv, in_io, out_io, err_io):
    exe = CsvPlotter()
    return exe.main(argv, in_io, out_io, err_io)


def console_main():
    main(sys.argv, sys.stdin, sys.stdout, sys.stderr)

        
if __name__ == "__main__":
    sys.exit(console_main())
