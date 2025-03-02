import enum
import re
import gifify

scr_file = "exported_data/char_tm_scr/scr_tm.py"

class MODE(enum.Enum) :
    UNKNOWN = enum.auto()
    INSTATE = enum.auto()
    INMOVE = enum.auto()

sprite_regex_str = r"\s+sprite\('(?P<name>.+)', ?(?P<nframes>[0-9]+)\)"
sprite_regex = re.compile(sprite_regex_str)

move_regex_str = r"def (?P<mname>[a-zA-Z0-9]+)\(\):"
move_regex = re.compile(move_regex_str)

state_leadin = "@State"

state = MODE.UNKNOWN

move_dict = {}

with open(scr_file, 'r') as f:
    mname = ""
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
                move_dict[mname] = []
                state = MODE.INMOVE
            res = None

        elif state == MODE.INMOVE :
            spr_res = re.match(sprite_regex, line)
            move_res = re.match(move_regex, line)
            if spr_res is not None :
                if spr_res.group("name") != "keep" and spr_res.group("name") != "null" :
                    move_dict[mname].append((spr_res.group("name"), spr_res.group("nframes")))

            elif move_res is not None :
                #print(mname)
                mname = move_res.group("mname")
                move_dict[mname] = []
            
            spr_res = None
            move_res = None

move_of_interest = "EventTMLaghing2"
move_of_interest = "NmlAtkDeadAngle"
move_of_interest = "CmnActFDash"
move_of_interest = "CmnActFWalk"
move_of_interest = "EventTMKnife" # jiggly?
move_of_interest = "EventTMAkire"
move_of_interest = "EventTMChouhatsu"
move_of_interest = "EventTMLaghing2"
#move_of_interest = "EventTMChouhatsuEnd"
#print(move_dict.keys())
#print(move_dict[move_of_interest])
gifify.make_gif_from_namedurs(move_dict[move_of_interest], "frommove.gif")

# for move in move_dict.keys() :
#     if len(move_dict[move]) > 0 and len(move_dict[move]) < 20 :
#         gifify.make_gif_from_namedurs(move_dict[move], "gif_debugging/%s.gif" %move)
