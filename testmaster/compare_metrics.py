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

    software = {}

    # If there aren't three split from the filename, then there is something
    # wrong.
    filename_parts = filename.split('-')[:3]
    if len(filename_parts) != 3:
        logging.error('Unknown filename format: {}'.format(row['filename']))
        sys.exit(1)

    # Determines the OS and version
    os_matches = regex.match(filename_parts[0])
    if os_matches:
        software['os'] = os_matches.groups()[0]
        software['os_version'] = os_matches.groups()[1]
    else:
        logging.error('Could not determine OS and version from: {}'.format(
            filename_parts[0]))
        sys.exit(1)

    # Determines the browser and version
    browser_matches = regex.match(filename_parts[1])
    if browser_matches:
        software['browser'] = browser_matches.groups()[0]
        software['browser_version'] = browser_matches.groups()[1]
    else:
        logging.error('Could not determine browser and version from: {}'.format(
            filename_parts[1]))

    # The NDT client name isn't versioned, so just return it whole.
    software['client'] = filename_parts[2]

    return software


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
        
        # Extracts software names and versions from 'filename' field.
        s = parse_filename(row['filename'])
        
        # Skip first item in list ('filename'), since we hande that elsewhere.
        for field in fields[1:]:
            # If this field/metric doesn't already exist for this
            # OS/browser/client combination, then create it as a list.
            if not e2e_metrics[s['os']][s['browser']][s['client']][field]:
                e2e_metrics[s['os']][s['browser']][s['client']][field] = []

            # Appends the value of this metric to the list.
            e2e_metrics[s['os']][s['browser']][s['client']][field].append(row[field])

    return e2e_metrics


def aggregate_metrics(results):
    return 'Do something eventually.'


def main():
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    args = parse_options(sys.argv[1:])

    try:
        with open(args.old_csv, 'r') as old_csv:
            old_results = parse_csv(old_csv)
        with open(args.new_csv, 'r') as new_csv:
            new_results = parse_csv(new_csv)
    except IOError as e:
        logging.error('IOError: {}'.format(e))
        sys.exit(1)

    old_aggs = aggregate_metrics(old_results)
    new_aggs = aggregate_metrics(new_results)
    

if __name__ == '__main__':
    main()
