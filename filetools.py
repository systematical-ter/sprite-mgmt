from functools import reduce
import os
import re
from typing import List, Tuple

def check_img_exists_and_png(loc) -> bool :
    if not os.path.exists(loc) :
        raise ValueError("Provided image %s does not exist." % loc)
    if not os.path.normpath(loc).endswith("png") :
        raise ValueError("Provided file %s is not a .png." % loc)
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

# fuck this
def _find_gifify_handholding(loc) -> Tuple[List[str], List[str]] :
    possible_png_paths = r"^char_[a-z]{2}_img$|^img$|^png$"
    possible_png_re = re.compile(possible_png_paths)
    possible_json_paths = r"^char_[a-z]{2}_col$|^col$|^json$"
    possible_json_re = re.compile(possible_json_paths)

    curdir = [f for f in os.listdir(loc)]
    found_png = list(filter(possible_png_re.match, curdir))
    found_json = list(filter(possible_json_re.match, curdir))

    if len(found_png) == 0 or len(found_json) == 0 :
        raise ValueError("Was not able to find png or json folders at the provided loc: %s.\n\tPlease check the usage guide." % loc)

    png_files = find_files_in_directory(os.path.join(loc, found_png[0]), ".png")
    json_files = find_files_in_directory(os.path.join(loc, found_json[0]), ".json")

    print(png_files[0])
    print(json_files[1])
    pass

def find_sprites(loc) -> List[str] :
    return find_files_in_directory(loc, ".png")

def find_collision(loc) -> List[str] :
    return find_files_in_directory(loc, ".json")

# link pngs to jsons
# awful performance, I'm sure I can do better, but it's a non-issue right now.
def ensure_order(pngs: List[str], jsons: List[str]) -> Tuple[List[str], List[str]] :
    out_png = []
    out_json = []

    while len(pngs) > 0 :
        p = pngs.pop()
        pname = os.path.splitext(p)[0]
        for i in range(0, len(jsons)) :
            lenj = len(jsons)
            j = jsons[lenj-i-1]
            if pname == os.path.splitext(j)[0] :
                out_png.append(p)
                out_json.append(j)
                break
        else :
            # TODO: found the ex versions. gotta make sure I turn those into Sprite objs in gifify.
            print("Could not find matching JSON for PNG with name: %s" % p)
    
    return(out_png, out_json)

#a = filetools.find_sprites("exported_data/char_tm_img")
#b = filetools.find_collision("exported_data/char_tm_col")