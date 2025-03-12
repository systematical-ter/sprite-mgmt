import json
import os
from typing import List, Tuple

def check_img_exists_and_png(loc) -> bool :
    if not os.path.exists(loc) :
        raise ValueError("Provided image %s does not exist." % loc)
    if not os.path.normpath(loc).endswith("png") :
        raise ValueError("Provided file %s is not a .png." % loc)
    return True

def check_coll_exists_and_json(loc) -> bool :
    if not os.path.exists(loc) :
        raise ValueError("Provided collision data file %s does not exist." % loc)
    if not os.path.normpath(loc).endswith("json") :
        raise ValueError("Provided file %s is not a .json." % loc)
    return True

def make_dir(loc) :
    if not os.path.exists(loc) :
        os.mkdir(loc)
    elif os.path.exists(loc) and not os.path.isdir(loc) :
        raise ValueError("Non-Directory file exists at output path: %s" % loc)

def _validate_dir_exists(loc):
    if not os.path.exists(loc) :
        raise ValueError("Provided directory %s does not exist." % loc)
    elif not os.path.isdir(loc) :
        raise ValueError("Provided path %s exists, but is not a directory; did you mean to use --file?" % loc)

def find_files_in_directory(loc, ext="") -> List[str] :
    _validate_dir_exists(loc)

    files = [f for f in os.listdir(loc)]
    matching_files = list(filter(lambda x: x.endswith(ext), files))
    
    if len(matching_files) == 0:
        raise ValueError("No files found matching the provided extension: %s" % ext)
    else :
        return matching_files

def _find_T(loc, ext) -> List[str] :
    files = find_files_in_directory(loc, ext)
    return files

def find_sprites(loc) -> List[str] :
    return _find_T(loc, ".png")

def find_collision(loc) -> List[str] :
    return _find_T(loc, ".json")

def read_collision_json(fileloc) -> str :
    out: str = ""
    with open(fileloc, 'r') as f:
        out = json.load(f)
    return out

def find_image(name:str, dir:str) -> str :
    """Returns the path to an image named `name` in `dir`, if present.

    :param name: Name of the image to look for.
    :type name: str
    :param dir: Directory where images are expected to be.
    :type dir: str
    :return: The path to the image, if it exists.
    :rtype: str
    """
    _validate_dir_exists(dir)
    expected_loc = os.path.join(dir, name + ".png")
    if os.path.exists(expected_loc) and os.path.isfile(expected_loc) :
        return expected_loc
    else :
        raise FileNotFoundError("Could not find an image named %s in %s." % (name, dir))