#!/usr/bin/env python3
# encoding: utf-8

# Author: Alex Flückiger <alex.flueckiger@gmail.com>


"""
A information extraction script that takes a downloaded plain text file from LexisNexis
and converts it into a proper CSV file. Wildcards such as *.txt may be used
as script argument to process multiple files at once.

This script was originally inspired by Neal Caren:
http://nealcaren.web.unc.edu/cleaning-up-lexisnexis-files/

Example use case:
python split_ln.py t*.txt

Processing the following file:
 test.txt

Meta tags that are actually considered for this file:
 ID_DOC
 PUBLICATION
 DATE
 TITLE
 URL
 PHOTO
 LENGTH

Wrote the following file with 187 items:
 test.csv

"""

import re
import csv
import sys
from dateutil.parser import parse

months = {'Januar': 1, 'Februar': 2, 'März': 3, 'Maerz': 3, 'April': 4, 'Mai': 5, 'Juni': 6,
          'Juli': 7, 'August': 8, 'September': 9, 'Oktober': 10, 'November': 11, 'Dezember': 12,
          'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
          'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12}


def new_parse_date(date_string):
    """
    This function parses date strings with the dateutil.parser

    Args:
        date_string (str): a text containing a German or English date
                           (e.g. 01. Januar 2000 or January 1, 2000)

    Returns:
        date (str): a standardized date as year-month-day or None
                    (e.g. 2000-01-01)

    """

    try:
        # try parsing with English  locale
        locale.setlocale(locale.LC_TIME, ("en", "us"))
        date = parse(date_string)
        return date.strftime('%Y-%m-%d')
    except ValueError:
        locale.setlocale(locale.LC_TIME, ("de", "de"))
        date = parse(date_string)
        return date.strftime('%Y-%m-%d')
    else:
        print('Date could not be parsed:', date_string)
        return None


def old_parse_date(date_string):
    """
    This function parses date strings with regular expressions .

    Args:
        date_string (str): a text containing a German or English date
                           (e.g. 01. Januar 2000 or January 1, 2000)

    Returns:
        date (str): a standardized date as year-month-day or None
                    (e.g. 2000-01-01)
    """

    for month in months:
        # try parsing German date
        ger_pattern = f'(\d+)\. ({ month }) (\d+)'
        ger_matches = re.search(ger_pattern, date_string, re.I)
        if ger_matches:
            day = int(ger_matches.group(1))
            month_name = ger_matches.group(2)
            year = ger_matches.group(3)
            date = f'{year}-{months[month]:02d}-{day:02d}'
            break
        # try parsing English date
        eng_pattern = f'({month}) (\d+), (\d+)'
        eng_matches = re.search(eng_pattern, date_string, re.I)
        if eng_matches:
            month_name = eng_matches.group(1)
            day = int(eng_matches.group(2))
            year = eng_matches.group(3)
            date = f'{year}-{months[month]:02d}-{day:02d}'
            break
    else:
        print('Date could not be parsed:', date_string)
        date = date_string

    return date


def split_ln(fname, outname=None):
    """

    """
    print('=' * 80)
    print('Processing the following file:\n', fname)

    # read the file
    with open(fname, encoding='UTF-8', ) as f:
        fcontent = f.read()

    # A silly hack to find the end of the documents.
    # The copyright information is normally stated in the middle of a new line.
    fcontent = (re.sub('\n\s{5,}Copyright .*?\n+', 'END_OF_DOC', fcontent))

    # Split the file into a list of documents and remove empty document after
    # last split.
    documents = fcontent.split('END_OF_DOC')[:-1]

    # Figure out potential meta tags that might be reported
    # Meta tags are capitalized, stated at the beginning of a line
    # and should consist of at leat 3 letters
    meta_tags = set(re.findall('\n([A-Z-]{3,}?): ', fcontent))

    # Keep only the meta tags that are given for at least 20% of documents
    meta_tags = {tag for tag in meta_tags if (
        fcontent.count(tag + ':') / len(documents)) > .20}

    # It is conceivable that the used pattern matches false positives such as the newspaper WELT or abbreviations.
    # Manually define these false positives here if this happens for your corpus.
    # As alternative, you can increase the threshold to more than 20% above.
    meta_false = ['WELT']
    meta_tags = {tag for tag in meta_tags if tag not in meta_false}

    # Meta tags that are extracted in any case
    attributes = ['ID_DOC', 'PUBLICATION', 'DATE', 'TITLE']

    # Unionization of the standard attributes and the extracted meta tags
    [attributes.append(tag) for tag in meta_tags if tag not in attributes]
    # Text should be the last column in the final csv-file
    attributes.append('TEXT')

    print('\nMeta tags that are actually considered for this file:')
    [print('', tag) for tag in attributes]

    # Create name of csv-file by replacing the extension .txt with .csv
    if not outname:
        outname = fname.replace(fname.split('.')[-1], 'csv')
    with open(outname, 'w') as csv_f:
        writer = csv.DictWriter(csv_f, fieldnames=attributes)
        writer.writeheader()
        for doc in documents:
            doc_information = information_extraction_per_doc(doc, attributes)
            writer.writerow(doc_information)
    print(
        f'\nWrote the following file with {len(documents)} items:\n', outname)
    print('=' * 80)


def information_extraction_per_doc(doc, attributes):
    """
    """

    meta_dict = {tag: str() for tag in attributes}

    # Split into lines or rather paragraphs
    lines = [paragraph for paragraph in doc.split('\n\n')]
    # Clean up the hard returns at the end of each line
    lines = [line.replace('\n', ' ') for line in lines if len(lines) > 0]

    # Remove copyright lines
    lines = [line for line in lines if line.lstrip().rstrip() is not (
        'Alle Rechte Vorbehalten' or 'All Rights Reserved')]

    # Parse various meta information at the beginning of the document before text
    # Parse document number according to two possible schemes
    for i, line in enumerate(lines):
        current_line = i
        match1 = re.search('do[k|c]ument (\d+)', line, re.I)
        match2 = re.search('(\d+) (?:of|von) (?:\d+) do[k|c]ument', line, re.I)
        if match1:
            meta_dict['ID_DOC'] = match1.group(1)
            break
        elif match2:
            meta_dict['ID_DOC'] = match2.group(1)
            break

    # Parse publication
    for line in lines[current_line + 1:]:
        current_line += 1
        if line:
            meta_dict['PUBLICATION'] = line.lstrip()
            break

    # Parse date
    for line in lines[current_line + 1:]:
        current_line += 1
        if line:
            date_raw = line.lstrip()
            meta_dict['DATE'] = old_parse_date(date_raw)
            break
            # Korrektes einlesen verschiedener Datumsvariationen

    # Parse title
    for line in lines[current_line + 1:]:
        current_line += 1
        if line:
            meta_dict['TITLE'] = line.lstrip()
            break

    # Extract further meta tags and text
    for line in lines[current_line + 1:]:
        # still look for tags, which are either in the header or footer section
        match = re.match('([A-Z-]+?): ', line)
        if match:
            tag = match.group(1)
            if tag in attributes:
                # save information according to defined meta tags
                meta_dict[tag] = line.replace(match.group(0), '')
                continue
        # apparently it seems to be normal text
        meta_dict['TEXT'] = meta_dict['TEXT'] + ' ' + line

    # Check mandatory attributes and length of text to ensure correct
    # extraction
    if (meta_dict['ID_DOC'] or meta_dict['TITLE'] or meta_dict['DATE']) is None \
            or len(meta_dict['TEXT']) < 100:
        print('Please check the following document whose extracted information shows an anomaly:')
        print(meta_dict['ID_DOC'], meta_dict['TITLE'], meta_dict['DATE'])

    return meta_dict


if __name__ == '__main__':
    # All given filenames are saved into a list
    flist = sys.argv[1:]

    for fname in flist:
        split_ln(fname)
