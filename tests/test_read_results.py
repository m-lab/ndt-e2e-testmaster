# Copyright 2016 Measurement Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
import datetime
import os
import unittest

import pytz

from testmaster import read_results
from testmaster.ndt_e2e_clientworker.client_wrapper import results

# The filename of a raw NDT result file.
RAW_RESULT_FILENAME = 'raw-result.json'
# The contents of the raw result file, represented as an NdtResult instance.
RAW_RESULT = results.NdtResult(
    browser='chrome',
    browser_version='50.0.2661.86',
    end_time=datetime.datetime(2016, 5, 24, 16, 55, 58, 756734, pytz.utc),
    client='ndt_js',
    client_version=None,
    os='OSX',
    os_version='10.11.3',
    start_time=datetime.datetime(2016, 5, 24, 16, 55, 22, 677309, pytz.utc),
    c2s_result=results.NdtSingleTestResult(
        start_time=datetime.datetime(2016, 5, 24, 16, 55, 34, 74628, pytz.utc),
        end_time=datetime.datetime(2016, 5, 24, 16, 55, 46, 944071, pytz.utc),
        throughput=0.938),
    s2c_result=results.NdtSingleTestResult(
        start_time=datetime.datetime(2016, 5, 24, 16, 55, 46, 944247, pytz.utc),
        end_time=datetime.datetime(2016, 5, 24, 16, 55, 58, 324334, pytz.utc),
        throughput=1.01),
    latency=564.0)
# The filename of a package of result files.
RESULT_PACKAGE_FILENAME = 'result-package.zip'
# A raw result file within the result package zip.
PACKAGED_RESULT_FILENAME = 'packaged-result.json'
# The contents of the packaged result, represented as an NdtResult instance.
PACKAGED_RESULT = results.NdtResult(
    browser='chrome',
    browser_version='50.0.2661.102',
    end_time=datetime.datetime(2016, 5, 24, 19, 18, 48, 173000, pytz.utc),
    client='banjo',
    client_version=None,
    os='Windows',
    os_version='2012ServerR2',
    start_time=datetime.datetime(2016, 5, 24, 19, 18, 3, 924000, pytz.utc),
    c2s_result=results.NdtSingleTestResult(
        start_time=datetime.datetime(2016, 5, 24, 19, 18, 35, 219000, pytz.utc),
        end_time=datetime.datetime(2016, 5, 24, 19, 18, 46, 765000, pytz.utc),
        throughput=36.1),
    s2c_result=results.NdtSingleTestResult(
        start_time=datetime.datetime(2016, 5, 24, 19, 18, 15, 991000, pytz.utc),
        end_time=datetime.datetime(2016, 5, 24, 19, 18, 25, 715000, pytz.utc),
        throughput=1.75),
    latency=79.2)
# A non-result file that parse_files should ignore.
GARBAGE_FILENAME = 'garbage.txt'


def add_testdata_prefix(filename):
    """Creates an absolute path to a file in the testdata directory."""
    testdata_dir = os.path.join(os.path.dirname(__file__), 'testdata')
    return os.path.join(testdata_dir, filename)


class ReadResultsTest(unittest.TestCase):

    def test_reads_raw_result_file_correctly(self):
        actual_results = read_results.parse_files(
            [add_testdata_prefix(RAW_RESULT_FILENAME)])
        expected_results = {RAW_RESULT_FILENAME: RAW_RESULT}
        self.assertDictEqual(expected_results, actual_results)

    def test_reads_packaged_result_file_correctly(self):
        actual_results = read_results.parse_files(
            [add_testdata_prefix(RESULT_PACKAGE_FILENAME)])
        expected_results = {PACKAGED_RESULT_FILENAME: PACKAGED_RESULT}
        self.assertDictEqual(expected_results, actual_results)

    def test_reads_mix_of_input_types_correctly(self):
        """Parser should process a mix of files and ignore non-result files."""
        actual_results = read_results.parse_files(
            [add_testdata_prefix(RAW_RESULT_FILENAME),
             add_testdata_prefix(RESULT_PACKAGE_FILENAME),
             add_testdata_prefix(GARBAGE_FILENAME)]) # yapf: disable
        expected_results = {
            RAW_RESULT_FILENAME: RAW_RESULT,
            PACKAGED_RESULT_FILENAME: PACKAGED_RESULT,
        }
        self.assertDictEqual(expected_results, actual_results)
