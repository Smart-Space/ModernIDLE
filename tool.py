import re
from tinui import ExpandPanel, HorizonPanel, VerticalPanel, BasicTinUI

vpanel: VerticalPanel|None = None
ui: BasicTinUI|None = None
def init_ui(_vpanel: VerticalPanel, _ui: BasicTinUI):
    global vpanel, ui
    vpanel = _vpanel
    ui = _ui

def search(text, pattern):
    ...
