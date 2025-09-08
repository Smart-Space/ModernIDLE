import re
from tinui import ExpandPanel, HorizonPanel, VerticalPanel, BasicTinUI

vpanel: VerticalPanel|None = None
ui: BasicTinUI|None = None
def init_ui(_vpanel: VerticalPanel, _ui: BasicTinUI):
    global vpanel, ui
    vpanel = _vpanel
    ui = _ui

def __get_index_line(index):
    return int(index.split('.')[0])

def __get_text_line(textbox):
    sel_start=textbox.index('sel.first')
    sel_end=textbox.index('sel.last')
    if not sel_start:
        sel_start=textbox.index('insert')
        sel_end=textbox.index('insert')
    startline=int(__get_index_line(sel_start))
    endline=int(__get_index_line(sel_end))
    return startline, endline

def search(text, pattern):
    ...

def toggle_comment(textbox):
    startline, endline = __get_text_line(textbox)
    startchar=textbox.get(f'{startline}.0')
    if startchar == '#':
        for i in range(startline, endline+1):
            if textbox.get(f'{i}.0') == '#':
                textbox.delete(f'{i}.0', f'{i}.1')
    else:
        for i in range(startline, endline+1):
            textbox.insert(f'{i}.0', '#')
    return "break"

def left_move(textbox):
    startline, endline = __get_text_line(textbox)
    for i in range(startline, endline+1):
        if textbox.get(f'{i}.0', f'{i}.4') == '    ':
            textbox.delete(f'{i}.0', f'{i}.4')
    return "break"

def right_move(textbox):
    startline, endline = __get_text_line(textbox)
    for i in range(startline, endline+1):
        textbox.insert(f'{i}.0', '    ')
    return "break"