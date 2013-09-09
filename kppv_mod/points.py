#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
 kppvh - points checking
"""

from lxml import etree
import re

class KPoints(object):
    """ Check combination where a comma is more warranted than a
    dot. Returns a sorted list of matching combinations. Duplicates
    are removed. """

    def check_points(self, myfile):

        # Transform html into text - get rid of <head> content first..
        head = myfile.tree.find('head')
        tail = head.tail
        head.clear()
        head.tail = tail
        text = etree.XPath("normalize-space(/)")(myfile.tree)

        self.point_matches = []

        for m in re.finditer("(\w+\.)»? [a-z]\w+", text):

            if m.group(1) in [ 'Voy.', 'voy.',            # voyez
                               'Biblioth.', 'Bibl.', 'biblioth.',     # bibliothèque
                               'man.', 'Man.', 'manusc.', # manuscript
                               'vol.',                    # volume
                               'fr.',                     # francs
                               'traduct.',                # traduction
                               'photo.', 'photogr.',      # photographie
                               'Rech.',                   # Recherches
                               'orig.',                   # origine, original
                               'Inst.',                   # catalogue
                               'éd.',                     # édition
                               'Collect.',                # collection
                               'Cf.', 'cf.',
                               'impr.',                   # imprimerie, impression
                               'Arch.',                   # archives
                               'hist.',                   # histoire
                               'Mém.',                    # Mémoire
                               'ff.',                     # digramme latin
                               'édit.',                   # édition
                               'M.', 'MM.',               # monsieur, messieurs
                               'mm.',                     # millimètre
                               ]:
                continue

            self.point_matches.append(m.group(0))

        self.point_matches = sorted(set(self.point_matches))




if __name__ == '__main__':

    import argparse
    import os

    import sourcefile

    parser = argparse.ArgumentParser(description='Diff text document for PGDP PP.')

    parser.add_argument('filename', metavar='FILENAME', type=str,
                        help='input text file')

    args = parser.parse_args()

    kp = KPoints()

    myfile = sourcefile.SourceFile()
    myfile.load_xhtml(args.filename)

    kp.check_points(myfile)

    for x in sorted(kp.point_matches):
        print (x)





