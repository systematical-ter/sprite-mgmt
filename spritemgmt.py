from typing import List
from PIL import Image
import spriterecolor
import gifify
import os

params_spriterecolor = {
"reference"   : "transparency_fixed_poc.png",
"names"             : 
    [os.path.join("exported_data/char_tm_img", "tm201_0" + str(i)) + ".png" 
    for i in range(0,8)],
}

pal, tra = spriterecolor.get_palette_and_transparency(params_spriterecolor["reference"])
recolored: List[Image.Image] = spriterecolor._spec_ret_IMG(params_spriterecolor["names"], pal, tra)

params_gifify = {
"names"             : ["tm201_0" + str(i) for i in range(0,8)],
"images"            : recolored,
"durations"         : 5,
"hitboxes"          : True
}

frames: List[Image.Image] = gifify._make_manual(**params_gifify)
frames[0].save("tool.gif", format="GIF", save_all=True, append_images=frames[1:], duration=16, disposal=2, loop=0, transparency=0)

