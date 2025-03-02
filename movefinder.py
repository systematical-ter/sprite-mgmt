import enum
import re

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

        elif state == MODE.INMOVE :
            spr_res = re.match(sprite_regex, line)
            move_res = re.match(move_regex, line)
            if spr_res is not None :
                move_dict[mname].append((spr_res.group("name"), spr_res.group("nframes")))
                pass

            elif move_res is not None :
                mname = res.group("mname")
                move_dict[mname] = []

print(move_dict)