from typing import List, Tuple
from PIL import Image, ImageFile, ImageDraw
import os
import spriterecolor
import json


Bbox = Tuple[int, int, int, int]
Relbox = Tuple[int, int, int, int]

idirectory = "exported_data/char_tm_img/"
mdirectory = "exported_data/char_tm_col/JSONs/"

draw_hitboxes: bool = False

mode = "theyeet"

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
elif mode =="theyeet" :
    # 6c
    images = ["tm213_%s.png" % str(i).zfill(2) for i in range(0,24)]
    metadata = ["tm213_%s.json" % str(i).zfill(2) for i in range(0,24)]


# get palette + transparency
p, t = spriterecolor.get_palette_and_transparency("palette_ref.png")

# load images and then apply our palette
l_i = [Image.open(os.path.join(idirectory,i)) for i in images]
l_pi = [spriterecolor._apply_palette(i, p, t).convert("RGBA") for i in l_i]

class Hurtbox() :
    w: int
    h: int
    c_x: int
    c_y: int

    def __init__(self, X,Y,Width,Height, **kwargs) :
        self.w = Width
        self.h = Height
        self.c_x = X
        self.c_y = Y

class img_metadata() :
    hitbox_count: int
    hurtbox_count: int

    canvas_w: int
    canvas_h: int
    
    center_x: int
    center_y: int

    img : ImageFile

    hurtboxes: List[Hurtbox]
    hitboxes: List[Hurtbox]

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

        self.hurtboxes = []
        for hurtbox in jdict["Hurtboxes"] :
            self.hurtboxes.append(Hurtbox(**hurtbox))
        
        self.hitboxes = []
        for hitbox in jdict["Hitboxes"] :
            self.hitboxes.append(Hurtbox(**hitbox))


    def get_bounding_relbox(self) -> Relbox:
        x, y, dx, dy = self.img.getbbox()
        if x > self.center_x :
            x = self.center_x
        if y > self.center_y :
            y = self.center_y

        bbox = (x,y,dx,dy)
        return self.bbox_to_relbox(bbox)
    
    def crop_to_box(self, bb: Relbox) -> None :
        bb = self.relbox_to_bbox(bb)
        self.img = self.img.crop(bb)

    def draw_box(self, bb:Relbox) -> None :
        bb = self.relbox_to_bbox(bb)
        i = ImageDraw.Draw(self.img)
        i.rectangle([(bb[0],bb[1]),(bb[2],bb[3])], fill=None, outline="red")

    def relbox_to_bbox(self, bb:Relbox) -> Bbox :
        return (bb[0] + self.center_x, bb[1] + self.center_y, 
                bb[2] + self.center_x, bb[3] + self.center_y)
    
    def bbox_to_relbox(self, bb:Bbox) -> Relbox :
        return (bb[0] - self.center_x, bb[1] - self.center_y,
                bb[2] - self.center_x, bb[3] - self.center_y)

    def draw_hitboxes(self) -> None :
        TINT_COLOR=(255,0,0)
        TRANSPARENCY = .3
        OPACITY= int(255*TRANSPARENCY)

        overlay = Image.new('RGBA', self.img.size, TINT_COLOR+(0,))
        draw = ImageDraw.Draw(overlay)

        for hb in self.hitboxes :
            tl_x = self.canvas_w - (self.center_x - hb.c_x)
            tl_y = self.canvas_h - (self.center_y - hb.c_y)
            draw.rectangle([(tl_x, tl_y), (tl_x + hb.w, tl_y + hb.h)], fill=TINT_COLOR+(OPACITY,), outline="red")
        
        self.img = Image.alpha_composite(self.img, overlay)
    
    def draw_hurtboxes(self) -> None :
        TINT_COLOR=(0,0,255)
        TRANSPARENCY = .3
        OPACITY= int(255*TRANSPARENCY)

        overlay = Image.new('RGBA', self.img.size, TINT_COLOR+(0,))
        draw = ImageDraw.Draw(overlay)

        for hb in self.hurtboxes :
            tl_x = self.canvas_w - (self.center_x - hb.c_x)
            tl_y = self.canvas_h - (self.center_y - hb.c_y)
            draw.rectangle([(tl_x, tl_y), (tl_x + hb.w, tl_y + hb.h)], fill=TINT_COLOR+(OPACITY,), outline="blue")
        
        self.img = Image.alpha_composite(self.img, overlay)

    def __str__(self):
        output = "IMAGE OBJECT\n"
        output += "\tHITBOXES: %i\n" % self.hitbox_count
        output += "\tHURTBOXES: %i\n" % self.hurtbox_count
        output += "\tWIDTH: %i\n" % self.canvas_w
        output += "\tHEIGHT: %i\n" % self.canvas_h
        output += "\tCENTER_X: %i\n" % self.center_x
        output += "\tCENTER_Y: %i\n" % self.center_y
        return output
    
def get_maximal_bb(bbs: List[Relbox]) -> Relbox:
    # we want to find the maximal bounding box _relative_ to
    #   the center point. That's because we don't particularly care about
    #   the exact x/ys, we just care about the difference of the x/ys
    #   from the center point when we're trying to make the sprites align.
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
if draw_hitboxes:
    for o in l_m :
        o.draw_hurtboxes()
        o.draw_hitboxes()

maxbb: Relbox = get_maximal_bb([o.get_bounding_relbox() for o in l_m])

for o in l_m :
    o.crop_to_box(maxbb)
    
l_output = [o.img for o in l_m]
l_output[0].save("test.gif", format="GIF", save_all=True, append_images=l_output[1:], duration=16, disposal=2, loop=0, transparency=0)