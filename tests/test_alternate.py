import os
import sys
import shutil

sys.path.insert(1, os.path.join(sys.path[0], '..'))

import gifify
import spriterecolor

ref_img = "transparency_fixed_poc.png"

png_dir = "exported_data/char_tm_img/"
jsons_dir = "exported_data/char_tm_col/JSONs/"
#names = ["tm300_03","tm300_04","tm300_05"]
tmpdir = "temp"
#names = ["tm000_0%i" % x for x in range(0,9)]
#names = ["tm001_0%i" % x for x in range(0,9)]
#names = ["tm010_0%i" % x for x in range(0,10)]
#names = ["tm201_0%i" % x for x in range(0,8)]
names = ["tm030_%sex" % str(x).zfill(2) for x in range(2,11)]

pal, tra = spriterecolor.get_palette_and_transparency(ref_img)
pngpaths = [os.path.join(png_dir, x) + ".png" for x in names]
os.makedirs(tmpdir)
for png in pngpaths :
    spriterecolor.apply_palette_to_img_and_save(png, pal, tra, tmpdir)

params = {
    "pngpaths": [os.path.join(tmpdir, x) + ".png" for x in names],
    "jsonpaths": [os.path.join(jsons_dir, x) + "01.json" for x in names],
    "duration": 5,
    "hb": False,
    "overwrite": True,
    "oformat": "GIF",
    "output": os.path.join("tests","test_alternate.gif")
}

gifify._from_given_paths(**params)

shutil.rmtree(tmpdir)