#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# checks on txt

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
 kppvh - performs some checking on PGDP or Project Gutenberg files.
"""

import re
import collections
from itertools import count, groupby
import datetime
from collections import Counter

class MiscChecks(object):

    def guess_language(self, myfile):
        # Look for strings like "Note de transcription" or
        # "Transcriber's Note:" in the first 500 lines, or the last
        # 500.
        mylen = min(500, len(myfile.text))
        for line in myfile.text[:mylen] + myfile.text[-mylen :]:
            if re.search("notes? .* transcription", line, re.IGNORECASE):
                self.language = "fr"
                break

            if re.search("transcriber.*note", line, re.IGNORECASE):
                self.language = "en"
                break
        else:
            self.language="unknown"


    def check_empty_lines(self, myfile):
        """Ensure correct spacing between paragraphs."""

        # Keep the chapters in a books. Each number is the number of
        # spaces before a non-empty line.
        # e.g.:  [[4, 1, 2, 1], [4, 1, 1]]
        self.empty_lines_blocks = []

        # Headers of section after 4 empty lines
        self.titles = []

        # Errors found. Kepp the (line number, number of spaces)
        self.empty_lines_errors = []

        # Current chapter. Always starts with a 4. eg.:
        #   [4, 1, 2, 1]

        cur_block = []
        nb_spaces = 0
        for lineno, line in enumerate(myfile.text, start=1):
            if len(line):
                if nb_spaces:

                    if nb_spaces not in [1, 2, 4]:
                        self.empty_lines_errors.append((lineno, nb_spaces))

                    if nb_spaces == 4:
                        # New chapter.

                        # Keep the title
                        self.titles.append(line.strip())

                        # Update the blocks.
                        if len(cur_block):
                            self.empty_lines_blocks.append(cur_block)
                            cur_block = []
                    cur_block.append(nb_spaces)
                    nb_spaces = 0
            else:
                # Empty
                nb_spaces += 1

        if len(cur_block):
            self.empty_lines_blocks.append(cur_block)


    def check_spaces(self, myfile):
        """Check there is no tabs anywhere, or eol characters."""
        self.spaces_tab_errors = []
        self.spaces_trailing_errors = []

        for lineno, line in enumerate(myfile.text):
            # Tab
            if "\t" in line:
                self.spaces_tab_errors.append(lineno)

            # EOL space - todo better
            if line.rstrip() != line:
                self.spaces_trailing_errors.append(lineno)



    def check_line_length(self, myfile):
        """Report lines too long (more than 72 characters)"""
        self.line_length_warning = []
        for lineno, line in enumerate(myfile.text, start = 1):
            if len(line) > 72:
                self.line_length_warning.append((lineno, line, len(line)))


    def check_stars(self, myfile):
        """Report stars."""
        self.stars_warning = []

        for lineno, line in enumerate(myfile.text, start = 1):
            if "*" in line:
                if line == "       *       *       *       *       *":
                    # regular break. Ignore.
                    continue

                self.stars_warning.append((lineno, line))


    def check_special_chars(self, myfile):
        """Look for presence of characters that should not exist."""
        self.special_chars_warning = []

        for lineno, line in enumerate(myfile.text, start = 1):
            if "[oe]" in line or "[ae]" in line:
                self.special_chars_warning.append((lineno, line))

    def check_adjacent_spaces(self, myfile):
        """Look for 2 spaces when only one should be."""
        self.adjacent_spaces = []

        # todo - better regex and cover more punctuation
        for lineno, line in enumerate(myfile.text, start = 1):
            if re.search("\w  [\[.;:,'`\w]", line) or re.search("[\[.;:,'`\w]  \w", line):
                self.adjacent_spaces.append((lineno, line))


    def check_format_markers(self, myfile):
        """Look for formatting markers (<i>, <b>, ...) that may be
        left over."""
        self.format_markers_warning = []

        for lineno, line in enumerate(myfile.text, start = 1):
            if re.search("</?[a-zA-Z]+>", line):
                self.format_markers_warning.append((lineno, line))


    def low_count_chars(self, myfile):
        """Report the characters with a low count ( <= 5)."""
        text= " ".join(myfile.text)

        chars = Counter(text)
        self.low_count_chars = []
        for char, count in chars.items():
            # Skip high count
            if count > 10:
                continue

            # Skip regular ascii
            #if char in a-zA-Z?

            self.low_count_chars.append((char, count))

    def find_french_dates(self, myfile):
        """Find dates, based on month, and ensure they are correct."""
        text= " ".join(myfile.text)
        self.dates_year_min = 999999999
        self.dates_year_max = -1
        self.dates_all = []
        self.dates_invalid = []

        fr_months = { "janvier": 1,
                   "février": 2,
                   "mars": 3,
                   "avril": 4,
                   "mai": 5,
                   "juin": 6,
                   "juillet": 7,
                   "août": 8,
                   "septembre": 9,
                   "octobre": 10,
                   "novembre": 11,
                   "décembre": 12 }

        m = re.findall("(\d+)? (" + '|'.join(fr_months.keys()) + ") (\d+)?", text, flags=re.IGNORECASE)

        # m is an array of tuples (day number, month, year)

        for date in m:

            # Record all dates found - at least the day or the
            # year is necessary.
            if date[0] != "" or date[2] != "":
                self.dates_all.append(" ".join(date))

            # Record youngest and oldest year
            if date[2]:
                self.dates_year_min = min(self.dates_year_min, int(date[2]))
                self.dates_year_max = max(self.dates_year_max, int(date[2]))

            # Check day number
            if date[0]:
                if int(date[0]) not in range(0, 32):
                    self.dates_invalid.append(" ".join(date))

            # Validate the whole date
            if date[0] != "" and date[2] != "":
                try:
                    datetime.datetime(year=int(date[2]), month=fr_months[date[1].lower()], day=int(date[0]))
                except ValueError:
                    self.dates_invalid.append(" ".join(date))


        # todo: sort/uniq dates_all


    def find_english_dates(self, myfile):
        """Find dates, based on month, and ensure they are correct."""
        text= " ".join(myfile.text)
        self.dates_year_min = 999999999
        self.dates_year_max = -1
        self.dates_all = []
        self.dates_invalid = []

        us_months = { "january": 1,
                   "february": 2,
                   "march": 3,
                   "april": 4,
                   "may": 5,
                   "june": 6,
                   "july": 7,
                   "august": 8,
                   "september": 9,
                   "october": 10,
                   "november": 11,
                   "december": 12 }

        m = re.findall("(" + '|'.join(us_months.keys()) + ") (\d+),?\s?(\d+)?", text, flags=re.IGNORECASE)

        # m is an array of tuples (day number, month, year)

        for date in m:

            # Record all dates found - at least the day or the
            # year is necessary.
            self.dates_all.append(" ".join(date))

            # november 2 1910
            # november 2
            # november 1910
            if date[2]:
                year = int(date[2])
            else:
                year = None

            day = int(date[1])
            if day > 31 and year == None:
                year = day
                day = None

            # Record youngest and oldest year
            if year:
                self.dates_year_min = min(self.dates_year_min, year)
                self.dates_year_max = max(self.dates_year_max, year)

            # Check day number
            if day:
                if day not in range(0, 32):
                    self.dates_invalid.append(" ".join(date))
                    continue

            # Validate the whole date
            try:
                if day and year:
                    datetime.datetime(year=year, month=us_months[date[0].lower()], day=day)
            except ValueError:
                self.dates_invalid.append(" ".join(date))


        # todo: sort/uniq dates_all
        self.dates_all=sorted(list(set(self.dates_all)))



    def check_indent(self, myfile):
        """Tries to find all the block indentations."""

        self.block_indent = []
        current_indent = -1

        for lineno, line in enumerate(myfile.text, start = 1):

            # A blank line doesn't change anything
            if len(line) == 0:
                continue

            # Count the number of whitespaces
            m = re.match('(\s+)', line)
            if m is None:
                i = 0
            else:
                i = len(m.group(1))

            if i != current_indent:
                if current_indent != -1:
                    self.block_indent.append(current_indent)
                current_indent = i

        if current_indent != -1:
            self.block_indent.append(current_indent)


    def check_regex(self, myfile):

        self.misc_regex_result = []

        # Try to find various string in the text
        strings = [ ("unusual ,!", ",!"),
                    ("unusual ,?", ",?"),
                    ("[oE]->[oe] or [OE]", "[oE]"),
                    ("[Oe]->[oe] or [OE]", "[Oe]"),
                    ("[ae]->æ", "[ae]"),
                    ("[AE]->Æ", "[AE]"),
                    ("[Blank Page]", "[Blank Page]"),
                    ("degré sign ?", "°"),
                    ("ordinal sign ?", "º"),
                    ("space then punctuation", " ."),
                    ("space then punctuation", " ,"),
                    ("space then punctuation", " ;"),
                    ("space then punctuation", " ]"),
                    ("space then punctuation", " »"),
                    ("space then punctuation", " ?"),
                    ("space then punctuation", " !"),
                    ("space then punctuation", " :"),
                    #("space then punctuation", " '"),
                    #("space then punctuation", " ’"),
                    ("dp marker?", "-*"),
                    ]

        for lineno, line in enumerate(myfile.text, start=myfile.start+1):

            for desc, string in strings:
                # Find all matches, and add them
                if string in line:
                    self.misc_regex_result.append((desc, line, lineno))

        # Try various regexes on the text
        text= " ".join(myfile.text)

        regexes = [ ("mdash->dash(?)", r"\d+--\d+"),
                    ("mdash->dash(?)", r"v\.--\d+"),
                    ("mdash->dash(?)", r"r\.--\d+"),
                    (",letter", r",[^\W\d_]+"),
                    ("bad guiguts find/replace?", r"\$\d[^\d][^ ]*\s"),
                    ("PP tag?", r"\n(/[CFQRPTUX\*#]|[CFQRPTUX\*#]/).*(?=\n)"),
                    ]

        for desc, regex in regexes:
            # Find all matches, and add them
            m = re.findall(regex, text)
            if m is None:
                continue

            for match in m:
                self.misc_regex_result.append((desc, "<regex match> " + match, 0))


    def check_ligatures(self, myfile):
        # If an æ or œ ligature is found, check that similar words
        # also have it.
        pass


    def check_misc(self, myfile):
        """Misc checks."""

        self.guess_language(myfile)
        if self.language == "fr":
            self.find_french_dates(myfile)
        elif self.language == "en":
            self.find_english_dates(myfile)

        self.check_empty_lines(myfile)
        self.check_spaces(myfile)
        self.check_spaces(myfile)
        self.check_line_length(myfile)
        self.check_stars(myfile)
        self.check_special_chars(myfile)
        self.check_adjacent_spaces(myfile)
        self.check_format_markers(myfile)
        self.low_count_chars(myfile)
        self.check_indent(myfile)
        self.check_regex(myfile)




def main():

    myfile = sourcefile.SourceFile()
#    myfile.load_text("egypte.txt")
#    myfile.load_text("../prostitution4/prostitution4.txt")
#    myfile.load_text("../prostitution2/prostitution2.txt")
#    myfile.load_text("textes/41102-0.txt")
#    myfile.load_text("textes/pg18637.txt")
    myfile.load_text("../../../downloads/41692-0.txt")

    x = MiscChecks()
    x.check_misc(myfile)

if __name__ == '__main__':

    import tempfile
    import subprocess
    import os

    import sourcefile

    main()



# For project....txt
#     spaces and punctuation immediately after <i>, <b>, or <sc>, or before </i>, </b>, or </sc> (not all of these are errors)
#    <i>, <b>, or <sc> at the end of a line, and </i>, </b>, or </sc> at the beginning
# Unmatched poetry /* ... */, block quote /# ... #/, and sic /$ ... $/ markup
