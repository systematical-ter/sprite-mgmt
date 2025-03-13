import os
import sys
import shutil

sys.path.insert(1, os.path.join(sys.path[0], '..'))

import gifify
import spriterecolor

ref_img = "transparency_fixed_poc.png"

png_dir = "exported_data/char_tm_img/"
jsons_dir = "exported_data/char_tm_col/JSONs/"
tmpdir = "temp"
names = ["tm030_%sex" % str(x).zfill(2) for x in range(2,11)]

pal, tra = spriterecolor.get_palette_and_transparency(ref_img)
pngpaths = [os.path.join(png_dir, x) + ".png" for x in names]
os.makedirs(tmpdir)
for png in pngpaths :
    spriterecolor.apply_palette_to_img_and_save(png, pal, tra, tmpdir)

names = ["tm030_%sex01" % str(x).zfill(2) for x in range(2,11)]

params = {
    "names" : names,
    "img_dir" : tmpdir,
    "clsn_dir" : jsons_dir,
    "duration": 5,
    "hb": False,
    "overwrite": True,
    "oformat": "GIF",
    "mouth": True,
    "flip_y" : True,
    "output": "tests/test_alternate_flipped"
}

gifify._draw_from_names(**params)

shutil.rmtree(tmpdir)