from functools import reduce
from typing import Dict, List, Tuple, Union
from PIL import Image, ImageDraw
import json
import filetools as ft
import os

Bbox = Tuple[int, int, int, int]
Relbox = Tuple[int, int, int, int]

class HBox() :
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
        super().__init__(x,y,w,h)
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
    hurtboxes: List[HBox]
    hitboxes: List[HBox]

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
            self.hurtboxes.append(HBox(**hurtbox))
        
        self.hitboxes = []
        for hitbox in coldict["Hitboxes"] :
            self.hitboxes.append(HBox(**hitbox))

        # got everything -- mark coldata as initialized
        self.img = self.img.convert("RGBA")
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

    @classmethod
    def _get_mouth(cls, img, metadata) -> ImgBox :
        x = int(metadata["X"])
        y = int(metadata["Y"])
        width = metadata["Width"]
        height = metadata["Height"]
        left = metadata["SrcX"]
        top = metadata["SrcY"]
        mouth_img = img.crop((left, top, left + width, top + height))

        return ImgBox(x, y, width, height, mouth_img)
    
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
        :param boxname: One of (Hitbox|HBox) signifying whether to draw the hitboxes or hurtboxes.
        :type boxname: str
        """
        TINT_COLOR: Tuple[int, int, int] = color
        TRANSPARENCY = .3
        OPACITY= int(255*TRANSPARENCY)

        overlay: Image.Image = Image.new('RGBA', self.img.size, TINT_COLOR+(0,))
        draw: ImageDraw.ImageDraw = ImageDraw.Draw(overlay)

        hb: HBox
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
    eff_sprites: Dict[str, Sprite]
    order: List[str]
    # effect sprites are, theoretically, similar to sprites...
    #   except they don't have collision information (I don't think).
    #   I might still want to make them a separate class that doesn't
    #   doesn't have the collision metadata handling.
    # UPDATE :
    #   this was wrong --- effect sprites actually DO have collision
    #   metadata, it's just *usually* empty. (450_90 has an "unknown" 
    #   box?)

    def __init__(self):
        self.sprites = {}
        self.order = []

    @classmethod
    def from_image_directory(cls, directory: str) -> 'SprCollection':
        coll: 'SprCollection' = cls()
        sprs: List[str] = ft.find_sprites(directory)
        for sp in sprs :
            name: str = sp.split(".png")
            loaded_sprite: Sprite = Sprite.fromImageFile(os.path.join(directory, sp))

            coll.sprites[name] = loaded_sprite
            coll.order.append(name)

        return coll

    @classmethod
    def from_names_imgonly(cls, img_dir: str, names: List[str]) -> 'SprCollection' :
        coll = cls()
        for img, nm in [(os.path.join(img_dir, x + ".png"), x) for x in names] :
            ft.check_img_exists_and_png(img)
            coll.sprites[nm] = Sprite.fromImageFile(img)
            coll.order.append(nm)
        
        return coll
    
    @classmethod
    def from_prerecolored_imgs(cls, imgs: Dict[str, Image.Image]) -> 'SprCollection' :
        coll: 'SprCollection' = cls()
        for nm, img in imgs.items() :
            loaded_sprite: Sprite = Sprite.fromImage(img)
            coll.sprites[nm] = loaded_sprite
            coll.order.append(nm)
        
        return coll
    
    @classmethod
    def from_collision_directory(cls, clsn_dir: str, img_dir: str) -> 'SprCollection' :
        coll: 'SprCollection' = cls()
        clsns: List[str] = ft.find_collision(clsn_dir)

        for clsn in clsns:
            img_name, spr = SprCollection._create_from_collision(
                os.path.join(clsn_dir, clsn), img_dir
                )

            coll.sprites[img_name] = spr
            coll.order.append(img_name)

        return coll

    @classmethod
    def from_names_clsns(cls, img_dir:str, clsn_dir: str, names: List[str]) -> 'SprCollection' :
        coll: 'SprCollection' = cls()
        for clsn, nm in [(os.path.join(clsn_dir, x + ".json"), x) for x in names] :
            ft.check_coll_exists_and_json(clsn)
            img_name, spr = SprCollection._create_from_collision(
                clsn, img_dir
            )

            coll.sprites[img_name] = spr
            coll.order.append(img_name)

        return coll

    @staticmethod
    def _create_from_collision(clsn_file: str, img_dir: str) -> Tuple[str, Sprite] :
        clsn_data = ft.read_collision_json(clsn_file)

        # I checked before and this should be only a 0-len list.
        # I can make this more futureproof later.
        img_name: str = clsn_data["Header"]["Images"][0].split(".bmp")[0]
        img_path: str = ft.find_image(img_name, img_dir)
        # find associated image

        spr: Sprite = Sprite.fromImageFile(img_path)
        spr.init_col_metadata(clsn_data)
        
        return(img_name, spr)

    def _add_collision(self, names: List[str], clsn_dir: str) -> None :
        for clsn, nm in [(os.path.join(clsn_dir, x + ".json"), x) for x in names] :
            ft.check_coll_exists_and_json(clsn)
            clsn_data = ft.read_collision_json(clsn)

            img_name: str = clsn_data["Header"]["Images"][0].split(".bmp")[0]
            if img_name not in self.order :
                raise ValueError("Collision data is pointing to a file I don't have in my list: %s" % img_name)
            
            self.sprites[img_name].init_col_metadata(clsn_data)

    def override_duration(self, duration: Union[int, List[int]]) -> None :
        if isinstance(duration, int) :
            for spr in self.sprites.values() :
                spr.duration = duration
        elif isinstance(duration, List[int]) :
            if len(duration) != len(self.sprites) :
                raise ValueError("Provided list of durations gives %i durations, but I have %i sprites." % 
                    (len(duration), len(list(self.sprites.values())))
                    )
            for dur, spr in zip(duration, self.sprites.values()) :
                spr.duration = dur

    def compile_sprites(self, hitboxes: bool = False, mouth: bool = False) -> List[Image.Image] :
        spr_objs = self.sprites.values()
        if mouth :
            for i,nm in enumerate(self.order) :
                if i % 2 == 0 :
                    if self.sprites[nm].has_mouth :
                        self.sprites[nm].draw_mouth() 

        if hitboxes :
            for spr in spr_objs :
                spr.draw_hitboxes()
                spr.draw_hurtboxes()

        # crop according to maximal bounding box
        maxbb: Bbox = Sprite.get_maximal_bb(spr_objs)
        for spr in spr_objs :
            spr.crop_to_box(maxbb)

        # iterate over sprites; add dur multiples of them in the list to imitate # of frames they are present
        output: List[Image.Image] = []
        for nm in self.order :
            spr = self.sprites[nm]
            # no matter what, to make this work, they have to be converted to RGBA?
            spr.img = spr.img.convert("RGBA")
            output.extend([spr.img] * spr.duration)
        # TODO : add effect sprites
        return output