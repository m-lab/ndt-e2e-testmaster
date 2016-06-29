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

import csv
import io
import operator

import result_metrics


def ndt_results_to_csv(results):
    """Converts a dictionary of NdtResult objects to a CSV summary.

    Given a dictionary of NdtResult objects, creates a CSV-formatted string with
    the information in the result list combined into a single document.

    Args:
        results: A dictionary of NdtResult objects, keyed by the filename of the
            original result file from which they were parsed.

    Returns:
        A CSV string describing the NDT results.
    """
    output = io.BytesIO()
    csv_writer = csv.DictWriter(output,
                                fieldnames=['filename', 'total_duration',
                                            'c2s_throughput', 'c2s_duration',
                                            's2c_throughput', 's2c_duration',
                                            'latency', 'error', 'error_list'])
    # Write a header row with friendly names for each column
    csv_writer.writerow({
        'filename': 'Filename',
        'total_duration': 'Total Duration (s)',
        'c2s_throughput': 'Upload Throughput (Mbps)',
        'c2s_duration': 'Upload Duration (s)',
        's2c_throughput': 'Download Througput (Mbps)',
        's2c_duration': 'Download Duration (s)',
        'latency': 'Latency (ms)',
        'error': 'Error occurred?',
        'error_list': 'Error List',
    })
    # Sort results so that rows are in ascending order of filename.
    sorted_results = sorted(results.items(), key=operator.itemgetter(0))
    for filename, result in sorted_results:
        csv_writer.writerow({
            'filename': filename,
            'total_duration':
            _format_float(result_metrics.total_duration(result)),
            'c2s_throughput': _format_float(result.c2s_result.throughput),
            'c2s_duration': _format_float(result_metrics.c2s_duration(result)),
            's2c_throughput': _format_float(result.s2c_result.throughput),
            's2c_duration': _format_float(result_metrics.s2c_duration(result)),
            'latency': _format_float(result.latency),
            'error': 1 if len(result.errors) > 0 else 0,
            'error_list': _join_errors(result.errors),
        })
    return output.getvalue()


def _format_float(value):
    if value is None:
        return ''
    return '%.1f' % value


def _join_errors(errors):
    return ','.join([x.message for x in errors]) if errors else ''
