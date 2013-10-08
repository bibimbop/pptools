=================================
COMP_PP - Compare 2 files for DP.
=================================


Introduction
------------

comp_pp can be used to compare 2 different files and generate an
exploitable output. Its goal is to look for discrepancies between the
text and html version produced at PGDP. However it can also be used to
compare a PGDP source with an external source (wikisource, ...) in
either text or html format.

The sources can be:

  - a text version or
  - an html version or
  - a text version coming from the P or F rounds or
  - a text/html coming from an external source (wikisource, internet, ...).

The text versions are identified by the .txt extension; the html by the
.htm or .html extension; and the Px or Fx version by its projectID
prefix.


Requirements
------------

comp_pp needs python 3 (not 2) to run, as well as the following
packages:

  - lxml
  - dwdiff             (http://os.ghalkes.nl/dwdiff.html)
  - python tinycss 0.3 (https://pypi.python.org/pypi/tinycss)
  - python cssselect   (https://pypi.python.org/pypi/cssselect)

Installation
------------

On Debian /  Ubuntu
~~~~~~~~~~~~~~~~~~~~

To install on Linux (Debian or Ubuntu):
::

  sudo apt-get install w3c-dtd-xhtml python3-lxml dwdiff

tinycss and cssselect are not present on these distributions yet for
python 3. Use pip to install them. Fist install pip for python3 if
it's not already installed:
::

  sudo apt-get install python3-pip

then install the missing packages:
::

  pip3 install tinycss
  pip3 install cssselect


On RedHat EL 6, CentOS 6, Scientific Linux 6
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Follow the procedures mentionned at

  http://linuxsysconfig.com/2013/03/running-multiple-python-versions-on-centos6rhel6sl6/

and

  http://wiki.centos.org/AdditionalResources/Repositories/RPMForge

to setup the PUIAS and RPMforge repositories.

Then install python 3 and dependencies:
::

  yum install python3  python3-tools  python3-devel
  yum install dwdiff

  wget http://python-distribute.org/distribute_setup.py
  python3 distribute_setup.py
  easy_install pip
  pip-3.3 install tinycss
  pip-3.3 install cssselect
  pip-3.3 install lxml
  pip-3.3 install roman
  pip-3.3 install cssutils
  pip-3.3 install jinja2

Note that pip requires gcc to build modules, so that may have to be installed too.


On Fedora 19
~~~~~~~~~~~~

To install, type:
::

  yum install python3  python3-tools  python3-devel dwdiff
  wget http://python-distribute.org/distribute_setup.py
  python3 distribute_setup.py
  easy_install pip
  pip-3.3 install tinycss
  pip-3.3 install cssselect
  yum install libxml2-devel libxslt-devel
  pip-3.3 install lxml
  pip-3.3 install roman
  pip-3.3 install cssutils
  pip-3.3 install jinja2


On anything else (Windows, OSX, ...)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No idea.


Usage
-----

Comparing two files is easy:
  **./comp_pp2.py file1.txt file2.html > result.html**
or
  **python comp_pp2.py file1.txt file2.html > result.html**

Internally, comp_pp will transform both files to make them closer to
each other. For instance, <i></i> in the html version will be
transformed to "_" so that will not generate a diff. Internally, a CSS transformation engine will take
care of the html. The transformations to a text version are currently
hardcoded.

Once both files are transformed, the diff happens (using dwdiff), then
its output is transformed into html. This html result is then sent to
the standard output where it can be redirected and finally loaded in a
browser. There is a small notice at the top explaining the diffs.

Footnotes
~~~~~~~~~

If the two versions have footnotes, but they are not placed in the
same spot (i.e. after each paragraph for the text, and at the end of
the book for the html), they can be extracted and compared separately:

  --extract-footnotes


Tuning
~~~~~~

By default, there is a few reasonnable rules applied to the html (See
the definition of self.mycss in the source code). However, it may be
necessary to go further in order to reduce the amount of noise.

Currently a few CSS targets are supported:
::

  :before  -- add a content before the tag
  :after   -- add a content after the tag

Some transformations are also supported:
::

  text-transform  -- transform the content to uppercase, lowercase or title
  _replace_with_attr -- replace the whole content with the value of an attribute
  text-replace    -- replace a string inside a content with another

Here are few command line arguments samples.

Illustrations
.............

If the diffs complain about a disppearing "Illustration" tag in the
html, add the following rule (adapt the CSS selector):
::

  --css '.figcenter:before { content: "[Illustration: "; }'
  --css '.figcenter:after { content: "]"; }'
  --css '.figcenter:before { content: "[Illustration: "; }'

Anchors
.......

By default anchors are expected to be surrounded by brackets. If it is
not the case in the html, this can be easily fixed with the following:

  --css '.fnanchor:before { content: "["; } .fnanchor:after { content: "]"; }'

Small caps
..........

Small caps can be transformed to look like the same in the text (upper
case). This can considerably reduce the noise in a document.

  --css '.smcap {  text-transform:uppercase; }'

Greek
.....

By default, if there is some greek and the text version has
transliterration only (i.e. it's in latin1), and if the html also has
the transliteration in the title attribute, the following is applied:
::

  --css 'body *[lang=grc] { _replace_with_attr: "title"; }'
  --css 'body *[lang=grc]:before, body *[lang=grc]:after { content: "+"; }'

Something like <p>φαγέδαινα</p> would become <p>+phagedaina+</p>
instead before the comparison takes place.

Footnotes
.........

In many document, the semantic of a footnote is html is lost because
they are put at the end of the file and look like any other
paragraph. A future version will add some extensions to deal with
that.








