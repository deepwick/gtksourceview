"""Show a file in a GtkSourceView 4 view with the 'deepwick' scheme from STYLES_DIR.

Usage: /usr/bin/python3 -I render_gsv4.py FILE STYLES_DIR
"""
import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkSource", "4")
from gi.repository import Gtk, GtkSource  # noqa: E402

path, styles = sys.argv[1], sys.argv[2]
schemes = GtkSource.StyleSchemeManager()
schemes.set_search_path([styles])
buffer = GtkSource.Buffer(
    language=GtkSource.LanguageManager.get_default().guess_language(path, None),
    style_scheme=schemes.get_scheme("deepwick"),
)
with open(path, encoding="utf-8") as f:
    buffer.set_text(f.read())
buffer.place_cursor(buffer.get_start_iter())
view = GtkSource.View(
    buffer=buffer, show_line_numbers=True, highlight_current_line=True, editable=False, monospace=True
)
scroller = Gtk.ScrolledWindow()
scroller.add(view)
window = Gtk.Window(title="Deepwick — GtkSourceView 4")
window.set_default_size(900, 680)
window.add(scroller)
window.connect("destroy", Gtk.main_quit)
window.show_all()
Gtk.main()
