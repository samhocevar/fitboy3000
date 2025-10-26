#!/usr/bin/env python

from sys import argv, exit
from math import ceil, floor
from io import BytesIO
from swf.movie import SWF
from swf.export import SVGExporter, SVGBounds, FrameSVGExporterMixin
import swf.tag as SWFTag
import skia 
from PIL import Image


#
# This is stuff that we know beforehands, and should be enough to let us
# extract the data and generate all the bitmap assets.
#

# Registry key to know where Steam is installed
STEAM_REG_KEY = r'SOFTWARE\Valve\Steam'
STEAM_REG_ENTRY = 'InstallPath'

# The Steam app id and the game file we are looking for
GAME_STEAMID = 377160
GAME_DATAFILE = 'Data/Fallout4 - Interface.ba2'

# This could work as a fallback, but bethesda_structs cannot parse these (yet?)
ALT_STEAMID = 1151340
ALT_DATAFILE = 'Data/SeventySix - Interface.ba2'

# The names of the body and head assets inside the game file, and the frames we want
SWF_BODY_FILE = 'Condition_Body_0.swf'
SWF_HEAD_FILE = 'Condition_Head.swf'
SWF_BODY_FRAMES = [0, 4, 8, 12, 16, 20, 24, 28]
SWF_HEAD_FRAMES = [0, 1, 8]


#
# Now do the work
#

class SWFToSVGFrameExporter(FrameSVGExporterMixin, SVGExporter):
    def __init__(self, swf):
        super(SWFToSVGFrameExporter, self).__init__()
        self.swf = swf

    def get_frame(self, f):
        svgdata = self.export(self.swf, f).read()
        bounds = SVGBounds(self.svg)
        anchors = {t.instanceName: t.matrix for t in self.get_display_tags(self.swf.tags) if t.instanceName}
        return svgdata, bounds, anchors


def find_game_file(appid, asset):
    # Find Steam installation directory
    try:
        from winreg import OpenKey, QueryValueEx, HKEY_LOCAL_MACHINE, KEY_READ, KEY_WOW64_32KEY
        k = OpenKey(HKEY_LOCAL_MACHINE, STEAM_REG_KEY, 0, KEY_READ | KEY_WOW64_32KEY)
        steamdir, _ = QueryValueEx(k, STEAM_REG_ENTRY)
    except:
        print(f'Error: could not find Steam installation in the registry')
        raise()

    # Find game installation directory
    try:
        import vdf
        with open(f'{steamdir}/steamapps/libraryfolders.vdf') as f:
            data = vdf.parse(f)
            for d in data['libraryfolders'].values():
                if str(appid) in d['apps']:
                    steamlib = d['path']
        with open(f'{steamlib}/steamapps/appmanifest_{appid}.acf') as f:
            data = vdf.parse(f)
            installdir = data['AppState']['installdir']
    except:
        print(f'Error: could not find game #{appid} installation in the Steam files')
        raise()

    return f'{steamlib}/steamapps/common/{installdir}/{asset}'


def extract_swf(path, name):
    from bethesda_structs.archive.btdx import BTDXArchive
    archive = BTDXArchive.parse_file(path)
    return next(SWF(BytesIO(f.data)) for f in archive.iter_files() if f.filepath.full_match(f'**/{name}'))


def render_swf_frames(swf, frames, scale):
    exporter = SWFToSVGFrameExporter(swf)
    coords = []
    width, height = 0, 0
    for f in frames:
        svgdata, bounds, anchors = exporter.get_frame(f)
        for k, v in anchors.items():
            print(f'Frame #{f} has anchor {k} at {floor(v.translateX * scale / 20)},{floor(v.translateY * scale / 20)}')
        # Grow surface for the next frame
        sw, sh = ceil(bounds.width * scale), ceil(bounds.height * scale)
        sx, sy = floor(bounds.minx * scale), floor(bounds.miny * scale)
        coords.append((width, 0, sw, sh, sx, sy))
        newsurface = skia.Surface(width + sw, max(height, sh))
        with newsurface as canvas:
            canvas.clear(0xff000000)
            if width != 0:
                canvas.drawImage(surface.makeImageSnapshot(), 0, 0)
            canvas.translate(width, 0)
            canvas.scale(scale, scale)
        surface = newsurface
        width, height = surface.width(), surface.height()
        # Blit new frame
        svgstream = skia.MemoryStream.MakeDirect(svgdata)
        svg = skia.SVGDOM.MakeFromStream(svgstream)
        with surface as canvas:
            svg.render(canvas)

    # Convert surface to an image
    with BytesIO(surface.makeImageSnapshot().encodeToData()) as pixels:
        img = Image.open(pixels)
        # Quantise to 4 colors, it does decent antialiasing without using too much memory
        pal = Image.new('L', (1, 1))
        pal.putpalette((0, 0, 0, 85, 85, 85, 150, 150, 150, 255, 255, 255))
        img = img.convert('RGB').quantize(palette=pal, dither=Image.Dither.NONE)

    return img, coords


# Find the game file that has our data
datafile = find_game_file(GAME_STEAMID, GAME_DATAFILE)
body = extract_swf(datafile, SWF_BODY_FILE)
head = extract_swf(datafile, SWF_HEAD_FILE)

#get_swf_frames(body)

# Create the body data
assert(body.header.frame_count == 32)
img, c1 = render_swf_frames(body, SWF_BODY_FRAMES, 0.8)
img.save('body.png')

# Create the head data
#print('\n'.join(map(str, head.tags)))
img, c2 = render_swf_frames(head, SWF_HEAD_FRAMES, 0.8)
img.save('head.png')

with open('body.fnt', '+w') as f:
    f.write(f'info face="Fit-Boy" size=120 bold=0 italic=0 charset="" unicode=1 stretchH=100 smooth=1 aa=4 padding=0,0,0,0 spacing=1,1 outline=0\n')
    f.write(f'common lineHeight=140 base=64 scaleW=300 scaleH=300 pages=2 packed=0 alphaChnl=0 redChnl=0 greenChnl=0 blueChnl=0\n')
    f.write(f'page id=0 file="body.png"\n')
    f.write(f'page id=1 file="head.png"\n')
    f.write(f'chars count=8\n')
    xoff = min(c[4] for c in c1)
    yoff = min(c[5] for c in c1)
    print('xoff/yoff', xoff, yoff)
    for n, c in enumerate(c1):
        x, y, sw, sh, sx, sy = c
        f.write(f'char id={ord("0")+n} x={x} y={y} width={sw} height={sh} xoffset={sx-xoff} yoffset={sy-yoff} xadvance=100 page=0 chnl=15\n')
    xoff = min(c[4] for c in c2)
    yoff = min(c[5] for c in c2)
    print('xoff/yoff', xoff, yoff)
    for n, c in enumerate(c2):
        x, y, sw, sh, sx, sy = c
        f.write(f'char id={ord("a")+n} x={x} y={y} width={sw} height={sh} xoffset={sx-xoff} yoffset={sy-yoff} xadvance=100 page=1 chnl=15\n')

