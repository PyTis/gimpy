"""
example map file:
    <img src="document3.png" width="3825" height="4950" border="0" usemap="#map" />

    <map name="map">
    <!-- #$-:Image Map file created by GIMP Imagemap Plugin -->
    <!-- #$-:GIMP Imagemap Plugin by Maurits Rijk -->
    <!-- #$-:Please do not edit lines starting with "#$" -->
    <!-- #$VERSION:2.0 -->
    <!-- #$AUTHOR:jlee -->
    <area shape="rect" coords="633,1243,1119,1367" href="full_name" />
    <area shape="rect" coords="2996,1264,3359,1369" href="date" />
    </map>


href = entity
coords = xstart, ystart, xend, yend (we care about xstart and yend)
target = font, fontsize
if one or the other, font or fontsize, is specifed then both must be specified.
Please do not use this directly, use gimPy.

"""


import os, binascii, datetime
from cStringIO import StringIO

from util import MapHTMLParser


class MapToPython(object):
    prog_name = 'gimPy, MapToPython'
    top_comment = '''#!/usr/bin/python2.4
"""
This file was auto generated by '%(name)s' on %(datestamp)s

USAGE
    if __name__ == '__main__':
        # Example Useage
        client = dict()
        x = %(name)s(ds=client)
        x.draw()

"""

import os, binascii, tempfile
from cStringIO import StringIO

# Note, you must have report lab installed
from reportlab.pdfgen import canvas

''' % dict(name=prog_name, datestamp=datetime.datetime.now().strftime('%Y%m%d'))
    ###########################################################################
    def __init__(self, path, my_name, map_source, img_source=None, dpi=150,
                 fontname=None, fontsize=None):
        file_name = "%s.py" % os.path.abspath(os.path.join(path,my_name))
        f = open(file_name, 'w')
        f.write(self.top_comment)
        f.write(self.startClass(my_name, map_source,dpi,fontname,fontsize))
        f.write(self.getInit(my_name))
        f.write(self.getPreRender(dpi))
        f.write(self.getDraw(img_source, map_source))
        f.write(self.getRender())
        if img_source is not None:  f.write(self.getImage(img_source, map_source))
        f.write(self.closeClass(my_name))
        f.close()
        self.cleanFile(file_name)

    ###########################################################################
    def cleanFile(self, file_name):
        f = open(file_name, 'r')
        contents = f.readlines(-1)
        f.close()
        f = open(file_name, 'w')
        [f.write(c.replace("\t", "    ")) for c in contents]
        f.close()

    ###########################################################################
    def startClass(self, my_name, map_source,dpi,default_fontname, default_fontsize):
        areas = map_source['areas']
        area_list = []
        for area in areas:
            if area['shape'] == "rect":
                coords = area['coords'].split(',')
                text = area['href']
                target = None
                if 'target' in area:
                    target = area['target'].split(',')
                    fontname = "'%s'" % target[0]
                    fontsize = target[1]
                else:
                    fontname = None
                    fontsize = None
                x = int(coords[0])
                y = int(coords[3])
                item = "{'item' : '%s', 'x' : %s, 'y' : %s, 'fontsize' : %s, 'fontname' : %s}"
                area_list.append(item % (text,x,y,fontsize,fontname))
        if default_fontname == None or default_fontname == '':
            default_fontname = None
        else:
            default_fontname = "'%s'" % default_fontname
        return """
class %(class_name)s(object):
    height_adjust = 0
    page_width = 8.5
    page_height = 11
    dpi = %(dpi)s
    fontname = %(fontname)s
    fontsize = %(fontsize)s
    areas = [
        %(areas)s
            ]
""" % dict(class_name=my_name, dpi=dpi, areas=",\n\t\t".join(area_list),
            fontname=default_fontname, fontsize=default_fontsize)


    ###########################################################################
    def getInit(self, my_name):
        file_name =  "%s.pdf" % my_name

        return """
    def __init__(self, file_name='%(fn)s', ds={}, my_canvas=None):
        if my_canvas is None:
            self.my_canvas = canvas.Canvas(file_name, #(destination_file)
                pagesize=(72 * self.page_width,72 * self.page_height))
        else:
            self.my_canvas = my_canvas
        self.ds = ds

        # Store old font stuff
        old_fontname = self.my_canvas._fontname
        old_fontsize = self.my_canvas._fontsize

        # Grab new font name
        if self.fontname is None:
            new_fontname = old_fontname
        else:
            new_fontname = self.fontname

        # Grab new font size
        if self.fontsize is None:
            new_fontsize = old_fontsize
        else:
            new_fontsize = self.fontsize

        # Set font stuff
        self.my_canvas.setFont('%%s' %% new_fontname, new_fontsize)
""" % dict(fn = file_name,)

    ###########################################################################
    def getImage(self, img_source,map_source):
        image = map_source['image']
        iname = image['src']
        return """
    def getBackGround(self):
       out = %(image)s
       img_src = binascii.a2b_base64(out)
       self.tmp_dir = tempfile.mkdtemp()
       self.tmp_img = '%(date)s_%(fname)s'
       handle = os.path.join(self.tmp_dir, self.tmp_img)
       f = open(handle, 'w')
       f.write(img_src)
       f.close()
       return handle

""" % dict(image=img_source,date=datetime.datetime.now().strftime('%Y%m%d'),fname=iname)

    ###########################################################################
    def getPreRender(self,dpi):
        return """
    def preRender(self):
        for area in self.areas:
            x = (72 * int(area['x'])) / int(self.dpi)
            y = (72 * self.page_height) - ((72 * int(area['y'])) / int(self.dpi))
            item = self.ds[area['item']]
            fontname = area['fontname']
            fontsize = area['fontsize']

            if callable(self.ds[area['item']]):
                self.ds[area['item']](self.my_canvas, area)
            else:
                if not item:
                    item = ''
                if fontname is not None or fontsize is not None:
                    old_fontname = self.my_canvas._fontname
                    old_fontsize = self.my_canvas._fontsize

                    if fontname is None:
                        new_fontname = old_fontname
                    else:
                        new_fontname = area['fontname']

                    if fontsize is None:
                        new_fontsize = old_fontsize
                    else:
                        new_fontsize = area['fontsize']

                    self.my_canvas.setFont('%s' % new_fontname, new_fontsize)
                    self.my_canvas.drawString(x,y,'%s' % item)
                    self.my_canvas.setFont('%s' % old_fontname, old_fontsize)
                    if item is None:
                        item = ''
                else:
                    self.my_canvas.drawString(x,y,'%s' % item)

"""
    ###########################################################################
    def getDraw(self, image_map, map_source):
        if image_map is not None:
            image = map_source['image']
            height = int(image['height'])
            width = int(image['width'])
            call_to_image = """
        new_width = 72 * self.page_width
        new_height = 72 * self.page_height
        self.my_canvas.drawInlineImage(self.getBackGround(),
                                 0, 0 + self.height_adjust,
                                 width=new_width,
                                 height=new_height)
""" % dict(width=width, height=height)
        else:
            call_to_image = ""

        return """
    def draw(self):
        %s
        self.preRender()
        os.unlink(os.path.abspath(os.path.join(self.tmp_dir,self.tmp_img)))
        os.rmdir(os.path.abspath(self.tmp_dir))
        self.my_canvas.showPage()
        return self.my_canvas
""" % call_to_image

    ###########################################################################
    def getRender(self):
        return """
    def render(self):
        self.draw()
        self.my_canvas.save()
"""
    def closeClass(self, my_name):
        return """
if __name__ == '__main__':
    # Test Data

    class default_dict(dict):
        def __init__(self, other={}, default=None):
            dict.__init__(self, other)
            self.default = default

        def __getitem__(self, key):
            try:
                return dict.__getitem__(self, key)
            except KeyError:
                return self.default
    x = %(class_name)s(ds=default_dict(default='Test'))
    x.render()
""" % dict(class_name=my_name)
    ###########################################################################
    # End of MapToPython


###############################################################################
# Helper functions

def get_xml_from_file(file):
    f = open(file)
    lines = f.readlines(-1)
    f.close()
    return lines

def process_xml(source):
    hp = None
    hp = MapHTMLParser()
    [hp.feed(line) for line in source]
    maps = hp.getMaps()
    hp.reset()
    hp.close()
    return maps


def towidth(input, width=80):
    assert width > 0
    idx = -1
    cbuf = StringIO()
    for c in input:
        idx = idx + 1
        if idx % width == 0:
            if cbuf.getvalue():
                yield cbuf.getvalue()
            cbuf = StringIO()
        cbuf.write(c)
    if cbuf.getvalue():
        yield cbuf.getvalue()


def image_source(image):
    f = open(os.path.abspath(image))
    dat = f.read(-1)
    asci_dat = binascii.b2a_base64(dat)
    code = towidth(asci_dat, 160)
    code = [c.replace('"', r'\"').replace("\n", r"\n") for c in code]
    code = ['"%s"' % c for c in code]
    return "(%s)" % "\n".join(code)
