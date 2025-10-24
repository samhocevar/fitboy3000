#!/usr/bin/env python

from sys import argv, exit
from math import ceil
from io import BytesIO
from swf.movie import SWF
from swf.export import SVGExporter, FrameSVGExporterMixin
import skia 
from PIL import Image

def find_game_file(appid, asset):
    STEAM_REG_KEY = r'SOFTWARE\Valve\Steam'
    STEAM_REG_ENTRY = 'InstallPath'

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
                if appid in d['apps']:
                    steamlib = d['path']
        with open(f'{steamlib}/steamapps/appmanifest_{appid}.acf') as f:
            data = vdf.parse(f)
            installdir = data['AppState']['installdir']
    except:
        print(f'Error: could not find game #{appid} installation in the Steam files')
        raise()

    return f'{steamlib}/steamapps/common/{installdir}/{asset}'

def get_archive_swf(path, name):
    from bethesda_structs.archive.btdx import BTDXArchive
    archive = BTDXArchive.parse_file(path)
    for f in archive.iter_files():
        if f.filepath.name == name:
            return SWF(BytesIO(f.data))

def render_swf_frames(swf, frames):
    class SVGFrameExporter(FrameSVGExporterMixin, SVGExporter):
        pass
    exporter = SVGFrameExporter()
    width, height = 0, 0
    for f in frames:
        svgdata = exporter.export(swf, f).read()
        # Grow surface for next bitmap
        newsurface = skia.Surface(width + ceil(exporter.bounds.width), max(height, ceil(exporter.bounds.height)))
        with newsurface as canvas:
            canvas.clear(0xff000000)
            if width != 0:
                canvas.drawImage(surface.makeImageSnapshot(), 0, 0)
            canvas.translate(width, 0)
        surface = newsurface
        width, height = surface.width(), surface.height()
        # Blit new frame
        svgstream = skia.MemoryStream.MakeDirect(svgdata)
        svg = skia.SVGDOM.MakeFromStream(svgstream)
        with surface as canvas:
            svg.render(canvas)

    # Return surface as 4-color image
    with BytesIO(surface.makeImageSnapshot().encodeToData()) as pixels:
        img = Image.open(pixels)
        #img.quantize(4)
        #img.putpalette([255] * 3 + [0] * 3)
        return img.convert('P', palette=Image.ADAPTIVE, colors=4)

# Find the game file that has our data
archive = find_game_file('377160', 'Data/Fallout4 - Interface.ba2')
#archive = find_game_file('1151340', 'Data/SeventySix - Interface.ba2') # Not supported by bethesda-structs yet

body = get_archive_swf(archive, 'Condition_Body_0.swf')
head = get_archive_swf(archive, 'Condition_Head.swf')

# Create the body data
assert(body.header.frame_count == 32)
img = render_swf_frames(body, [n * 4 for n in range(8)])
img.save('body.png')

# Create the head data
print('\n'.join(map(str, head.tags)))
img = render_swf_frames(head, [0, 1, 8])
img.save('head.png')
