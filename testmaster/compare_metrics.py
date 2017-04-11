#!/usr/bin/env python
"""Compares two different sets of E2E results."""

import argparse
import collections
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

    args = parser.parse_args(args)
    return args


def parse_filename(filename):
    # All the information we need about the OS, OS version, browser version and
    # NDT client are embedded in the filename field. This regex will be used to
    # help split software from it's version number.
    regex = re.compile('^([a-z]+)(\d.*)$')

    metadata = {}

    # The filenames we know about should contain 7 parts separated by dashes.
    filename_parts = filename.split('-')
    if len(filename_parts) != 7:
        logging.error('Unknown filename format: {}'.format(row['filename']))
        sys.exit(1)

    # Determines the OS and version
    os_matches = regex.match(filename_parts[0])
    if os_matches:
        metadata['os'] = os_matches.groups()[0]
        metadata['os_version'] = os_matches.groups()[1]
    else:
        logging.error('Could not determine OS and version from: {}'.format(
            filename_parts[0]))
        sys.exit(1)

    # Determines the browser and version
    browser_matches = regex.match(filename_parts[1])
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
    # Creates a collections.defaultdict object which can have as many nested
    # dicts as we may need.
    factory = lambda: collections.defaultdict(factory)
    e2e_metrics = factory()

    # This is the order of the fields in E2E CSV files. We could use the names
    # in the first row of the CSV file, but those have spaces and aren't short
    # or code friendly.
    fields = ['filename', 'total_duration', 'c2s_speed', 'c2s_duration',
              's2c_speed', 's2c_duration', 'latency', 'has_error', 'error_list']

    rows = csv.DictReader(csv_file, fields)
    for row in rows:
        # The first row of the CSV file has field names, which we don't care
        # about since we've created our own mapping in the 'fields' list.
        if row['filename'] == 'Filename':
            continue

        # Extracts metadata about the test from the filename.
        m = parse_filename(row['filename'])

        for field in fields:
            # We've already processed the field 'filename' and we don't care
            # about the field 'error_list'.
            if field in ['filename', 'error_list']:
                continue
            e2e_metrics[m['os']]['version'] = m['os_version']
            e2e_metrics[m['os']]['browsers'][m['browser']]['version'] = m[
                'browser_version']
            e2e_metrics[m['os']]['browsers'][m['browser']]['clients'][m[
                'client']][field][m['timestamp']] = row[field]

    return e2e_metrics


def average_metrics(results):
    avgs = results
    for opersys in results:
        for browser in results[opersys]['browsers']:
            for client in results[opersys]['browsers'][browser]['clients']:
                for metric in results[opersys]['browsers'][browser]['clients'][
                        client]:
                    count = len(results[opersys]['browsers'][browser][
                        'clients'][client][metric])
                    metric_sum = 0
                    for ts, data in results[opersys]['browsers'][browser][
                            'clients'][client][metric].iteritems():
                        if data:
                            metric_sum += float(data)
                    mean = metric_sum / count
                    avgs[opersys]['browsers'][browser]['clients'][client][
                        metric] = round(mean, 2)
    return avgs


def compare_metrics(old_avgs, new_avgs):
    print 'os,browser,client,metric,old,new,%change'
    for opersys in new_avgs:
        for browser in new_avgs[opersys]['browsers']:
            for client in new_avgs[opersys]['browsers'][browser]['clients']:
                for metric in new_avgs[opersys]['browsers'][browser]['clients'][
                        client]:
                    new_avg = new_avgs[opersys]['browsers'][browser]['clients'][client][metric]

                    # If this OS/browser/client/metric doesn't exist in the old
                    # results, then note that.
                    try:
                        old_avg = old_avgs[opersys]['browsers'][browser]['clients'][client][metric]
                    except KeyError as e:
                        old_avg = 'none'

                    # Don't do any division by or to zero, or a string.
                    if new_avg != 0 and old_avg != 0 and old_avg != 'none':
                        delta = round((new_avg - old_avg) / new_avg, 2) * 100
                    else:
                        delta = 'error'

                    print '{:10},{:10},{:10},{:15},{:7},{:7},{:>7}'.format(opersys, browser,
                            client, metric, old_avg, new_avg, delta)


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

    old_avgs = average_metrics(old_results)
    new_avgs = average_metrics(new_results)

    compare_metrics(old_avgs, new_avgs)


if __name__ == '__main__':
    main()
