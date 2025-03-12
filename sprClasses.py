from functools import reduce
from typing import Dict, List, Tuple
from PIL import Image, ImageDraw
import json
import filetools as ft
import os

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
    duration: int = 3 # default duration is 3

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

    @classmethod
    def fromImage(cls, image: Image.Image) :
        return cls(image)

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
    
    def set_duration(self, duration:int) :
        self.duration = duration

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

class SprCollection() :
    # storing sprites by "name" so we can easily reconnect with collision data
    sprites: Dict[str, Sprite]

    def __init__(self):
        self.sprites = {}

    @classmethod
    def from_image_directory(cls, directory: str) -> 'SprCollection':
        coll = cls.__init__()
        sprs: List[str] = ft.find_sprites(directory)
        for sp in sprs :
            name: str = sp.split(".png")
            loaded_sprite: Sprite = Sprite.fromImageFile(os.path.join(directory, sp))

            coll.sprites[name] = loaded_sprite

        return coll
    
    @classmethod
    def from_images_names(cls, images: List[Image.Image], names: List[str]) -> 'SprCollection' :
        coll = cls.__init__()
        for im, nm in zip(images, names) :
            coll.sprites[nm] = Sprite.fromImage(im)

        return coll

    def init_collision_directory(self, directory: str) :
        colls: List[str] = ft.find_collision(directory) 
        for coll in colls :
            fullpath = os.path.join(directory, coll)
            self.init_collision_file(fullpath)

    def init_collision_file(self, filepath: str) :
        with open(filepath, 'r') as f:
            colldata = json.load(f)
            self.init_collision_data(colldata)

    def init_collision_data(self, colldata: Dict[str, str]) :
        related_spr = colldata["Header"]["Images"][0].split(".bmp")[0]
        if related_spr in self.sprites.keys() :
            self.sprites[related_spr].init_col_metadata(colldata)
        else :
            print("ERR: Unknown sprited requeste: %s" % related_spr)