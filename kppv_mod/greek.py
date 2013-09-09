#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
 kppvh - check greek transliteration

 This module wouldn't exist without Xavier Faure's kind cooperation.
"""

from itertools import count, groupby
from lxml import etree
import re

from dchars.dchars import new_dstring

class KGreekTrans(object):

    def check_greek_trans(self, myfile):

        greek_trans = []

        # We suppose the greek is inside a span, and the transliterration
        # is in the title attribute.
        for find in [ "//span[@title]" ]:
            for element in etree.XPath(find)(myfile.tree):

                if not element.attrib:
                    continue

                # Encyclopaedia Britanicca
                if "correction" in element.attrib.get("class", ""):
                    continue

                title = element.attrib['title']

                # Special book - remove [Griech.: ...]
                if title.startswith("[Griech.: "):
                    title = title[10:-1]
                else:
                    print (title)

                greek_trans += [ ( element.xpath("string()" ), title) ]


        # Now, compare.
        DSTRING_Y = new_dstring(language='grc',
                                transliteration_method="gutenberg",
                                options = { "gutenberg:transliteration for upsilon" : "u or y",
                                            }
                                )
        self.good_trans = []
        self.bad_trans = []

        for g in greek_trans:
            print (g)
            # greek, transliteration, and expected transliteration
            # strip leading/trailing and double withe spaces
            grec = re.sub("\s+", " ", g[0].lstrip().rstrip())
            triplet = ( grec,
                        re.sub("\s+", " ", g[1].lstrip().rstrip()),
                        DSTRING_Y(grec).get_transliteration() )

            if triplet[1] == triplet[2]:
                self.good_trans += [ triplet ]
            else:
                self.bad_trans += [ triplet ]
