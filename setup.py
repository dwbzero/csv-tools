##  Copyright (c) 2018-2020 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##


from setuptools import setup


setup(
    name = 'csv-tools',
    version = '0.6.0',
    description = 'CSV commandline tools',
    url = 'http://github.com/Upstream-Research/csv-tools',
    author = 'Upstream Research, Inc.',
    author_email = '',
    license = 'MIT',
    keywords = 'csv pipe filter',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        ],
    packages = [ 
        'csv_tools',
        'csv_tools.base',
        ],
    entry_points = {
        'console_scripts': [
            'csvf = csv_tools.csv_cmd:console_main',
            ]
        },
    long_description = '''
    Python scripts for processing CSV files from commandline.
    ''',
    ),
