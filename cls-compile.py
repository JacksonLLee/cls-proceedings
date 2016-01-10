#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# A tool for compiling the proceedings of the Chicago Linguistic Society.
# Download, documentation etc: <https://github.com/JacksonLLee/cls-proceedings>
# Author: Jackson Lee <jsllee.phon@gmail.com>
# Last updated on 2016-01-10

import sys
import shutil
import argparse
import os
import csv
import subprocess

# check python version
current_version = sys.version_info[:2]
if current_version < (3, 3):
    sys.exit('Error: Python 3.3 or above is needed for shutil.which().\n'
             'You are using Python {}.{}.'.format(*current_version))

# check if PyPDF2 is installed
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
    sys.exit('Error: The Python package PyPDF2 is not available.')

from PyPDF2 import (PdfFileWriter, PdfFileReader)

# check if the command "pdflatex" is available
if not shutil.which('pdflatex'):
    sys.exit('Error: The command "pdflatex" is not available.')

# set up this script's information
__author__ = 'Jackson Lee'
__author_email__ = 'jsllee.phon@gmail.com'
__url__ = 'https://github.com/JacksonLLee/cls-proceedings'

__longdescr__ = '''\
Compiling the proceedings of the Chicago Linguistic Society\n
Download, documentation etc: <{}>\n
Author: {} <{}>'''.format(__url__, __author__, __author_email__)

print('*************************************************\n{}\n'
      '*************************************************'.format(__longdescr__))

# ---------------------------------------------------------------------------- #
# some handy functions

def read_csv(fname, delim=',;\t| '):
    """
    Read a CSV file (n rows, m columns) with filename *fname*,
        and return a list containing n lists each containing m strings.
    """
    with open(fname, 'rU') as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(), delimiters=delim)
        csvfile.seek(0)
        data = csv.reader(csvfile, dialect)
        return list(data)

def ensure_empty_dir(abs_dir_path):
    """
    Ensure that *abs_dir_path* is an empty folder.
    """
    if os.path.isdir(abs_dir_path):
        # delete everything inside the folder
        existing_filenames = os.listdir(abs_dir_path)
        for filename in existing_filenames:
            filename_abs_path = os.path.join(abs_dir_path, filename)
            os.remove(filename_abs_path)
    else:
        # create the empty folder
        os.makedirs(headers_abs_dir)

# ---------------------------------------------------------------------------- #
# parse command line arguments

parser = argparse.ArgumentParser(description=__longdescr__,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--directory', type=str, default='example',
                    help='working directory, where all necessary files and'
                         ' subdirectories are')
parser.add_argument('--frontmatter', type=str, default='front-matter',
                    help='directory name for front matter')
parser.add_argument('--acknowledgments', type=str, default='acknowledgments',
                    help='directory name for acknowledgments')
parser.add_argument('--papers', type=str, default='papers-without-headers',
                    help='directory name for papers without headers')
parser.add_argument('--templates', type=str, default='templates',
                    help='directory name for templates (for headers etc)')
parser.add_argument('--toc', type=str, default='table-of-contents',
                    help='directory name for table of contents')
parser.add_argument('--headers', type=str, default='headers',
                    help='directory name for headers of papers')
parser.add_argument('--papersfinal', type=str, default='papers-with-headers',
                    help='directory name for papers with headers')
parser.add_argument('--organizer', type=str, default='organizer.csv',
                    help='filename of the organizer CSV file')
parser.add_argument('--maxheaderlength', type=int, default=55,
                    help='maximum number of characters in a header')
parser.add_argument('--proceedingsname', type=str, default='proceedings.pdf',
                    help='filename of the final proceedings pdf output')
command_line_args = parser.parse_args()

front_matter_dir = command_line_args.frontmatter
acknowledgments_dir = command_line_args.acknowledgments
papers_dir = command_line_args.papers
templates_dir = command_line_args.templates
toc_dir = command_line_args.toc
headers_dir = command_line_args.headers
papersfinal_dir = command_line_args.papersfinal
organizer_name = command_line_args.organizer
max_header_length = command_line_args.maxheaderlength
proceedings_pdf_filename = command_line_args.proceedingsname

working_dir = os.path.abspath(command_line_args.directory)

if not os.path.isdir(working_dir):
    sys.exit('Error: The directory {} does not exist.'.format(
        working_dir))

print('\nYour working directory:\n{}'.format(working_dir))

# ---------------------------------------------------------------------------- #
print('\nReading the organizer CSV file...')

organizer_path = os.path.join(working_dir, organizer_name)

if not os.path.isfile(organizer_path):
    sys.exit('The organizer "{}" is not found.'.format(organizer_path))

organizer = read_csv(organizer_path)
number_of_papers = len(organizer) - 1

organizer_headers = [x.lower().strip() for x in organizer[0]]
expected_organizer_headers = ['index', 'authors', 'paper title',
                              'authors in header', 'paper title in header',
                              'paper filename']

header_to_index = dict()
for expected_header in expected_organizer_headers:
    try:
        header_to_index[expected_header] = \
            organizer_headers.index(expected_header)
    except ValueError:
        sys.exit('Error: The header "{}" is not found in the organizer CSV'
                 ' file.'.format(expected_header))

authors_list = [row[header_to_index['authors']] for row in organizer[1:]]
paper_title_list = [row[header_to_index['paper title']]
                    for row in organizer[1:]]
authors_as_header_list = [row[header_to_index['authors in header']]
                          for row in organizer[1:]]
paper_title_as_header_list = [row[header_to_index['paper title in header']]
                              for row in organizer[1:]]
paper_filename_list = [row[header_to_index['paper filename']]
                       for row in organizer[1:]]

# ---------------------------------------------------------------------------- #
print('Checking if any author or paper tile headers are too long...')

error_template = 'Error: The header "{}" for paper {} is longer than {} ' + \
                 'characters.'
for i in range(number_of_papers):
    authors_in_header = authors_as_header_list[i]
    paper_title_in_header = paper_title_as_header_list[i]

    # if no header specified, use the full author/title name
    if not authors_in_header:
        authors_in_header = authors_list[i]
        authors_as_header_list[i] = authors_in_header
    if not paper_title_in_header:
        paper_title_in_header = paper_title_list[i]
        paper_title_as_header_list[i] = paper_title_in_header

    # max_header_length can be set at command line arguments
    if len(authors_in_header) > max_header_length:
        sys.exit(error_template.format(authors_in_header, i + 1,
                                       max_header_length))

    if len(paper_title_in_header) > max_header_length:
        sys.exit(error_template.format(paper_title_in_header, i + 1,
                                       max_header_length))

# ---------------------------------------------------------------------------- #
print('Checking if front matter file(s) are present...')

front_matter_abs_dir = os.path.join(working_dir, front_matter_dir)
if not os.path.isdir(front_matter_abs_dir):
    sys.exit('Error: The front matter directory {} does not exist.'
             .format(front_matter_abs_dir))
front_matter_filenames = sorted([x for x in os.listdir(front_matter_abs_dir)
                                 if x.lower().endswith('.pdf')])

# ---------------------------------------------------------------------------- #
print('Checking if acknowledgments file(s) are present...')

acknowledgments_abs_dir = os.path.join(working_dir, acknowledgments_dir)
if not os.path.isdir(acknowledgments_abs_dir):
    sys.exit('Error: The acknowledgments directory {} does not exist.'
             .format(acknowledgments_abs_dir))
acknowledgments_filenames = sorted([x for x in
                                    os.listdir(acknowledgments_abs_dir)
                                    if x.lower().endswith('.pdf')])

# ---------------------------------------------------------------------------- #
print('Checking if templates file(s) are present...')

templates_abs_dir = os.path.join(working_dir, templates_dir)
if not os.path.isdir(templates_abs_dir):
    sys.exit('Error: The templates directory {} does not exist.'
             .format(templates_abs_dir))
headers_template_path = os.path.join(templates_abs_dir, 'headers.tex')
blank_page_path = os.path.join(templates_abs_dir, 'blank.pdf')
toc_template_path = os.path.join(templates_abs_dir, 'table-of-contents.tex')

# ---------------------------------------------------------------------------- #
print('Checking if all pdf papers are present, '
      'and getting number of pages for each paper...')

number_of_pages_list = list()  # list of int
page_range_list = list()  # list of (int, int)
cumulative_start_page = 1
start_page = 1

for paper_filename in paper_filename_list:
    paper_path = os.path.join(working_dir, papers_dir, paper_filename)
    if not os.path.isfile(paper_path):
        sys.exit('Error: The file "{}" is not found in {}.\nCheck if actual '
                 'filenames match those in the CSV organizer.'.format(
            paper_filename, os.path.join(working_dir, papers_dir)))
    pdf_object = PdfFileReader(open(paper_path, 'rb'))
    number_of_pages = pdf_object.getNumPages()
    end_page = start_page + number_of_pages - 1

    number_of_pages_list.append(number_of_pages)
    page_range_list.append((start_page, end_page))

    cumulative_start_page += number_of_pages

    if cumulative_start_page % 2:  # if odd num
        pass
    else:
        cumulative_start_page += 1

    start_page = cumulative_start_page

# ---------------------------------------------------------------------------- #
print('Creating headers\' latex files and generating the headers\' pdfs...')

headers_abs_dir = os.path.join(working_dir, headers_dir)
ensure_empty_dir(headers_abs_dir)
header_template_str = open(headers_template_path).read()

for i in range(number_of_papers):
    # noinspection PyRedeclaration
    latex_str = header_template_str
    authors_as_header = authors_as_header_list[i].upper()  # all uppercase
    paper_title_as_header = paper_title_as_header_list[i].upper()  # uppercase
    number_of_pages = number_of_pages_list[i]
    start_page, end_page = page_range_list[i]

    page_range_str = '{}-{}'.format(start_page, end_page)
    insert_pages_str = '\\newpage\n\n\\mbox{}\n' * (number_of_pages - 1)
    headers_latex_filename = 'headers{}.tex'.format(i)

    latex_str = latex_str.replace('XXStartPageXX', str(start_page))
    latex_str = latex_str.replace('XXAuthorsXX', authors_as_header)
    latex_str = latex_str.replace('XXTitleXX', paper_title_as_header)
    latex_str = latex_str.replace('XXPageRangeXX', page_range_str)
    latex_str = latex_str.replace('XXInsertPagesXX', insert_pages_str)

    output_latex_path = os.path.join(headers_abs_dir, headers_latex_filename)
    with open(output_latex_path, 'w') as f:
        f.write(latex_str)

    subprocess.call(('pdflatex', '-output-directory', headers_abs_dir,
                     output_latex_path))

# ---------------------------------------------------------------------------- #
print('Creating paper pdfs with headers...')

papersfinal_abs_dir = os.path.join(working_dir, papersfinal_dir)
ensure_empty_dir(papersfinal_abs_dir)

for i, paper_filename in enumerate(paper_filename_list):
    paper_filename_abs_path = os.path.join(working_dir, papers_dir,
                                           paper_filename)
    headers_abs_path = os.path.join(headers_abs_dir, 'headers{}.pdf'.format(i))

    output_pdf = PdfFileWriter()
    paper_pdf = PdfFileReader(open(paper_filename_abs_path, 'rb'))
    headers_pdf = PdfFileReader(open(headers_abs_path, 'rb'))
    number_of_pages = number_of_pages_list[i]

    # align the paper pdf and the headers pdf and merge (="superimpose") them
    for j in range(number_of_pages):
        page = paper_pdf.getPage(j)
        page.mergePage(headers_pdf.getPage(j))
        output_pdf.addPage(page)

    output_pdf_abs_path = os.path.join(papersfinal_abs_dir, paper_filename)
    output_pdf.write(open(output_pdf_abs_path, 'wb'))

# ---------------------------------------------------------------------------- #
print('Creating the table of contents...')

toc_abs_dir = os.path.join(working_dir, toc_dir)
ensure_empty_dir(toc_abs_dir)

toc_template = open(toc_template_path).read()
toc_entry_template = '\\TocEntry{{{}}}{{{}}}{{{}}}\n\n'

toc_entries_str = ''

for i in range(number_of_papers):
    authors = authors_list[i]
    paper_title = paper_title_list[i]
    start_page = page_range_list[i][0]

    toc_entries_str += toc_entry_template.format(authors, paper_title,
                                                 start_page)

toc_template = toc_template.replace('XXInsertTocEntriesXX', toc_entries_str)

output_toc_tex_path = os.path.join(toc_abs_dir, 'table-of-contents.tex')
with open(output_toc_tex_path, 'w') as f:
    f.write(toc_template)

subprocess.call(('pdflatex', '-output-directory', toc_abs_dir,
                 output_toc_tex_path))

# ---------------------------------------------------------------------------- #
print('\n==================================================================\n'
      'Working directory:\n{}\n\n'
      'Creating the final proceedings pdf output...\n\n'
      'Input pdf files from the working directory are concatenated in the '
      'following order.\n'
      '(Blank pages are automatically added if necessary.)\n'
      .format(working_dir))

proceedings_pdf = PdfFileWriter()
proceedings_pdf_abs_path = os.path.join(working_dir, proceedings_pdf_filename)

cumulative_page_count = 0
blank_page_pdf = PdfFileReader(open(blank_page_path, 'rb'))

def add_files(category, filenames, input_abs_dir):
    """
    Handle pdf files for *category* (str).
        Input pdf files are in *input_abs_dir* (str)
        *filenames* gives the list of filenames relative to *input_abs_dir*.
    """
    global proceedings_pdf
    global cumulative_page_count
    global blank_page_pdf
    print('(For {})'.format(category))
    for filename in filenames:
        input_pdf_path = os.path.join(input_abs_dir, filename)
        print('\t' + os.path.relpath(input_pdf_path, working_dir))
        input_pdf = PdfFileReader(open(input_pdf_path, 'rb'))
        input_number_of_pages = input_pdf.getNumPages()
        proceedings_pdf.appendPagesFromReader(input_pdf)

        cumulative_page_count += input_number_of_pages
        if cumulative_page_count % 2:  # if odd number
            cumulative_page_count += 1
            proceedings_pdf.appendPagesFromReader(blank_page_pdf)

add_files('front matter', front_matter_filenames, front_matter_abs_dir)
add_files('acknowledgments', acknowledgments_filenames, acknowledgments_abs_dir)
add_files('table of contents', ['table-of-contents.pdf'], toc_abs_dir)
add_files('papers', paper_filename_list, papersfinal_abs_dir)

proceedings_pdf.write(open(proceedings_pdf_abs_path, 'wb'))

print('\nAll done!!\n\nPlease find "{}" in the working directory.'
      .format(os.path.basename(proceedings_pdf_abs_path)))
