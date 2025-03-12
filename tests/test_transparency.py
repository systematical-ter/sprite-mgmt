import os
import sys
import shutil

sys.path.insert(1, os.path.join(sys.path[0], '..'))

import gifify
import spriterecolor

ref_img = "transparency_fixed_poc.png"

png_dir = "exported_data/char_tm_img/"
jsons_dir = "exported_data/char_tm_col/JSONs/"
names = ["tm300_03","tm300_04","tm300_05"]
tmpdir = "temp"

pal, tra = spriterecolor.get_palette_and_transparency(ref_img)
pngpaths = [os.path.join(png_dir, x) + ".png" for x in names]
os.makedirs(tmpdir)
for png in pngpaths :
    spriterecolor.apply_palette_to_img_and_save(png, pal, tra, tmpdir)

params = {
    "names": names,
    "img_dir": tmpdir,
    "clsn_dir": jsons_dir,
    "duration": 4,
    "hb": False,
    "mouth": True,
    "overwrite": True,
    "oformat": "PNG",
    "output": "test_transparency"
}

gifify._from_names(**params)

shutil.rmtree(tmpdir)