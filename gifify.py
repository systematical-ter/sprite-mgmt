import argparse
from functools import reduce
from typing import List, Tuple, Union
from PIL import Image, ImageDraw
import os
import json

import filetools


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
    
    offset_x: int
    offset_y: int

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

        # hitboxes are based on the character sprite offset
        #   which is stored in negative for some reason.
        self.offset_x = -c["X"]
        self.offset_y = -c["Y"]

        # sets the first color to be completely transparent only if
        #   transparency has not already been defined.
        if "transparency" not in img.info.keys() :
            img.info["transparency"] = b'\x00'

        # check if the background is weird -- 
        #    e.g. terumi 030_06 has a weird error where
        #    a huge chunk of it is orange
        h, w = img.size
        br_color = img.getpixel((w-1, h-1))
        if br_color != 0 :
            img = self.remove_strange_behavior(img)


        # I'm not dealing with mouths. Crop them out so they don't
        #   mess with position normalization.
        if len(jdict["Chunks"]) > 1 :
            chunk_left_x = jdict["Chunks"][1]["SrcX"]
            img = self.remove_secondary_boxes(img, chunk_left_x)
        

        self.img = img.convert("RGBA")
        self.tl_x, self.tl_y,_,_ = self.img.getbbox()
        #self.draw_center()
        self.duration = int(duration)

        self.hurtboxes = []
        for hurtbox in jdict["Hurtboxes"] :
            self.hurtboxes.append(Hurtbox(**hurtbox))
        
        self.hitboxes = []
        for hitbox in jdict["Hitboxes"] :
            self.hitboxes.append(Hurtbox(**hitbox))

    def remove_secondary_boxes(self, img: Image.Image, chunk_x: int) -> Image.Image :
        img2 = Image.new("PA", img.size, 0)
        img2.putpalette(img.palette)
        _,h = img.size

        img = img.crop((0,0,chunk_x, h))
        img2.paste(img, (0,0))
        return img2
    
    def remove_strange_behavior(self, img: Image.Image) -> Image.Image:
        """Fix strange miscolored backgrounds

        Some images have strange behavior where the image is filled
        with some extra color. (Example: Terumi 030 frame 06.) This
        resolves that by finding the area of the image that is
        correctly transparent, cropping the image to only that region,
        and then re-sizing the image back to the original size with
        a transparent background.

        :param img: Image to fix
        :type img: Image.Image
        :return: Image with a hopefully fixed background.
        :rtype: Image.Image
        """
        # create temporary image
        img2 = Image.new("PA", img.size, 0)
        img2.putpalette(img.palette)

        # find the transparent pixel box
        found_pixels = [i for i, pixel in enumerate(img.getdata()) if pixel == 0]
        w,_ = img.size
        found_pixels_coords = [divmod(index, w) for index in found_pixels]
        
        # apparently x[0] ix y and x[1] is x for how I did it above.
        y_only = list(map(lambda x: x[0], found_pixels_coords))
        x_only = list(map(lambda x: x[1], found_pixels_coords))
        min_x = reduce(lambda x,y : x if x < y else y, x_only)
        max_x = reduce(lambda x,y: x if x > y else y, x_only)
        min_y = reduce(lambda x,y : x if x < y else y, y_only)
        max_y = reduce(lambda x,y: x if x > y else y, y_only)

        # crop it and re-extend it
        img = img.crop((min_x, min_y, max_x, max_y))
        img2.paste(img, (min_x, min_y))
        
        return img2
    
    def get_bounding_bbox(self) -> Bbox :
        x, y, dx, dy = self.img.getbbox()

        bbox = (x,y,dx,dy)
        return bbox
    
    def crop_to_box(self, bb: Bbox) -> None :
        self.img = self.img.crop(bb)

    def draw_center(self) -> None :
        i = ImageDraw.Draw(self.img)
        x,y = self.center_x, self.center_y
        i.rectangle([(x-5, y-5),(x+5,y+5)], fill="red")

    def draw_box(self, bb:Bbox) -> None :
        i = ImageDraw.Draw(self.img)
        i.rectangle([(bb[0],bb[1]),(bb[2],bb[3])], fill=None, outline="red")

    def relbox_to_bbox(self, bb:Relbox) -> Bbox :
        return (bb[0] - self.offset_x, bb[1] - self.offset_y, 
                bb[2] - self.offset_x, bb[3] - self.offset_y)
    
    def bbox_to_relbox(self, bb:Bbox) -> Relbox :
        return (bb[0] + self.offset_x, bb[1] + self.offset_y,
                bb[2] + self.offset_x, bb[3] + self.offset_y)

    def draw_hitboxes(self) -> None :
        TINT_COLOR=(255,0,0)
        TRANSPARENCY = .3
        OPACITY= int(255*TRANSPARENCY)

        overlay = Image.new('RGBA', self.img.size, TINT_COLOR+(0,))
        draw = ImageDraw.Draw(overlay)

        for hb in self.hitboxes :
            tl_x = self.offset_x + hb.c_x
            tl_y = self.offset_y + hb.c_y
            draw.rectangle([(tl_x, tl_y), (tl_x + hb.w, tl_y + hb.h)], fill=TINT_COLOR+(OPACITY,), outline="red")
        
        self.img = Image.alpha_composite(self.img, overlay)
    
    def draw_hurtboxes(self) -> None :
        TINT_COLOR=(0,0,255)
        TRANSPARENCY = .3
        OPACITY= int(255*TRANSPARENCY)

        overlay = Image.new('RGBA', self.img.size, TINT_COLOR+(0,))
        draw = ImageDraw.Draw(overlay)

        for hb in self.hurtboxes :
            tl_x = self.offset_x + hb.c_x
            tl_y = self.offset_y + hb.c_y
            draw.rectangle([(tl_x, tl_y), (tl_x + hb.w, tl_y + hb.h)], fill=TINT_COLOR+(OPACITY,), outline="blue")
        
        self.img = Image.alpha_composite(self.img, overlay)

    def __str__(self):
        output = "IMAGE OBJECT\n"
        output += "\tHITBOXES: %i\n" % self.hitbox_count
        output += "\tHURTBOXES: %i\n" % self.hurtbox_count
        output += "\tWIDTH: %i\n" % self.canvas_w
        output += "\tHEIGHT: %i\n" % self.canvas_h
        output += "\tOFFSET_X: %i\n" % self.offset_x
        output += "\tOFFSET_Y: %i\n" % self.offset_y
        return output
    
def get_maximal_bb(bbs: List[Bbox]) -> Bbox:
    x,y,dx,dy = 700,700,0,0
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
    durations = [int(d) for _,d in nds]

    # guaranteed to be in the same order b/c of the way image_paths,
    #   col_paths were made
    return from_png_col_durs(image_paths, col_paths, durations, hitboxes)

def from_png_col_durs(pngs: List[str], cols: List[str], durs: List[int], hitboxes: bool = False) -> List[Image.Image] :
    # confirmed to be in the same order before getting here
    images: List[Image.Image] = [Image.open(path) for path in pngs]
    coldata: List = []
    for c in cols :
        with open(c) as f:
            coldata.append(json.load(f))

    # create Sprite objects
    sprites:List[Sprite] = []
    for i in range(0, len(images)) :
        if durs[i] > 30 :
            durs[i] = 30
        sprites.append(Sprite(coldata[i], images[i], durs[i]))

    return compile_sprites(sprites, hitboxes)

def compile_sprites(sprites: List[Sprite], hitboxes: bool = False) -> List[Image.Image] :
    if hitboxes :
        for spr in sprites :
            spr.draw_hitboxes()
            spr.draw_hurtboxes()

    # get the maximal bounding box, for centering purposes
    maxbb: Relbox = get_maximal_bb([spr.get_bounding_bbox() for spr in sprites])

    # crop according to maximal bounding box
    for spr in sprites :
        spr.crop_to_box(maxbb)

    # iterate over sprites; add dur multiples of them in the list to imitate # of frames they are present
    output: List[Image.Image] = []
    for i,spr in enumerate(sprites):
        img_l = [spr.img]
        img_l = img_l * spr.duration
        output.extend(img_l)

    return output

def make_gif_from_namedurs(nds: List[Tuple[str, int]], filename: str, hitboxes: bool = False) :
    giffps = 16
    #giffps = giffps * 2
    imgs: List[Image.Image] = from_namedurs(nds, hitboxes)
    imgs[0].save(filename, format="GIF", save_all=True, append_images=imgs[1:], duration=giffps, disposal=2, loop=0, transparency=0)

def make_gif_from_names(names: List[str], filename: str, duration:int = 3, hitboxes: bool = False) :
    nds = list(zip(names, [duration]*len(names)))
    make_gif_from_namedurs(nds, filename, hitboxes)

def make_gif_from_sprlocs_collocs(sprlocs: List[str], collocs: List[str], durs: List[int], filename: str, hitboxes: bool = False, overwrite: bool = False) :
    imgs: List[Image.Image] = from_png_col_durs(sprlocs, collocs, durs, hitboxes)
    if not overwrite :
        if os.path.exists(filename) :
            raise ValueError("A file already exists at %s and overwrite is set to False." % filename)
        
    imgs[0].save(filename, format="GIF", save_all=True, append_images=imgs[1:], duration=16, disposal=2, loop=0, transparency=0)

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
        if durations[i] > 30 :
            durations[i] = 30
        sprites.append(Sprite(coldata[i], images[i], durations[i]))
    
    return compile_sprites(sprites, hitboxes)

def _from_given_paths(pngpaths, jsonpaths, duration, hb, overwrite, output) :
    pngs = pngpaths
    jsons = jsonpaths
    duration = [int(duration)] * len(pngs)
    make_gif_from_sprlocs_collocs(pngs, jsons, duration, output, hb, overwrite)

def main(pngdir, jsondir, duration, hb, overwrite, output) :
    pngs = filetools.find_sprites(pngdir)
    jsons = filetools.find_collision(jsondir)

    pngs, jsons = filetools.ensure_order(pngs, jsons)
    pngs = list(map(lambda x: os.path.join(pngdir, x), pngs))
    jsons = list(map(lambda x: os.path.join(jsondir, x), jsons))
    duration = [int(duration)] * len(pngs)
    make_gif_from_sprlocs_collocs(pngs, jsons, duration, output, hb, overwrite)

if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description="Generates a gif from a folder of PNG sprite files and a folder of JSON collision files.")
    parser.add_argument("--pngdir", help="Path to directory containing PNG sprite files.")
    parser.add_argument("--jsondir", help="Path to directory containing JSON collision files.")
    parser.add_argument("--duration", help="The duration of each frame.")
    parser.add_argument("--hb", action="store_true", help="Whether to render hitboxes.")
    parser.add_argument("--overwrite", action="store_true", help="If file already exists at output location, overwrite it.")
    parser.add_argument("output", help="Path to save generated .gif to.")

    main(**vars(parser.parse_args()))
    