from typing import List
from PIL import Image
import os
import argparse

import filetools

### file system funcs ###
def _apply_specific_images_IMG(files, pal, tra) -> List[Image.Image] :
    output: List[Image.Image] = []
    for f in files :
        output.append(_read_apply_palette(f, pal, tra))
    return output

def _apply_directory_images_IMG(directory, pal, tra) -> List[Image.Image]:
    output: List[Image.Image] = []
    files = filetools.find_files_in_directory(directory, ".png")
    for f in files :
        output.append(_read_apply_palette(os.path.join(directory, f), pal, tra))
    return output

def run_over_dir(directory, pal, tra, output, overwrite:bool = False) :
    files = filetools.find_files_in_directory(directory, ".png")
    
    for f in files :
        apply_palette_to_img_and_save(os.path.join(directory, f), pal, tra, output, overwrite)

### palette + img funcs ###

def get_palette_and_transparency(ref_img_loc: str) :
    """Get palette object and transparency information from image at provided location.

    :param ref_img_loc: Path of image to take information from.
    :type ref_img_loc: str
    :return: Palette and Transparency information
    :rtype: Tuple[ImagePalette.ImagePalette, binary string]
    """
    img = Image.open(ref_img_loc)
    pal = img.getpalette()
    tra = img.info["transparency"]

    return pal, tra

def _apply_palette(img: Image.Image, pal, tra) -> Image.Image :
    """Apply palette and transparency to a loaded Image.

    :param img: Loaded image to recolor.
    :type img: Image.Image
    :param pal: Palette to recolor image with
    :type pal: ImagePalette.ImagePalette
    :param tra: Transparency information to apply
    :type tra: binary string
    :return: Recolored image.
    :rtype: Image.Image
    """
    img.putpalette(pal)
    img.info["transparency"] = tra
    return img

def _read_apply_palette(img_loc: str, pal, tra) -> Image.Image :
    """Open file, apply palette and transparency, then return Image

    :param img_loc: Path of image to recolor
    :type img_loc: str
    :param pal: Palette to recolor image with
    :type pal: ImagePalette.ImagePalette
    :param tra: Transparency information to apply
    :type tra: binary string
    :return: Image with adjusted palette and transparency
    :rtype: Image.Image
    """
    img = Image.open(img_loc)
    img = _apply_palette(img, pal, tra)
    return img

def apply_palette_to_img_and_save(img_loc: str, pal, tra, newdir:str, overwrite:bool = False) :
    """Apply a palette to an image and then save to the provided location.

    :param img_loc: Path of image to recolor
    :type img_loc: str
    :param pal: Palette to recolor image with
    :type pal: ImagePalette.ImagePalette
    :param tra: Transparency information to apply
    :type tra: binary string
    :param newdir: Path of directory to save image to.
    :type newdir: str
    :param overwrite: Whether to overwrite any files at the given location, defaults to False
    :type overwrite: bool, optional
    :raises ValueError: If a file of the expected name exists and overwrite is False.
    """
    filetools.make_dir(newdir)
    filetools.check_img_exists_and_png(img_loc)
    img = _read_apply_palette(img_loc, pal, tra)

    filename = os.path.basename(img_loc)
    outloc = os.path.join(newdir, filename)
    if os.path.exists(outloc) and not overwrite:
        raise ValueError("File already exists at location %s and overwrite is not set." % outloc)

    img.save(os.path.join(newdir, filename))


### main funcs ###

def main(file, directory, reference, output, overwrite) :
    filetools.check_img_exists_and_png(reference)
    pal, tra = get_palette_and_transparency(reference)

    if file is not None:
        apply_palette_to_img_and_save(file, pal, tra, output, overwrite)
    else :
        run_over_dir(directory, pal, tra, output, overwrite)

if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description="Given an indexed .png file or a directory of indexed .png files, recolors them using another provided indexed .png file's palette.")
    pasted = parser.add_mutually_exclusive_group(required=True)
    pasted.add_argument("--file", help="File to recolor.")
    pasted.add_argument("--directory", help="Directory of files to recolor.")
    
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files in output directory.")
    
    parser.add_argument("--reference", required=True, help="Reference file to take palette from.")
    parser.add_argument("output", help="Directory to put output files.")

    main(**vars(parser.parse_args()))