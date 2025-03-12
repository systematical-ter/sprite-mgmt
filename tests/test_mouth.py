import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))
import gifify

png_dir = "exported_data/char_tm_img/"
jsons_dir = "exported_data/char_tm_col/JSONs/"
names = ["tm300_03","tm300_04","tm300_05"]

params = {
    "names" : names,
    "img_dir" : png_dir,
    "clsn_dir" : jsons_dir,
    "duration": 4,
    "hb": False,
    "overwrite": True,
    "oformat": "PNG",
    "mouth": True,
    "output": "tests/test_mouth"
}

gifify._from_names(**params)