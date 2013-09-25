#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2012-2013 bibimbop at pgdp

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""
 kppvh - performs some checking on PGDP or Project Gutenberg files.
"""

import sys
import codecs
import re
import os
from itertools import count, groupby
import operator
import argparse
import subprocess
import collections
import unicodedata
from lxml import etree
import io
import roman

import helpers.sourcefile as sourcefile
import kppv_mod.duplicates as duplicates
import kppv_mod.footnotes as footnotes
import kppv_mod.kxhtml as kxhtml
import kppv_mod.furtif as furtif
import kppv_mod.images as images
import kppv_mod.pages as pages
import kppv_mod.pptxt as pptxt
import kppv_mod.points as points
import kppv_mod.greek as greek

from jinja2 import Template, Environment, PackageLoader

KPPV_DIR = os.path.dirname(__file__)

class Kppvh(object):

    def __init__(self):
        pass

    def check_furtif(self, myfile):
        """Check for typos/scannos."""

        x = furtif.Furtif()
        x.load_config()
        x.check_furtif(myfile, "<span class='highlight'>", "</span>")

        html = "<h2>Possible stealth scannos/typos in " + myfile.basename + "</h2>"
        self.body.append(etree.fromstring(html))

        if x.matching:
            html = "<div class='box'><ul>"

            for line in x.matching:
                html += "<li>" + line + "</li>"

            html += "</ul></div>"

        else:
            html = "<p>None found</p>"

        self.body.append(etree.fromstring(html))


    def process_pgdp(self, myfile):
        """Process a text file."""

        jinja_env = Environment(loader=PackageLoader('kppvh', ''))
        template = jinja_env.get_template('kppv_templates/kppvh-pgdp.tmpl')

        dup = duplicates.DuplicateLines()
        dup.check_duplicates(myfile)

        # self.check_furtif(myfile)
        return (myfile.basename,
                template.render(myfile=myfile, dup=dup))


    def process_text(self, myfile):
        """Process a text file."""

        jinja_env = Environment(loader=PackageLoader('kppvh', ''))
        template = jinja_env.get_template('kppv_templates/kppvh-text.tmpl')

        dup = duplicates.DuplicateLines()
        dup.check_duplicates(myfile)

        fn = footnotes.FootNotes()
        fn.check_footnotes(myfile)

        misc = pptxt.MiscChecks()
        misc.check_misc(myfile)

        # self.check_furtif(myfile)

        return (myfile.basename,
                template.render(myfile=myfile, dup=dup, fn=fn, misc=misc))


    def process_html(self, myfile):
        """Process an html file."""

        jinja_env = Environment(loader=PackageLoader('kppvh', ''))
        template = jinja_env.get_template('kppv_templates/kppvh-html.tmpl')

        x = kxhtml.KXhtml()
        x.check_document(myfile)
        x.check_title(myfile)
        x.epub_toc(myfile)
        x.check_anchors(myfile)

        css = kxhtml.KXhtml()
        css.check_css(myfile)

        img = images.KImages()
        img.check_images(myfile)

        pgs = pages.KPages()
        pgs.check_pages_links(myfile)
        pgs.check_footnotes(myfile)
        pgs.check_pages_sequence(myfile)

        pts = points.KPoints()
        pts.check_points(myfile)

        grc = greek.KGreekTrans()
        grc.check_greek_trans(myfile)

        return (myfile.basename,
                template.render(myfile=myfile, x=x, css=css, img=img, pages=pgs, points=pts, greek=grc))


def main():

    # Command line arguments
    parser = argparse.ArgumentParser(description='Text Document checker PGDP PP.')

    parser.add_argument('--outfile', type=str,
                        help='XHTML output file name',
                        default='kppvh.html')

    parser.add_argument('filename', metavar='FILENAME', type=str,
                        help='input text file', nargs='+')

    args = parser.parse_args()

    # Keep the files. 1st=pgdp, 2nd=text, 3rd=xhtml
    files = {}

    for fname in args.filename:

        ftype = None
        basename = os.path.basename(fname)
        if basename.startswith("projectID") and basename.endswith(".txt"):
            ftype = 'pgdp'
        elif basename.endswith((".txt", ".ltn")):
            ftype = 'text'
        elif basename.endswith((".htm", ".html")):
            ftype = 'html'

        if ftype is None:
            print("Error: couldn't find type of file " + fname)
            return

        if files.get(ftype):
            print("Error: a file of the same type as", fname, "already exists")
            return

        myfile = sourcefile.SourceFile()

        if ftype == 'html':
            myfile.load_xhtml(fname)
        else:
            myfile.load_text(fname)

        if myfile.text is None:
            print("Cannot read file", f)
            return

        myfile.outname = None

        files[ftype] = myfile


    kppvh = Kppvh()

    outdata = []

    myfile_text = files.get('text', None)
    if myfile_text:
        outdata.append(kppvh.process_text(myfile_text))

    myfile_html = files.get('html', None)
    if myfile_html:
        outdata.append(kppvh.process_html(myfile_html))

    myfile_pgdp = files.get('pgdp', None)
    if myfile_pgdp:
        outdata.append(kppvh.process_pgdp(myfile_pgdp))


    # Write all the nice report tree we've been building
    # todo - no need to call Environment several times
    jinja_env = Environment(loader=PackageLoader('kppvh', ''))
    template = jinja_env.get_template('kppv_templates/kppvh-main.tmpl')

    # Create output file
    out = template.render(outdata=outdata)
    with open(args.outfile, "w") as f:
        f.write(out)


if __name__ == '__main__':

    main()





