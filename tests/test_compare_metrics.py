#!/usr/bin/env python

import operator
import StringIO
import unittest

from testmaster import compare_metrics

# Sample E2E CSV results
OLD_CSV = '''filename,total_duration,c2s_throughput,c2s_duration,s2c_throughput,s2c_duration,latency,error,error_list
ubuntu14.04-chrome49-banjo-2016-11-29T140016Z-results.json,27.8,94.0,11.4,95.6,10.3,201.0,0,
ubuntu14.04-chrome49-banjo-2016-11-29T140902Z-results.json,27.6,94.1,11.4,95.6,10.3,202.0,0,
win10-firefox45-banjo-2016-11-29T130814Z-results.json,15.0,,,,,,1,"Timed out waiting for page to load.,Failed to load URL: http://localhost:53467/search?q=internet+speed+test"
osx10.11-chrome53-banjo-2016-11-29T150436Z-results.json,30.2,93.0,11.2,79.4,10.2,50.0,0,
osx10.11-chrome53-banjo-2016-11-29T150507Z-results.json,29.7,93.3,11.1,87.4,10.8,55.0,0,'''

# Sample E2E CSV results
NEW_CSV = '''filename,total_duration,c2s_throughput,c2s_duration,s2c_throughput,s2c_duration,latency,error,error_list
osx10.12-chrome57-banjo-2017-04-06T223328Z-results.json,36.0,93.5,11.1,92.8,10.3,73.0,0,
osx10.12-firefox52-ndt_js-2017-04-06T213908Z-results.json,32.0,94.3,11.9,93.8,10.4,85.0,0,
osx10.12-firefox52-ndt_js-2017-04-06T213940Z-results.json,32.0,94.2,11.9,93.8,10.4,85.0,0,
ubuntu16.04-chrome56-banjo-2017-04-06T212522Z-results.json,27.6,94.1,11.0,95.5,10.5,204.0,0,
win10-firefox49-banjo-2017-04-06T200458Z-results.json,33.4,94.9,11.0,96.4,10.2,43.0,0,
win10-firefox49-banjo-2017-04-06T200850Z-results.json,33.3,94.4,11.1,96.2,10.2,43.0,0,'''

# This is sample output from the compare_metrics() function. It is depenent on
# the contents of OLD_CSV and NEW_CSV above. If those change, then this may need
# to change too.
COMP_OUTPUT = [
    {'os': 'osx',
     'browser': 'firefox',
     'client': 'ndt_js',
     'metric': 's2c_throughput',
     'old_avg': 'none',
     'new_avg': 93.8,
     '%change': 'error'},
    {'os': 'win',
     'browser': 'firefox',
     'client': 'banjo',
     'metric': 'latency',
     'old_avg': 0.0,
     'new_avg': 43.0,
     '%change': 'error'},
    {'os': 'ubuntu',
     'browser': 'chrome',
     'client': 'banjo',
     'metric': 'total_duration',
     'old_avg': 27.7,
     'new_avg': 27.6,
     '%change': -0.0},
]


class CompareMetricsTest(unittest.TestCase):

    def setUp(self):
        self.csv_fieldnames = ['os', 'browser', 'client', 'metric', 'old_avg',
                               'new_avg', '%change']

    def test_parse_options_without_output_file_returns_default(self):
        passed_args = ['--old_csv', '/tmp/lol.csv', '--new_csv',
                       '/opt/rofl.csv']
        expected_output_file = 'e2e_comparison_results.csv'

        args = compare_metrics.parse_options(passed_args)

        self.assertEqual(args.output_file, expected_output_file)

    def test_parse_csv(self):
        # The dicts returned by parse_csv() are too large to go about checking
        # them completely, even with only 4 or 5 sample rows in the CSV, so
        # we'll just spot check. The following dict has the expected metric
        # value as the key and the map to the result for that metric as the
        # value (list). These mappings are dervied from the OLD_CSV and NEW_CSV
        # global variables.
        old_result_mappings = {
            '79.4': ['osx-chrome-banjo', 'metrics', 's2c_throughput',
                     '2016-11-29T150436Z'],
            '201.0':
            ['ubuntu-chrome-banjo', 'metrics', 'latency', '2016-11-29T140016Z'],
            '15.0': ['win-firefox-banjo', 'metrics', 'total_duration',
                     '2016-11-29T130814Z']
        }
        new_result_mappings = {
            '10.4': ['osx-firefox-ndt_js', 'metrics', 's2c_duration',
                     '2017-04-06T213908Z'],
            '94.1': ['ubuntu-chrome-banjo', 'metrics', 'c2s_throughput',
                     '2017-04-06T212522Z'],
            '43.0':
            ['win-firefox-banjo', 'metrics', 'latency', '2017-04-06T200458Z']
        }

        # Create parsed CSV objects for both OLD_CSV and NEW_CSV
        old_csv = StringIO.StringIO(OLD_CSV)
        old_results = compare_metrics.parse_csv(old_csv)
        new_csv = StringIO.StringIO(NEW_CSV)
        new_results = compare_metrics.parse_csv(new_csv)

        # Make sure that the parsed results for OLD_CSV and NEW_CSV are what we
        # expected.
        for value, mapping in old_result_mappings.iteritems():
            self.assertEqual(value, reduce(operator.getitem, mapping,
                                           old_results))
        for value, mapping in new_result_mappings.iteritems():
            self.assertEqual(value, reduce(operator.getitem, mapping,
                                           new_results))

    def test_average_metrics(self):
        # The dicts returned by average_metrics() are too large to go about
        # checking them completely, even with only 4 or 5 sample rows in the
        # CSV, so we'll just spot check. The following dict has the expected
        # metric value as the key and the map to the result for that metric as
        # the value (list). These mappings are dervied from the OLD_CSV and
        # NEW_CSV global variables.
        old_result_mappings = {
            '94.05': ['ubuntu-chrome-banjo', 'metrics', 'c2s_throughput'],
            '83.40': ['osx-chrome-banjo', 'metrics', 's2c_throughput']
        }
        new_result_mappings = {
            '94.25': ['osx-firefox-ndt_js', 'metrics', 'c2s_throughput'],
            '33.35': ['win-firefox-banjo', 'metrics', 'total_duration']
        }

        # Aggregate metrics from OLD_CSV
        old_csv = StringIO.StringIO(OLD_CSV)
        old_results = compare_metrics.parse_csv(old_csv)
        old_averages = compare_metrics.average_metrics(old_results)
        # Aggregate metrics from NEW_CSV
        new_csv = StringIO.StringIO(NEW_CSV)
        new_results = compare_metrics.parse_csv(new_csv)
        new_averages = compare_metrics.average_metrics(new_results)

        # Check whether aggregations for OLD_CSV are the expected ones.
        for value, mapping in old_result_mappings.iteritems():
            self.assertEqual(
                float(value), reduce(operator.getitem, mapping, old_averages))
        # Check whether aggregations for NEW_CSV are the expected ones.
        for value, mapping in new_result_mappings.iteritems():
            self.assertEqual(
                float(value), reduce(operator.getitem, mapping, new_averages))

    def test_compare_metrics(self):
        # Like other tests here, there are too many results to reasonably check
        # for every one of them, so we spot check instead. The spot checks we
        # make can be found in the global variable COMP_OUTPUT.

        # Aggregate metrics from OLD_CSV
        old_csv = StringIO.StringIO(OLD_CSV)
        old_results = compare_metrics.parse_csv(old_csv)
        old_averages = compare_metrics.average_metrics(old_results)
        # Aggregate metrics from NEW_CSV
        new_csv = StringIO.StringIO(NEW_CSV)
        new_results = compare_metrics.parse_csv(new_csv)
        new_averages = compare_metrics.average_metrics(new_results)
        # Compare the aggregation results
        comps = compare_metrics.compare_metrics(old_averages, new_averages)

        # comps is a list of dicts. Make sure that each of our expected dicts is
        # in comps.
        for expected_result in COMP_OUTPUT:
            self.assertIn(expected_result, comps)

    def test_write_results(self):
        expected_file_content = '''os,browser,client,metric,old_avg,new_avg,%change\r
osx,firefox,ndt_js,s2c_throughput,none,93.8,error\r
win,firefox,banjo,latency,0.0,43.0,error\r
ubuntu,chrome,banjo,total_duration,27.7,27.6,-0.0\r\n'''

        # Generate output and write it.
        output_csv = StringIO.StringIO()
        compare_metrics.write_results(output_csv, COMP_OUTPUT,
                                      self.csv_fieldnames)

        # Verify that what was written is what we expected.
        self.assertEquals(expected_file_content, output_csv.getvalue())


if __name__ == '__main__':
    unittest.main()
