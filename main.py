from tkinter import Tk
from tkinter.filedialog import askopenfilename, asksaveasfilename
import sys
import re
import idlelib.colorizer as idc
import idlelib.percolator as idp
import os

os.chdir(os.path.dirname(__file__))

from tinui import BasicTinUI, ExpandPanel, VerticalPanel, HorizonPanel, show_question
from tinui.theme.tinuilight import TinUILight

from process import init_shell_window, show_shell_window
import tool

filename = sys.argv[1] if len(sys.argv) > 1 else None
saved = True


def modifed_callback(event):
    global saved
    if not textbox.edit_modified():
        return
    if saved and filename:
        saved = False
        change_title(filename + " *")


def save_file(event):
    global saved
    if saved:
        return
    saved = True
    with open(filename, "w", encoding="utf-8") as f:
        f.write(textbox.get("1.0", "end-1c"))
    change_title(filename)
    textbox.edit_modified(False)


def save_as_file(event):
    global filename, saved
    if not saved:
        q = show_question(
            root,
            "Save changes?",
            "Do you want to save changes before saving as a new file?",
        )
        if q:
            save_file(None)
    _filename = asksaveasfilename(
        filetypes=[("Python files", "*.py"), ("All files", "*.*")]
    )
    if _filename:
        filename = _filename
        with open(filename, "w", encoding="utf-8") as f:
            f.write(textbox.get("1.0", "end-1c"))
        textbox.edit_reset()
        change_title(filename)
        saved = True
        textbox.edit_modified(False)


def open_file(event):
    global filename, saved
    if not saved:
        q = show_question(
            root,
            "Save changes?",
            "Do you want to save changes before opening a new file?",
        )
        if q:
            save_file(None)
    _filename = askopenfilename(
        filetypes=[("Python files", "*.py"), ("All files", "*.*")]
    )
    if _filename:
        filename = _filename
        with open(filename, "r", encoding="utf-8") as f:
            textbox.delete("1.0", "end")
            textbox.insert("1.0", f.read())
            textbox.mark_set("insert", "1.0")
        textbox.edit_reset()
        change_title(filename)
        saved = True
        textbox.edit_modified(False)
    return "break"


def toggle_comment(event):
    tool.toggle_comment(textbox)


def debug_callback(event):
    if filename:
        show_shell_window(filename, debug=True)


def run_script_callback(event):
    if filename:
        save_file(None)
        show_shell_window(filename)


def get_insert_index(event):
    index = textbox.index("insert")
    line, col = index.split(".")
    col = int(col) + 1
    ui.itemconfig(locp, text=f"Line: {line}, Column: {col}")


line_end_chars = ("pass", "return", "break", "continue", "raise", "yield")
line_pattern = re.compile(r"^(\s{0,})(.*)")


def add_newline(event):
    index = textbox.index("insert")
    line, _ = index.split(".")
    line = int(line)
    res = line_pattern.match(textbox.get(f"{line}.0", "insert"))
    textbox.insert("insert", "\n")
    chars = res.group(2)
    if not chars:
        textbox.insert(f"{line + 1}.0", res.group(1))
    elif chars[-1] == ":":
        textbox.insert(f"{line + 1}.0", res.group(1) + "    ")
    elif chars in line_end_chars or chars.startswith("return") or chars.startswith('yield') or chars.startswith('raise'):
        textbox.insert(f"{line + 1}.0", res.group(1)[:-4])
    else:
        textbox.insert(f"{line + 1}.0", res.group(1))
    return "break"


def add_tab(event):
    index = textbox.index("insert")
    line, _ = index.split(".")
    res = line_pattern.match(textbox.get(f"{line}.0", "insert"))
    if res.group(2):
        textbox.insert("insert", "\t")
    else:
        textbox.insert("insert", "    ")
    return "break"


def root_quit():
    if not saved:
        q = show_question(
            root, "Save changes?", "Do you want to save changes before quitting?"
        )
        if q:
            save_file(None)
    root.destroy()


def on_resize(event):
    rpanel.update_layout(0, 0, event.width, event.height)


def change_title(name):
    root.title(f"ModernIDLE - {name}")


root = Tk()
root.title("ModernIDLE")
root.geometry("700x700")
root.iconbitmap("logo.ico")

ui = BasicTinUI(root)
ui.pack(fill="both", expand=True)
uitheme = TinUILight(ui)

rpanel = ExpandPanel(ui)

vpanel = VerticalPanel(ui)
rpanel.set_child(vpanel)

toolpanel = HorizonPanel(ui, padding=(0, 5, 0, 0))
vpanel.add_child(toolpanel, 40)
barbutton = uitheme.add_barbutton(
    (0, 0),
    content=(
        ("", "\ue8e5", open_file),
        ("", "\ue74e", save_file),
        ("", "\ue792", save_as_file),
        "",
        ("", "\ue7a7", lambda _: textbox.edit_undo()),
        ("", "\ue7a6", lambda _: textbox.edit_redo()),
        ("", "\ue8a4", lambda _: tool.toggle_comment(textbox)),
        ("", "\ue8e4", lambda _: tool.left_move(textbox)),
        ("", "\ue8e2", lambda _: tool.right_move(textbox)),
        "",
        ("", "\ue71e", tool.search_show),
        ("", "\ue8ab", tool.replace_show),
        ("", "\ue751", tool.goto_line_show),
    ),
    anchor="w",
)[-1]
toolpanel.add_child(barbutton)
debug_button = uitheme.add_button2(
    (0, 0), text="Debug", icon="\uebe8", anchor="e", command=debug_callback
)[-1]
toolpanel.add_child(debug_button, weight=1)
accentbutton = uitheme.add_accentbutton(
    (0, 0), text="Run", icon="\ue768", anchor="e", command=run_script_callback
)[-1]
toolpanel.add_child(accentbutton)

textboxs = uitheme.add_textbox((0, 0), font="Consolas 12", scrollbar=True)
textpanel = ExpandPanel(ui, textboxs[-1], (0, 3, 3, 0))
vpanel.add_child(textpanel, weight=1)
textbox = textboxs[0]
ui.textbox = textbox
textbox.config(wrap="none", undo=True)
idc.color_config(textbox)
p = idp.Percolator(textbox)
d = idc.ColorDelegator()
p.insertfilter(d)

locp = uitheme.add_paragraph(
    (0, 0), font="Consolas 11", text="Line: 1, Column: 1", anchor="w"
)
vpanel.add_child(locp)

root.protocol("WM_DELETE_WINDOW", root_quit)

ui.bind("<Configure>", on_resize)

textbox.bind("<Control-o>", open_file)
textbox.bind("<Control-s>", save_file)
textbox.bind("<Control-Shift-S>", save_as_file)
textbox.bind("<F5>", run_script_callback)
textbox.bind("<Control-z>", lambda _: textbox.edit_undo())
textbox.bind("<Control-y>", lambda _: textbox.edit_redo())
textbox.bind("<Control-/>", lambda _: tool.toggle_comment(textbox))
textbox.bind("<Control-[>", lambda _: tool.left_move(textbox))
textbox.bind("<Control-]>", lambda _: tool.right_move(textbox))
textbox.bind("<KeyRelease>", get_insert_index)
textbox.bind("<ButtonRelease-1>", get_insert_index)
textbox.bind("<Control-f>", tool.search_show)
textbox.bind("<Control-h>", tool.replace_show)
textbox.bind("<Control-g>", tool.goto_line_show)
textbox.bind("<Return>", add_newline)
textbox.bind("<Tab>", add_tab)

root.update()
textbox.focus_set()

if filename:
    with open(filename, "r", encoding="utf-8") as f:
        textbox.insert("1.0", f.read())
        textbox.mark_set("insert", "1.0")
    textbox.edit_reset()
    textbox.edit_modified(False)
    change_title(filename)
textbox.bind("<<Modified>>", modifed_callback, add=True)

tool.init_ui(vpanel, uitheme)
init_shell_window()

textbox.tag_configure("sel", background="#ADD6FF", foreground="")

root.mainloop()
