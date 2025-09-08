from tkinter import Tk
from tkinter.filedialog import askopenfilename, asksaveasfilename
import sys
import idlelib.colorizer as idc
import idlelib.percolator as idp

from tinui import BasicTinUI, ExpandPanel, VerticalPanel, HorizonPanel, show_question
from tinui.theme.tinuilight import TinUILight

from process import run_script
import tool

filename = sys.argv[1] if len(sys.argv) > 1 else None
saved = True


def modifed_callback(event):
    global saved
    if not textbox.edit_modified():
        return
    if saved and filename:
        saved = False
        change_title(filename + ' *')

def save_file(event):
    global saved
    if saved:
        return
    saved = True
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(textbox.get('1.0', 'end-1c'))
    change_title(filename)
    textbox.edit_modified(False)

def save_as_file(event):
    global filename, saved
    if not saved:
        q = show_question(root, 'Save changes?', 'Do you want to save changes before saving as a new file?')
        if q:
            save_file(None)
    _filename = asksaveasfilename(filetypes=[('Python files', '*.py'), ('All files', '*.*')])
    if _filename:
        filename = _filename
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(textbox.get('1.0', 'end-1c'))
        textbox.edit_reset()
        change_title(filename)
        saved = True
        textbox.edit_modified(False)

def open_file(event):
    global filename, saved
    if not saved:
        q = show_question(root, 'Save changes?', 'Do you want to save changes before opening a new file?')
        if q:
            save_file(None)
    _filename = askopenfilename(filetypes=[('Python files', '*.py'), ('All files', '*.*')])
    if _filename:
        filename = _filename
        with open(filename, 'r', encoding='utf-8') as f:
            textbox.delete('1.0', 'end')
            textbox.insert('1.0', f.read())
        textbox.edit_reset()
        change_title(filename)
        saved = True
        textbox.edit_modified(False)
    return "break"

def toggle_comment(event):
    tool.toggle_comment(textbox)

def run_script_callback(event):
    if filename:
        run_script(filename)


def root_quit():
    if not saved:
        q = show_question(root, 'Save changes?', 'Do you want to save changes before quitting?')
        if q:
            save_file(None)
    root.destroy()

def on_resize(event):
    rpanel.update_layout(0, 0, event.width, event.height)

def change_title(name):
    root.title(f'ModernIDLE - {name}')


root = Tk()
root.title("ModernIDLE")
root.geometry("700x700")

ui = BasicTinUI(root)
ui.pack(fill="both", expand=True)
uitheme = TinUILight(ui)

rpanel = ExpandPanel(ui)

vpanel = VerticalPanel(ui)
rpanel.set_child(vpanel)

toolpanel = HorizonPanel(ui, padding=(0,5,0,0))
vpanel.add_child(toolpanel, 40)
barbutton = uitheme.add_barbutton((0,0), content=(
    ('','\uE8E5',open_file),
    ('','\uE74E',save_file),
    ('','\uE792',save_as_file),
    '',
    ('','\uE7A7',lambda e: textbox.edit_undo()),
    ('','\uE7A6',lambda e: textbox.edit_redo()),
    ('','\uE8A4',lambda e: tool.toggle_comment(textbox)),
    ('','\uE8E4',lambda e: tool.left_move(textbox)),
    ('','\uE8E2',lambda e: tool.right_move(textbox)),
    ), anchor='w')[-1]
toolpanel.add_child(barbutton, weight=1)
accentbutton = uitheme.add_accentbutton((0,0), text='Run', icon='\uE768', anchor='w', command=run_script_callback)[-1]
toolpanel.add_child(accentbutton)

textboxs = uitheme.add_textbox((0,0), font='Consolas 12', scrollbar=True)
textpanel = ExpandPanel(ui, textboxs[-1], (0,3,3,0))
vpanel.add_child(textpanel, weight=1)
textbox = textboxs[0]
textbox.config(wrap='none', undo=True)
idc.color_config(textbox)
p = idp.Percolator(textbox)
d = idc.ColorDelegator()
p.insertfilter(d)

root.protocol("WM_DELETE_WINDOW", root_quit)

ui.bind("<Configure>", on_resize)

textbox.bind("<Control-o>", open_file)
textbox.bind("<Control-s>", save_file)
textbox.bind("<Control-Shift-S>", save_as_file)
textbox.bind("<F5>", run_script_callback)
textbox.bind("<Control-z>", lambda e: textbox.edit_undo())
textbox.bind("<Control-y>", lambda e: textbox.edit_redo())
textbox.bind("<Control-/>", lambda e: tool.toggle_comment(textbox))
textbox.bind("<Control-[>", lambda e: tool.left_move(textbox))
textbox.bind("<Control-]>", lambda e: tool.right_move(textbox))

root.update()
textbox.focus_set()

if filename:
    with open(filename, 'r', encoding='utf-8') as f:
        textbox.insert('1.0', f.read())
    textbox.edit_reset()
    textbox.edit_modified(False)
    change_title(filename)
textbox.bind("<<Modified>>", modifed_callback)

tool.init_ui(vpanel, ui)

root.mainloop()
