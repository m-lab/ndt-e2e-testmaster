#!/usr/bin/env python
"""Compares metrics from two different sets of E2E results."""

import argparse
import collections
import copy
import csv
import logging
import re
import sys


def parse_options(args):
    """Parses the options passed to this script.

    Args:
        args: list of options passed on command line

    Returns:
        An argparse.ArgumentParser object containing the passed options and
        their values.
    """
    parser = argparse.ArgumentParser(
        description='Compares two different sets of E2E results.')
    parser.add_argument('--old_csv',
                        dest='old_csv',
                        required=True,
                        help='Filesystem path to old results CSV file.')
    parser.add_argument('--new_csv',
                        dest='new_csv',
                        required=True,
                        help='Filesystem path to new results CSV file.')
    parser.add_argument('--output_file',
                        dest='output_file',
                        default='e2e_comparison_results.csv',
                        help='Filesystem path where output will be written.')

    args = parser.parse_args(args)
    return args


def parse_filename(filename):
    """Parses the filename field of the CSV file into its constituent parts.

    An example filename input will look like:

        'osx10.12-chrome57-ndt_js-2017-04-06T215733Z-results.json'

    ... and based on this input the output would look like:

        {
            'os': 'osx',
            'os_version': '10.12',
            'browser': 'chrome',
            'browser_version': '57',
            'client': 'ndt_js',
            'timestamp': '2017-04-06T215733Z'
        }

    Args:
        filename: str, filename field from a CSV input file.

    Returns:
        dict: metadata values extracted from the filename.
    """
    # All the information we need about the OS, OS version, browser version and
    # NDT client are embedded in the filename field. The following pattern will
    # be used to help split software from it's version number. For example, it
    # will split 'chrome57' into ['chrome', '57'].
    split_pattern = '^([a-z]+)(\d.*)$'

    metadata = {}

    # The filenames we know about should contain 7 parts separated by dashes.
    filename_parts = filename.split('-')
    if len(filename_parts) != 7:
        logging.error('Unknown filename format: {}'.format(filename_parts[0]))
        sys.exit(1)

    # Determines the OS and version
    os_matches = re.match(split_pattern, filename_parts[0])
    if os_matches:
        metadata['os'] = os_matches.groups()[0]
        metadata['os_version'] = os_matches.groups()[1]
    else:
        logging.error('Could not determine OS and version from: {}'.format(
            filename_parts[0]))
        sys.exit(1)

    # Determines the browser and version
    browser_matches = re.match(split_pattern, filename_parts[1])
    if browser_matches:
        metadata['browser'] = browser_matches.groups()[0]
        metadata['browser_version'] = browser_matches.groups()[1]
    else:
        logging.error('Could not determine browser and version from: {}'.format(
            filename_parts[1]))

    # The NDT client name isn't versioned, so just return it whole.
    metadata['client'] = filename_parts[2]

    # Fields 4-6 are datetime data... rejoin them.
    metadata['timestamp'] = '-'.join(filename_parts[3:6])

    return metadata


def parse_csv(csv_file):
    """Parses an input CSV file.

    Args:
        csv_file: an open file handle to a CSV file.

    Returns:
        A highly nested collections.defaultdict object holding data from an
        input CSV file.
    """
    # Creates a collections.defaultdict object which can have as many nested
    # dicts as we may need.
    factory = lambda: collections.defaultdict(factory)
    e2e_metrics = factory()

    rows = csv.DictReader(csv_file)
    for row in rows:
        # Extracts metadata about the test from the filename.
        m = parse_filename(row['filename'])

        for k, v in row.iteritems():
            # We've already processed 'filename' above and we don't care about
            # 'error_list', so skip them.
            if k in ['filename', 'error_list']:
                continue
            software = '-'.join([m['os'], m['browser'], m['client']])
            e2e_metrics[software]['os_version'] = m['os_version']
            e2e_metrics[software]['browser_version'] = m['browser_version']
            e2e_metrics[software]['metrics'][k][m['timestamp']] = v

    return e2e_metrics


def average_metrics(results):
    """Calculates the average for all metrics in input.

    Args:
        results: collections.defaultdict, metrics compiled from an input CSV.

    Returns:
        A nested collections.defaultdict object with individual metrics replaced
        with aggregated values (mean).
    """
    avgs = copy.deepcopy(results)
    for software in results:
        for metric in results[software]['metrics']:
            count = len(results[software]['metrics'][metric])
            metric_sum = 0
            for ts, data in results[software]['metrics'][metric].iteritems():
                if data:
                    metric_sum += float(data)
            mean = metric_sum / count
            avgs[software]['metrics'][metric] = round(mean, 2)
    return avgs


def compare_metrics(old_avgs, new_avgs):
    """Compares aggregated metrics from two different E2E result sets.

    Args:
        old_avgs: collections.defaultdict, metric averages from an old E2E run.
        new_avgs: collections.defaultdict, metric averages from an new E2E run.

    Returns:
        list: a list of dicts containing comparison data.
    """
    rows = []

    print '# E2E comparison results'

    for software in sorted(new_avgs):
        for metric in new_avgs[software]['metrics']:
            new_avg = new_avgs[software]['metrics'][metric]
            # If this software/metric doesn't exist in the old results, then the
            # return type of the following statement will be
            # collections.defaultdict. This is because of the nature of our
            # defaultdict, which will automatically create keys as defaultdicts
            # if they don't already exist. If it's a string, we know it's a
            # value we can use, but if it's a defaultdict, then we can assume
            # that no such software/metric exists in the old CSV.
            old_avg = old_avgs[software]['metrics'][metric]
            if type(old_avg) is collections.defaultdict:
                old_avg = 'none'

            # Don't do any division by or to zero, or a string.
            if new_avg != 0 and old_avg != 0 and old_avg != 'none':
                delta = round((new_avg - old_avg) / new_avg, 2) * 100
            else:
                delta = 'error'

            (opersys, browser, client) = software.split('-')
            row = {
                'os': opersys,
                'browser': browser,
                'client': client,
                'metric': metric,
                'old_avg': old_avg,
                'new_avg': new_avg,
                '%change': delta
            }
            rows.append(row)

            print '{os:10},{browser:10},{client:10},{metric:15},' \
                  '{old_avg:>7},{new_avg:>7},{%change:>7}'.format(**row)

    return rows


def write_results(output_file, rows, fieldnames):
    """Writes comparison results to a file in CSV format.

    Args:
        output_file: an open file handle for writing the output.
        rows: list, a list of dicts to write to the output CSV file.
        fieldnames: list, the column names for the CSV (first row).
    """
    writer = csv.DictWriter(output_file, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)


def print_software_summary(label, results):
    """Prints software and versions used in each E2E results set.

    Args:
        label: str, a label to identify the output.
        results: collections.defaultdict, metric averages from an E2E run.
    """
    print label
    for software in sorted(results):
        (opersys, browser, client) = software.split('-')
        print '    {}: {}, {}: {}, client: {}'.format(
            opersys, results[software]['os_version'], browser,
            results[software]['browser_version'], client)
    # Insert a newline after each software summary
    print ''


def main():
    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=logging.DEBUG)

    args = parse_options(sys.argv[1:])

    try:
        with open(args.old_csv, 'r') as old_csv:
            old_results = parse_csv(old_csv)
        with open(args.new_csv, 'r') as new_csv:
            new_results = parse_csv(new_csv)
    except IOError as e:
        logging.error('IOError: {}'.format(e))
        sys.exit(1)

    # Calculate averages for each metric in each result set
    old_avgs = average_metrics(old_results)
    new_avgs = average_metrics(new_results)

    # Print software and version for each set of results. This is just
    # informational to the user.
    print_software_summary('# Software used in old CSV (--old_csv)', old_avgs)
    print_software_summary('# Software used in new CSV (--new_csv)', old_avgs)

    results = compare_metrics(old_avgs, new_avgs)

    # 'results' is a list of dicts, with each dict representing data for one
    # row. Here we apply some useful column names for the first row of the CSV
    # file that will be written.
    csv_fieldnames = ['os', 'browser', 'client', 'metric', 'old_avg', 'new_avg',
                      '%change']
    try:
        with open(args.output_file, 'w') as output:
            write_results(output, results, csv_fieldnames)
    except IOError as e:
        logging.error('IOError: {}'.format(e))
        sys.exit(1)


if __name__ == '__main__':
    main()
