import argparse
from typing import List, Tuple, Union
from PIL import Image
from sprClasses import Sprite, Bbox
import os
import json

import filetools

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
    # create a class for managing sprite collections?
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
    