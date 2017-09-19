cls-compile.py
==============

[`cls-compile.py`](cls-compile.py) is a tool for compiling the proceedings of
the [Chicago Linguistic Society](http://chicagolinguisticsociety.org/).

When the individual paper PDFs and other necessary PDFs
(front matter, acknowledgments, etc) are in place,
this tool compiles the proceedings PDF output, automatically taking care of
the following:

* figuring out the page numbers for individual papers
* generating the paper headers and adding them to the paper PDFs
* generating the table of contents
* concatenating everything to create the final proceedings PDF outputs
  (one for the size 8.5' x 11' and the other for 6' x 9';
   some printers require 6' x 9')

This tool is based essentially on what was used to compile the CLS 48 volume,
plus a few upgrades.
It has been used to compile the CLS 50, 51, and 52 volumes.


Download
--------

`cls-compile.py` is currently available on GitHub:
<https://github.com/jacksonllee/cls-proceedings>

Two ways of downloading it:

* Run this if you have `git`:

    ```
    $ git clone https://github.com/jacksonllee/cls-proceedings.git
    ```

* Download the zipped version:

  <https://github.com/jacksonllee/cls-proceedings/archive/master.zip>

Contents
--------

This repository contains the following:

* `cls-compile.py`: where all the magic happens
* `example`: a folder as a sample "working directory" where all necessary input
  files are found
* `readme.md`: this readme file you are reading
* `CLS51_Author_kit.zip`: the CLS 51 author kit with the CLS stylesheet and
  templates; included here for reference

System requirements
-------------------

1. A Unix-like environment

   `cls-compile.py` is a command line tool out of the box. As of November 2016,
    all use cases of `cls-compile.py` have been on Unix-like environments only
    (Linux and Mac OS). Windows is not actively supported. (Cygwin and the like
    should work in principle, but not tested.)

2. Python

    Python is required to run `cls-compile.py`. If you are on Linux or Mac OS,
    Python is readily available. Either Python 2 or 3 works with
    `cls-compile.py`.

    Throughout this readme document, we use `python` to generically
    mean the Python command for your terminal.

3. The Python package PyPDF2 (https://pypi.python.org/pypi/PyPDF2)

    We need this package to manipulate PDF files in Python:

    ```
    $ python -m pip install PyPDF2
    ```

    Administrative privileges (e.g. `sudo` on Ubuntu) may be
    required.

    If Python complains that `pip` is unavailable, you'll need to get it first.
    See [here](https://pip.pypa.io/en/stable/installing/).
    Alternatively, PyPDF2 can be installed through its source on
    [PyPI](https://pypi.python.org/pypi/PyPDF2) or
    [GitHub](https://github.com/mstamy2/PyPDF2).

4. The `pdflatex` program

    The `pdflatex` command has to be available in your path
    so that we can call it to compile LaTeX documents.
    If you are on Linux or Mac and TeX Live is installed, then you probably
    have `pdflatex` already.


Requirements for the input PDF files
------------------------------------

All the PDFs needed to compile the CLS proceedings must all be in a working
directory -- let's call this directory [`example`](example)
(as shown in this repository).

Inside `example`, all PDFs must be organized in the following way in order for
`cls-compile.py` to work:

```
example/
    front-matter/
        front-matter.pdf
    acknowledgments/
        acknowledgments.pdf
    papers-without-headers/
        <all individual paper PDFs without headers or paper numbers>
    templates/
        headers.tex
        table-of-contents.tex
        blank.pdf
    organizer.csv
```

Four folders are expected inside `example`; a fifth required item right under
`example`---`organizer.csv`---is explained in the next section.


* `front-matter`

    Only one PDF file is expected in this folder, e.g.,
    [`front-matter.pdf`](example/front-matter/front-matter.pdf)
    (`.tex` template also provided).
    `cls-compile.py` ignores all other non-PDF files in this folder, so you may
    work within this folder
    with LaTeX files etc to generate the required PDF file.

* `acknowledgments`

    Only one PDF file is expected in this folder, e.g.,
    [`acknowledgments.pdf`](example/acknowledgments/acknowledgments.pdf)
    (`.tex` template also provided).
    `cls-compile.py` ignores all other non-PDF files in this folder, so you may 
    work within this folder
    with LaTeX files etc to generate the required PDF file.

* `papers-without-headers`

    This folder contains all PDFs of the individual papers without headers or
    page numbers.

* `templates`

    This folder contains templates and other files needed. Do NOT change their
    names, though the contents of `headers.tex` and `table-of-contents.tex` can
    be updated if necessary.
    `blank.pdf` is the blank PDF page inserted here and there in the final
    proceedings PDF so that all items start on the right-hand side in the
    printed volume.


The organizer CSV file
----------------------

An organizer CSV file (e.g., [`organizer.csv`](example/organizer.csv)) is
required to provide the essential information about authors, paper titles, etc.
This CSV file must contain six columns with the following header names:

1. `index`

    An index number just for convenience. The first paper is 1 and so forth.
    Note that the order of the rows in this CSV file (regardless of what the
    column `index` says) determines the order by which the papers appear in the
    proceedings PDF.
    So make sure all the papers are ordered correctly in the organizer by
    alphabetical order of first authors' last names or whatever the CLS members
    would like.

2. `authors`

    The cell for each paper in the column `authors` shows exactly how author
    names appear in the table of contents.
    Use LaTeX formatting for non-ASCII characters (accented characters etc).

3. `paper title`

    (similar to `authors` above)

4. `authors in header`

    The cell for each paper in the column `authors in header` shows exactly how
    author names appear in
    the paper's header. Use LaTeX formatting for non-ASCII characters (accented
    characters etc).
    The cell content will be forced to be in the uppercase in the output
    proceedings PDF.

    If this cell is empty, then the cell content from `authors` for the paper
    in question will be used.

    Note the cell content of `authors in header` cannot exceed a certain
    character length
    (controlled by the optional argument `--maxheaderlength` for
    `cls-compile.py`;
    more on running `cls-compile.py` below)
    because the header naturally cannot accommodate something too long that
    would go over one line
    or cover up the page number.
    So for a paper with a long chain of author names,
    you have to put down something much shorter here (e.g., only the
    lastnames?).

5. `paper title in header`

    (similar to `authors in header` above)

6. `paper filename`

    The cell for each paper in the column `paper filename` shows the paper's
    filename (e.g., `smith.pdf`)
    as it appears in the folder `papers-without-headers`.


How to run `cls-compile.py`
---------------------------

If you have a working directory like `example` with all necessary files
properly organized by the guidelines here,
then do this at your current directory where `cls-compile.py` is:

```
$ python cls-compile.py --directory=<relative-path-to-your-working-directory>
```

If you don't provide `--directory=<relative-path-to-your-working-directory>`
(i.e., if you run `python cls-compile.py` without any arguments),
`cls-compile.py` assumes the `example` folder is at the current directory and
it is your working directory.

`cls-compile.py` allows various optional arguments for changing file/folder
names etc.
Please run `python cls-compile.py -h` for details.
Among the array of optional parameters, you may be interested in the following:

* `--maxheaderlength`

    The maximum length (by number of characters) of the author or paper title
    headers in the
    paper PDFs (default: 55). This cap ensures that the header does not go over
    one line or
    cover up the page number in the header. To change the value to, say, 60, do
    something like
    `python cls-compile.py --maxheaderlength=60`.

* `--startpagenumber`

    The starting page number of the first paper by order in the proceedings
    volume (default: 1).

Multiple optional parameters are possible, in the form of
`python cls-compile.py --<parametername1>=<parametervalue1> --<parametername2>=<parametervalue2>`.


Outputs
-------

If you run `cls-compile.py` and all goes well, the final proceedings PDF outputs
should be sitting right inside your working directory (hurray!).
In addition, all intermediate files are kept for reference.
Inside the working directory, you should see the new folders
`table-of-contents`, `headers`, and `papers-with-headers`
(all individual paper PDFs nicely typeset with headers and page numbers here!).

Note that if you are running `cls-compile.py` multiple times, all
already-existing contents inside
the folders `table-of-contents`, `headers`, and `papers-with-headers` will be
removed at each run to ensure clean output files.

Upon completion of the final PDF compilation, three log files are generated
at the working directory: `master.log`, `pdflatex.log`, and `directory.log`.


Technical support etc.
----------------------

CLS officers are welcome to contact [Jackson Lee](http://jacksonllee.com/)
for any questions regarding this tool.
If you run into any issues and would like Jackson's help for troubleshooting,
doing the following will help him to figure out how to help you:

* Tell him what error messages (if any) appear on the terminal.
* Send him the three log files
  (`master.log`, `pdflatex.log`, and `directory.log`);
  these should be at the same directory as `cls-compile.py`.

To take advantage of the GitHub infrastructure -- Code contributions through
pull requests are more than welcome!
Questions and bug reports? Please submit a ticket
[here](https://github.com/jacksonllee/cls-proceedings/issues/new).


Development notes
-----------------

The overarching strategies of `cls-compile.py`:

* Check if everything needed is in place before any PDF manipulation is done
* Issue an error (and exit) as soon as one is detected

Everything in the proceedings volume that comes after the table of contents is
treated as "papers". This means that, for instance,
if something like a prompt page to introduce the main
session or parasession papers is desired, it should be treated as a "paper" and
included in the organizer CSV file (but we probably don't want headers and page
numbers for these -- would need some way to handle this).

Use flake8 to maintain high code quality.
To install it (assume `pip` is available):

```
$ pip install flake8
```

To run it (no output means everything's great!):

```
$ flake8 cls-compile.py
```

License
-------

The MIT License. See [LICENSE.txt](LICENSE.txt).
