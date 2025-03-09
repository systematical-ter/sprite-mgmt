import argparse
from functools import reduce
from typing import Dict, List, Tuple, Union
from PIL import Image, ImageDraw
import os
import json

import filetools


Bbox = Tuple[int, int, int, int]
Relbox = Tuple[int, int, int, int]

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

class Box() :
    x: int
    y: int
    w: int
    h: int

    def __init__(self, x, y, w, h) :
        self.x = x
        self.y = y
        self.w = w
        self.h = h

class ImgBox(Box) :
    img: Image.Image

    def __init__(self, x, y, w, h, img) :
        super(x,y,w,h)
        self.img = img

class Sprite() :
    img : Image.Image
    duration: int

    coldata_init:bool = False
    # Sprite must have had its collision data loaded to fill the
    #   attributes below.

    # Sprite canvas information
    #   (used for hithurtbox & mouth drawing)
    canvas_w: int
    canvas_h: int
    offset_x: int
    offset_y: int

    # Sprite "mouth" information
    has_mouth: bool
    mouth_box: ImgBox

    # Sprite hit/hurt box information
    hurtboxes: List[Hurtbox]
    hitboxes: List[Hurtbox]

    def __init__(self, img: Image.Image) :
        # Technically, minimal info we need for a Sprite is just an image.

        # Ensure transparency exists:
        if "transparency" not in img.info.keys() :
            img.info["transparency"] = b'\x00' #sets color 0 to transparent

        # Check if image has the weird orange background issue
        #    e.g. terumi 030_06
        h, w = img.size
        br_color = img.getpixel((w-1, h-1))
        if br_color != 0 :
            img = Sprite.remove_abnormal_bg(img)

        # .. and that's all we can do without collision metadata!
        self.img = img

    @classmethod
    def fromImageFile(cls, filename: str) :
        return cls(Image.open(filename))

    def init_col_metadata(self, coldict: Dict[str, str]) :
        """Add metadata read from a _col file to this sprite.
        Reads in canvas size information, sprite offset information.
            chunk information (e.g. whether/where there is a mouth),
            hitbox and hurtbox information.

        :param coldict: The json dict from a sprite's associated .json file
        :type coldict: Dict[str, str]
        """
        # realizing that I'm kind of doing this backwards --
        #   col metadata cnotains the images related to it in the header
        #   so technically I should be starting with the headers.
        #   but oh well, I will refactor this to support that method
        #   of work later.

        c:Dict[str, str] = coldict["Chunks"][0]
        self.canvas_w = c["Width"]
        self.canvas_h = c["Height"]

        # hitboxes (& mouthbox) are based on the character sprite offset
        #   which is stored as a negative for some reason I haven't found
        #   important yet...
        self.offset_x = -c["X"]
        self.offset_y = -c["Y"]

        # if there is more than 1 chunk in the coldata, that means
        #   (as far as I am aware) that there is a mouth sprite.
        #   handle it.
        if len(coldict["Chunks"]) > 1 :
            self.has_mouth = True
            self.mouth_box = Sprite._get_mouth(self.img, coldict["Chunks"][1])

            self.img = Sprite.remove_secondary_boxes(self.img, coldict["Chunks"][1])
        else :
            self.has_mouth = False

        # load in (hit|hurt)boxes
        self.hurtboxes = []
        for hurtbox in coldict["Hurtboxes"] :
            self.hurtboxes.append(Hurtbox(**hurtbox))
        
        self.hitboxes = []
        for hitbox in coldict["Hitboxes"] :
            self.hitboxes.append(Hurtbox(**hitbox))

        # got everything -- mark coldata as initialized
        self.coldata_init = True

    def init_col_file(self, filename:str) :
        """Add metadata from a _col.json file to this sprite.
        (Just reads the file and calls Sprite.init_col_metadata)

        :param filename: Path to a .json file to associate with this sprite.
        :type filename: str
        """
        coldata: Dict[str, str]
        with open(filename, 'r') as f:
            coldata = json.load(f)
        self.init_col_metadata(coldata)

    def Old__init__(self, jdict, img, duration) :
        c = jdict["Chunks"][0]
        self.canvas_w = c["Width"]
        self.canvas_h = c["Height"]

        # hitboxes (& mouthbox) are based on the character sprite offset
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

        if len(jdict["Chunks"]) > 1 :
            self.has_mouth = True
            self.mouth_box = Sprite._get_mouth(img, jdict["Chunks"][1])

            # TODO: make this a little easier to read.
            chunk_left_x = jdict["Chunks"][1]["SrcX"]
            img = self.remove_secondary_boxes(img, chunk_left_x)
        else :
            self.has_mouth = False
        

        # convert to RGBA for drawing purposes later
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

    @classmethod
    def _get_mouth(cls, img, metadata) -> ImgBox :
        x = int(metadata["X"])
        y = int(metadata["Y"])
        width = metadata["Width"]
        height = metadata["Height"]
        left = metadata["SrcX"]
        top = metadata["SrcY"]
        mouth_img = img.crop((left, top, left + width, top + height))

        return Box(x, y, width, height, mouth_img)
    
    def draw_mouth(self) :
        x = int(self.offset_x + self.mouth_box.x)
        y = int(self.offset_y + self.mouth_box.y)

        tmp_image = Image.new("RGBA", self.img.size)
        tmp_image.paste(self.mouth_box.img, (x,y))
        self.img.alpha_composite(tmp_image)

    @classmethod
    def remove_secondary_boxes(cls, img: Image.Image, chunk: Dict[str, str]) -> Image.Image :
        img2 = Image.new("PA", img.size, img.getpixel((0,0)))
        img2.putpalette(img.palette)
        img2.info["transparency"] = img.info["transparency"]
        _,h = img.size

        chunk_x = chunk["SrcX"]
        img = img.crop((0,0,chunk_x, h))
        img2.paste(img, (0,0))
        return img2
    
    @classmethod
    def remove_abnormal_bg(cls, img: Image.Image) -> Image.Image:
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

        # find the transparent pixel box
        found_pixels = [i for i, pixel in enumerate(img.getdata()) if pixel == 0]
        w,_ = img.size
        found_pixels_coords = [divmod(index, w) for index in found_pixels]
        
        # apparently x[0] ix y and x[1] is x for how I did it above.
        y_only = list(map(lambda x: x[0], found_pixels_coords))
        x_only = list(map(lambda x: x[1], found_pixels_coords))
        min_x = reduce(lambda x,y : x if x < y else y, x_only)+1
        max_x = reduce(lambda x,y: x if x > y else y, x_only)
        min_y = reduce(lambda x,y : x if x < y else y, y_only)+1
        max_y = reduce(lambda x,y: x if x > y else y, y_only)

        img2 = Image.new("P", img.size, img.getpixel((min_x, min_y)))
        img2.putpalette(img.palette)
        img2.info["transparency"] = img.info["transparency"]

        # crop it and re-extend it
        img = img.crop((min_x, min_y, max_x, max_y))
        img2.paste(img, (min_x, min_y))
        img2.info["transparency"] = img.info["transparency"]
        
        return img2
    
    def get_bounding_bbox(self) -> Bbox :
        x, y, dx, dy = self.img.getbbox()

        bbox = (x,y,dx,dy)
        return bbox
    
    def crop_to_box(self, bb: Bbox) -> None :
        self.img = self.img.crop(bb)

    def draw_hbox(self, color: Tuple[int, int, int], boxname: str) -> None:
        """Draws [hit|hurt]boxes onto this sprite's Img.

        :param color: A 3-ple with values [0-255] representing the color to make these boxes. (Generally, hitboxes are (255,0,0) and hurtboxes are (0,0,255).)
        :type color: Tuple[int, int, int]
        :param boxname: One of (Hitbox|Hurtbox) signifying whether to draw the hitboxes or hurtboxes.
        :type boxname: str
        """
        TINT_COLOR: Tuple[int, int, int] = color
        TRANSPARENCY = .3
        OPACITY= int(255*TRANSPARENCY)

        overlay: Image.Image = Image.new('RGBA', self.img.size, TINT_COLOR+(0,))
        draw: ImageDraw.ImageDraw = ImageDraw.Draw(overlay)

        hb: Hurtbox
        for hb in self.__getattribute__(boxname) :
            tl_x: int = self.offset_x + hb.c_x
            tl_y: int = self.offset_y + hb.c_y
            draw.rectangle([(tl_x, tl_y), (tl_x + hb.w, tl_y + hb.h)], fill=TINT_COLOR+(OPACITY,), outline=TINT_COLOR)
        
        self.img = Image.alpha_composite(self.img, overlay)

    def draw_hitboxes(self) -> None :
        """Draw Hitboxes onto this sprite's Img.
        """
        TINT_COLOR=(255,0,0)
        self.draw_hbox(TINT_COLOR, "hitboxes")
    
    def draw_hurtboxes(self) -> None :
        """Draw Hurtboxes onto this sprite's Img.
        """
        TINT_COLOR=(0,0,255)
        self.draw_hbox(TINT_COLOR, "hurtboxes")

    def __str__(self):
        output = "IMAGE OBJECT\n"
        output += "\tWIDTH: %i\n" % self.canvas_w
        output += "\tHEIGHT: %i\n" % self.canvas_h
        output += "\tOFFSET_X: %i\n" % self.offset_x
        output += "\tOFFSET_Y: %i\n" % self.offset_y
        return output
    
    @classmethod
    def get_maximal_bb(cls, sprs: List['Sprite']) -> Bbox :
        x,y,dx,dy = 700,700,0,0
        
        spr: Sprite
        for spr in sprs:
            bb: Bbox = spr.get_bounding_bbox()
            if bb[0] < x :
                x = bb[0]
            if bb[1] < y :
                y = bb[1]
            if bb[2] > dx :
                dx = bb[2]
            if bb[3] > dy :
                dy = bb[3]
        return (x,y,dx,dy)

    ###### DEBUG METHODS ######
    def _draw_center(self) -> None :
        """Debug method -- draw a box around the sprite's offset point.
        """
        i: ImageDraw.ImageDraw = ImageDraw.Draw(self.img)
        x,y = self.offset_x, self.offset_y
        i.rectangle([(x-5, y-5),(x+5,y+5)], fill="red")

    def _draw_box(self, bb:Bbox) -> None :
        """Debug method - draw a red box at the given location.

        :param bb: Box to draw.
        :type bb: Bbox
        """
        i: ImageDraw.ImageDraw = ImageDraw.Draw(self.img)
        i.rectangle([(bb[0],bb[1]),(bb[2],bb[3])], fill=None, outline="red")

    def _relbox_to_bbox(self, bb:Relbox) -> Bbox :
        """Given a box relative to the sprite's offset, returns an absolute box.
        """
        return (bb[0] - self.offset_x, bb[1] - self.offset_y, 
                bb[2] - self.offset_x, bb[3] - self.offset_y)
    
    def _bbox_to_relbox(self, bb:Bbox) -> Relbox :
        """Given an absolute box, returns a box relative to the sprite's offset.
        """
        return (bb[0] + self.offset_x, bb[1] + self.offset_y,
                bb[2] + self.offset_x, bb[3] + self.offset_y)

# should be 2 modes of operation:
#   1. list of sprite names provided
#   2. tuples of names + duration provided
# for now I'm ignoring spawned entities.

#### YouLiveLikeThis?.png

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
    
    # add option to toggle mouth later. I don't want to deal with it right now
    # honestly I want to re-write basically the entire second half of this file
    #   so I'll do this when I do that.
    if True :
        for i,spr in enumerate(sprites) :
            if i % 2 == 0 :
                if spr.has_mouth :
                    spr.draw_mouth()
    return compile_sprites(sprites, hitboxes)

def compile_sprites(sprites: List[Sprite], hitboxes: bool = False) -> List[Image.Image] :
    if hitboxes :
        for spr in sprites :
            spr.draw_hitboxes()
            spr.draw_hurtboxes()

    # get the maximal bounding box, for centering purposes
    maxbb: Bbox = Sprite.get_maximal_bb(sprites)

    # crop according to maximal bounding box
    for spr in sprites :
        spr.crop_to_box(maxbb)

    # iterate over sprites; add dur multiples of them in the list to imitate # of frames they are present
    output: List[Image.Image] = []
    for i,spr in enumerate(sprites):
        output.extend([spr.img] * spr.duration)

    return output

def make_gif_from_namedurs(nds: List[Tuple[str, int]], filename: str, hitboxes: bool = False, oformat: str = "PNG") :
    giffps = 16
    #giffps = giffps * 2
    imgs: List[Image.Image] = from_namedurs(nds, hitboxes)
    if oformat == "PNG" :
        imgs[0].save(filename, format="PNG", save_all=True, append_images=imgs[1:], duration=giffps, disposal=1, loop=0)
    elif oformat == "GIF" :
        imgs[0].save(filename, format="GIF", save_all=True, append_images=imgs[1:], duration=giffps, disposal=2, loop=0, transparency=0)
    else :
        raise ValueError("Invalid output format provided.")

def make_gif_from_names(names: List[str], filename: str, duration:int = 3, hitboxes: bool = False, oformat: str = "PNG") :
    nds = list(zip(names, [duration]*len(names)))
    make_gif_from_namedurs(nds, filename, hitboxes, oformat)

def make_gif_from_sprlocs_collocs(sprlocs: List[str], collocs: List[str], durs: List[int], filename: str, hitboxes: bool = False, overwrite: bool = False, oformat: str = "PNG", flip_y: bool = False) :
    imgs: List[Image.Image] = from_png_col_durs(sprlocs, collocs, durs, hitboxes)

    if not overwrite :
        if os.path.exists(filename) :
            raise ValueError("A file already exists at %s and overwrite is set to False." % filename)
        
    if flip_y :
        for i,img in enumerate(imgs) :
            imgs[i] = img.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)

    if oformat == "PNG" :
        imgs[0].save(filename, format="PNG", save_all=True, append_images=imgs[1:], duration=16, disposal=1, loop=0)
    elif oformat == "GIF" :
        imgs[0].save(filename, format="GIF", save_all=True, append_images=imgs[1:], duration=16, disposal=2, loop=0, transparency=0)
    else : 
        raise ValueError("Invalid output format provided.")

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
        
    if True :
        for i,spr in enumerate(sprites) :
            if i % 2 == 0 :
                if spr.has_mouth :
                    spr.draw_mouth() 
    return compile_sprites(sprites, hitboxes)

def _from_given_paths(pngpaths, jsonpaths, duration, hb, overwrite, output, oformat, flip_y: bool = False) :
    pngs = pngpaths
    jsons = jsonpaths
    
    pngs, jsons = filetools.ensure_order(pngs, jsons)
    duration = [int(duration)] * len(pngs)
    make_gif_from_sprlocs_collocs(pngs, jsons, duration, output, hb, overwrite, oformat, flip_y)

def main(pngdir, jsondir, duration, hb, overwrite, output, oformat, flip_y) :
    pngs = filetools.find_sprites(pngdir)
    jsons = filetools.find_collision(jsondir)

    pngs, jsons = filetools.ensure_order(pngs, jsons)
    pngs = list(map(lambda x: os.path.join(pngdir, x), pngs))
    jsons = list(map(lambda x: os.path.join(jsondir, x), jsons))
    duration = [int(duration)] * len(pngs)

    make_gif_from_sprlocs_collocs(pngs, jsons, duration, output, hb, overwrite, oformat, flip_y)

if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description="Generates a gif from a folder of PNG sprite files and a folder of JSON collision files.")
    parser.add_argument("--pngdir", help="Path to directory containing PNG sprite files.")
    parser.add_argument("--jsondir", help="Path to directory containing JSON collision files.")
    parser.add_argument("--duration", default=3, help="The duration of each frame.")
    parser.add_argument("--hb", action="store_true", help="Whether to render hitboxes.")
    parser.add_argument("--overwrite", action="store_true", help="If file already exists at output location, overwrite it.")
    parser.add_argument("--oformat", choices=["GIF","PNG"], default="PNG", 
        help="Wether to save as a GIF or PNG. Note that only animated PNGs can support partial transparency.")
    parser.add_argument("--flip_y", action="store_true", help="Flip the output gif along the y axis.")
    parser.add_argument("output", help="Path to save generated .gif to.")

    main(**vars(parser.parse_args()))
    