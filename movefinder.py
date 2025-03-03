import enum
import re
from typing import Dict, List, Tuple
import gifify

scr_file = "exported_data/char_tm_scr/scr_tm.py"

class MODE(enum.Enum) :
    UNKNOWN = enum.auto()
    INSTATE = enum.auto()
    INMOVE = enum.auto()
    INIF = enum.auto()


class MoveSprites :
    name: str
    sprites: Dict[str, List[Tuple[str, int]]]
    curLabel: int
    relationships: List[Tuple[int, int]]

    def __init__(self, name) :
        self.name = name
        self.curLabel = '-1'
        self.sprites = {}
        self.sprites[self.curLabel] = []

        self.relationships = []

    def new_label(self, label) :
        self.sprites[label] = []
        self.curLabel = label
    
    def add_sprite(self, name, dur) :
        self.sprites[self.curLabel].append((name, dur))

    def new_relationship(self, l_from, l_to) :
        self.relationships.append((l_from, l_to))

    def get_current_label(self) :
        return self.curLabel
    
    def nLabels(self) -> int :
        return len(self.sprites.keys())
    
    def remove_empty_labels(self) -> None :
        for label in list(self.sprites.keys()) :
            if len(self.sprites[label]) == 0 :
                del self.sprites[label]
    
    def __str__(self) -> str:
        output = "MOVE %s\n" % self.name
        output += "  nLabels: %i\n" % int(self.nLabels())
        for s in list(self.sprites.keys()) :
            output += "  label: %s\n" % s
        for r in self.relationships :
            output += "  relation: %s -> %s\n" % (r[0], r[1])
        return output


def read_scr_file(scr_file:str) :
    sprite_regex_str = r"\s+sprite\('(?P<name>.+)', ?(?P<nframes>[0-9]+)\)"
    sprite_regex = re.compile(sprite_regex_str)

    move_regex_str = r"def (?P<mname>[a-zA-Z0-9_]+)\(\):"
    move_regex = re.compile(move_regex_str)

    label_regex_str = r"\s+label\((?P<lnum>[0-9]+)\)"
    label_regex = re.compile(label_regex_str)
    goto_label_regex_str = r"\s+sendToLabel\((?P<lnum>[0-9]+)\)"
    goto_label_regex = re.compile(goto_label_regex_str)

    state_leadin = "@State"

    state = MODE.UNKNOWN
    move_list: List[MoveSprites] = []

    with open(scr_file, 'r') as f:
        mname = ""
        curMove = None
        for line in f:
            line = line.rstrip()
            if state == MODE.UNKNOWN :
                # only check for a state definition,
                #   swap to the interesting state if we find it
                if line == state_leadin :
                    state = MODE.INSTATE

            elif state == MODE.INSTATE :
                res = re.match(move_regex, line)
                if res is not None :
                    mname = res.group("mname")
                    curMove = MoveSprites(mname)
                    move_list.append(curMove)
                    state = MODE.INMOVE
                res = None

            elif state == MODE.INMOVE :
                spr_res = re.match(sprite_regex, line)
                move_res = re.match(move_regex, line)
                label_res = re.match(label_regex, line)
                goto_label_res = re.match(goto_label_regex, line)

                if spr_res is not None :
                    if spr_res.group("name") != "keep" and spr_res.group("name") != "null" :
                        curMove.add_sprite(spr_res.group("name"), spr_res.group("nframes"))
                        #move_dict[mname].append((spr_res.group("name"), spr_res.group("nframes")))

                elif move_res is not None :
                    mname = move_res.group("mname")
                    curMove = MoveSprites(mname)
                    move_list.append(curMove)

                elif label_res is not None :
                    curMove.new_label(label_res.group("lnum"))
                
                elif goto_label_res is not None :
                    curMove.new_relationship(curMove.get_current_label(), goto_label_res.group("lnum"))
                
                spr_res = None
                move_res = None
                label_res = None
                goto_label_res = None
    for move in move_list :
        move.remove_empty_labels()
    
    final_move_list = list(filter(lambda x: True if x.nLabels() > 0 else False, move_list))
    return final_move_list

# move_of_interest = "EventTMLaghing2"
# move_of_interest = "NmlAtkDeadAngle"
# move_of_interest = "CmnActFDash"
# move_of_interest = "CmnActFWalk"
# move_of_interest = "EventTMKnife" # jiggly?
# move_of_interest = "EventTMAkire"
# move_of_interest = "EventTMChouhatsu"
# move_of_interest = "EventTMLaghing2"
# move_of_interest = "UltimateShot_AntiLand"
# #move_of_interest = "EventTMChouhatsuEnd"

# move_list = read_scr_file(scr_file)
# for i in range(0, len(move_list)) :
#     if move_list[i].name == "UltimateShot_AntiLand" :
#         print(move_list[i])
    #if len(move_list[i].relationships)> 0 :
    #    print(move_list[i])

#print(move_dict[move_of_interest])
#gifify.make_gif_from_namedurs(move_dict[move_of_interest], "frommove.gif")

# for move in move_dict.keys() :
#     if len(move_dict[move]) > 0 and len(move_dict[move]) < 20 :
#         gifify.make_gif_from_namedurs(move_dict[move], "gif_debugging/%s.gif" %move)
