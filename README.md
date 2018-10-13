# CSV Commandline tools

Light-weight python scripts for processing CSV files from commandline.


Copyright (c) 2016-2018 Upstream Research, Inc.  All Rights Reserved.

Source Code is made available under an MIT License.

Revised 2018-10-13 (db)

### Overview

This project consists of a set of separate commandline programs for manipulating CSV data.
These programs are implemented in Python and are intended to be copied and modified
in order to accommodate the many idiosyncrasies of CSV data in the wild.
The general rule here has been to make each program as "dumb" as possible
in an attempt to follow the "do only one thing, and do it well" principle.

There are a few other decent commandline CSV processing tool-sets out there,
and this project is not really intended to duplicate those efforts.

The goals for this project are:

  * Minimal external dependencies (best if there are no dependencies at all).
  * Reusable source code - so that more processing tools may be readily developed.
  * Program independence - scripts can be copied individually.
  * Stream processing via STD I/O - to accommodate very large CSV data sources.

Some consequences of these goals are that Python 2.x is not supported,
and some extended cases of CSV format are not easy to support.

Development and usage has been with Python 3.5 on Windows.
Some attempt has been made to keep compatibility with non-Windows environments
and with earlier versions of Python, but there are no guarantees right now.


### Requirements

Python 3.5 or later.  
Earlier versions of Python 3.x may also work, but are untested.  
Unfortunately, Python 2.x does not work due to some issues with unicode support in its base library CSV module.


### Installation

This project has been packaged using Python `setuptools`.

For an ordinary installation which will copy files to an installation directory:

    > python setup.py install

Or - for a "development" installation which allows code to be modified in place:

    > python setup.py develop

See the `setuptools` documentation for details.


### Usage

Most programs here are intended to be executed independently;
there is no single "main" program.
Each provides commandline help using the `--help` option.
For example:

    > csv-translate --help

Programs are written to work with STD I/O.  
By default, most programs accept CSV data from STDIN and write CSV data back to STDOUT.
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

### Example: Lyme Disease Cases from US CDC

Suppose you have downloaded the `ld-case-counts-by-county-00-15.csv` data file from the US CDC website.
(It turns-out that this file is not very large, and you could view it using a Spreadsheet program,
but this example applies to very large files that are often impractical to open.)
It is claimed that this file contains numbers of confirmed cases of Lyme disease in various counties in the USA.
The first step is to see if there is a "header" row containing column names;
this will reveal a lot about the data.  We use the `csv-columns` program for this:

    > csv-columns ld-case-counts-by-county-00-15.csv
    
    STNAME
    CTYNAME
    STCODE
    CTYCODE
    Cases2000
    Cases2001
    Cases2002
    Cases2003
    Cases2004
    Cases2005
    Cases2006
    Cases2007
    Cases2008
    Cases2009
    Cases2010
    Cases2011
    Cases2012
    Cases2013
    Cases2014
    Cases2015

We can see above a list of column names from the CSV file.
It is often instructive to see data associated with these columns
and it is quite annoying to try and read this in the raw CSV,
however, it is quite a bit easier to read if we "transpose"
the data so that columns read horizontally instead of vertically.
We can do this with `csv-columns`:
The `-N 3` option says "read only the first 3 rows from the input".

    > csv-columns -N 3 ld-case-counts-by-county-00-15.csv

    STNAME,Alabama,Alabama
    CTYNAME,Autauga County,Baldwin County
    STCODE,1,1
    CTYCODE,1,3
    Cases2000,0,1
    Cases2001,0,0
    Cases2002,0,1
    Cases2003,0,0
    Cases2004,0,0
    Cases2005,0,0
    Cases2006,0,0
    Cases2007,0,0
    Cases2008,0,0
    Cases2009,0,1
    Cases2010,0,0
    Cases2011,0,1
    Cases2012,0,1
    Cases2013,0,0
    Cases2014,0,3
    Cases2015,0,1

With this information, we migt want to make a print-out of a selection
of the data which will allow some greater scrutiny of the data.
We will use a command process pipe to select a subset of the columns using `csv-select`
and to "pretty-print" them using `csv-print`.
The `csv-print` options `-H` means to print the full header names,
`-N 10` means "analyze the first 10 rows to determine column widths",
and `-n 20` means "stop printing after 20 rows".

    > csv-select STNAME,CTYNAME,Cases2000,Cases2005,Cases2010,Cases2015 ld-case-counts-by-county-00-15.csv 
      | csv-print -H -N 10 -n 20
    
    STNAME  CTYNAME         Cases2000 Cases2005 Cases2010 Cases2015
    Alabama Autauga County  0         0         0         0
    Alabama Baldwin County  1         0         0         1
    Alabama Barbour County  0         0         0         0
    Alabama Bibb County     0         0         0         0
    Alabama Blount County   0         0         0         0
    Alabama Bullock County  0         0         0         0
    Alabama Butler County   0         0         0         0
    Alabama Calhoun County  0         0         0         0
    Alabama Chambers County 0         0         0         1
    Alabama Cherokee County 0         0         0         0
    Alabama Chilton County  0         0         0         0
    Alabama Choctaw County  0         0         0         0
    Alabama Clarke County   0         0         0         0
    Alabama Clay County     0         0         0         1
    Alabama Cleburne County 0         0         0         0
    Alabama Coffee County   0         0         1         0
    Alabama Colbert County  0         0         0         0
    Alabama Conecuh County  0         0         0         0
    Alabama Coosa County    0         0         0         0

It turns out that for Lyme disease, Alabama is not as interesting as some other US States,
we can use the `csv-filter` command to select a different state.
But first, we have to handle a problem:

    > csv-filter STNAME = "New Hampshire" ld-case-counts-by-county-00-15.csv 
      | csv-select STNAME,CTYNAME,Cases2000,Cases2005,Cases2010,Cases2015 
      | csv-print -H -N 10 -n 20
    
    Traceback (most recent call last):
      File "csv-filter-script.py", line 9, in <module>
        load_entry_point('csv-tools==0.5.0', 'console_scripts', 'csv-filter')()
      ...
      File "utf_8_sig.py", line 69, in _buffer_decode
        return codecs.utf_8_decode(input, errors, final)
    UnicodeDecodeError: 'utf-8' codec can't decode byte 0xa4 in position 3156: invalid start byte
    STNAME        CTYNAME        Cases2000 Cases2005 Cases2010 Cases2015
    New Hampshire Belknap County 5         2         34        20
    New Hampshire Carroll County 2         4         35        12

This is a complicated way of saying that the CSV file is not encoded as UTF-8.
We can try to read the file using a different charset.
We `csv-translate` with the `-E cp437` option to interpret the input in "DOS" codepage,
and we use the `-e utf-8` option so that our output is piped along as UTF-8.
(If you are used to fighting with CSV files, then you are probably aware
of text encoding issues and "codepages", so I will not describe 
what "cp437" means here.  However, it is interesting to note
that our problem comes from the `LATIN SMALL LETTER N WITH TILDE`
character found in "Doña Ana" county New Mexico).
Additionally, if we are running this in a Windows console, 
we will need to issue a `chcp` command to change the console's code page
so that it will know how to display the output:

    @REM if this is a Windows command prompt, change the active code page to UTF-8
    > chcp 65001
    
    > csv-translate -E cp850 -e utf-8 ld-case-counts-by-county-00-15.csv 
      | csv-filter STNAME = "New Hampshire" 
      | csv-select STNAME,CTYNAME,Cases2000,Cases2005,Cases2010,Cases2015 
      | csv-print -H -N 10 -n 20
      
    STNAME        CTYNAME             Cases2000 Cases2005 Cases2010 Cases2015
    New Hampshire Belknap County      5         2         34        20
    New Hampshire Carroll County      2         4         35        12
    New Hampshire Cheshire County     7         6         29        30
    New Hampshire Coos County         3         4         5         2
    New Hampshire Grafton County      4         5         45        27
    New Hampshire Hillsborough County 14        75        423       123
    New Hampshire Merrimack County    8         9         109       83
    New Hampshire Rockingham County   31        129       500       142
    New Hampshire Strafford County    10        31        137       65
    New Hampshire Sullivan County     0         0         22        12
    New Hampshire New Hampshire       0         0         0         13

This could go on.  Other operations you might want to do could be:

* Use `csv-rowcalc` to pad the `STCODE` and `CTYCODE` columns with extra zeros to make them into valid "FIPS" codes.
* Use `csv-col2row` to transpose the `CasesYYYY` columns into rows containing "Year" and "Cases" columns.



