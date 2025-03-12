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

def _find_T(loc, ext) -> List[str] :
    files = find_files_in_directory(loc, ext)
    #files.sort(key=lambda x: int(re.search("[0-9]+",x.split("_")[1].split(".")[0].split("ex")[0]).group(0)))
    return files

def find_sprites(loc) -> List[str] :
    return _find_T(loc, ".png")

def find_collision(loc) -> List[str] :
    return _find_T(loc, ".json")

# link pngs to jsons
# awful performance, I'm sure I can do better, but it's a non-issue right now.
def ensure_order(pngs: List[str], jsons: List[str]) -> Tuple[List[str], List[str]] :
    out_png = []
    out_json = []

    while len(pngs) > 0 :
        p = pngs.pop(0)
        pname = os.path.splitext(os.path.basename(p))[0]
        for i in range(0, len(jsons)) :
            j = jsons[i]
            json_name = os.path.splitext(os.path.basename(j))[0]
            if pname == json_name or (pname + "01") == json_name :
                out_png.append(p)
                out_json.append(j)
                break
        else :
            # TODO: found the ex versions. gotta make sure I turn those into Sprite objs in gifify.
            print("Could not find matching JSON for PNG with name: %s" % p)
    
    return(out_png, out_json)

#a = filetools.find_sprites("exported_data/char_tm_img")
#b = filetools.find_collision("exported_data/char_tm_col")