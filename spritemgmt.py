from typing import List
from PIL import Image
import spriterecolor
import gifify
import os

names = ["tm201_0" + str(i) for i in range(0,8)]
params_spriterecolor = {
"reference"   : "transparency_fixed_poc.png",
"names"             : 
    [os.path.join("exported_data/char_tm_img", x + ".png") for x in names],
}

pal, tra = spriterecolor.get_palette_and_transparency(params_spriterecolor["reference"])
recolored: List[Image.Image] = spriterecolor._apply_specific_images_IMG(params_spriterecolor["names"], pal, tra)
named_dict = {}
for i in range(0, len(names)) :
    named_dict[names[i]] = recolored[i]

params_gifify = {
"names"             : names,
"imgs"              : named_dict,
"clsn_dir"          : "exported_data/char_tm_col/JSONs",
"hb"                : False,
"mouth"             : True,
"duration"          : 4,
"overwrite"         : True,
"oformat"           : "GIF",
"output"            : "tests/test_spritemgmt"
}

gifify._from_recolored_pngs(**params_gifify)