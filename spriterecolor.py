from PIL import Image
import os
import argparse

### file system funcs ###

def check_img_exists_and_png(loc) :
    if not os.path.exists(loc) :
        raise ValueError("Provided image %s does not exist." % loc)
    if not os.path.normpath(loc).endswith("png") :
        raise ValueError("Provided file %s is not a .png." % loc)
    return True

def run_over_dir(directory, pal, tra, output, overwrite:bool = False) :
    if not os.path.exists(directory) :
        raise ValueError("Provided directory %s does not exist." % directory)
    elif not os.path.isdir(directory) :
        raise ValueError("Provided path %s exists, but is not a directory; did you mean to use --file?" % directory)
    
    files = [f for f in os.listdir(directory) if f.endswith('png')]
    if len(files) == 0 :
        raise ValueError("Couldn't find any .png files in provided directory %s." % directory)
    
    for f in files :
        apply_palette_to_img(os.path.join(directory, f), pal, tra, output, overwrite)

### palette + img funcs ###

def get_palette_and_transparency(ref_img_loc: str) :
    img = Image.open(ref_img_loc)
    pal = img.getpalette()
    tra = img.info["transparency"]

    return pal, tra

def apply_palette_to_img(img_loc: str, pal, tra, newdir:str, overwrite:bool = False) :
    if not os.path.exists(newdir) :
        os.mkdir(newdir)
    elif os.path.exists(newdir) and not os.path.isdir(newdir) :
        os.mkdir(newdir)

    check_img_exists_and_png(img_loc)
    img = Image.open(img_loc)
    img.putpalette(pal)
    img.info["transparency"] = tra

    filename = os.path.basename(img_loc)
    outloc = os.path.join(newdir, filename)
    if os.path.exists(outloc) and not overwrite:
        raise ValueError("File already exists at location %s and overwrite is not set." % outloc)

    img.save(os.path.join(newdir, filename))

### main funcs ###

def main(file, directory, reference, output, overwrite) :
    check_img_exists_and_png(reference)
    pal, tra = get_palette_and_transparency(reference)

    if file is not None:
        apply_palette_to_img(file, pal, tra, output, overwrite)
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