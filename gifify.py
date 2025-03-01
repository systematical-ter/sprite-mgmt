from typing import List, Tuple
from PIL import Image, ImageFile, ImageDraw
import os
import spriterecolor
import json


type bbox = Tuple[int, int, int, int]
type relbox = Tuple[int, int, int, int]

idirectory = "exported_data/char_tm_img/"
mdirectory = "exported_data/char_tm_col/JSONs/"

mode = "backthrowex"

if mode == "groundex" :
    # 5b
    images = ["tm201_0" + str(i) + ".png" for i in range(0,8)]
    metadata = ["tm201_0" + str(i) + ".json" for i in range(0,8)]
elif mode == "airex" :
    # air dp
    images = ["tm432_" + str(i) + ".png" for i in range(25,29)]
    metadata = ["tm432_" + str(i) + ".json" for i in range(25,29)]
elif mode == "airthrowex" :
    # air throw
    images = ["tm321_0" + str(i) + ".png" for i in range(2,7)]
    metadata = ["tm321_0" + str(i) + ".json" for i in range(2,7)]
elif mode =="backthrowex" :
    # back throw
    images = ["tm313_%s.png" % str(i).zfill(2) for i in range(0,14)]
    metadata = ["tm313_%s.json" % str(i).zfill(2) for i in range(0,14)]


palette_img = Image.open("transparency_fixed_poc.png")

# get palette + transparency
p, t = spriterecolor.get_palette_and_transparency("transparency_fixed_poc.png")

# load images and then apply our palette
l_i = [Image.open(os.path.join(idirectory,i)) for i in images]
l_pi = [spriterecolor._apply_palette(i, p, t).convert("RGBA") for i in l_i]

class img_metadata() :
    hitbox_count: int
    hurtbox_count: int

    canvas_w: int
    canvas_h: int
    
    center_x: int
    center_y: int

    img : ImageFile

    def __init__(self, jdict, img) :
        self.hitbox_count = jdict["Header"]["hitboxCount"]
        self.hurtbox_count = jdict["Header"]["hurtboxCount"]

        # ignoring mouths and secondary chunks for now.
        c = jdict["Chunks"][0]
        self.canvas_w = c["Width"]
        self.canvas_h = c["Height"]

        # X,Y of the centerpoint dot are stored in relation to canvas width and height (for some reason)
        #   so we get the center by adding them.
        self.center_x = self.canvas_w + c["X"]
        self.center_y = self.canvas_h + c["Y"]

        self.img = img

    def get_bounding_relbox(self) -> relbox:
        x, y, dx, dy = self.img.getbbox()
        if x > self.center_x :
            x = self.center_x
        if y > self.center_y :
            y = self.center_y

        bbox = (x,y,dx,dy)
        return self.bbox_to_relbox(bbox)
    
    def crop_to_box(self, bb: relbox) -> None :
        bb = self.relbox_to_bbox(bb)
        self.img = self.img.crop(bb)

    def draw_box(self, bb:relbox) -> None :
        bb = self.relbox_to_bbox(bb)
        i = ImageDraw.Draw(self.img)
        i.rectangle([(bb[0],bb[1]),(bb[2],bb[3])], fill=None, outline="red")

    def relbox_to_bbox(self, bb:relbox) -> bbox :
        return (bb[0] + self.center_x, bb[1] + self.center_y, 
                bb[2] + self.center_x, bb[3] + self.center_y)
    
    def bbox_to_relbox(self, bb:bbox) -> relbox :
        return (bb[0] - self.center_x, bb[1] - self.center_y,
                bb[2] - self.center_x, bb[3] - self.center_y)

    def __str__(self):
        output = "IMAGE OBJECT\n"
        output += "\tHITBOXES: %i\n" % self.hitbox_count
        output += "\tHURTBOXES: %i\n" % self.hurtbox_count
        output += "\tWIDTH: %i\n" % self.canvas_w
        output += "\tHEIGHT: %i\n" % self.canvas_h
        output += "\tCENTER_X: %i\n" % self.center_x
        output += "\tCENTER_Y: %i\n" % self.center_y
        return output
    
def get_maximal_bb(bbs: List[relbox]) -> relbox:
    x,y,dx,dy = 500,500,0,0
    for bb in bbs :
        if bb[0] < x :
            x = bb[0]
        if bb[1] < y :
            y = bb[1]
        if bb[2] > dx :
            dx = bb[2]
        if bb[3] > dy :
            dy = bb[3]
    return (x,y,dx,dy)

# get metadata for each image
l_m: List[img_metadata] = []
for i,m in enumerate(metadata):
    with open(os.path.join(mdirectory, m)) as f:
        l_m.append(img_metadata(json.load(f), l_pi[i]))

# TODO : crop out empty space at the top?
# TODO : test on vertical movement.
maxbb: relbox = get_maximal_bb([o.get_bounding_relbox() for o in l_m])
for o in l_m :
#    o.draw_box(maxbb)
    o.crop_to_box(maxbb)
l_output = [o.img for o in l_m]
l_output[0].save("test.gif", format="GIF", save_all=True, append_images=l_output[1:], duration=16, disposal=2, loop=0, transparency=0)