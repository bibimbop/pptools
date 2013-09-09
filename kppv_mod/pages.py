#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
 kppvh - page checking
"""

import re
import roman
from lxml import etree
from itertools import count, groupby

class KPages(object):

    def check_pages_sequence(self, myfile):
        """Check the page numbers
        """

        self.ranges_num = []
        self.ranges_roman = []

        # Find the tags similar to <a id="Page_...." ...>
        # If style is not consistent within a book then some numbers
        # will be missed
        for find_str in [ "//a[starts-with(@id, 'Page_')]",
                          "//a[starts-with(@id, 'page_')]",
                          "//a[starts-with(@id, 'page')]",
                          "//span[starts-with(@class, 'pagenum')]",
                          "//div[starts-with(@id, 'Page_')]" ]:

            find = etree.XPath(find_str)
            elements = find(myfile.tree)

            if elements != []:
                break

        if elements == []:
            return

        # Find all the page numbers, and store them in a list, as
        # arabic or roman numbers
        pages_num = []              # list of (page numbers, source line in xml)
        pages_roman = []
        for element in elements:
            # Extract number from the element
            # It's a bit crude because we take the first number.
            if element.tag == 'a':
                # a tag, get number from id attribute
                text = element.attrib['id']
            elif element.text:
                # no a tag, get number from the text
                text = element.text
            else:
                # No text either in the tag. Maybe it's hiding inside
                # a sub-element.
                text = element.xpath('text()') # text is a list
                text = ''.join(text)           # now it's a string

            if text is None:
                # Nothing was found
                continue

            # From the text, now try to find a regular number
            m = re.match('[^\d]*(\d+)', text)
            if m is not None:
                # Got one
                num = int(m.group(1))
                pages_num.append(num)
            else:
                # Try to identify a roman number. Best effort.
                # First try to get rid of the prefix/suffix.
                text = text.replace("Page_", "")
                text = text.replace("page_", "")
                text = text.replace("page", "")
                text = text.replace("[", "")
                text = text.replace("]", "")
                text = text.replace("p.", "")
                text = text.replace("P.", "")
                text = text.replace("Pg.", "")
                text = text.replace("Pg", "")
                text = text.strip()

                try:
                    num = roman.fromRoman(text.upper())
                except roman.InvalidRomanNumeralError:
                    # We tried ...
                    # Move to new anchor
                    continue

                pages_roman.append(text)


        # Create ranges
        # Numeral pages.
        # Python magic to go from [1, 2, 5, 6, 7] to [[1,2], [5, 7]]
        G = (list(x) for _, x in groupby(pages_num, lambda x, c=count(): next(c)-x))
        self.ranges_num = [[g[0], g[-1]] for g in G]

        # Find errors
        last = -1
        for myrange in self.ranges_num:
            page_l, page_h = myrange

            if page_h == last:
                myrange.append("Block is duplicated")
            elif page_h < last:
                myrange.append("Block is out of sequence")
            else:
                myrange.append(None)

            last = page_h


        # Numeral pages.
        # Python magic to go from ['i', 'ii', 'iv', 'v', 'vi'] to [['i', 'ii'], ['iv', 'vi']]
        G = (list(x) for _, x in groupby(pages_roman, lambda x, c=count():
                                             next(c)-roman.fromRoman(x.upper())))
        self.ranges_roman = [[g[0], g[-1]] for g in G]

        # Find errors
        last = -1
        for myrange in self.ranges_roman:
            page_l, page_h = myrange

            if roman.fromRoman(page_h.upper()) == last:
                myrange.append("Block is duplicated")
            elif roman.fromRoman(page_h.upper()) < last:
                myrange.append("Block is out of sequence")
            else:
                myrange.append(None)

            last = roman.fromRoman(page_h.upper())


    def check_pages_links(self, myfile):
        """Check whether the links to a page number look correct. This
        should be useful for a table of content.
        """

        self.inconsistencies = []

        #
        # Check
        #
        find = etree.XPath("//a[starts-with(@href, '#Page_')]")
        elements = find(myfile.tree)
        if elements == []:
            find = etree.XPath("//a[starts-with(@href, '#page_')]")
            elements = find(myfile.tree)
        if elements == []:
            find = etree.XPath("//a[starts-with(@href, '#page')]")
            elements = find(myfile.tree)

        for element in elements:

            if not element.text:
                continue

            # Extract number from the id attribute
            # Crude - find the first number.
            m = re.match('[^\d]*(\d+)', element.attrib['href'])
            if m == None:
                continue

            num = int(m.group(1))

            # Get the first number.
            m = re.match('[^\d]*(\d+)', element.text)

            if m == None:
                # We can't really print a message. It will be noise. The text could be anything.)
                continue

            text_num = int(m.group(1))

            if num != text_num:
                self.inconsistencies.append((element.sourceline, num, text_num))


    def check_footnotes(self, myfile):
        """Performs some checking on footnotes. Only arabic numeral are considered.
        """

        # Find the anchors
        self.note_anchors = []
        for xpath in [ "//a[starts-with(@id, 'FNanchor_')]",
                       "//a[starts-with(@id, 'Anchor-')]",
                       "//a[starts-with(@id, 'FA_')]", ]:
            find = etree.XPath(xpath)
            elements = find(myfile.tree)
            if len(elements):
                break

        for element in elements:
            text = element.attrib['id']
            m = re.match('[^\d]*(\d+)', text)
            if m is not None:
                # Got one
                num = int(m.group(1))
                self.note_anchors.append([element.sourceline, num])
