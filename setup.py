##  Copyright (c) 2018 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##


from setuptools import setup


setup(
    name = 'csv-tools'
    ,version = '0.5.0'
    ,description = 'CSV commandline tools'
    ,url = 'http://github.com/Upstream-Research/csv-tools'
    ,author = 'Upstream Research, Inc.'
    ,author_email = ''
    ,license = 'MIT'
    ,keywords = 'csv pipe filter'
    ,classifiers = [
        'Development Status :: 3 - Alpha'
        ,'Environment :: Console'
        ,'License :: OSI Approved :: MIT License'
        ,'Programming Language :: Python'
        ,'Programming Language :: Python :: 3.5'
        ]
    ,packages = [ 
        'csv_tools' 
        ]
    ,entry_points = {
        'console_scripts': [
            'csv-append = csv_tools.csv_append:console_main'
            ,'csv-col2row = csv_tools.csv_col2row:console_main'
            ,'csv-columns = csv_tools.csv_columns:console_main'
            ,'csv-count = csv_tools.csv_count:console_main'
            ,'csv-distinct = csv_tools.csv_distinct:console_main'
            ,'csv-filter = csv_tools.csv_filter:console_main'
            ,'csv-headmerge = csv_tools.csv_headmerge:console_main'
            ,'csv-join = csv_tools.csv_join:console_main'
            ,'csv-json = csv_tools.csv_json:console_main'
            ,'csv-prepend = csv_tools.csv_prepend:console_main'
            ,'csv-print = csv_tools.csv_print:console_main'
            ,'csv-rejoin = csv_tools.csv_rejoin:console_main'
            ,'csv-row2col = csv_tools.csv_row2col:console_main'
            ,'csv-rowcalc = csv_tools.csv_rowcalc:console_main'
            ,'csv-rownum = csv_tools.csv_rownum:console_main'
            ,'csv-select = csv_tools.csv_select:console_main'
            ,'csv-sort = csv_tools.csv_sort:console_main'
            ,'csv-tail = csv_tools.csv_tail:console_main'
            ,'csv-translate = csv_tools.csv_translate:console_main'
            ]
        }
    ,long_description = '''
    Light-weight python scripts for processing CSV files from commandline.
    '''
    )
