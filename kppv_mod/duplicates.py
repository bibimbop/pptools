#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
 kppvh - performs some checking on PGDP or Project Gutenberg files.
"""

import collections
from itertools import count, groupby

class DuplicateLines(object):

    def check_duplicates(self, myfile):
        """Check duplicate lines."""

        dup_lines = []

        # Creates a temporary counter collection
        for x, y in collections.Counter(myfile.text).items():
            if y == 1:
                # Unique
                continue

            if len(x) == 0:
                # Empty
                continue

            if x == "       *       *       *       *       *":
                continue

            dup_lines.append(x)

        # Find the first occurence of the line in the text, and store
        # it in a new list of tuples (line number, line).
        dup_lines = [ myfile.start+1+myfile.text.index(line) for line in dup_lines]
        dup_lines = sorted(dup_lines)

        # anchors. Create ranges
        # Python magic to go from [1, 2, 2, 2, 5, 6, 7] to [[1,2], [5, 7]]
        dup_line = [x[0] for x in groupby(dup_lines)]
        G=(list(x) for _,x in groupby(dup_lines, lambda x,c=count(): next(c)-x))
        ranges = [[g[0], g[-1]] for g in G]

        # Kepp only ranges that span more that "threshold" lines.
        threshold = 1
        self.ranges = [ entry for entry in ranges if entry[1] >= entry[0] + threshold ]
