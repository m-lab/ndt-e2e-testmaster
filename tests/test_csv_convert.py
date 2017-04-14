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
import unittest

import pytz

from testmaster import csv_convert
from testmaster.ndt_e2e_clientworker.client_wrapper import results

# An NDT result in which no errors occur and both s2c and c2s complete
# successfully.
NO_ERRORS_RESULT = results.NdtResult(
    end_time=datetime.datetime(2016, 5, 24, 16, 55, 58, 756734, pytz.utc),
    start_time=datetime.datetime(2016, 5, 24, 16, 55, 22, 677309, pytz.utc),
    c2s_result=results.NdtSingleTestResult(
        start_time=datetime.datetime(2016, 5, 24, 16, 55, 34, 74628, pytz.utc),
        end_time=datetime.datetime(2016, 5, 24, 16, 55, 46, 944071, pytz.utc),
        throughput=0.938),
    s2c_result=results.NdtSingleTestResult(
        start_time=datetime.datetime(2016, 5, 24, 16, 55, 46, 944247, pytz.utc),
        end_time=datetime.datetime(2016, 5, 24, 16, 55, 58, 324334, pytz.utc),
        throughput=1.01),
    latency=15.0)
# An NDT result in which s2c and c2s tests fail to complete and generate errors.
MISSING_FIELDS_RESULT = results.NdtResult(
    end_time=datetime.datetime(2016, 5, 24, 19, 18, 48, 173000, pytz.utc),
    start_time=datetime.datetime(2016, 5, 24, 19, 18, 3, 924000, pytz.utc),
    c2s_result=results.NdtSingleTestResult(start_time=datetime.datetime(
        2016, 5, 24, 19, 18, 35, 219000, pytz.utc)),
    s2c_result=results.NdtSingleTestResult(start_time=datetime.datetime(
        2016, 5, 24, 19, 18, 15, 991000, pytz.utc)),
    errors=[results.TestError('dummy s2c error'),
            results.TestError('dummy c2s error')])


def normalizeNewlines(content):
    return content.replace('\r\n', '\n').replace('\r', '\n')


class ReadResultsTest(unittest.TestCase):

    def assertCSVsEqual(self, expected, actual):
        """Checks equality of two CSV strings, normalizing newlines."""
        self.assertMultiLineEqual(
            normalizeNewlines(expected), normalizeNewlines(actual))

    def test_empty_dictionary_produces_csv_with_just_header_line(self):
        actual_csv = csv_convert.ndt_results_to_csv({})
        expected_csv = 'filename,total_duration,c2s_throughput,c2s_duration,s2c_throughput,s2c_duration,latency,error,error_list\n'
        self.assertCSVsEqual(expected_csv, actual_csv)

    def test_populated_results_produce_correct_csv(self):
        actual_csv = csv_convert.ndt_results_to_csv({
            'no-errors.json': NO_ERRORS_RESULT,
            'missing-fields.json': MISSING_FIELDS_RESULT,
        })
        expected_csv = """filename,total_duration,c2s_throughput,c2s_duration,s2c_throughput,s2c_duration,latency,error,error_list
missing-fields.json,44.2,,,,,,1,"dummy s2c error,dummy c2s error"
no-errors.json,36.1,0.9,12.9,1.0,11.4,15.0,0,
"""
        self.assertCSVsEqual(expected_csv, actual_csv)
