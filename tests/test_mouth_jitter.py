import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

import gifify

png_dir = "exported_data/char_tm_img/"
jsons_dir = "exported_data/char_tm_col/JSONs/"
names = ["tm300_03","tm300_04","tm300_05"]
#names = ["tm000_0%i" % x for x in range(0,9)]
#names = ["tm001_0%i" % x for x in range(0,9)]
#names = ["tm010_0%i" % x for x in range(0,10)]
#names = ["tm201_0%i" % x for x in range(0,8)]

params = {
    "pngpaths": [os.path.join(png_dir, x) + ".png" for x in names],
    "jsonpaths": [os.path.join(jsons_dir, x) + ".json" for x in names],
    "duration": 3,
    "hb": True,
    "overwrite": True,
    "oformat": "PNG",
    "output": "test_jitter.png"
}
#params["duration"] = [3]*len(params["jsonpaths"])

gifify._from_given_paths(**params)