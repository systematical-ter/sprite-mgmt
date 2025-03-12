import argparse
from typing import List, Dict
from PIL import Image
from sprClasses import SprCollection

# should be 2 modes of operation:
#   1. list of sprite names provided
#   2. tuples of names + duration provided
# for now I'm ignoring spawned entities.

#### YouLiveLikeThis?.png

def _from_directories(img_dir, clsn_dir, duration, hb, mouth: bool = False, **kwargs) :
    collection: SprCollection = SprCollection.from_collision_directory(clsn_dir, img_dir)
    collection.override_duration(int(duration))
    spr: List[Image.Image] = collection.compile_sprites(hb, mouth)

    _draw_it(spr, **kwargs)

def _from_names(names, img_dir, clsn_dir, duration, hb, mouth: bool = False, **args) :
    collection: SprCollection = SprCollection.from_names_clsns(img_dir, clsn_dir, names)
    collection.override_duration(int(duration))
    spr: List[Image.Image] = collection.compile_sprites(hb, mouth)
    
    _draw_it(spr, **args)

def _from_recolored_pngs(names, imgs: Dict[str, Image.Image], clsn_dir, duration, hb, mouth: bool = False, **args) :
    coll: SprCollection = SprCollection.from_prerecolored_imgs(imgs)
    coll.override_duration(int(duration))
    coll._add_collision(names, clsn_dir)
    _draw_it(coll.compile_sprites(hb, mouth), **args)

def _draw_it(sprs: List[Image.Image], overwrite, oformat, output, flip_y: bool = False) :
    if flip_y :
        for i,img in enumerate(sprs) :
            sprs[i] = img.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)

    output_params = {
        "fp" : output + "." + str.lower(oformat),
        "format" : oformat,
        "save_all" : True,
        "append_images" : sprs[1:],
        "duration" : 16,
        "disposal" : 1 if oformat == "PNG" else 2,
        "loop" : 0
    }
    if oformat == "GIF" :
        output_params["transparency"] = 0
    
    sprs[0].save(**output_params)

def main(pngdir, jsondir, duration, hb, mouth, overwrite, output, oformat, flip_y) :
    _from_directories(pngdir, jsondir, duration, hb, mouth, 
        overwrite=overwrite, oformat=oformat, output=output, flip_y=flip_y)

if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description="Generates a gif from a folder of PNG sprite files and a folder of JSON collision files.")
    parser.add_argument("--pngdir", help="Path to directory containing PNG sprite files.")
    parser.add_argument("--jsondir", help="Path to directory containing JSON collision files.")
    parser.add_argument("--duration", default=3, help="The duration of each frame.")
    parser.add_argument("--hb", action="store_true", help="Whether to render hitboxes.")
    parser.add_argument("--mouth", action="store_true", help="Whether to animate the mouth.")
    parser.add_argument("--overwrite", action="store_true", help="If file already exists at output location, overwrite it.")
    parser.add_argument("--oformat", choices=["GIF","PNG"], default="PNG", 
        help="Wether to save as a GIF or PNG. Note that only animated PNGs can support partial transparency.")
    parser.add_argument("--flip_y", action="store_true", help="Flip the output gif along the y axis.")
    parser.add_argument("output", help="Path to save generated .gif to.")

    main(**vars(parser.parse_args()))
    