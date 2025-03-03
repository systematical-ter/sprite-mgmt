import tkinter as tk
from tkinter import ttk
from typing import List, Tuple
from PIL import Image
import movefinder

class SpriteDisplay :
    img: tk.Image
    canvas: tk.Canvas

    def __init__(self, frame):
        self.canvas = tk.Canvas(frame, width=500, height=500)
        self.canvas.grid(column=2,row=0,rowspan=3)

    def set_image(self, loc) :
        self.img = tk.PhotoImage(file = loc)
        self.canvas.create_image((0,0), anchor=tk.NW, image=self.img)

class OptionListbox:
    values : List[str]
    lb: tk.Listbox
    svar: tk.StringVar

    def __init__(self, frame, values = []) :
        self.values = values
        self.lb = tk.Listbox(frame, height=20,
                            selectmode="single", exportselection=False)
        self.replace_values(values)

    def replace_values(self, nu_values) :
        self.lb.delete(0, tk.END)
        for s in nu_values :
            self.lb.insert(tk.END, s)
        self.lb.selection_set(0)

    def get_selected(self) -> str:
        return self.lb.get(self.lb.curselection())
    
    def grid(self, **kwargs) :
        self.lb.grid(kwargs)

    def bind(self, event, fnc) :
        self.lb.bind(event, fnc)

moves = movefinder.read_scr_file("scr_tm.py")
move_names = [m.name for m in moves]

root = tk.Tk("Move Display Preview","mfinder","MoveFinder")
w = tk.Label(root, text="Move Finder")

moveselect_frame = ttk.Frame(root)

move_name_var = tk.StringVar()
movebox = ttk.Combobox(moveselect_frame, textvariable=move_name_var)
movebox['values'] = move_names
movebox.current(0)

current_move = moves[movebox.current()]
current_poss_states = list(current_move.sprites.keys())

def update_state_spinbox(mbx:ttk.Combobox, labell:OptionListbox, spritel:OptionListbox, cvs: SpriteDisplay, moves:List[movefinder.MoveSprites]) :
    print(moves[mbx.current()])
    name = mbx.current()
    states = list(moves[name].sprites.keys())
    labell.replace_values(states)

    update_sprite_spinbox(labell, spritel, cvs, moves[mbx.current()])

label_listbox = OptionListbox(moveselect_frame, current_poss_states)

global img_tk
def update_sprite_spinbox(labell:OptionListbox, spritel:OptionListbox, 
                          cvs: SpriteDisplay, moves:movefinder.MoveSprites) :
    name = labell.get_selected()
    sprites = [x[0] for x in moves.sprites[name]]
    spritel.replace_values(sprites)
    update_sprite_display(spritel, cvs)

def update_sprite_display(spritel:OptionListbox, cvs: SpriteDisplay) :
    name = spritel.get_selected()
    path = "C:/Users/shpil/Documents/bbcf modding exports/TerumiFiles/char_tm_img/" + name + ".png"
    cvs.set_image(path)


curr_poss_sprites = current_move.sprites[str(label_listbox.get_selected())]
sprite_listbox = OptionListbox(moveselect_frame, [x[0] for x in curr_poss_sprites])

moveselect_frame.grid(column=0, row=0)
movebox.grid(column=0, row=0)
label_listbox.grid(column=0,row=1)
sprite_listbox.grid(column=1,row=1)


cv = SpriteDisplay(moveselect_frame)
update_sprite_display(sprite_listbox, cv)

movebox.bind('<<ComboboxSelected>>',
             lambda event:
             update_state_spinbox(movebox, label_listbox, sprite_listbox, cv, moves))
label_listbox.bind('<<ListboxSelect>>', 
              lambda event:
               update_sprite_spinbox(label_listbox, sprite_listbox, cv, moves[movebox.current()]))
sprite_listbox.bind('<<ListboxSelect>>',
                    lambda event:
                    update_sprite_display(sprite_listbox, cv))
root.mainloop()