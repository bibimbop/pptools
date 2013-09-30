#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# sourcefile -

# Copyright (C) 2012 bibimbop at pgdp

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
 kppvh - file loading
"""

import os
from lxml import etree
import re

def clear_element(element):
    """In an XHTML tree, remove all sub-elements of a given element.

    We can't properly remove an XML element while traversing the
    tree. But we can clean it. Remove its text and children. However
    the tail must be preserved because it belong to the next element,
    so re-attach."""
    tail = element.tail
    element.clear()
    element.tail = tail

class SourceFile(object):
    """Represent a file in memory. """

    def __init__(self):
        self.text = None
        self.xhtml = None

        # Number of the first line in the text after the PG header.
        self.start = 0


    def load_file(self, fname, encoding=None):
        """Load a file (text ot html) and finds its encoding."""

        # Keep the full name, the file name and its path
        self.fullname = fname
        self.basename = os.path.basename(fname)
        self.dirname = os.path.dirname(fname)

        with open(fname, "rb") as f:
            rawdata = f.read()

        if rawdata is None:
            return

        # Remove BOM if present
        if rawdata[0] == 0xef and rawdata[1] == 0xbb and rawdata[2] == 0xbf:
            rawdata = rawdata[3:]

        # Try various encodings. Much faster than using chardet
        if encoding is None:
            encodings = [ 'utf-8', 'latin1' ]
        else:
            encodings = [ encoding ]

        for enc in encodings:
            try:
                # Encode the raw data string into an internal unicode
                # string, according to the discovered encoding.
                self.text = rawdata.decode(enc)
                self.encoding = enc
            except:
                continue

            break


    def strip_pg_boilerplate(self):
        """Remove the PG header and footer from a text version if present.
        """
        new_text = []
        num = 0
        self.start = 0
        for line in self.text:
            num += 1
            # Find the markers. Unfortunately PG lacks consistency
            if (line.startswith("*** START OF THIS PROJECT GUTENBERG EBOOK") or
                line.startswith("*** START OF THE PROJECT GUTENBERG EBOOK") or
                line.startswith("***START OF THE PROJECT GUTENBERG EBOOK")):
                new_text = []
                self.start = num
            elif (line.startswith("*** END OF THIS PROJECT GUTENBERG EBOOK") or
                  line.startswith("***END OF THIS PROJECT GUTENBERG EBOOK") or
                  line.startswith("*** END OF THE PROJECT GUTENBERG EBOOK") or
                  line.startswith("End of the Project Gutenberg EBook of") or
                  line.startswith("End of Project Gutenberg's") or
                  line.startswith("***END OF THE PROJECT GUTENBERG EBOOK")):
                break
            else:
                new_text.append(line)

        self.text = new_text


    def load_xhtml(self, name, encoding=None):

        self.load_file(name, encoding)

        if self.text is None:
            return

        # todo - get rid of BOM

        # Get rid of the encoding declaration. It throws off lxml.
        if self.text.startswith("<?xml"):
            index = self.text.find('>')
            if index != -1:
                self.text = self.text[index+1:]

        # Try the XML then HTML parser
        for xparser in [ ('XML', etree.XMLParser(load_dtd=True)),
                         ('HTML', etree.HTMLParser()) ]:
            try:
                self.tree = etree.fromstring(self.text, xparser[1]).getroottree()
            except:
                continue

            self.parser_used = xparser[0]
            break
        else:
            # Could not parse the file
            return

        # Find the namespace - HOW ?
        #self.xmlns = "{http://www.w3.org/XML/1998/namespace}"
#        print(self.tree.getroot())
#        print(self.tree.getroot().attrib)
#        print(self.tree.docinfo.doctype)
        xmlns = self.tree.getroot().attrib.get('xmlns', None)
        if xmlns:
            self.xmlns = '{' + xmlns + '}'
        else:
            self.xmlns = ""

        # Remove the namespace from the tags
        # (eg. {http://www.w3.org/1999/xhtml})
        for element in self.tree.iter(tag=etree.Element):
            element.tag = element.tag.replace(self.xmlns, "")

        # Split the source file into lines
        self.text = self.text.splitlines()

        # Find type of xhtml (10 or 11 for 1.0 and 1.1). 0=html or
        # unknown. So far, no need to differentiate 1.0 strict and
        # transitional.
        if "DTD/xhtml1-strict.dtd" in self.tree.docinfo.doctype or "DTD/xhtml1-transitional.dtd" in self.tree.docinfo.doctype:
            self.xhtml=10
        elif "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd" in self.tree.docinfo.doctype:
            self.xhtml=11
        else:
            self.xhtml=0

        # Remove PG boilerplate. These are kept in a <pre> tag.
        find = etree.XPath("//pre")
        for element in find(self.tree):
            if element.text is None:
                continue

            text = element.text.strip()

            if re.match(".*?\*\*\* START OF THIS PROJECT GUTENBERG EBOOK.*?\*\*\*(.*)", text, flags=re.MULTILINE | re.DOTALL):
                clear_element(element)

            elif text.startswith("End of the Project Gutenberg") or text.startswith("End of Project Gutenberg"):
                clear_element(element)

    def load_text(self, fname, encoding=None):
        """Load the file as text."""
        self.load_file(fname, encoding)

        if self.text:
            self.text = self.text.splitlines()
            self.strip_pg_boilerplate()
