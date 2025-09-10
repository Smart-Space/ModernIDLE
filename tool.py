import re

from tinui import ExpandPanel, HorizonPanel, VerticalPanel

vpanel: VerticalPanel|None = None
def init_ui(_vpanel: VerticalPanel, _ui):
    global vpanel, ui
    vpanel = _vpanel
    ui = _ui
    search_init()

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

search_show_flag = False
case_flag = False
regex_flag = False
def search_init():
    global search_entry, search_panel
    search_panel = HorizonPanel(ui.ui, spacing=5, padding=(0,10,0,5))
    exppanel = ExpandPanel(ui.ui)
    entryd = ui.add_entry((0,0), width=100, anchor='w')
    exppanel.set_child(entryd[-1])
    search_panel.add_child(exppanel, weight=1)
    tbuttond = ui.add_togglebutton((0,0), text='Aa', anchor='w', command=toggle_case)
    search_panel.add_child(tbuttond[-1])
    tbuttond2 = ui.add_togglebutton((0,0), text='.*?', anchor='w', command=toggle_regex)
    search_panel.add_child(tbuttond2[-1])
    buttond = ui.add_toolbutton((0,0), icon='\uE74B', text='', anchor='w', command=lambda e: search_next(ui.ui.textbox))
    search_panel.add_child(buttond[-1])
    buttond2 = ui.add_toolbutton((0,0), icon='\uE74A', text='', anchor='w', command=lambda e: search_prev(ui.ui.textbox))
    search_panel.add_child(buttond2[-1])
    ui.ui.addtag_withtag('search', entryd[-1])
    ui.ui.addtag_withtag('search', buttond[-1])
    ui.ui.addtag_withtag('search', buttond2[-1])
    ui.ui.addtag_withtag('search', tbuttond[-1])
    ui.ui.addtag_withtag('search', tbuttond2[-1])
    search_entry = entryd[0]
    search_entry.bind('<Escape>', search_hide)
    search_entry.bind('<Return>', lambda e: search_next(ui.ui.textbox))
    search_entry.bind('<Shift-Return>', lambda e: search_prev(ui.ui.textbox))
    ui.ui.moveto('search', 0, -50)

def toggle_case(e):
    global case_flag
    case_flag = not case_flag

def toggle_regex(e):
    global regex_flag
    regex_flag = not regex_flag

def search_show(e=None):
    global search_show_flag
    selstart = ui.ui.textbox.index('sel.first')
    selend = ui.ui.textbox.index('sel.last')
    if selstart:
        search_entry.delete(0, 'end')
        search_entry.insert(0, ui.ui.textbox.get(selstart, selend))
    if search_show_flag:
        search_entry.focus_set()
        return
    search_show_flag = True
    vpanel.add_child(search_panel, 35, index=1)
    search_entry.focus_set()
    ui.ui.event_generate('<Configure>', width=ui.ui.winfo_width(), height=ui.ui.winfo_height())

def search_hide(e=None):
    global search_show_flag
    search_show_flag = False
    vpanel.pop_child(1)
    ui.ui.moveto('search', 0, -50)
    ui.ui.textbox.focus_set()
    ui.ui.event_generate('<Configure>', width=ui.ui.winfo_width(), height=ui.ui.winfo_height())

def __get_real_pattern_from_re(textbox, pattern, index):
    if not regex_flag:
        return pattern
    line = __get_index_line(index)
    chars = textbox.get(index, f'{line}.end')
    flag = 0
    if not case_flag:
        flag = re.IGNORECASE
    res = re.search(pattern, chars, flag)
    return res.group(0)

def search_next(textbox):
    index = textbox.index('insert') + '+1c'
    pattern = search_entry.get()
    if not pattern:
        return
    res = textbox.search(pattern, index, forwards=True, stopindex='end', nocase=not case_flag, regexp=regex_flag)
    show_search_result(textbox, pattern, res)

def search_prev(textbox):
    index = textbox.index('insert')
    pattern = search_entry.get()
    if not pattern:
        return
    res = textbox.search(pattern, index, backwards=True, stopindex='1.0', nocase=not case_flag, regexp=regex_flag)
    show_search_result(textbox, pattern, res)

def show_search_result(textbox, pattern, res):
    if res:
        textbox.tag_remove('sel', '1.0', 'end')
        textbox.mark_set('insert', res)
        pattern = __get_real_pattern_from_re(textbox, pattern, res)
        textbox.tag_add('sel', res, res + '+%dc' % len(pattern))
        textbox.see('insert')
    else:
        textbox.bell()

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