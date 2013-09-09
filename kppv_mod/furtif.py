#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
 furtif - a python version of lvl's furtif.pl
"""

class Furtif(object):

    def load_config(self):
        """Load the configuration file."""
        self.regexes = []

        with open("regles.txt", "r") as f:
            for line in f.readlines():

                # Get rid of comments
                line = line.partition('#')[0].strip()
                if not line:
                    continue

                if ((line[0] == '"' and line[-1] == '"') or
                    (line[0] == "'" and line[-1] == "'")):
                    # A string - remove quotes
                    line = line[1:-1]

                    if line[0] == ' ':
                        # Starts with a space. Replace with \b to
                        # denote start of word
                        line = r"\b" + line[1:]

                    if line[-1] == ' ':
                        # End with a space. Replace with \b to
                        # denote start of word
                        line = line[:-1] + r"\b"

                    linne = line.replace('.', r'\.')


                    self.regexes.append(re.compile(line))

                elif (line[0] == '/' and line[-1] == '/'):
                    # Regex
                    self.regexes.append(re.compile(line[1:-1]))

                else:
                    # A simple word - If written in lower case, then
                    # also search for the word capitalized
                    if line[0] == line[0].lower():
                        self.regexes.append(re.compile(r"\b" + line + r"\b", flags=re.I))
                    else:
                        self.regexes.append(re.compile(r"\b" + line + r"\b"))


    def check_furtif(self, myfile, start, end):
        """Search for regexes/expressions in the text. """
        self.matching = []

        # Regex
        for regex in self.regexes:
            for lineno, line in enumerate(myfile.text, start=myfile.start+1):
                for g in regex.finditer(line):
                    # Found one. Tag it with the start/end markers
                    # given by the caller
                    self.matching.append("<b>%6d</b> :" % lineno + line[:g.start()] + start + line[g.start():g.end()] + end + line[g.end():])

        self.matching = sorted(self.matching)


if __name__ == '__main__':

    import sys
    import re

    import sourcefile

    myfile = sourcefile.SourceFile()
    myfile.load_text(sys.argv[1])

    furtif = Furtif()
    furtif.load_config()
    furtif.check_furtif(myfile, ">", "<")

    for line in furtif.matching:
        print(line)


