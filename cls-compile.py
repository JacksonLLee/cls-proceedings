"""A tool for compiling the proceedings of the Chicago Linguistic Society
<http://chicagolinguisticsociety.org/>.
Download, documentation etc: <https://github.com/jacksonllee/cls-proceedings>
Author: Jackson Lee <jacksonlunlee@gmail.com>
Last updated on 2017-09-18
"""

from __future__ import print_function
import sys
import argparse
import os
import csv
import subprocess
import platform
import logging

from PyPDF2 import (PdfFileWriter, PdfFileReader)

# --------------------------------------------------------------------------- #
# set up logging

MASTER_LOG_NAME = "master.log"

MASTER_LOGGER = logging.getLogger(__name__)
MASTER_LOGGER.setLevel(logging.INFO)

file_handler = logging.FileHandler(MASTER_LOG_NAME)
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s: %(message)s')
file_handler.setFormatter(formatter)

MASTER_LOGGER.addHandler(file_handler)

# --------------------------------------------------------------------------- #
# some handy functions


def read_csv(fname, delim=',;\t| '):
    """Read a CSV file (n rows, m columns) with filename *fname*,
    and return a list containing n lists each containing m strings.
    """
    with open(fname, 'rU') as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(), delimiters=delim)
        csvfile.seek(0)
        data = csv.reader(csvfile, dialect)
        return list(data)


def ensure_empty_dir(abs_dir_path):
    """Ensure that *abs_dir_path* is an empty folder."""
    if os.path.isdir(abs_dir_path):
        # delete everything inside the folder
        existing_filenames = os.listdir(abs_dir_path)
        for filename_ in existing_filenames:
            filename_abs_path = os.path.join(abs_dir_path, filename_)
            os.remove(filename_abs_path)
    else:
        # create the empty folder
        os.makedirs(abs_dir_path)


# --------------------------------------------------------------------------- #
# set up this script's information

__author__ = 'Jackson Lee'
__author_email__ = 'jacksonlunlee@gmail.com'
__url__ = 'https://github.com/jacksonllee/cls-proceedings'

__longdescr__ = """\
Compiling the proceedings of the Chicago Linguistic Society\n
Download, documentation etc: <{}>\n
Author: {} <{}>""".format(__url__, __author__, __author_email__)

# --------------------------------------------------------------------------- #
# parse command line arguments

parser = argparse.ArgumentParser(
    description=__longdescr__,
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
parser.add_argument('--output', type=str, default='proceedings.pdf',
                    help='filename of the final proceedings pdf output '
                         '(size 8.5" x 11")')
parser.add_argument('--output6by9', type=str, default='proceedings6by9.pdf',
                    help='filename of the final proceedings pdf output '
                         '(size 6" x 9")')
parser.add_argument('--scale', type=float, default=0.95,
                    help='Scale factor for the 6" x 9" output based on the '
                         '8.5" x 11". Try a slightly smaller value if '
                         'material is still cut off at the margins.')
parser.add_argument('--startpagenumber', type=int, default=1,
                    help='the starting page number of the first paper by order'
                         'in the volume')
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
proceedings_pdf_filename = command_line_args.output
proceedings_pdf_6by9_filename = command_line_args.output6by9
scale_factor = command_line_args.scale
start_page_number = command_line_args.startpagenumber

working_dir = os.path.abspath(command_line_args.directory)

if not os.path.isdir(working_dir):
    raise RuntimeError('The directory {} does not exist.'.format(working_dir))

# --------------------------------------------------------------------------- #
MASTER_LOGGER.info('Defining log filenames and file objects')

PDFLATEX_LOG_NAME = 'pdflatex.log'
DIRECTORY_LOG_NAME = 'directory.log'

PDFLATEX_LOG = open(PDFLATEX_LOG_NAME, 'w')
DIRECTORY_LOG = open(DIRECTORY_LOG_NAME, 'w')


def print_directory_log(msg):
    print(msg, file=DIRECTORY_LOG)
    for dir_, _, filenames in os.walk(working_dir):
        for filename in filenames:
            print(os.path.join(dir_, filename), file=DIRECTORY_LOG)
    print(file=DIRECTORY_LOG)


# --------------------------------------------------------------------------- #
MASTER_LOGGER.info('Logging directory contents before PDF manipulation')

print_directory_log('Before any PDF manipulation:')

# --------------------------------------------------------------------------- #
# print basic info/metadata to master log

MASTER_LOGGER.info('System: {}'.format(platform.system()))
MASTER_LOGGER.info('Node: {}'.format(platform.node()))
MASTER_LOGGER.info('Release: {}'.format(platform.release()))
MASTER_LOGGER.info('Version: {}'.format(platform.version()))
MASTER_LOGGER.info('Machine: {}'.format(platform.machine()))
MASTER_LOGGER.info('Processor: {}'.format(platform.processor()))
MASTER_LOGGER.info('Python version: {}'.format(platform.python_version()))
MASTER_LOGGER.info('sys.argv: {}'.format(sys.argv))
MASTER_LOGGER.info('Your working directory: {}'.format(working_dir))

# --------------------------------------------------------------------------- #
MASTER_LOGGER.info('Reading the organizer CSV file')

organizer_path = os.path.join(working_dir, organizer_name)

if not os.path.isfile(organizer_path):
    raise RuntimeError('The organizer "{}" is not found.'
                       .format(organizer_path))

organizer = read_csv(organizer_path)
number_of_papers = len(organizer) - 1

organizer_headers = [x.lower().strip() for x in organizer[0]]
expected_organizer_headers = ['index', 'authors', 'paper title',
                              'authors in header', 'paper title in header',
                              'paper filename']

header_to_index = dict()
# key: a header in the organizer CSV (e.g., 'index', 'author', 'paper title')
# value: the index of that header in the list expected_organizer_headers

for expected_header in expected_organizer_headers:
    try:
        header_to_index[expected_header] = \
            organizer_headers.index(expected_header)
    except ValueError:
        raise RuntimeError("The header {} is not found in the organizer CSV "
                           "file.".format(expected_header))

authors_list = [row[header_to_index['authors']] for row in organizer[1:]]
paper_title_list = [row[header_to_index['paper title']]
                    for row in organizer[1:]]
authors_in_header_list = [row[header_to_index['authors in header']]
                          for row in organizer[1:]]
paper_title_in_header_list = [row[header_to_index['paper title in header']]
                              for row in organizer[1:]]
paper_filename_list = [row[header_to_index['paper filename']]
                       for row in organizer[1:]]

MASTER_LOGGER.info('The organizer is: {}'.format(organizer_path))

# --------------------------------------------------------------------------- #
MASTER_LOGGER.info('Checking if any author or paper tile headers are too '
                   'long')

error_template = 'The header "{}" for paper {} is longer than {} characters.'

for i in range(number_of_papers):
    authors_in_header = authors_in_header_list[i]
    paper_title_in_header = paper_title_in_header_list[i]

    # if no header specified, use the full author/title name
    if not authors_in_header:
        authors_in_header = authors_list[i]
        authors_in_header_list[i] = authors_in_header
    if not paper_title_in_header:
        paper_title_in_header = paper_title_list[i]
        paper_title_in_header_list[i] = paper_title_in_header

    MASTER_LOGGER.info(authors_in_header)
    MASTER_LOGGER.info(paper_title_in_header)

    # max_header_length can be set at command line arguments
    if len(authors_in_header) > max_header_length:
        raise RuntimeError(error_template.format(authors_in_header, i + 1,
                                                 max_header_length))

    if len(paper_title_in_header) > max_header_length:
        raise RuntimeError(error_template.format(paper_title_in_header, i + 1,
                                                 max_header_length))

# --------------------------------------------------------------------------- #

# For front matter and acknowledgments, I intentionally use lists here
# (front_matter_filenames and acknowledgments_filenames) to allow the
# possibility that more than one PDFs---as opposed to just exactly one---may
# be allowed for whatever reason. In that case, care should be taken for
# where the blank pages should be inserted (cf. towards the end of the code
# below).

MASTER_LOGGER.info('Checking if the front matter file is present')

front_matter_abs_dir = os.path.join(working_dir, front_matter_dir)

if not os.path.isdir(front_matter_abs_dir):
    raise RuntimeError("The front matter directory {} does not exist."
                       .format(front_matter_abs_dir))

front_matter_filenames = sorted([x for x in os.listdir(front_matter_abs_dir)
                                 if x.lower().endswith('.pdf')])

if len(front_matter_filenames) == 0:
    raise RuntimeError('No front matter pdf is found at {}'
                       .format(front_matter_abs_dir))

if len(front_matter_filenames) > 1:
    raise RuntimeError('More than 1 pdf file is found at {}\n'
                       '(Only 1 pdf is allowed.)'
                       .format(front_matter_abs_dir))

# --------------------------------------------------------------------------- #
MASTER_LOGGER.info('Checking if acknowledgments pdf is present')

acknowledgments_abs_dir = os.path.join(working_dir, acknowledgments_dir)

if not os.path.isdir(acknowledgments_abs_dir):
    raise RuntimeError('The acknowledgments directory {} does not exist.'
                       .format(acknowledgments_abs_dir))

acknowledgments_filenames = sorted([x for x in
                                    os.listdir(acknowledgments_abs_dir)
                                    if x.lower().endswith('.pdf')])

if len(acknowledgments_filenames) == 0:
    raise RuntimeError('No acknowledgments pdf is found at {}'
                       .format(acknowledgments_abs_dir))

if len(acknowledgments_filenames) > 1:
    raise RuntimeError('More than 1 pdf file is found at {}\n'
                       '(Only 1 pdf is allowed.)'
                       .format(acknowledgments_abs_dir))

# --------------------------------------------------------------------------- #
MASTER_LOGGER.info('Checking if templates files are present')

templates_abs_dir = os.path.join(working_dir, templates_dir)

if not os.path.isdir(templates_abs_dir):
    raise RuntimeError('The templates directory {} does not exist.'
                       .format(templates_abs_dir))

headers_template_path = os.path.join(templates_abs_dir, 'headers.tex')
blank_page_path = os.path.join(templates_abs_dir, 'blank.pdf')
toc_template_path = os.path.join(templates_abs_dir, 'table-of-contents.tex')

if not os.path.isfile(headers_template_path):
    raise RuntimeError('Expected template file not found -- {}'
                       .format(headers_template_path))

if not os.path.isfile(blank_page_path):
    raise RuntimeError('Expected template file not found -- {}'
                       .format(blank_page_path))

if not os.path.isfile(toc_template_path):
    raise RuntimeError('Expected template file not found -- {}'
                       .format(toc_template_path))

# --------------------------------------------------------------------------- #
MASTER_LOGGER.info('Checking if all pdf papers are present, '
                   'and getting number of pages for each paper')

number_of_pages_list = list()  # list of int
page_range_list = list()  # list of (int, int)
cumulative_start_page = start_page_number
current_paper_start_page = start_page_number

for paper_filename in paper_filename_list:
    paper_path = os.path.join(working_dir, papers_dir, paper_filename)

    if not os.path.isfile(paper_path):
        raise RuntimeError('The file "{}" is not found in {}.\nCheck if '
                           'actual filenames match those in the CSV organizer.'
                           .format(paper_filename,
                                   os.path.join(working_dir, papers_dir)))

    pdf_object = PdfFileReader(open(paper_path, 'rb'))
    number_of_pages = pdf_object.getNumPages()
    end_page = current_paper_start_page + number_of_pages - 1

    number_of_pages_list.append(number_of_pages)
    page_range_list.append((current_paper_start_page, end_page))

    cumulative_start_page += number_of_pages

    if cumulative_start_page % 2:  # if cumulative_start_page is an odd number
        pass

        # The current paper ends on the *left*-hand side in the printed volume.
        # The next paper will start immediately afterwards (no blank page
        # insertion needed), on the right-hand side in the printed volume.
    else:
        cumulative_start_page += 1

        # The paper ends on the *right*-hand side in the printed volume.
        # We will need to insert a blank page right after this page,
        # so that the next paper starts on the right-hand side.
        # In terms of page number tracking, the next paper will skip one page
        # (= the blank page), and therefore we need to increment
        # cumulative_start_page by 1.

    current_paper_start_page = cumulative_start_page

# --------------------------------------------------------------------------- #
MASTER_LOGGER.info("Creating headers' latex files and "
                   "generating the headers' pdfs")

headers_abs_dir = os.path.join(working_dir, headers_dir)
ensure_empty_dir(headers_abs_dir)
header_template_str = open(headers_template_path).read()

for i in range(number_of_papers):
    # noinspection PyRedeclaration
    latex_str = header_template_str
    authors_in_header = authors_in_header_list[i].upper()  # all uppercase
    paper_title_in_header = paper_title_in_header_list[i].upper()  # uppercase
    number_of_pages = number_of_pages_list[i]
    current_paper_start_page, end_page = page_range_list[i]

    page_range_str = '{}-{}'.format(current_paper_start_page, end_page)
    insert_pages_str = '\\newpage\n\n\\mbox{}\n' * (number_of_pages - 1)
    headers_latex_filename = 'headers{}.tex'.format(i)

    latex_str = latex_str.replace('XXStartPageXX',
                                  str(current_paper_start_page))
    latex_str = latex_str.replace('XXAuthorsXX', authors_in_header)
    latex_str = latex_str.replace('XXTitleXX', paper_title_in_header)
    latex_str = latex_str.replace('XXPageRangeXX', page_range_str)
    latex_str = latex_str.replace('XXInsertPagesXX', insert_pages_str)

    output_latex_path = os.path.join(headers_abs_dir, headers_latex_filename)
    with open(output_latex_path, 'w') as f:
        f.write(latex_str)

    subprocess.call(('pdflatex', '-output-directory', headers_abs_dir,
                     output_latex_path), stdout=PDFLATEX_LOG)

# --------------------------------------------------------------------------- #
MASTER_LOGGER.info('Creating paper pdfs with headers')

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

# --------------------------------------------------------------------------- #
MASTER_LOGGER.info('Creating the table of contents')

toc_abs_dir = os.path.join(working_dir, toc_dir)
ensure_empty_dir(toc_abs_dir)

toc_template = open(toc_template_path).read()
toc_entry_template = '\\TocEntry{{{}}}{{{}}}{{{}}}\n\n'

toc_entries_str = ''

for i in range(number_of_papers):
    authors = authors_list[i]
    paper_title = paper_title_list[i]
    current_paper_start_page = page_range_list[i][0]

    toc_entries_str += toc_entry_template.format(authors, paper_title,
                                                 current_paper_start_page)

toc_template = toc_template.replace('XXInsertTocEntriesXX', toc_entries_str)

output_toc_tex_path = os.path.join(toc_abs_dir, 'table-of-contents.tex')
with open(output_toc_tex_path, 'w') as f:
    f.write(toc_template)

subprocess.call(('pdflatex', '-output-directory', toc_abs_dir,
                 output_toc_tex_path), stdout=PDFLATEX_LOG)

# --------------------------------------------------------------------------- #
MASTER_LOGGER.info("""Working directory: {}
Creating the final proceedings pdf output
Input pdf files are concatenated in the following order.
(Blank pages are automatically added if necessary.)""".format(working_dir))

proceedings_pdf = PdfFileWriter()
proceedings_pdf_abs_path = os.path.join(working_dir, proceedings_pdf_filename)

cumulative_page_count = 0
blank_page_pdf = PdfFileReader(open(blank_page_path, 'rb'))


def add_files(category, filenames_, input_abs_dir):
    """
    Handle pdf files for *category* (str).
        Input pdf files are in *input_abs_dir* (str)
        *filenames* gives the list of filenames relative to *input_abs_dir*.
    """
    global proceedings_pdf
    global cumulative_page_count
    global blank_page_pdf

    MASTER_LOGGER.info('(For {})'.format(category))

    for filename_ in filenames_:
        input_pdf_path = os.path.join(input_abs_dir, filename_)

        MASTER_LOGGER.info('\t' + os.path.relpath(input_pdf_path, working_dir))

        input_pdf = PdfFileReader(open(input_pdf_path, 'rb'))
        input_number_of_pages = input_pdf.getNumPages()
        proceedings_pdf.appendPagesFromReader(input_pdf)

        cumulative_page_count += input_number_of_pages

        # check if blank page insertion is needed
        if cumulative_page_count % 2:  # if odd number
            cumulative_page_count += 1
            proceedings_pdf.appendPagesFromReader(blank_page_pdf)


add_files('front matter', front_matter_filenames, front_matter_abs_dir)
add_files('acknowledgments', acknowledgments_filenames,
          acknowledgments_abs_dir)
add_files('table of contents', ['table-of-contents.pdf'], toc_abs_dir)
add_files('papers', paper_filename_list, papersfinal_abs_dir)

proceedings_pdf.write(open(proceedings_pdf_abs_path, 'wb'))

# --------------------------------------------------------------------------- #
MASTER_LOGGER.info('Creating the 6" x 9" final proceedings PDF')

proceedings_pdf_85by11 = PdfFileReader(open(proceedings_pdf_abs_path, 'rb'))
page1 = proceedings_pdf_85by11.getPage(0)
original_page_width, original_page_height = page1.mediaBox.getUpperRight()

new_page_width = original_page_width * scale_factor
new_page_height = original_page_height * scale_factor

page_width_delta = (original_page_width - new_page_width) / 2
page_height_delta = (original_page_height - new_page_height) / 2

trim_from_left_right_margins = (original_page_width * (1.25 / 8.5) -
                                page_width_delta)
trim_from_top_margin = original_page_height * (0.67 / 11) - page_height_delta
trim_from_bottom_margin = (original_page_height * (1.33 / 11) -
                           page_height_delta)

new_lower_left = (trim_from_left_right_margins, trim_from_bottom_margin)
new_upper_right = (new_page_width - trim_from_left_right_margins,
                   new_page_height - trim_from_top_margin)

proceedings_pdf_6by9 = PdfFileWriter()
proceedings_pdf_6by9_abs_path = os.path.join(working_dir,
                                             proceedings_pdf_6by9_filename)

for i in range(proceedings_pdf_85by11.getNumPages()):
    page = proceedings_pdf_85by11.getPage(i)
    page.scaleBy(scale_factor)
    page.mediaBox.lowerLeft = new_lower_left
    page.mediaBox.upperRight = new_upper_right
    proceedings_pdf_6by9.addPage(page)

proceedings_pdf_6by9.write(open(proceedings_pdf_6by9_abs_path, 'wb'))

# --------------------------------------------------------------------------- #
MASTER_LOGGER.info('All done!! Please find these in the working directory:\n'
                   '\tSize 8.5" x 11": {}\n'
                   '\tSize 6" x 9": {}\n'
                   .format(os.path.basename(proceedings_pdf_abs_path),
                           os.path.basename(proceedings_pdf_6by9_abs_path)))

MASTER_LOGGER.info("Other output files are in the following subfolders:\n"
                   "{}\n{}\n{}"
                   .format(os.path.relpath(papersfinal_abs_dir, working_dir),
                           os.path.relpath(toc_abs_dir, working_dir),
                           os.path.relpath(headers_abs_dir, working_dir)))

MASTER_LOGGER.info('Log files:')
MASTER_LOGGER.info('{} (this current file)'.format(MASTER_LOG_NAME))
MASTER_LOGGER.info('{} (log by the "pdflatex" command)'
                   .format(PDFLATEX_LOG_NAME))
MASTER_LOGGER.info('{} (all contents at the working directory)'
                   .format(DIRECTORY_LOG_NAME))

# --------------------------------------------------------------------------- #
MASTER_LOGGER.info('Printing the directory tree after final PDf compilation')

print_directory_log('After completion of final PDF compilation:')

# --------------------------------------------------------------------------- #
MASTER_LOGGER.info('Closing log files for pdflatex and directory tree')

PDFLATEX_LOG.close()
DIRECTORY_LOG.close()
