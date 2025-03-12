import json
import pytest
from sprClasses import Sprite, SprCollection

def test_create_Spr_img_file() :
    spr: Sprite = Sprite.fromImageFile("exported_data/char_tm_img/tm201_01.png")
    assert spr.img is not None

def test_Spr_add_col() :
    spr: Sprite = Sprite.fromImageFile("exported_data/char_tm_img/tm201_01.png")

    jsonloc: str = "exported_data/char_tm_col/JSONs/tm201_01.json"
    spr.init_col_file(jsonloc)
    with open(jsonloc, 'r') as f:
        exp_data = json.load(f)

    assert spr.coldata_init
    
    if len(exp_data["Chunks"]) > 1 :
        assert spr.has_mouth
        # mouth should be cut off, if any
        # spr.img.show()
    else :
        assert not spr.has_mouth

    assert len(spr.hitboxes) == len(exp_data["Hitboxes"])

def test_Spr_weird_bg() :
    spr: Sprite = Sprite.fromImageFile("exported_data/char_tm_img/tm030_06.png")
    #spr.img.show()

def test_SprColl_fromFiles() :
    params = {
        "names"             : 
            ["tm201_0" + str(i) + ".png" for i in range(0,8)],
        "img_path"          :
            "exported_data/char_tm_img",
        }

    SprCollection.from_images_names()