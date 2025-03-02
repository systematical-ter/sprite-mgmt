from typing import List, Tuple, Union
from PIL import Image, ImageFile, ImageDraw
import os
import spriterecolor
import json


Bbox = Tuple[int, int, int, int]
Relbox = Tuple[int, int, int, int]

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


# # get palette + transparency
# p, t = spriterecolor.get_palette_and_transparency("palette_ref.png")

# # load images and then apply our palette
# l_i = [Image.open(os.path.join(idirectory,i)) for i in images]
# l_pi = [spriterecolor._apply_palette(i, p, t).convert("RGBA") for i in l_i]

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

class Sprite() :
    hitbox_count: int
    hurtbox_count: int

    canvas_w: int
    canvas_h: int
    
    center_x: int
    center_y: int

    img : Image.Image
    duration: int

    hurtboxes: List[Hurtbox]
    hitboxes: List[Hurtbox]

    def __init__(self, jdict, img, duration) :
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

        self.img = img.convert("RGBA")
        self.duration = duration

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

# should be 2 modes of operation:
#   1. list of sprite names provided
#   2. tuples of names + duration provided
# for now I'm ignoring spawned entities.

def get_png_paths(names: List[str]) -> List[str] :
    basedir = "exported_data/char_tm_img"
    paths = [os.path.join(basedir, n) + ".png" for n in names]
    return paths

def get_col_paths(names: List[str]) -> List[str] :
    basedir = "exported_data/char_tm_col/JSONs"
    paths = [os.path.join(basedir, n) + ".json" for n in names]
    return paths

def from_namedurs(nds: List[Tuple[str, int]], hitboxes:bool = False) -> List[Image.Image] :
    # nds = namedurs

    image_paths = get_png_paths([n for n,_ in nds])
    col_paths = get_col_paths([n for n,_ in nds])
    durations = [d for _,d in nds]

    # guaranteed to be in the same order b/c of the way image_paths,
    #   col_paths were made
    images: List[Image.Image] = [Image.open(path) for path in image_paths]  # image objects
    coldata: List = []                                                      # JSON collision data
    for m in col_paths :
        with open(m) as f :
            coldata.append(json.load(f))

    # create Sprite objects
    sprites:List[Sprite] = []
    for i in range(0, len(nds)) :
        sprites.append(Sprite(coldata[i], images[i], durations[i]))

    return compile_sprites(sprites)

def compile_sprites(sprites: List[Sprite], hitboxes: bool = False) -> List[Image.Image] :
    if hitboxes :
        for spr in sprites :
            spr.draw_hitboxes()
            spr.draw_hurtboxes()

    # get the maximal bounding box, for centering purposes
    maxbb: Relbox = get_maximal_bb([spr.get_bounding_relbox() for spr in sprites])

    # crop according to maximal bounding box
    for spr in sprites :
        spr.crop_to_box(maxbb)

    # iterate over sprites; add dur multiples of them in the list to imitate # of frames they are present
    output: List[Image.Image] = []
    for spr in sprites:
        img_l = [spr.img]
        img_l = img_l * spr.duration
        output.extend(img_l)

    return output

def make_gif_from_namedurs(nds: List[Tuple[str, int]], filename: str, hitboxes: bool = False) :
    imgs: List[Image.Image] = from_namedurs(nds, hitboxes)
    imgs[0].save(filename, format="GIF", save_all=True, append_images=imgs[1:], duration=16, disposal=2, loop=0, transparency=0)

def make_gif_from_names(names: List[str], filename: str, duration:int = 3, hitboxes: bool = False) :
    nds = list(zip(names, [duration]*len(names)))
    make_gif_from_namedurs(nds, filename, hitboxes)

def _make_manual(names: List[str], images: List[Image.Image], durations: Union[List[int], int], hitboxes: bool = False) -> List[Image.Image]:
    # check if all lists are of the same length
    col_paths = get_col_paths(names)
    if isinstance(durations, int) :
        durations = [durations] * len(names)

    coldata: List = []
    for m in col_paths:
        with open(m) as f:
            coldata.append(json.load(f))
    
    sprites: List[Sprite] = []
    for i in range(0, len(images)) :
        sprites.append(Sprite(coldata[i], images[i], durations[i]))
    
    return compile_sprites(sprites, hitboxes)

#make_gif_from_names(["tm201_0" + str(i) for i in range(0,8)], "test.gif", duration=5, hitboxes=True)