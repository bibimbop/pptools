#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
 kppvh - various checks on xhtml
"""

from lxml import etree
from lxml.cssselect import CSSSelector
import cssutils
import re
import logging
import io
import os

# The xml: prefix is equivalent to the following
XMLNS="{http://www.w3.org/XML/1998/namespace}"

# List of language, indexed on the language tag, from
#   http://www.iana.org/assignments/language-subtag-registry
def load_languages():
    with open(os.path.dirname(__file__) + "/../kppv_misc/language-subtag-registry", "r") as f:

        languages={}
        current = {}

        for line in f.readlines():
            if line.startswith('  '):
                # Continuation of previous field on a new line
                continue

            line = line.strip()

            if line == '%%':
                if 'Subtag' in current:
                    languages[current['Subtag']] = current
                current = {}
                continue

            m = re.match("(.*): (.*)", line)
            if m is None:
                # parse Error ?
                continue

            key = m.group(1)
            value = m.group(2)
            if key in [ 'Type', 'Subtag', 'Description' ]:
                if key is 'Description':
                    # Some languages have several descriptions, so concat them
                    current[key] = ','.join([current.get('Description', None), value])
                else:
                    current[key] = value


        if 'Subtag' in current:
            languages[current['Subtag']] = current

        return languages


class KXhtml(object):

    def check_css(self, myfile):
        """Find unused CSS and undefined used CCS.
        """

        # Fails on a few corner cases, such as
        #  ".tdm > tbody > tr > td:first-child + td"
        #  ".onetable td"
        #
        # Ignores @media

        # Find the CCS style
        css_selectors = []
        css = myfile.tree.find('head').find('style')

        if css == None:
            return

        # The CSS can be in a comment or not
        if len(css):
            # Not sure whether that covers all the comment cases. Maybe add
            # all the children
            css_string = etree.tostring(css[0])
        else:
            css_string = css.text

        # Parse the CSS and retrieve the errors
        mylog = io.StringIO()
        h = logging.StreamHandler(mylog)
        h.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
        cssutils.log.addHandler(h)
        cssutils.log.setLevel(logging.INFO)
        css_sheet = cssutils.parseString(css_string)

        self.cssutils_errors = [ x for x in mylog.getvalue().splitlines() if x ]


        for rule in css_sheet:

            # We don't want comments, media, ...
            if rule.type != cssutils.css.CSSRule.STYLE_RULE:
                continue

            rules = rule.selectorText.split(',')
            for rule in rules:
                # Cleanup rule
                selector = rule.strip()

                css_selectors.append(selector)


        # Find the unused/undefined CSS. It is possible 2 rules will
        # match the same class (for instance "p.foo" and ".foo" will
        # match "class=foo"). That is not detected, and both rules
        # will be valid.
        self.sel_unchecked = []
        self.sel_unused = []
        for selector in css_selectors:

            # Get the selector (eg. "body", "p", ".some_class")
            try:
                sel = CSSSelector(selector)
            except:
                self.sel_unchecked.append(selector)
                continue

            # Retrieve where it is used in the xhtml
            occurences = sel(myfile.tree)

            if len(occurences) == 0:
                self.sel_unused.append(sel.css)
                continue

            # If it's from a class, find the name. It should be the
            # last word starting with a dot (eg. "p.foo", ".foo",
            # "#toc .foo" => "foo")
            m = re.match('^.*\.([\w-]+)$', sel.css)

            if m == None:
                continue

            cl = m.group(1)
            assert len(cl) > 0

            # Mark the class wherever it is used, in each element
            for item in occurences:
                if 'class' in item.attrib:
                    old_classes = item.attrib['class'].split(' ')

                    found = 0
                    for it_cl in old_classes:
                        it_cl.strip()
                        if it_cl == cl:
                            # The class has been found. Mark it.
                            found = 1
                            if '__used_classes' not in item.attrib:
                                item.attrib['__used_classes'] = it_cl
                            else:
                                item.attrib['__used_classes'] += ' ' + it_cl

                    assert found == 1

                else:
                    # I don't think that should happen
                    print("KPPVH ERROR - matches " + cl + " but no class - line " + str(item.sourceline))

        # Look for unused classes
        self.classes_undefined = []
        # todo- use xpath instead
        for element in myfile.tree.iter(tag=etree.Element):
            if 'class' in element.attrib:
                classes = element.attrib['class'].strip()
                classes = re.sub(r"\s+", " ", classes)
                classes = classes.split(' ')

                if '__used_classes' in element.attrib:
                    used_classes = element.attrib['__used_classes'].strip().split(' ')

                    # Substract content of used_classes from classes
                    classes = list(set(classes) - set(used_classes))

                # Finally, print the warning)
                for cl in classes:
                    self.classes_undefined.append([element.sourceline, cl])


    def check_title(self, myfile):
        """Check whether the title is built accoring to PG or PGDP suggestion.
        """
        title = myfile.tree.find('head').find('title')
        lines = [ line.strip() for line in title.text.splitlines()]
        title_str = ' '.join(lines).strip()
        title_str = title_str.replace('—', '&mdash;')

        # Try the recommended format
        for regex in [ r'^The Project Gutenberg eBook of (.*),\s+by (.*)$',
                       r'^(.*), by (.*)\s?&mdash;\s?A Project Gutenberg eBook\.?$' ]:

            m = re.match(regex, title_str)
            if m:
                self.good_format = True
                self.title = m.group(1)
                self.author = m.group(2)
                return

        self.good_format = False

        # Try variations
        for regex in [ "^The Project Gutenberg's eBook of (.*),\s+by (.*)$",
                       "^The Project Gutenberg eBook of (.*),\s+by (.*)$",
                       "^The Project Gutenberg eBook of (.*),\s+par (.*)$",
                       "^The Project Gutenberg eBook of (.*),\s+edited by (.*)$",
                       ]:

            m = re.match(regex, title_str, flags=re.I)
            if m:
                self.title = m.group(1)
                self.author = m.group(2)
                return

        self.title = None
        self.author = None


    def epub_toc(self, myfile):
        """Build the ePub table of content.
        indent will be added in front of each line, once per level.
        """

        self.toc = []

        find = etree.XPath("//h1|//h2|//h3|//h4")
        elements = find(myfile.tree)
        for element in elements:
            # Compute an offset for future indent. h1=0, h2=1, h3=2, h4=3
            level = int(element.tag[1]) - 1

            # Attribute title overrides the content
            if 'title' in element.attrib:
                text = element.attrib['title'].replace('\n', ' ').strip(' ')
            else:
                text = etree.tostring(element).decode("utf-8").replace('\n', ' ')

                # Remove the tag markers
                text = re.sub('<[^<]*>', ' ', text, 0)

                # Replace series of spaces with only one space
                text = re.sub(' +', ' ', text, 0)

                # Strip leading and trailing spaces
                text = text.strip(' ')

            # Print the title with an offset and indent)
            if text != "":
                self.toc.append((level, text))


    def check_document(self, myfile):
        """Check for language
        """

        # May be this does not belong here
        self.iana_languages = load_languages()

        attr = myfile.tree.getroot().attrib

        # Get the document's language
        self.document_lang = attr.get('lang', None)
        self.document_xmllang = attr.get(XMLNS + 'lang')

        if myfile.xhtml == 0 and self.document_lang:
            languages = set([self.document_lang])
        elif myfile.xhtml != 0 and self.document_xmllang:
            languages = set([self.document_xmllang])
        else:
            languages = set()

        # Enumerate all languages found
        lang_set = set()
        xmllang_set = set()
        for element in myfile.tree.iter():
            # With the lang attribute
            if 'lang' in element.attrib:
                languages.add(element.attrib['lang'])
                lang_set.add(element)

            # With the xml:lang attribute
            if XMLNS+'lang' in element.attrib:
                languages.add(element.attrib[XMLNS+'lang'])
                xmllang_set.add(element)
                continue

        self.languages = list(languages)

        # Find elements with lang but not xml:lang
        self.missing_xmllang = []
        for element in lang_set - xmllang_set:
            self.missing_xmllang.append((element.sourceline, element.tag))

        # Find elements with xml:lang but not lang
        self.missing_lang = []
        for element in xmllang_set - lang_set:
            self.missing_lang.append((element.sourceline, element.tag))

        # Find elements with different values for xml:lang and lang
        self.different_lang = []
        if myfile.xhtml != 0:
            for element in xmllang_set & lang_set: # intersection of both sets
                if element.attrib['lang'] != element.attrib[XMLNS+'lang']:
                    self.different_lang.append((element.sourceline, element.tag))

        # Misc errors

        # Ensure there is only one h1.
        elements = myfile.tree.findall('//h1')
        self.num_h1 = len(elements)

        # Ensure not * inside <sup>, because * is already superscript
        self.stars_in_sup = []
        elements = myfile.tree.findall('//sup')
        for element in elements:
            if element.text and '*' in element.text:
                self.stars_in_sup.append(element.sourceline)

        # No inline style
        self.inline_style = []
        image_position = frozenset(["figcenter", "figleft", "figright"])
        elements = myfile.tree.findall('//*[@style]')
        for element in elements:
            # Ignore if it's a div with a figcenter/figleft/figright class
            # It's used to position an image in some documents
            myclass = element.attrib.get('class', None)
            if element.tag == 'div' and myclass is not None and (image_position & set(myclass.split(' '))):
                # One of the image_position style was found
                continue

            self.inline_style.append((element.sourceline, element.tag))

        # No empty td
#        elements = myfile.tree.findall('//td')
#        for element in elements:
#            # Check for no child and no text
#            if len(element) == 0 and not element.text:
#                print(str(element.sourceline) + ": found empty td")

        # Check what is just after a <sup> tag. It's likely an error.
        self.text_after_sup = []
        elements = myfile.tree.findall('//sup')
        for element in elements:
            # Check for no child and no text
            if element.tail and element.tail[0].isalpha():
                self.text_after_sup.append(element.sourceline)

        self.misc_regex_result = []

        # Try to find various strings in the text
        strings = [ ("unusual punctuation", "[,:;][!?]"),
                    ("[oE]->[oe], [OE] or œ", "[oE]"),
                    ("[Oe]->[oe], [OE] or Œ", "[Oe]"),
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
        for element in myfile.tree.find('body').iter():
            for desc, string in strings:
                if element.text and string in element.text:
                    self.misc_regex_result.append((desc, element.text, element.sourceline))
                if element.tail and string in element.tail:
                    self.misc_regex_result.append((desc, element.tail, element.sourceline))

        # Try various regexes on the text
        text = etree.XPath("string(//body)")(myfile.tree)
        regexes = [ ("mdash->ndash(?)", r"\d+--\d+"),
                    ("mdash->ndash(?)", r"[rv]\.--\d+"), # recto/verso

                    ("dash->ndash(?)", r"\d+-\d+"),
                    ("mdash->ndash(?)", r"\b[rv]\.—\d+"), # recto/verso

                    ("mdash->ndash(?)", r"\d+—\d+"),
                    ("mdash->ndash(?)", r"\b[rv]\.—\d+"), # recto/verso

                    (",letter", r",[^\W\d_]+"),
                    ("bad guiguts find/replace?", r"\$\d[^\d][^ ]*\s"),

                    ("PP tag?", r"\n(/[CFQRPTUX\*#]|[CFQRPTUX\*#]/).*(?=\n)"),
                    ]
        # Find all matches, and add them
        for desc, regex in regexes:
            m = re.findall(regex, text)
            if m is None:
                continue

            for match in m:
                self.misc_regex_result.append((desc, match, 0))


        # Ensure that quote types are not mixed. If straight quotes
        # are found, suggest curly quotes. Same for double quotes.
        self.misc_has_straight_quote = "'" in text
        self.misc_has_curly_quote = "’" in text
        self.misc_has_straight_dquote = '"' in text
        self.misc_has_curly_dquote = '“' in text or '”' in text


    def check_anchors(self, myfile):
        """Perform check on anchors: id must be equal to name, find
        undefined or unused anchors.
        """

        name_set = set()
        id_set = set()
        hrefs = set()

        self.different_id_name = []
        self.missing_name = []
        self.missing_id = []
        self.bad_hrefs = []

        # Ensure all 'a' have both a name and an id, and that they are identical
        # Inspect all 'a' for href/id/name and the other elements for id
        find = etree.XPath("/html/body//*")
        for element in find(myfile.tree):

            # Find id
            attr_id = element.attrib.get("id", None)
            if attr_id:
                id_set.add((element.sourceline, attr_id))

            if element.tag != 'a':
                # Not an anchor
                continue

            # Find href and name
            attr_href = element.attrib.get("href", None)
            if attr_href and attr_href[0] == '#':
                hrefs.add((element.sourceline, attr_href[1:]))

            attr_name = element.attrib.get("name", None)
            if attr_name:
                name_set.add((element.sourceline, attr_name))

            # Checks name and id present
            if attr_id and not attr_name:
                self.missing_name.append((element.sourceline, attr_id))

            if attr_name and not attr_id:
                self.missing_id.append((element.sourceline, attr_name))

            # If we have id and name, the must be the same
            if attr_id and attr_name and attr_id != attr_name:
                self.different_id_name.append((element.sourceline, attr_name, attr_id))

        if myfile.xhtml == 11:
            # XHTML 1.1 -- only id matters
            name_id_set = id_set
            self.missing_name = []

        elif myfile.xhtml == 10:
            # XHTML 1.0 -- id + name
            name_id_set = id_set

        else:
            # HTML - only name matters
            name_id_set = name_set
            self.missing_id = []


        # Find hrefs not referenced.
        # todo - There must be a more pythonic way to do that.
        for lineno, href in hrefs:
            for _, name in name_id_set:
                if name == href:
                    break
            else:
                # href was not found
                self.bad_hrefs.append((lineno, href))

        self.bad_hrefs = sorted(self.bad_hrefs)

        # todo - find anchor with name/id that have no corresponding href
        #  self.unused_anchors = name_id_set - hrefs
        self.unused_anchors = []
