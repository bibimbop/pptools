#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
 kppvh - performs some checking on PGDP or Project Gutenberg files.
"""

import re
from itertools import count, groupby

class FootNotes(object):

    def check_footnotes(self, myfile):
        """Performs some checking on footnotes. Only arabic numeral are considered.
        """

        self.anchor_not_found = []

        # Find all footnotes and their anchors
        anchors = []

        # Does the line start with "[xx]", "[Note xx:" or "[Footnote
        # xx:" ? Also, expect a space or a newline right after the
        # closing bracket; having something else is probably an error,
        # or it's an anchor. Don't expect an anchor inside a footnote,
        # at least on the first line.
        regexes = [ r"^\[(\w+)\]( |$)",
                    r"^ \[(\w+)\]( |$)",
                    r"^  \[(\w+)\]( |$)",
                    r"^   \[(\w+)\]( |$)",
                    r"^    \[(\w+)\]( |$)",
                    r"^     \[(\w+)\]( |$)",
                    r"^      \[(\w+)\]( |$)",
                    r"^\[Note ([\w\-]+):( |$)",
                    r"^  \[Note ([\w\-]+):( |$)",
                    r"^     \[Note ([\w\-]+):( |$)",
                    r"^          \[Note ([\w\-]+):( |$)",
                    r"^\[Footnote ([\w\-]+):( |$)",
                    r"^     \[Footnote ([\w\-]+):( |$)",
                    r"^          \[Footnote ([\w\-]+):( |$)",
                    r"^\     Note ([\w\-]+):",
                    r"^\      Note ([\w\-]+):",
                    ]

        # note_regexes[1] will contain matching numerical matches,
        # while note_regexes[2] will contain the other (non numerical)
        note_regexes = [ (re.compile(x), [], []) for x in regexes ]

        for line in myfile.text:
            # Look for the Footnote
            for regex in note_regexes:
                m = regex[0].match(line)
                if m is not None:
                    # Add it to the 1st list if it's a number
                    # otherwise put it on the 2nd list.
                    if m.group(1).isdigit():
                        regex[1].append(int(m.group(1)))
                    else:
                        # Remove known words, that are certainly not a
                        # footnote
                        if m.group(1) in [ "Illustration", "Decoration", "Décoration", "Bandeau" ]:
                            m = None
                            continue

                        regex[2].append(m.group(1))
                    break
            else:
                # The line doesn't have a footnote. Check for one or more
                # numerical anchors anywhere on the line.
                for m in re.finditer("\[(\d+)\]", line):
                    anchors.append(int(m.group(1)))

        # anchors. Remove consecutive duplicates and create ranges
        # Python magic to go from [1, 2, 2, 2, 5, 6, 7] to [[1,2], [5, 7]]
        anchors = [x[0] for x in groupby(anchors)]
        G = (list(x) for _, x in groupby(anchors, lambda x, c=count(): next(c)-x))
        self.anchor_ranges = [[g[0], g[-1]] for g in G]

        # For each non numerical footnote, try to find an anchor.
        for regex in note_regexes:
            for note in regex[2]:
                anchor = '['+note+']'
                found = 0

                for line in myfile.text:
                    if anchor in line:

                        # Ensure it's not the declaration
                        if regex[0].match(line):
                            continue

                        found = 1
                        break

                if not found:
                    self.anchor_not_found.append(anchor)

        # Build ranges of footnotes found
        index = -1
        self.fn_found = {}
        for regex in note_regexes:
            index += 1
            if len(regex[1]) == 0 and len(regex[2]) == 0:
                continue

            # Footnotes: create range. More than one range might indicate an
            # error in the document.
            G = (list(x) for _, x in groupby(regex[1], lambda x, c=count(): next(c)-x))
            notes_ranges = [[g[0], g[-1]] for g in G]

            # Put the ranges in a dictionary, indexed by the regular
            # expression that found them. First in the tuple is the
            # numerical range, second is the non-numerical instances,
            # with duplicates removed, then sorted.
            self.fn_found[regexes[index]] = (notes_ranges, sorted(list(set(regex[2]))))





