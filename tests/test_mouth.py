import os
import sys
import json
from PIL import Image

sys.path.insert(1, os.path.join(sys.path[0], '..'))
import gifify

# json_l = "tests/taunt_test/tm300_03.json"
# png = "tests/taunt_test/tm300_03.png"

# json_r = {}
# with open(json_l, 'r') as f:
#     json_r = json.load(f)

# img_r = Image.open(png)

# spr = gifify.Sprite(json_r, img_r, 3)
# print(spr.has_mouth)

# x = int(spr.offset_x + spr.mouth_x)
# y = int(spr.offset_y + spr.mouth_y)

# tmp_image = Image.new("RGBA", spr.img.size)
# tmp_image.paste(spr.mouth_img, (x,y))
# spr.img.alpha_composite(tmp_image)
# spr.img.paste(spr.mouth_img)
# spr.img.save("tests/mouthtest.png")


png_dir = "exported_data/char_tm_img/"
jsons_dir = "exported_data/char_tm_col/JSONs/"
names = ["tm300_03","tm300_04","tm300_05"]
names = ["tm300_%s" % str(x).zfill(2) for x in range(0,10)]
#names = ["tm000_0%i" % x for x in range(0,9)]
#names = ["tm001_0%i" % x for x in range(0,9)]
#names = ["tm010_0%i" % x for x in range(0,10)]
#names = ["tm201_0%i" % x for x in range(0,8)]

params = {
    "pngpaths": [os.path.join(png_dir, x) + ".png" for x in names],
    "jsonpaths": [os.path.join(jsons_dir, x) + ".json" for x in names],
    "duration": 4,
    "hb": False,
    "overwrite": True,
    "oformat": "PNG",
    "output": "tests/test_mouth.png"
}
#params["duration"] = [3]*len(params["jsonpaths"])

gifify._from_given_paths(**params)