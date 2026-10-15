"""Write gtksourceview-5/deepwick.xml and gtksourceview-4/deepwick.xml from the Deepwick palette.

GtkSourceView 4 rejects <metadata>, so the two files differ only there and in
current-line-number. Run from this directory: PYTHONPATH=../spec python3 generate.py
"""
from pathlib import Path
from xml.sax.saxutils import quoteattr

from deepwick_spec.palette import Palette, load_palette

ROOT = Path(__file__).parent
ATTRS = ("foreground", "background", "bold", "italic", "underline", "strikethrough")
# (style id, {attribute: palette name or "true"/"single"/"error"})
GLOBAL = [
    ("text", {"foreground": "foreground", "background": "background"}),
    ("selection", {"background": "selection"}),
    ("selection-unfocused", {"background": "overlay"}),
    ("cursor", {"foreground": "foreground"}),
    ("secondary-cursor", {"foreground": "muted"}),
    ("current-line", {"background": "surface"}),
    ("line-numbers", {"foreground": "muted", "background": "background"}),
    ("line-numbers-border", {"background": "background"}),
    ("right-margin", {"foreground": "overlay"}),
    ("draw-spaces", {"foreground": "overlay"}),
    ("background-pattern", {"background": "overlay"}),
    ("bracket-match", {"background": "overlay", "bold": "true"}),
    ("bracket-mismatch", {"foreground": "red", "underline": "single"}),
    ("search-match", {"background": "selection"}),
    ("map-overlay", {"background": "overlay"}),
    ("snippet-focus", {"background": "overlay"}),
]
CURRENT_LINE_NUMBER = {
    5: {"foreground": "foreground", "background": "surface"},
    4: {"background": "surface"},
}
SYNTAX = [
    ("def:comment", {"foreground": "comment", "italic": "true"}),
    ("def:shebang", {"foreground": "comment", "italic": "true"}),
    ("def:doc-comment-element", {"foreground": "comment", "italic": "true"}),
    ("def:keyword", {"foreground": "blue"}),
    ("def:special-constant", {"foreground": "blue"}),
    ("def:boolean", {"foreground": "blue"}),
    ("def:statement", {"foreground": "magenta"}),
    ("def:operator", {"foreground": "foreground"}),
    ("def:type", {"foreground": "teal"}),
    ("def:function", {"foreground": "yellow"}),
    ("def:builtin", {"foreground": "yellow"}),
    ("def:identifier", {"foreground": "lightBlue"}),
    ("def:constant", {"foreground": "cyan"}),
    ("def:string", {"foreground": "orange"}),
    ("def:character", {"foreground": "orange"}),
    ("def:inline-code", {"foreground": "orange"}),
    ("def:preformatted-section", {"foreground": "orange"}),
    ("def:special-char", {"foreground": "gold"}),
    ("def:number", {"foreground": "sage"}),
    ("def:preprocessor", {"foreground": "muted", "bold": "true"}),
    ("def:heading", {"foreground": "blue", "bold": "true"}),
    ("def:emphasis", {"italic": "true"}),
    ("def:strong-emphasis", {"bold": "true"}),
    ("def:link-text", {"foreground": "orange"}),
    ("def:link-destination", {"foreground": "orange", "underline": "single"}),
    ("def:net-address", {"foreground": "orange", "underline": "single"}),
    ("def:error", {"foreground": "red", "underline": "error"}),
    ("def:reserved", {"foreground": "red"}),
    ("def:deletion", {"foreground": "red", "strikethrough": "true"}),
    ("def:insertion", {"foreground": "green"}),
    ("def:note", {"foreground": "background", "background": "yellow", "bold": "true"}),
    ("python:module-handler", {"foreground": "magenta"}),
    ("python:class-name", {"foreground": "teal"}),
    ("python:decorator", {"foreground": "yellow"}),
    ("python:special-variable", {"foreground": "blue"}),
    ("python:builtin-object", {"foreground": "teal"}),
    ("c:keyword", {"foreground": "magenta"}),
    ("c:type-keyword", {"foreground": "blue"}),
    ("c:storage-class", {"foreground": "blue"}),
    ("c:type", {"foreground": "blue"}),
    ("c:included-file", {"foreground": "orange"}),
    ("c:common-defines", {"foreground": "cyan"}),
    ("js:regex", {"foreground": "rose"}),
    ("js:regex-group", {"foreground": "gold"}),
    ("js:directive", {"foreground": "orange"}),
    ("js:template-placeholder", {"foreground": "blue"}),
    ("js:built-in-property", {"foreground": "lightBlue"}),
    ("js:built-in-constructor", {"foreground": "teal"}),
    ("markdown:blockquote-marker", {"foreground": "muted"}),
    ("markdown:label", {"foreground": "lightBlue"}),
    ("html:element-name", {"foreground": "blue"}),
    ("xml:element-name", {"foreground": "blue"}),
    ("xml:attribute-name", {"foreground": "lightBlue"}),
]


def styles(version: int) -> list[tuple[str, dict]]:
    out = GLOBAL[:6] + [("current-line-number", CURRENT_LINE_NUMBER[version])] + GLOBAL[6:]
    return out + SYNTAX


def render(palette: Palette, version: int) -> str:
    used = sorted({v for _, a in styles(version) for k, v in a.items() if k in ("foreground", "background")})
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<!-- Deepwick is an unofficial theme derived from Polywick Blue by Polywick Studio (MIT).",
        f"     Generated by generate.py for GtkSourceView {version}. -->",
        '<style-scheme id="deepwick" name="Deepwick" version="1.0">',
        "  <author>Deepwick contributors</author>",
        "  <description>Deep navy with Visual Studio 2022 syntax colors.</description>",
    ]
    if version >= 5:
        lines += ["  <metadata>", '    <property name="variant">dark</property>', "  </metadata>"]
    lines.append("")
    lines += [f'  <color name="{name}" value="{palette.colors[name]}"/>' for name in used]
    lines.append("")
    for style_id, attrs in styles(version):
        rendered = " ".join(f"{k}={quoteattr(attrs[k])}" for k in ATTRS if k in attrs)
        lines.append(f'  <style name="{style_id}" {rendered}/>')
    lines += ["</style-scheme>", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    palette = load_palette()
    for version in (5, 4):
        out = ROOT / f"gtksourceview-{version}" / "deepwick.xml"
        out.parent.mkdir(exist_ok=True)
        out.write_text(render(palette, version), encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)}")
