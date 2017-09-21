# CSV Commandline tools

Light-weight python scripts for processing CSV files from commandline.

Copyright (c) 2016-2017 Upstream Research, Inc.  All Rights Reserved.

Source Code is made available under the MIT License.


### In Development

(2017-06-02 (db))

Warning: alpha quality code.

These scripts are written as relatively independent commandline tools,
with few external dependencies (other than Python) and are
intended for processing CSV (Comma-Separated-Value) files that may be very large.
They have been developed to accomplish immediate tasks
and have not yet been refined into a more friendly, distributable package.

Development and usage has been with Python 3.5 on Windows.
Some attempt has been made to keep compatibility with non-Windows environments
and with earlier versions of Python, but there are no guarantees right now.


### Requirements

Python 3.5 or later.  
Earlier versions of Python 3.x may also work, but are untested.  
Unfortunately, Python 2.x does not work due to some issues with unicode support in its base library CSV module.


### Usage

Most scripts here are intended to be executed independently;
there is no single "main" script.
Each provides commandline help using the `--help` option.
For example:

        python csv-translate.py --help

Scripts are written to work with STD I/O.  
By default, most scripts accept CSV data from STDIN and write CSV data back to STDOUT.
Python and Windows make this a little difficult for non-ASCII character encodings and for Windows newline (CR-LF) sequences, so be careful.
The tools can handle any character encoding that python can handle, 
but piping I/O in the Windows command shell doesn't always work so well.

Most tools assume that the CSV file has a header row.


### The Tools

You can expect this document to be out-of-date, 
but here is a brief description of some of the tools so that you can get an idea of the flavor of this library.

* `csv-translate` : This is the "prototype" script.  It hardly does anything.
    It's function is to translate the formatting of delimited text files,
    which includes the delimiter, the newline encodings, and the character set encodings.
    This tool is used as a baseline for the other tools, 
    so most of the other tools are derived from the code from this one.
* `csv-append` : Combines CSV files by matching row data to column names.
* `csv-col2row` : Transpose a subset of named columns into rows.
* `csv-columns` : Transposes a CSV stream.
    In the default case, it prints the first row of an input CSV stream,
    one line of output per column from the input.
    This has the effect of printing the column header names
    on separate lines in the default case.
    In more extended cases, it prints the data across rather than down,
    which can be useful for reading CSV data in a terminal.
* `csv-count` : Count rows, columns, cells in a CSV stream.
* `csv-distinct` : Finds distict values in a column of a CSV stream.
* `csv-filter` : Very simplistic row filter for a CSV stream
* `csv-headmerge` : Merge multiple header rows into one row.
* `csv-join` : Joins records from an input CSV stream to records in a base CSV file.
* `csv-json` : Does a simplistic conversion of JSON to CSV.
* `csv-prepend` : Insert a header row to a CSV stream.
* `csv-print` : Converts CSV to fixed-with text which is helpful for reading CSV data in a terminal.
* `csv-row2col` : Transposes "named rows" into columns
* `csv-rowcalc` : Runs a python script for each row in a CSV stream.
    Can be used as a "field calculator".
* `csv-rownum` : Prepends a row number column to a CSV stream.
* `csv-select` : Selects a subset of columns from a CSV stream.
* `csv-sort` : Sort rows in a CSV stream.
* `csv-tail` : Filters the tail rows from a CSV stream.

      
