import importlib.util
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import pytest

from deepwick_spec.check_port import check_port
from deepwick_spec.palette import load_palette

REPO = Path(__file__).resolve().parents[1]
SAMPLES = REPO.parent / "spec" / "samples"
PALETTE = load_palette()
C = PALETTE.colors
FILES = {5: REPO / "gtksourceview-5" / "deepwick.xml", 4: REPO / "gtksourceview-4" / "deepwick.xml"}
TYPELIB = Path("/usr/lib64/girepository-1.0/GtkSource-4.typelib")
EXPECTED = {
    "text": ("foreground", "background"),
    "selection": (None, "selection"),
    "current-line": (None, "surface"),
    "line-numbers": ("muted", "background"),
    "search-match": (None, "selection"),
    "def:comment": ("comment", None),
    "def:keyword": ("blue", None),
    "def:statement": ("magenta", None),
    "def:operator": ("foreground", None),
    "def:type": ("teal", None),
    "def:function": ("yellow", None),
    "def:identifier": ("lightBlue", None),
    "def:constant": ("cyan", None),
    "def:string": ("orange", None),
    "def:special-char": ("gold", None),
    "def:number": ("sage", None),
    "def:preprocessor": ("muted", None),
    "def:heading": ("blue", None),
    "python:module-handler": ("magenta", None),
    "python:decorator": ("yellow", None),
    "python:special-variable": ("blue", None),
    "c:keyword": ("magenta", None),
    "c:included-file": ("orange", None),
    "js:regex": ("rose", None),
}


def load(version):
    return ET.parse(FILES[version]).getroot()


def resolved_styles(version):
    root = load(version)
    colors = {c.get("name"): c.get("value") for c in root.iter("color")}
    styles = {}
    for s in root.iter("style"):
        styles[s.get("name")] = {
            k: colors.get(v, v) if k in ("foreground", "background") else v for k, v in s.attrib.items()
        }
    return styles


@pytest.mark.parametrize("version", [5, 4])
def test_root(version):
    root = load(version)
    assert root.tag == "style-scheme"
    assert root.get("id") == "deepwick"
    assert root.get("name") == "Deepwick"
    assert root.get("version") == "1.0"


def test_gsv5_is_dark():
    variant = load(5).find("metadata/property[@name='variant']")
    assert variant is not None and variant.text == "dark"


def test_gsv4_file_has_no_metadata():
    assert load(4).find("metadata") is None
    assert "weight" not in FILES[4].read_text(encoding="utf-8")


def test_same_style_ids():
    assert set(resolved_styles(5)) == set(resolved_styles(4))


@pytest.mark.parametrize("version", [5, 4])
def test_colors_are_palette(version):
    allowed = {v.lower() for v in C.values()}
    for c in load(version).iter("color"):
        assert c.get("value").lower() == C[c.get("name")].lower()
        assert c.get("value").lower() in allowed


@pytest.mark.parametrize("version", [5, 4])
@pytest.mark.parametrize("style_id", sorted(EXPECTED))
def test_style_colors(version, style_id):
    fg, bg = EXPECTED[style_id]
    style = resolved_styles(version)[style_id]
    if fg:
        assert style.get("foreground", "").lower() == C[fg].lower()
    if bg:
        assert style.get("background", "").lower() == C[bg].lower()


@pytest.mark.parametrize("version", [5, 4])
def test_comment_italic_preprocessor_bold(version):
    styles = resolved_styles(version)
    assert styles["def:comment"].get("italic") == "true"
    assert styles["def:preprocessor"].get("bold") == "true"


def test_committed_files_match_generator():
    spec = importlib.util.spec_from_file_location("generate", REPO / "generate.py")
    generate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generate)
    for version, path in FILES.items():
        assert path.read_text(encoding="utf-8") == generate.render(PALETTE, version)


@pytest.mark.skipif(not TYPELIB.exists(), reason="needs the GtkSource-4 typelib")
def test_gsv4_scheme_loads():
    code = (
        "import sys, gi\n"
        "gi.require_version('GtkSource', '4')\n"
        "from gi.repository import GtkSource\n"
        "m = GtkSource.StyleSchemeManager()\n"
        "m.set_search_path([sys.argv[1]])\n"
        "s = m.get_scheme('deepwick')\n"
        "st = s.get_style('def:comment')\n"
        "print(s.get_name(), st.props.foreground, st.props.italic)\n"
    )
    result = subprocess.run(
        ["/usr/bin/python3", "-I", "-c", code, str(FILES[4].parent)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert "could not load" not in result.stderr
    assert result.stdout.split() == ["Deepwick", C["comment"], "True"]


def test_port_conventions():
    assert check_port(REPO, PALETTE.allowed_hex()) == []


VSHOT = REPO.parent / "tools" / "vshot"
needs_vshot = pytest.mark.skipif(
    not (VSHOT.is_file() and shutil.which("kwin_wayland") and shutil.which("spectacle") and shutil.which("magick")),
    reason="needs tools/vshot, kwin_wayland, spectacle and ImageMagick",
)


def vshot(base, *cmd, **env):
    """Run cmd off-screen with SHOT_XDG=base; return the screenshot's color histogram."""
    out = base / "shot.png"
    subprocess.run(
        [str(VSHOT), str(out), "--", *cmd],
        env={**os.environ, "SHOT_XDG": str(base), **env},
        check=True,
        timeout=120,
    )
    hist = subprocess.run(
        ["magick", str(out), "-alpha", "off", "-format", "%c", "histogram:info:-"],
        capture_output=True, text=True, check=True,
    ).stdout
    counts = Counter()
    for m in re.finditer(r"^\s*(\d+):.*?#([0-9A-Fa-f]{6})", hist, re.M):
        counts["#" + m.group(2).lower()] += int(m.group(1))
    return counts


def px(counts, name):
    return counts[PALETTE.colors[name].lower()]


def render(base, styles_dir):
    return vshot(
        base, "/usr/bin/python3", "-I", str(REPO / "tests" / "render_gsv4.py"),
        str(SAMPLES / "sample.py"), str(styles_dir),
    )


@needs_vshot
@pytest.mark.skipif(not TYPELIB.exists(), reason="needs the GtkSource-4 typelib")
def test_gsv4_render(tmp_path):
    counts = render(tmp_path, FILES[4].parent)
    assert px(counts, "background") > 20000
    assert px(counts, "surface") > 1000, "no current-line highlight"


@needs_vshot
@pytest.mark.skipif(not TYPELIB.exists(), reason="needs the GtkSource-4 typelib")
def test_gsv4_render_without_scheme_is_not_deepwick(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    counts = render(tmp_path, empty)
    assert px(counts, "background") < 500


RNG = Path("/usr/share/gtksourceview-4/styles/styles.rng")


@pytest.mark.skipif(not (RNG.exists() and shutil.which("xmllint")), reason="needs styles.rng and xmllint")
def test_gsv4_validates_against_styles_rng():
    result = subprocess.run(["xmllint", "--noout", "--relaxng", str(RNG), str(FILES[4])], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_gsv4_current_line_number_contrast():
    from deepwick_spec.color import contrast_ratio
    style = resolved_styles(4)["current-line-number"]
    assert contrast_ratio(C["muted"], style.get("background", C["background"])) >= 4.5


@pytest.mark.parametrize("version", [5, 4])
def test_deletion_is_red_only(version):
    style = resolved_styles(version)["def:deletion"]
    assert style.get("foreground", "").lower() == C["red"].lower()
    assert "strikethrough" not in style


def _runtime_available():
    return shutil.which("flatpak") and subprocess.run(
        ["flatpak", "info", "org.gnome.Platform//51"], capture_output=True).returncode == 0


@pytest.mark.skipif(not _runtime_available(), reason="needs the GNOME 51 flatpak runtime")
def test_gsv5_scheme_loads(tmp_path):
    code = (
        "import sys, gi\n"
        "gi.require_version('GtkSource', '5')\n"
        "from gi.repository import GtkSource\n"
        "m = GtkSource.StyleSchemeManager()\n"
        "m.set_search_path([sys.argv[1]])\n"
        "s = m.get_scheme('deepwick')\n"
        "st = s.get_style('def:comment')\n"
        "print(s.get_name(), s.get_metadata('variant'), st.props.foreground, st.props.italic)\n"
    )
    result = subprocess.run(
        ["flatpak", "run", f"--filesystem={FILES[5].parent}:ro", "--command=python3", "org.gnome.Platform//51",
         "-c", code, str(FILES[5].parent)],
        capture_output=True, text=True, env={**os.environ, "HOME": str(tmp_path)}, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "could not load" not in result.stderr
    assert result.stdout.split() == ["Deepwick", "dark", C["comment"], "True"]
