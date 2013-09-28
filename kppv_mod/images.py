#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
 kppvh - image checking
"""

import os
import imghdr

class KImages(object):
    """Check images. """

    def __init__(self):
        self.coverpage = None
        self.coverpage_invalid_ext = False
        self.errors = []

    def check_images(self, myfile):
        """Inspect images and check whether the cover page is present.
        """

        images = []

        # Get images in <head>. Search for the coverpage at the same time
        links = myfile.tree.findall('/head/link')
        for link in links:
            if 'rel' in link.attrib and link.attrib['rel'] == 'coverpage':
                if 'href' not in link.attrib:
                    self.errors.append((link.sourceline , "found cover image without a href"))
                else:
                    images.append(link.attrib['href'])
                    if self.coverpage is None:
                        self.coverpage = link.attrib['href']
                    else:
                        self.errors.append((link.sourceline, "found more than one cover image in <head>"))

        # Find images in body's <img>. Search for the coverpage at the same time
        elements = myfile.tree.findall('//img')
        for img in elements:

            images.append(img.attrib['src'])

            if 'id' in img.attrib and img.attrib['id'] == 'coverpage':
                # Note: since it's a valid document, id 'coverpage'
                # can only exist once, so if coverpage is already
                # defined, it must be from the <head>
                if self.coverpage is None:
                    self.coverpage = img.attrib['src']
                else:
                    # Also declared in <head>. Ensure they are the same.
                    if self.coverpage != img.attrib['src']:
                        self.errors.append((img.sourceline, "different cover image declared than in the head (" + self.coverpage + " and " + img.attrib['src'] + ")"))


            # images should have a alt attribute but no title.
            #
            # hdmtrad: On nous demande une brève description pour «alt»
            # (principalement pour les versions audio éventuelles), mais
            # il n'est pas nécessaire de répéter la description dans
            # «title» (en «audio» on les entendrez deux fois). En
            # principe, nous ne mentionnons même plus le «title».
            if 'alt' not in img.attrib:
                self.errors.append((img.sourceline, "missing 'alt' attribute to 'img'"))
            elif len(img.attrib['alt']) > 40:
                self.errors.append((img.sourceline, "'alt' attribute too long? (" + str(len(img.attrib['alt'] > 40)) + " characters"))

            if "title" in img.attrib:
                 self.errors.append((img.sourceline, "'title' attribute found in 'img'. Remove?"))

        # Check whether coverpage in jpeg
        if self.coverpage:
            self.coverpage_invalid_ext = not self.coverpage.endswith(('.jpg', '.jpeg'))

        # Find images in body's <a>.
        elements = myfile.tree.findall('//a')
        for element in elements:
            try:
                image = element.attrib['href']
                if image.startswith('images/'):
                    images.append(image)
            except KeyError:
                continue

        # Check for the images, and extra images in the images directory
        for img in images:
            if not img.startswith('images/'):
                self.errors.append((0, "image " + img + " doesn't points to the images/ directory"))

        # Get the name of files in the images/ directory
        try:
            img_files = os.listdir(os.path.join(myfile.dirname, "images/"))
        except:
            img_files = []

        # Add images/ to every filename. set() also removes duplicate entries.
        img_files = [ "images/"+x for x in img_files]

        img_files_set = set(img_files)
        images_set = set(images)

        # Check extensions
        for img in img_files_set:
            imgtype = imghdr.what(os.path.join(myfile.dirname, img))

            if imgtype is None:
                 self.errors.append((0, "cannot detect image format for image " + img + "; is it really an image?"))

            elif imgtype not in [ 'jpeg', 'png', 'gif' ]:
                self.errors.append((0, "wrong(?) image format for image " + img + "; detected format is " + imgtype))

            elif ((imgtype == 'jpeg' and not img.endswith(('.jpg', '.jpeg'))) or
                (imgtype == 'png' and not img.endswith('.png')) or
                (imgtype == 'gif' and not img.endswith('.gif'))):
                self.errors.append((0, "wrong extension for image " + img + "; format is " + imgtype))

        for img in img_files_set - images_set:
            self.errors.append((0, "found extra image in images/ directory: " + img))

        for img in images_set - img_files_set:
            self.errors.append((0, "image " + img + " doesn't exist"))

        self.errors = sorted(self.errors)
