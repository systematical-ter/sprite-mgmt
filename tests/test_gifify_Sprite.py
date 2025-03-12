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

def test_SprColl_fromNameImgs() :
    params = {
        "names"             : 
            ["tm201_0" + str(i) for i in range(0,8)],
        "img_dir"          :
            "exported_data/char_tm_img",
        }

    coll = SprCollection.from_names_imgonly(**params)
    imgs = coll.compile_sprites()
    imgs[0].save("tests/outputs/test_SprColl_fromNameImgs.png", format = "PNG",  save_all=True, append_images=imgs[1:], duration=16, disposal=1, loop=0)

def test_SprColl_fromCollDir() :
    params = {
        "clsn_dir": "tests/taunt_test",
        "img_dir": "tests/taunt_test"
    }

    coll = SprCollection.from_collision_directory(**params)
    imgs = coll.compile_sprites(True)
    imgs[0].save("tests/outputs/test_SprColl_fromCollDir.png", format = "PNG",  save_all=True, append_images=imgs[1:], duration=16, disposal=1, loop=0)

def test_SprColl_fromNameClsns() :
    params = {
        "names"             : 
            ["tm201_0" + str(i) for i in range(0,8)],
        "img_dir"           :
            "exported_data/char_tm_img",
        "clsn_dir"          :
            "exported_data/char_tm_col/JSONs"
    }

    coll = SprCollection.from_names_clsns(**params)
    imgs = coll.compile_sprites(True)
    imgs[0].save("tests/outputs/test_SprColl_FromNameClsns.png", format = "PNG",  save_all=True, append_images=imgs[1:], duration=16, disposal=1, loop=0)
