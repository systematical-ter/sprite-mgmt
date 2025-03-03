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
    frame: tk.Frame
    animating: bool
    animate_func: callable = None
    animate_func_args: Tuple = None

    def __init__(self, frame, values = []) :
        self.values = values
        self.frame = frame
        self.lb = tk.Listbox(frame, height=20,
                            selectmode="single", exportselection=False)
        self.replace_values(values)

    def provide_animation_function(self, func, args) :
        self.animate_func=func
        self.animate_func_args = args

    def replace_values(self, nu_values) :
        self.values = nu_values
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

    def move_down(self) :
        cur = int(self.lb.curselection()[0])
        i = 0
        if cur == len(self.values) - 1 :
            i = 0
        else :
            i = cur + 1
        self.lb.selection_clear(cur)
        self.lb.selection_set(i)

    def animate_loop(self) :
        if self.animating:
            self.move_down()
            if self.animate_func is not None :
                self.animate_func(*self.animate_func_args)
            self.frame.after(60, self.animate_loop)

    def start_animation(self) :
        self.animating=True
        self.frame.after(60, self.animate_loop)
    
    def stop_animation(self):
        self.animating=False

class CycleButton:
    options: List[str]
    funcs: List[callable]
    mode: int
    frame: tk.Frame

    def __init__(self, frame, options, funcs) :
        self.options=options
        self.mode = 0
        self.frame=frame
        self.funcs = []
        for f in funcs:
            self.funcs.append(self._add_toggle_to_funcs(f))

        self.button = ttk.Button(frame, text=self.options[self.mode])
        self.button.configure(command = self.funcs[self.mode])
    
    def _increment_mode(self) :
        if self.mode < len(self.options)-1 :
            self.mode = self.mode+1
        else :
            self.mode = 0

    def _add_toggle_to_funcs(self, func) :
        return lambda x=func: (
            self.go_next(),
            x()
            )

    def grid(self, **kwargs) :
        self.button.grid(kwargs)

    def go_next(self) :
        self._increment_mode()
        self.button.configure(command=self.funcs[self.mode], text=self.options[self.mode])

moves = movefinder.read_scr_file("scr_tm.py")
move_names = [m.name for m in moves]

root = tk.Tk("Move Display Preview","mfinder","MoveFinder")

moveselect_frame = ttk.Frame(root)
spriteframe = ttk.Frame(root)

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

playpause_button = CycleButton(moveselect_frame, ["Play","Pause"], [sprite_listbox.start_animation, sprite_listbox.stop_animation])

movebox.grid(column=0, row=0, columnspan=2, sticky="WENS")
label_listbox.grid(column=0,row=1)
sprite_listbox.grid(column=1,row=1)
playpause_button.grid(column=0,row=2,columnspan=2, sticky="WENS")

cv = SpriteDisplay(spriteframe)
update_sprite_display(sprite_listbox, cv)

sprite_listbox.provide_animation_function(update_sprite_display, (sprite_listbox, cv))
sprite_listbox.start_animation()

# def animate() :
#     sprite_listbox.move_down()
#     update_sprite_display(sprite_listbox, cv)
#     root.after(60, animate)
# root.after(60, animate)


movebox.bind('<<ComboboxSelected>>',
             lambda event:
             update_state_spinbox(movebox, label_listbox, sprite_listbox, cv, moves))
label_listbox.bind('<<ListboxSelect>>', 
              lambda event:
               update_sprite_spinbox(label_listbox, sprite_listbox, cv, moves[movebox.current()]))
sprite_listbox.bind('<<ListboxSelect>>',
                    lambda event:
                    update_sprite_display(sprite_listbox, cv))

moveselect_frame.pack(side="left")
spriteframe.pack(side="right")
root.mainloop()