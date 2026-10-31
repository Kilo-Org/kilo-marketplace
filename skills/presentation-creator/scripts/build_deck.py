#!/usr/bin/env python3
"""Build a themed .pptx deck from a JSON deck spec.

Usage:
    python3 build_deck.py deck.json -o deck.pptx [--force]

The JSON spec contract is documented in the skill's SKILL.md. Output is
deterministic for a given spec, theme, and python-pptx version.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.dml.color import RGBColor
    from pptx.enum.chart import XL_CHART_TYPE
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.util import Emu, Inches, Pt
except ModuleNotFoundError:  # pragma: no cover - environment guard
    sys.stderr.write(
        "error: python-pptx is not installed. Install it with\n"
        "  python3 -m venv /tmp/pptx-venv && /tmp/pptx-venv/bin/pip install python-pptx\n"
        "or `pip install --user python-pptx`.\n"
    )
    raise SystemExit(2)


THEMES: dict[str, dict] = {
    "clean-light": {
        "bg": "FFFFFF",
        "surface": "F2F4F7",
        "text": "1A1A1A",
        "muted": "5A6472",
        "accent": "1F6FEB",
        "accent2": "0E9F6E",
        "accent3": "D9381E",
        "band": "1F6FEB",
        "band_text": "FFFFFF",
        "title_font": "Segoe UI Semibold",
        "body_font": "Segoe UI",
    },
    "corporate-blue": {
        "bg": "FFFFFF",
        "surface": "E8EEF7",
        "text": "0B1F33",
        "muted": "4A5A6A",
        "accent": "0B3D91",
        "accent2": "2E7DD1",
        "accent3": "C9A227",
        "band": "0B3D91",
        "band_text": "FFFFFF",
        "title_font": "Calibri",
        "body_font": "Calibri",
    },
    "dark-tech": {
        "bg": "0D1117",
        "surface": "161B22",
        "text": "E6EDF3",
        "muted": "8B949E",
        "accent": "58A6FF",
        "accent2": "3FB950",
        "accent3": "F85149",
        "band": "0B3D91",
        "band_text": "E6EDF3",
        "title_font": "Segoe UI Semibold",
        "body_font": "Segoe UI",
    },
}

ASPECTS = {
    "16:9": (13.333, 7.5),
    "4:3": (10.0, 7.5),
}

LAYOUTS = {
    "title",
    "section",
    "bullets",
    "two_column",
    "image",
    "table",
    "quote",
    "chart",
    "closing",
    "stats",
    "timeline",
    "comparison",
    "cards",
    "before_after",
    "problem_solution_impact",
    "kpi_row",
    "flow",
    "process_flow",
    "process_vertical",
    "image_caption",
}

LAYOUT_ALIASES = {
    "kpi": "stats",
    "kpi_row": "stats",
    "process": "timeline",
    "process_steps": "timeline",
    "card": "cards",
    "card_grid": "cards",
    "psi": "problem_solution_impact",
    "problem-solution-impact": "problem_solution_impact",
    "before/after": "before_after",
    "before-after": "before_after",
    "comparison_table": "table",
    "image_caption": "image",
    "captioned_image": "image",
    "figure": "image",
    "flow": "flow",
    "process_flow": "flow",
    "chevrons": "flow",
    "arrow_flow": "flow",
    "process_vertical": "process_vertical",
    "vertical_process": "process_vertical",
    "vertical_timeline": "process_vertical",
}


def rgb(hexstr: str) -> RGBColor:
    hexstr = str(hexstr).lstrip("#")
    return RGBColor(int(hexstr[0:2], 16), int(hexstr[2:4], 16), int(hexstr[4:6], 16))


def _hex_luminance(hexstr: str) -> float:
    hexstr = str(hexstr).lstrip("#")
    try:
        r = int(hexstr[0:2], 16) / 255.0
        g = int(hexstr[2:4], 16) / 255.0
        b = int(hexstr[4:6], 16) / 255.0
    except Exception:
        return 0.5

    def ch(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def _is_path(value) -> bool:
    return isinstance(value, str) and ("/" in value or "\\" in value or "." in Path(value).name)


class DeckBuilder:
    def __init__(self, spec: dict):
        theme_spec = spec.get("theme", "clean-light")
        palette_override = spec.get("palette")
        if isinstance(theme_spec, dict):
            palette_override = {**(theme_spec.get("palette") or {}), **(palette_override or {})}
            theme_spec = theme_spec.get("name") or theme_spec.get("base") or "clean-light"

        base_name = "clean-light" if theme_spec == "custom" else theme_spec
        if base_name not in THEMES:
            raise ValueError(
                f"unknown theme {theme_spec!r}; choose from {sorted(THEMES)} or 'custom'"
            )
        self.theme = dict(THEMES[base_name])
        if isinstance(palette_override, dict):
            for key, value in palette_override.items():
                if key in self.theme and isinstance(value, str):
                    self.theme[key] = value.lstrip("#")

        # fonts
        self.theme.setdefault("title_font_fallbacks", [])
        self.theme.setdefault("body_font_fallbacks", [])
        self._apply_fonts(spec, theme_spec)

        self.theme_name = str(theme_spec)
        if isinstance(palette_override, dict) and palette_override:
            self.theme_name = f"{self.theme_name} (palette override)"

        aspect = spec.get("aspect", "16:9")
        if aspect not in ASPECTS:
            raise ValueError(f"unknown aspect {aspect!r}; choose from {sorted(ASPECTS)}")
        width_in, height_in = ASPECTS[aspect]

        self.prs = Presentation()
        self.prs.slide_width = Inches(width_in)
        self.prs.slide_height = Inches(height_in)
        self.width_in = width_in
        self.height_in = height_in
        self.margin = 0.6
        self.content_w = width_in - 2 * self.margin

        scale = 1.0 if aspect == "16:9" else 0.93
        self.sizes = {
            "deck_title": round(40 * scale),
            "title": round(30 * scale),
            "section": round(34 * scale),
            "body": round(18 * scale),
            "caption": 12,
            "quote": round(26 * scale),
        }
        self._blank = self.prs.slide_layouts[6]
        self.deck_title = spec.get("title")
        self.deck_subtitle = spec.get("subtitle")
        self._slide_no = 0
        self.accent_bar = bool(spec.get("accent_bar", True))
        self.accent_bar_color = spec.get("accent_bar_color", self.theme["accent"])
        self.accent_bar_height = float(spec.get("accent_bar_height", 0.03))
        self.accent_bar_width = spec.get("accent_bar_width", None)
        self.card_padding = 0.25
        self.band_color = spec.get("band_color", self.theme["band"])
        self.band_text_color = spec.get("band_text_color", self.theme["band_text"])
        self.band_height = spec.get("band_height", None)
        self.title_band_color = spec.get("title_band_color", self.band_color)
        self.title_band_height = float(spec.get("title_band_height", 2.4))
        self.closing_band_color = spec.get("closing_band_color", self.band_color)
        self.section_band_color = spec.get("section_band_color", self.theme["accent"])
        self.section_band_height = float(spec.get("section_band_height", 0.1))

        # footer options
        footer = spec.get("footer", True)
        if isinstance(footer, bool):
            footer = {"enabled": footer}
        if not isinstance(footer, dict):
            footer = {"enabled": True}
        self.footer = {
            "enabled": footer.get("enabled", True),
            "page_numbers": footer.get("page_numbers", True),
            "title": footer.get("title", True),
            "confidential": footer.get("confidential", spec.get("confidential", False)),
            "mark": footer.get("mark", footer.get("text", "")),
            "position": footer.get("position", "bottom"),
        }
        if spec.get("confidential") is not None and "confidential" not in footer:
            self.footer["confidential"] = spec.get("confidential")

        # logo
        logo = spec.get("logo")
        if isinstance(logo, str):
            logo = {"path": logo}
        if not isinstance(logo, dict):
            logo = None
        self.logo = logo
        if self.logo and self.logo.get("path"):
            p = Path(self.logo["path"])
            if not p.is_file():
                raise FileNotFoundError(f"logo not found: {self.logo['path']}")
        # font files (validated, not embedded by python-pptx)
        font_files = spec.get("font_files", [])
        if isinstance(font_files, str):
            font_files = [font_files]
        for fp in font_files or []:
            if not Path(fp).is_file():
                raise FileNotFoundError(f"font file not found: {fp}")
        self.font_files = list(font_files or [])

    def _apply_fonts(self, spec, theme_spec):
        # theme-level font overrides (when theme is a dict)
        if isinstance(theme_spec, dict):
            if theme_spec.get("title_font"):
                self.theme["title_font"] = theme_spec["title_font"]
            if theme_spec.get("body_font"):
                self.theme["body_font"] = theme_spec["body_font"]
        fonts = spec.get("fonts")
        if isinstance(fonts, dict):
            if fonts.get("title") or fonts.get("title_font"):
                self.theme["title_font"] = fonts.get("title", fonts.get("title_font"))
            if fonts.get("body") or fonts.get("body_font"):
                self.theme["body_font"] = fonts.get("body", fonts.get("body_font"))
            if fonts.get("fallbacks"):
                self.theme["title_font_fallbacks"] = list(fonts.get("fallbacks", []))
                self.theme["body_font_fallbacks"] = list(fonts.get("fallbacks", []))
            if fonts.get("title_fallbacks"):
                self.theme["title_font_fallbacks"] = list(fonts["title_fallbacks"])
            if fonts.get("body_fallbacks"):
                self.theme["body_font_fallbacks"] = list(fonts["body_fallbacks"])
        if spec.get("title_font"):
            self.theme["title_font"] = spec["title_font"]
        if spec.get("body_font"):
            self.theme["body_font"] = spec["body_font"]
        # allow list as primary + fallbacks
        for key in ("title_font", "body_font"):
            val = self.theme.get(key)
            if isinstance(val, (list, tuple)):
                self.theme[key] = val[0] if val else self.theme.get(key)
                if key == "title_font":
                    self.theme["title_font_fallbacks"] = list(val[1:]) + list(self.theme.get("title_font_fallbacks", []))
                else:
                    self.theme["body_font_fallbacks"] = list(val[1:]) + list(self.theme.get("body_font_fallbacks", []))

    # -- primitives -----------------------------------------------------

    def _new_slide(self) -> "object":
        slide = self.prs.slides.add_slide(self._blank)
        self._fill_background(slide)
        self._slide_no += 1
        return slide

    def _fill_background(self, slide) -> None:
        try:
            fill = slide.background.fill
            fill.solid()
            fill.fore_color.rgb = rgb(self.theme["bg"])
        except Exception:
            band = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE, 0, 0, self.prs.slide_width, self.prs.slide_height
            )
            band.fill.solid()
            band.fill.fore_color.rgb = rgb(self.theme["bg"])
            band.line.fill.background()
            band.shadow.inherit = False

    def _textbox(self, slide, x, y, w, h):
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = box.text_frame
        tf.word_wrap = True
        return box, tf

    def _rect(self, slide, x, y, w, h, color, shape=MSO_SHAPE.RECTANGLE):
        shp = slide.shapes.add_shape(
            shape, Inches(x), Inches(y), Inches(w), Inches(h)
        )
        shp.fill.solid()
        shp.fill.fore_color.rgb = rgb(color)
        shp.line.fill.background()
        shp.shadow.inherit = False
        return shp

    def _card(self, slide, x, y, w, h, color):
        shp = self._rect(slide, x, y, w, h, color, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        try:
            shp.adjustments[0] = 0.05
        except Exception:
            pass
        return shp

    def _style_run(self, run, size, color, bold=False, italic=False, font=None):
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.name = font or self.theme["body_font"]
        run.font.color.rgb = rgb(color)

    def _heading(self, slide, text, size, color, x=None, y=0.45, w=None, h=1.0):
        x = self.margin if x is None else x
        w = self.content_w if w is None else w
        box, tf = self._textbox(slide, x, y, w, h)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        run = p.add_run()
        run.text = text or ""
        self._style_run(
            run, size, color, bold=True, font=self.theme["title_font"]
        )
        current = getattr(self, "_current_slide_spec", {}) or {}
        accent_bar = current.get("accent_bar", getattr(self, "accent_bar", True))
        if accent_bar:
            try:
                bar_color = current.get("accent_bar_color", getattr(self, "accent_bar_color", self.theme["accent"]))
                bar_h = float(current.get("accent_bar_height", getattr(self, "accent_bar_height", 0.03)))
                bar_w = current.get("accent_bar_width", getattr(self, "accent_bar_width", None))
                if bar_w is None:
                    bar_w = min(w, 1.6)
                else:
                    bar_w = float(bar_w)
                self._rect(slide, x, y + h - 0.26, bar_w, bar_h, bar_color)
            except Exception:
                pass
        return box

    def _notes(self, slide, notes) -> None:
        if notes:
            slide.notes_slide.notes_text_frame.text = str(notes)

    def _add_bullets(self, slide, items, x, y, w, h, size, color):
        box, tf = self._textbox(slide, x, y, w, h)
        tf.vertical_anchor = MSO_ANCHOR.TOP
        for i, text in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.level = 0
            run = p.add_run()
            run.text = f"\u2022  {text}"
            self._style_run(run, size, color)
            p.space_after = Pt(8)
        return box

    def _add_icon(self, slide, x, y, w, h, icon, color=None):
        color = color or self.theme["accent"]
        if icon is None or str(icon).strip() == "":
            return
        icon = str(icon)
        if _is_path(icon) and Path(icon).is_file():
            try:
                pic = slide.shapes.add_picture(icon, Inches(x), Inches(y), width=Inches(w))
                if pic.height > Inches(h):
                    ratio = h / (pic.height / 914400)
                    pic.width = Emu(int(pic.width * ratio))
                    pic.height = Emu(int(pic.height * ratio))
                pic.left = Emu(int((Inches(x) + Inches(w) - pic.width) / 2)) if False else Inches(x + (w - pic.width / 914400) / 2)
                pic.top = Inches(y)
            except Exception:
                pass
            return
        box, tf = self._textbox(slide, x, y, w, h)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER
        run = tf.paragraphs[0].add_run()
        run.text = icon
        self._style_run(run, min(30, max(18, int(h * 18))), color, bold=True)

    def _add_logo(self, slide, override=None) -> None:
        logo = override if override is not None else self.logo
        if not logo:
            return
        if isinstance(logo, str):
            logo = {"path": logo}
        if not isinstance(logo, dict):
            return
        path = logo.get("path")
        if not path or not Path(path).is_file():
            return
        if logo.get("enabled", True) is False:
            return
        pos = logo.get("position", "top-right")
        size = float(logo.get("size", 0.7))
        margin = float(logo.get("margin", 0.35))
        if pos == "top-left":
            x, y = self.margin, 0.2
        elif pos == "top-right":
            x, y = self.width_in - margin - size, 0.2
        elif pos == "bottom-left":
            x, y = self.margin, self.height_in - margin - size
        elif pos == "bottom-right":
            x, y = self.width_in - margin - size, self.height_in - margin - size
        else:
            x, y = self.width_in - margin - size, 0.2
        try:
            pic = slide.shapes.add_picture(str(path), Inches(x), Inches(y), height=Inches(size))
            opacity = logo.get("opacity", logo.get("alpha"))
            if opacity is not None:
                try:
                    from pptx.oxml.ns import qn
                    blip = pic._element.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
                    if blip is not None:
                        from lxml import etree
                        ns = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
                        alpha = etree.SubElement(blip, ns + 'alphaModFix')
                        alpha.set('amt', str(int(float(opacity) * 100000)))
                except Exception:
                    pass
        except Exception:
            pass

    def _add_footer(self, slide) -> None:
        if not self.footer.get("enabled", True):
            return
        footer_color = self.theme["muted"]
        for shape in slide.shapes:
            try:
                x, y, w, h = shape.left or 0, shape.top or 0, shape.width or 0, shape.height or 0
            except Exception:
                continue
            if w >= self.prs.slide_width * 0.9 and h >= self.prs.slide_height * 0.9:
                footer_color = self.theme["band_text"]
        y = self.height_in - 0.42
        parts = []
        if self.footer.get("title", True) and self.deck_title:
            parts.append(str(self.deck_title))
        mark = self.footer.get("mark", "")
        if self.footer.get("confidential"):
            mark = "CONFIDENTIAL" if not mark else f"CONFIDENTIAL  |  {mark}"
        if mark:
            parts.append(str(mark))
        left_text = "  ·  ".join(parts)
        left_w = self.content_w - 1.1
        box, tf = self._textbox(slide, self.margin, y, left_w, 0.36)
        run = tf.paragraphs[0].add_run()
        run.text = left_text
        self._style_run(run, self.sizes["caption"], footer_color)
        if self.footer.get("page_numbers", True):
            box, tf = self._textbox(slide, self.width_in - self.margin - 1.0, y, 1.0, 0.36)
            tf.paragraphs[0].alignment = PP_ALIGN.RIGHT
            run = tf.paragraphs[0].add_run()
            run.text = str(self._slide_no)
            self._style_run(run, self.sizes["caption"], footer_color)

    def _normalize_items(self, raw):
        if raw is None:
            return []
        if isinstance(raw, dict):
            raw = [raw]
        if not isinstance(raw, (list, tuple)):
            raw = [raw]
        items = []
        for it in raw:
            if it is None:
                items.append({})
                continue
            if isinstance(it, dict):
                items.append(dict(it))
                continue
            if isinstance(it, (list, tuple)):
                items.append({
                    "value": it[0] if len(it) > 0 else "",
                    "label": it[1] if len(it) > 1 else "",
                    "delta": it[2] if len(it) > 2 else None,
                    "title": it[0] if len(it) > 0 else "",
                    "body": it[1] if len(it) > 1 else "",
                    "items": it[2] if len(it) > 2 else None,
                    "bullets": it[2] if len(it) > 2 and isinstance(it[2], (list, tuple)) else [],
                    "icon": None,
                })
                continue
            items.append({"value": str(it), "label": "", "title": str(it), "body": "", "bullets": [], "icon": None})
        return items

    # -- layouts --------------------------------------------------------

    def add_title(self, slide_spec):
        slide = self._new_slide()
        band_h = float(slide_spec.get("band_height", slide_spec.get("title_band_height", self.title_band_height)))
        band_color = slide_spec.get("band_color", slide_spec.get("title_band_color", self.title_band_color))
        self._rect(slide, 0, 0, self.width_in, band_h, band_color)
        _, tf = self._textbox(slide, self.margin, 0.9, self.content_w, 1.2)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        run = tf.paragraphs[0].add_run()
        run.text = slide_spec.get("title") or self.deck_title or ""
        self._style_run(
            run, self.sizes["deck_title"], self.theme["band_text"], bold=True,
            font=self.theme["title_font"],
        )
        sub = slide_spec.get("subtitle") or self.deck_subtitle
        if sub:
            _, stf = self._textbox(slide, self.margin, band_h + 0.5, self.content_w, 1.0)
            run = stf.paragraphs[0].add_run()
            run.text = sub
            self._style_run(run, self.sizes["body"] + 4, self.theme["muted"])
        self._notes(slide, slide_spec.get("notes"))

    def add_section(self, slide_spec):
        slide = self._new_slide()
        band_color = slide_spec.get("band_color", slide_spec.get("section_band_color", self.section_band_color))
        band_h = float(slide_spec.get("band_height", slide_spec.get("section_band_height", self.section_band_height)))
        self._rect(slide, 0, self.height_in / 2 - band_h / 2, self.width_in, band_h, band_color)
        _, tf = self._textbox(slide, self.margin, self.height_in / 2 - 1.5, self.content_w, 1.4)
        tf.vertical_anchor = MSO_ANCHOR.BOTTOM
        run = tf.paragraphs[0].add_run()
        run.text = slide_spec.get("title", "")
        self._style_run(
            run, self.sizes["section"], self.theme["text"], bold=True,
            font=self.theme["title_font"],
        )
        sub = slide_spec.get("subtitle")
        if sub:
            _, stf = self._textbox(slide, self.margin, self.height_in / 2 + 0.2, self.content_w, 1.0)
            run = stf.paragraphs[0].add_run()
            run.text = sub
            self._style_run(run, self.sizes["body"], self.theme["muted"])
        self._notes(slide, slide_spec.get("notes"))

    def add_bullets(self, slide_spec):
        slide = self._new_slide()
        self._heading(slide, slide_spec.get("title", ""), self.sizes["title"], self.theme["text"])
        items = slide_spec.get("bullets", [])
        self._add_bullets(
            slide, items, self.margin, 1.6, self.content_w, self.height_in - 2.2,
            self.sizes["body"], self.theme["text"],
        )
        if slide_spec.get("subtitle"):
            _, tf = self._textbox(slide, self.margin, 1.25, self.content_w, 0.4)
            run = tf.paragraphs[0].add_run()
            run.text = slide_spec["subtitle"]
            self._style_run(run, self.sizes["caption"] + 2, self.theme["muted"])
        self._notes(slide, slide_spec.get("notes"))

    def add_two_column(self, slide_spec):
        slide = self._new_slide()
        self._heading(slide, slide_spec.get("title", ""), self.sizes["title"], self.theme["text"])
        gap = 0.4
        col_w = (self.content_w - gap) / 2
        columns = slide_spec.get("columns", [[], []])
        left = columns[0] if len(columns) > 0 else []
        right = columns[1] if len(columns) > 1 else []
        pad = self.card_padding
        for idx, items in enumerate((left, right)):
            x = self.margin + idx * (col_w + gap)
            self._card(slide, x, 1.6, col_w, self.height_in - 2.2, self.theme["surface"])
            self._add_bullets(
                slide, items, x + pad, 1.9, col_w - 2 * pad, self.height_in - 2.8,
                self.sizes["body"] - 1, self.theme["text"],
            )
        self._notes(slide, slide_spec.get("notes"))

    def add_image(self, slide_spec):
        slide = self._new_slide()
        self._heading(slide, slide_spec.get("title", ""), self.sizes["title"], self.theme["text"])
        img = slide_spec.get("image")
        if not img:
            raise ValueError("image layout requires an 'image' path")
        path = Path(img)
        if not path.is_file():
            raise FileNotFoundError(f"image not found: {img}")
        fit = slide_spec.get("fit", "contain")
        caption_pos = slide_spec.get("caption_position", "bottom")
        top = 1.6
        max_h = self.height_in - 2.3
        if caption_pos == "top":
            top = 2.1
            max_h = self.height_in - 2.8
        pic = slide.shapes.add_picture(
            str(path), Inches(self.margin), Inches(top), width=Inches(self.content_w)
        )
        if fit == "contain" and pic.height > Inches(max_h):
            ratio = max_h / (pic.height / 914400)
            pic.width = Emu(int(pic.width * ratio))
            pic.height = Emu(int(pic.height * ratio))
            pic.left = Emu(int((self.prs.slide_width - pic.width) / 2))
            pic.top = Inches(top)
        caption = slide_spec.get("caption")
        if caption:
            cy = self.height_in - 0.7
            if caption_pos == "top":
                cy = 1.6
            _, tf = self._textbox(slide, self.margin, cy, self.content_w, 0.4)
            run = tf.paragraphs[0].add_run()
            run.text = caption
            self._style_run(run, self.sizes["caption"], self.theme["muted"])
        self._notes(slide, slide_spec.get("notes"))

    def add_table(self, slide_spec):
        slide = self._new_slide()
        self._heading(slide, slide_spec.get("title", ""), self.sizes["title"], self.theme["text"])
        tbl = slide_spec.get("table", {})
        headers = tbl.get("headers", [])
        rows = tbl.get("rows", [])
        n_cols = len(headers) or (len(rows[0]) if rows and isinstance(rows[0], (list, tuple)) else 0)
        if n_cols == 0 and rows:
            n_cols = 1
        n_rows = len(rows) + (1 if headers else 0)
        if n_cols == 0:
            raise ValueError("table layout requires headers or rows")
        if n_rows == 0:
            n_rows = 1
        shape = slide.shapes.add_table(
            n_rows, n_cols, Inches(self.margin), Inches(1.75),
            Inches(self.content_w), Inches(self.height_in - 2.5),
        )
        table = shape.table
        header_fill = tbl.get("header_fill", self.theme["band"])
        header_text = tbl.get("header_text", self.theme["band_text"])
        zebra = tbl.get("zebra", True)
        font_size = tbl.get("font_size", self.sizes["body"] - 3)
        if headers:
            for c, text in enumerate(headers):
                if c >= n_cols:
                    break
                cell = table.cell(0, c)
                cell.text = "" if text is None else str(text)
                cell.fill.solid()
                cell.fill.fore_color.rgb = rgb(header_fill)
                for p in cell.text_frame.paragraphs:
                    for r in p.runs:
                        r.font.size = Pt(font_size)
                        r.font.bold = True
                        r.font.color.rgb = rgb(header_text)
                        r.font.name = self.theme["body_font"]
        start_row = 1 if headers else 0
        for offset, row in enumerate(rows):
            r_i = start_row + offset
            if r_i >= n_rows:
                break
            row = row if isinstance(row, (list, tuple)) else [row]
            for c_i in range(n_cols):
                cell = table.cell(r_i, c_i)
                val = row[c_i] if c_i < len(row) else ""
                if val is None:
                    val = ""
                cell.text = str(val)
                if zebra and headers and (offset % 2 == 1):
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = rgb(self.theme["surface"])
                for p in cell.text_frame.paragraphs:
                    for r in p.runs:
                        r.font.size = Pt(font_size)
                        r.font.color.rgb = rgb(self.theme["text"])
                        r.font.name = self.theme["body_font"]
                        if tbl.get("bold_first_column") and c_i == 0:
                            r.font.bold = True
        self._notes(slide, slide_spec.get("notes"))

    def add_quote(self, slide_spec):
        slide = self._new_slide()
        self._rect(slide, self.margin, 2.0, 0.12, 3.0, self.theme["accent"])
        box, tf = self._textbox(slide, self.margin + 0.5, 2.0, self.content_w - 0.5, 2.4)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        run = tf.paragraphs[0].add_run()
        run.text = f"\u201c{slide_spec.get('quote', '')}\u201d"
        self._style_run(
            run, self.sizes["quote"], self.theme["text"], italic=True,
            font=self.theme["title_font"],
        )
        attr = slide_spec.get("attribution")
        if attr:
            p = tf.add_paragraph()
            p.space_before = Pt(12)
            run = p.add_run()
            run.text = f"\u2014 {attr}"
            self._style_run(run, self.sizes["caption"] + 2, self.theme["muted"])
        self._notes(slide, slide_spec.get("notes"))

    def add_chart(self, slide_spec):
        slide = self._new_slide()
        self._heading(slide, slide_spec.get("title", ""), self.sizes["title"], self.theme["text"])
        chart = slide_spec.get("chart", {})
        engine = chart.get("engine", "pptx")
        if engine == "matplotlib":
            self._add_chart_matplotlib(slide, slide_spec, chart)
            self._notes(slide, slide_spec.get("notes"))
            return
        ctype = chart.get("type", "bar")
        types = {
            "bar": XL_CHART_TYPE.COLUMN_CLUSTERED,
            "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
            "line": XL_CHART_TYPE.LINE_MARKERS,
            "pie": XL_CHART_TYPE.PIE,
            "doughnut": XL_CHART_TYPE.DOUGHNUT,
            "area": XL_CHART_TYPE.AREA,
        }
        if ctype not in types:
            raise ValueError(f"unknown chart type {ctype!r}; choose from {sorted(types)}")
        data = CategoryChartData()
        data.categories = [str(c) for c in chart.get("categories", [])]
        series_list = chart.get("series", [])
        if not isinstance(series_list, (list, tuple)):
            series_list = [series_list]
        for series in series_list:
            if not isinstance(series, dict):
                raise ValueError("chart series must be objects with name/values")
            data.add_series(str(series.get("name", "Series")), tuple(series.get("values", [])))
        if not series_list:
            raise ValueError("chart layout requires at least one series")
        if ctype in ("pie", "doughnut") and len(series_list) != 1:
            raise ValueError("pie/doughnut charts require exactly one series")
        series_colors = chart.get("colors") or [
            self.theme["accent"], self.theme["accent2"], self.theme["accent3"], self.theme["muted"]
        ]
        graphic = slide.shapes.add_chart(
            types[ctype], Inches(0.9), Inches(1.7), Inches(self.content_w - 0.6),
            Inches(self.height_in - 2.6), data,
        )
        ch = graphic.chart
        ch.has_legend = chart.get("legend", len(series_list) > 2)
        unit = chart.get("unit")
        x_title = chart.get("x_title")
        y_title = chart.get("y_title")
        if x_title:
            try:
                ch.category_axis.axis_title.text_frame.text = str(x_title)
            except Exception:
                pass
        if y_title or unit:
            try:
                txt = str(y_title or "")
                if unit:
                    txt = f"{txt} ({unit})".strip() if txt else f"Value ({unit})"
                ch.value_axis.axis_title.text_frame.text = txt
            except Exception:
                pass
        try:
            if ctype not in ("pie", "doughnut"):
                ch.value_axis.tick_labels.font.size = Pt(self.sizes["caption"])
                ch.category_axis.tick_labels.font.size = Pt(self.sizes["caption"])
                try:
                    ch.value_axis.major_gridlines.format.line.color.rgb = rgb(self.theme["muted"])
                except Exception:
                    pass
        except Exception:
            pass
        total_points = len(data.categories) * len(series_list)
        show_values = chart.get("show_values", total_points <= 12)
        if ctype in ("pie", "doughnut"):
            try:
                ch.plots[0].has_data_labels = True
                dl = ch.plots[0].data_labels
                dl.font.size = Pt(self.sizes["caption"] + 1)
                dl.font.color.rgb = rgb(self.theme["text"])
                if unit:
                    try:
                        dl.number_format = f'0.0"{unit}"'
                    except Exception:
                        pass
            except Exception:
                pass
        else:
            try:
                ch.plots[0].has_data_labels = bool(show_values)
                if ch.plots[0].has_data_labels:
                    dl = ch.plots[0].data_labels
                    dl.font.size = Pt(self.sizes["caption"] + 1)
                    dl.font.color.rgb = rgb(self.theme["text"])
                    dl.show_value = True
                    dl.show_category_name = False
                    if unit:
                        try:
                            dl.number_format = f'0.0"{unit}"'
                        except Exception:
                            pass
            except Exception:
                pass
        for i, s in enumerate(ch.series):
            color = series_colors[i % len(series_colors)]
            try:
                s.format.fill.solid()
                s.format.fill.fore_color.rgb = rgb(color)
            except Exception:
                pass
            try:
                s.format.line.color.rgb = rgb(color)
                s.format.line.width = Pt(2.25)
            except Exception:
                pass
            try:
                s.marker.style = 2  # circle
            except Exception:
                pass
        self._notes(slide, slide_spec.get("notes"))

    def _add_chart_matplotlib(self, slide, slide_spec, chart):
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except Exception as exc:
            raise ValueError(f"matplotlib is not available: {exc}")
        ctype = chart.get("type", "bar")
        categories = [str(c) for c in chart.get("categories", [])]
        series_list = chart.get("series", [])
        if not isinstance(series_list, (list, tuple)):
            series_list = [series_list]
        colors = chart.get("colors") or [
            "#" + self.theme["accent"], "#" + self.theme["accent2"], "#" + self.theme["accent3"], "#" + self.theme["muted"]
        ]
        unit = chart.get("unit")
        fig, ax = plt.subplots(figsize=(9, 4.5))
        # theme-ish styling
        fig.patch.set_facecolor("#" + self.theme["bg"])
        ax.set_facecolor("#" + self.theme["surface"])
        ax.tick_params(colors="#" + self.theme["text"], labelsize=9)
        ax.xaxis.label.set_color("#" + self.theme["text"])
        ax.yaxis.label.set_color("#" + self.theme["text"])
        ax.title.set_color("#" + self.theme["text"])
        code = chart.get("code")
        if code:
            ns = {
                "plt": plt, "fig": fig, "ax": ax, "categories": categories,
                "series_list": series_list, "colors": colors, "unit": unit,
                "theme": self.theme,
            }
            exec(code, ns)
        else:
            if ctype in ("bar", "column"):
                width = 0.8 / max(1, len(series_list))
                x = range(len(categories))
                for i, s in enumerate(series_list):
                    vals = s.get("values", []) if isinstance(s, dict) else s
                    offset = (i - (len(series_list) - 1) / 2) * width
                    xs = [xi + offset for xi in x]
                    ax.bar(xs, vals, width=width, label=s.get("name") if isinstance(s, dict) else None,
                           color=colors[i % len(colors)])
                ax.set_xticks(list(x))
                ax.set_xticklabels(categories, rotation=30, ha="right")
            elif ctype == "line":
                for i, s in enumerate(series_list):
                    vals = s.get("values", []) if isinstance(s, dict) else s
                    ax.plot(categories, vals, marker="o", label=s.get("name") if isinstance(s, dict) else None,
                            color=colors[i % len(colors)])
                plt.xticks(rotation=30, ha="right")
            elif ctype in ("pie", "doughnut"):
                s = series_list[0]
                vals = s.get("values", []) if isinstance(s, dict) else s
                wedges, _ = ax.pie(vals, labels=categories, colors=colors)
                if ctype == "doughnut":
                    centre = plt.Circle((0, 0), 0.55, fc="#" + self.theme["bg"])
                    fig.gca().add_artist(centre)
            elif ctype == "scatter":
                for i, s in enumerate(series_list):
                    vals = s.get("values", []) if isinstance(s, dict) else s
                    xs = s.get("x", list(range(len(vals)))) if isinstance(s, dict) else list(range(len(vals)))
                    ax.scatter(xs, vals, color=colors[i % len(colors)], label=s.get("name") if isinstance(s, dict) else None)
            if chart.get("x_title"):
                ax.set_xlabel(chart["x_title"])
            if chart.get("y_title") or unit:
                ax.set_ylabel(f"{chart.get('y_title', '')} ({unit})".strip(" ()") if False else (chart.get("y_title") or "") + (f" ({unit})" if unit else ""))
            if chart.get("legend", len(series_list) > 1):
                ax.legend(fontsize=8)
            if chart.get("show_values", True) and ctype in ("bar", "column"):
                for container in ax.containers:
                    ax.bar_label(container, fontsize=8, color="#" + self.theme["text"])
        # save
        fd, tmp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        fig.tight_layout()
        fig.savefig(tmp_path, dpi=150, facecolor=fig.get_facecolor())
        plt.close(fig)
        pic = slide.shapes.add_picture(tmp_path, Inches(0.9), Inches(1.7), width=Inches(self.content_w - 0.6))
        if pic.height > Inches(self.height_in - 2.6):
            ratio = (self.height_in - 2.6) / (pic.height / 914400)
            pic.width = Emu(int(pic.width * ratio))
            pic.height = Emu(int(pic.height * ratio))
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    def add_closing(self, slide_spec):
        slide = self._new_slide()
        band_h = self.height_in
        band_color = slide_spec.get("band_color", slide_spec.get("closing_band_color", self.closing_band_color))
        self._rect(slide, 0, 0, self.width_in, band_h, band_color)
        _, tf = self._textbox(
            slide, self.margin, self.height_in / 2 - 1.5, self.content_w, 1.4
        )
        tf.vertical_anchor = MSO_ANCHOR.BOTTOM
        run = tf.paragraphs[0].add_run()
        run.text = slide_spec.get("title", "Thank you")
        self._style_run(
            run, self.sizes["deck_title"] - 6, self.theme["band_text"], bold=True,
            font=self.theme["title_font"],
        )
        sub = slide_spec.get("subtitle") or slide_spec.get("quote")
        if sub:
            _, stf = self._textbox(
                slide, self.margin, self.height_in / 2 + 0.2, self.content_w, 1.0
            )
            run = stf.paragraphs[0].add_run()
            run.text = sub
            self._style_run(run, self.sizes["body"] + 2, self.theme["band_text"])
        self._notes(slide, slide_spec.get("notes"))

    def add_stats(self, slide_spec):
        slide = self._new_slide()
        self._heading(slide, slide_spec.get("title", ""), self.sizes["title"], self.theme["text"])
        raw = slide_spec.get("stats", slide_spec.get("items", slide_spec.get("kpis", [])))
        items = self._normalize_items(raw)
        if not items:
            self._notes(slide, slide_spec.get("notes"))
            return
        n = len(items)
        if n > 6:
            raise ValueError("stats layout supports at most 6 items")
        gap = 0.25
        card_w = (self.content_w - gap * (n - 1)) / n
        if card_w <= 0:
            raise ValueError("stats layout: too many items for slide width")
        y = 1.6
        h = self.height_in - 2.4
        pad = self.card_padding
        for i, it in enumerate(items):
            x = self.margin + i * (card_w + gap)
            self._card(slide, x, y, card_w, h, self.theme["surface"])
            icon = it.get("icon")
            value = it.get("value", it.get("number", it.get("stat", "")))
            label = it.get("label", it.get("title", it.get("name", "")))
            delta = it.get("delta", it.get("change", None))
            iy = y + 0.25
            if icon:
                self._add_icon(slide, x + pad, iy, card_w - 2 * pad, 0.7, icon, it.get("icon_color"))
                iy += 0.75
            _, tf = self._textbox(slide, x + pad, iy, card_w - 2 * pad, 1.2)
            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            run = tf.paragraphs[0].add_run()
            run.text = "" if value is None else str(value)
            self._style_run(run, self.sizes["deck_title"] - (4 if n > 4 else 0), self.theme["accent"], bold=True,
                            font=self.theme["title_font"])
            _, tf = self._textbox(slide, x + pad, iy + 1.2, card_w - 2 * pad, 0.8)
            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            run = tf.paragraphs[0].add_run()
            run.text = "" if label is None else str(label)
            self._style_run(run, self.sizes["body"], self.theme["text"])
            if delta is not None and str(delta).strip() != "":
                _, tf = self._textbox(slide, x + pad, iy + 2.0, card_w - 2 * pad, 0.5)
                tf.paragraphs[0].alignment = PP_ALIGN.CENTER
                run = tf.paragraphs[0].add_run()
                run.text = str(delta)
                color = self.theme["muted"]
                ds = str(delta).strip()
                if ds.startswith("+"):
                    color = self.theme["accent2"]
                elif ds.startswith("-"):
                    color = self.theme["accent3"]
                self._style_run(run, self.sizes["caption"] + 6, color, bold=True)
        self._notes(slide, slide_spec.get("notes"))

    def add_timeline(self, slide_spec):
        slide = self._new_slide()
        self._heading(slide, slide_spec.get("title", ""), self.sizes["title"], self.theme["text"])
        raw = slide_spec.get("steps", slide_spec.get("items", slide_spec.get("stages", [])))
        items = []
        for it in (raw if isinstance(raw, (list, tuple)) else [raw] if raw is not None else []):
            if it is None:
                items.append({"title": "", "body": "", "icon": None})
                continue
            if isinstance(it, str):
                items.append({"title": it, "body": "", "icon": None})
                continue
            if isinstance(it, (list, tuple)):
                items.append({"title": it[0] if len(it) > 0 else "", "body": it[1] if len(it) > 1 else "", "icon": it[2] if len(it) > 2 and not isinstance(it[2], (list, tuple)) else None})
                continue
            if isinstance(it, dict):
                items.append({
                    "title": it.get("title", it.get("name", it.get("heading", ""))),
                    "body": it.get("body", it.get("description", it.get("text", ""))),
                    "icon": it.get("icon"),
                })
                continue
            items.append({"title": str(it), "body": "", "icon": None})
        if not items:
            self._notes(slide, slide_spec.get("notes"))
            return
        n = len(items)
        if n > 6:
            raise ValueError("timeline layout supports at most 6 steps")
        gap = 0.2
        card_w = (self.content_w - gap * (n - 1)) / n
        if card_w <= 0:
            raise ValueError("timeline layout: too many steps for slide width")
        y = 1.7
        card_h = self.height_in - 2.5
        if n > 1:
            self._rect(slide, self.margin + 0.5, y + 0.45, self.content_w - 1.0, 0.06, self.theme["muted"])
        circle = 0.6
        pad = self.card_padding
        for i, it in enumerate(items):
            x = self.margin + i * (card_w + gap)
            cx = x + (card_w - circle) / 2
            self._rect(slide, cx, y + 0.15, circle, circle, self.theme["accent"], shape=MSO_SHAPE.OVAL)
            _, tf = self._textbox(slide, cx, y + 0.15, circle, circle)
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            run = tf.paragraphs[0].add_run()
            icon = it.get("icon")
            run.text = str(icon) if icon else str(i + 1)
            accent_lum = _hex_luminance(self.theme["accent"])
            number_color = self.theme["bg"] if accent_lum > 0.2 else self.theme["band_text"]
            if number_color == self.theme["bg"] and _hex_luminance(self.theme["bg"]) > 0.5:
                number_color = "1A1A1A"
            self._style_run(run, self.sizes["body"], number_color, bold=True,
                            font=self.theme["title_font"])
            _, tf = self._textbox(slide, x + pad, y + 0.9, card_w - 2 * pad, 0.6)
            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            run = tf.paragraphs[0].add_run()
            run.text = str(it.get("title", ""))
            self._style_run(run, self.sizes["body"], self.theme["text"], bold=True)
            _, tf = self._textbox(slide, x + pad, y + 1.55, card_w - 2 * pad, card_h - 1.55)
            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            run = tf.paragraphs[0].add_run()
            run.text = str(it.get("body", it.get("description", "")))
            self._style_run(run, self.sizes["caption"] + 2, self.theme["muted"])
        self._notes(slide, slide_spec.get("notes"))

    def add_flow(self, slide_spec):
        slide = self._new_slide()
        self._heading(slide, slide_spec.get("title", ""), self.sizes["title"], self.theme["text"])
        raw = slide_spec.get("steps", slide_spec.get("items", slide_spec.get("stages", [])))
        items = []
        for it in (raw if isinstance(raw, (list, tuple)) else [raw] if raw is not None else []):
            if it is None:
                items.append({"title": "", "body": ""})
                continue
            if isinstance(it, str):
                items.append({"title": it, "body": ""})
                continue
            if isinstance(it, (list, tuple)):
                items.append({"title": it[0] if len(it) > 0 else "", "body": it[1] if len(it) > 1 else ""})
                continue
            if isinstance(it, dict):
                items.append({
                    "title": it.get("title", it.get("name", it.get("heading", ""))),
                    "body": it.get("body", it.get("description", it.get("text", ""))),
                })
                continue
            items.append({"title": str(it), "body": ""})
        if not items:
            self._notes(slide, slide_spec.get("notes"))
            return
        n = len(items)
        if n > 5:
            raise ValueError("flow layout supports at most 5 steps")
        gap = 0.15
        arrow_w = 0.35
        card_w = (self.content_w - gap * (n - 1) - arrow_w * (n - 1)) / n
        if card_w <= 0:
            raise ValueError("flow layout: too many steps for slide width")
        y = 2.0
        h = self.height_in - 3.0
        pad = self.card_padding
        for i, it in enumerate(items):
            x = self.margin + i * (card_w + gap + arrow_w)
            self._card(slide, x, y, card_w, h, self.theme["surface"])
            _, tf = self._textbox(slide, x + pad, y + 0.2, card_w - 2 * pad, 0.6)
            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            run = tf.paragraphs[0].add_run()
            run.text = str(it.get("title", ""))
            self._style_run(run, self.sizes["body"], self.theme["text"], bold=True)
            _, tf = self._textbox(slide, x + pad, y + 0.9, card_w - 2 * pad, h - 1.0)
            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            run = tf.paragraphs[0].add_run()
            run.text = str(it.get("body", ""))
            self._style_run(run, self.sizes["body"] - 2, self.theme["muted"])
            if i < n - 1:
                ax = x + card_w + gap
                ay = y + h / 2 - 0.18
                self._rect(slide, ax, ay, arrow_w, 0.36, self.theme["accent"], shape=MSO_SHAPE.RIGHT_ARROW)
        self._notes(slide, slide_spec.get("notes"))

    def add_process_vertical(self, slide_spec):
        slide = self._new_slide()
        self._heading(slide, slide_spec.get("title", ""), self.sizes["title"], self.theme["text"])
        raw = slide_spec.get("steps", slide_spec.get("items", slide_spec.get("stages", [])))
        items = []
        for it in (raw if isinstance(raw, (list, tuple)) else [raw] if raw is not None else []):
            if it is None:
                items.append({"title": "", "body": ""})
                continue
            if isinstance(it, str):
                items.append({"title": it, "body": ""})
                continue
            if isinstance(it, (list, tuple)):
                items.append({"title": it[0] if len(it) > 0 else "", "body": it[1] if len(it) > 1 else ""})
                continue
            if isinstance(it, dict):
                items.append({
                    "title": it.get("title", it.get("name", it.get("heading", ""))),
                    "body": it.get("body", it.get("description", it.get("text", ""))),
                })
                continue
            items.append({"title": str(it), "body": ""})
        if not items:
            self._notes(slide, slide_spec.get("notes"))
            return
        n = len(items)
        if n > 6:
            raise ValueError("process_vertical layout supports at most 6 steps")
        gap = 0.18
        card_h = (self.height_in - 2.2 - gap * (n - 1)) / n
        if card_h <= 0:
            raise ValueError("process_vertical layout: too many steps")
        y = 1.6
        pad = self.card_padding
        for i, it in enumerate(items):
            yy = y + i * (card_h + gap)
            self._rect(slide, self.margin, yy, 0.45, card_h, self.theme["accent"], shape=MSO_SHAPE.OVAL)
            _, tf = self._textbox(slide, self.margin, yy, 0.45, card_h)
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            run = tf.paragraphs[0].add_run()
            run.text = str(i + 1)
            num_color = self.theme["bg"] if _hex_luminance(self.theme["accent"]) > 0.2 else self.theme["band_text"]
            self._style_run(run, self.sizes["body"], num_color, bold=True, font=self.theme["title_font"])
            cx = self.margin + 0.6
            cw = self.content_w - 0.6
            self._card(slide, cx, yy, cw, card_h, self.theme["surface"])
            _, tf = self._textbox(slide, cx + pad, yy + 0.15, cw - 2 * pad, 0.5)
            run = tf.paragraphs[0].add_run()
            run.text = str(it.get("title", ""))
            self._style_run(run, self.sizes["body"], self.theme["text"], bold=True)
            _, tf = self._textbox(slide, cx + pad, yy + 0.65, cw - 2 * pad, card_h - 0.75)
            run = tf.paragraphs[0].add_run()
            run.text = str(it.get("body", ""))
            self._style_run(run, self.sizes["body"] - 2, self.theme["muted"])
            if i < n - 1:
                self._rect(slide, self.margin + 0.18, yy + card_h, 0.09, gap, self.theme["muted"])
        self._notes(slide, slide_spec.get("notes"))

    def add_comparison(self, slide_spec):
        slide = self._new_slide()
        self._heading(slide, slide_spec.get("title", ""), self.sizes["title"], self.theme["text"])
        headers = slide_spec.get("headers")
        columns = slide_spec.get("columns", slide_spec.get("items", slide_spec.get("cols", [])))
        if headers is None and isinstance(columns, (list, tuple)) and columns and isinstance(columns[0], dict) and ("header" in columns[0] or "title" in columns[0]):
            headers = [c.get("header", c.get("title", "")) for c in columns]
            columns = [c.get("items", c.get("bullets", c.get("points", []))) for c in columns]
        headers = headers or []
        columns = columns or []
        if isinstance(columns, dict):
            columns = list(columns.values())
        if not isinstance(columns, (list, tuple)):
            columns = [columns]
        n = max(1, min(4, max(len(headers), len(columns))))
        if n > 4:
            raise ValueError("comparison layout supports at most 4 columns")
        highlight = slide_spec.get("highlight", slide_spec.get("emphasis"))
        gap = 0.3
        col_w = (self.content_w - gap * (n - 1)) / n
        if col_w <= 0:
            raise ValueError("comparison layout: too many columns for slide width")
        y = 1.6
        header_h = 0.5
        body_y = y + header_h + 0.15
        body_h = self.height_in - body_y - 0.7
        pad = self.card_padding
        for i in range(n):
            x = self.margin + i * (col_w + gap)
            hdr = headers[i] if i < len(headers) else ""
            hdr_color = self.theme["band"]
            hdr_text_color = self.theme["band_text"]
            if highlight is not None and i == highlight:
                hdr_color = self.theme["accent"]
                hdr_text_color = self.theme["band_text"]
            if str(hdr).strip() != "":
                self._rect(slide, x, y, col_w, header_h, hdr_color)
                _, tf = self._textbox(slide, x + pad, y, col_w - 2 * pad, header_h)
                tf.vertical_anchor = MSO_ANCHOR.MIDDLE
                tf.paragraphs[0].alignment = PP_ALIGN.CENTER
                run = tf.paragraphs[0].add_run()
                run.text = str(hdr)
                self._style_run(run, self.sizes["body"], hdr_text_color, bold=True)
            card_color = self.theme["surface"]
            if highlight is not None and i == highlight:
                card_color = self.theme["surface"]
            self._card(slide, x, body_y, col_w, body_h, card_color)
            items = columns[i] if i < len(columns) else []
            if isinstance(items, dict):
                items = items.get("items", items.get("bullets", items.get("points", [])))
            if isinstance(items, str):
                items = [items]
            self._add_bullets(
                slide, items or [], x + pad, body_y + 0.2, col_w - 2 * pad, body_h - 0.4,
                self.sizes["body"] - 1, self.theme["text"],
            )
        self._notes(slide, slide_spec.get("notes"))

    def add_cards(self, slide_spec):
        slide = self._new_slide()
        self._heading(slide, slide_spec.get("title", ""), self.sizes["title"], self.theme["text"])
        raw = slide_spec.get("cards", slide_spec.get("items", slide_spec.get("tiles", [])))
        items = []
        for it in (raw if isinstance(raw, (list, tuple)) else [raw] if raw is not None else []):
            if it is None:
                items.append({"title": "", "body": "", "bullets": [], "icon": None})
                continue
            if isinstance(it, str):
                items.append({"title": it, "body": "", "bullets": [], "icon": None})
                continue
            if isinstance(it, (list, tuple)):
                items.append({
                    "title": it[0] if len(it) > 0 else "",
                    "body": it[1] if len(it) > 1 else "",
                    "bullets": it[2] if len(it) > 2 else [],
                    "icon": it[3] if len(it) > 3 else None,
                })
                continue
            if isinstance(it, dict):
                items.append({
                    "title": it.get("title", it.get("heading", it.get("name", ""))),
                    "body": it.get("body", it.get("text", it.get("description", ""))),
                    "bullets": it.get("bullets", it.get("items", it.get("points", []))),
                    "icon": it.get("icon"),
                })
                continue
            items.append({"title": str(it), "body": "", "bullets": [], "icon": None})
        if not items:
            self._notes(slide, slide_spec.get("notes"))
            return
        n = len(items)
        if n > 6:
            raise ValueError("cards layout supports at most 6 cards")
        cols = slide_spec.get("columns")
        if not cols:
            if n <= 3:
                cols = n
            elif n == 4:
                cols = 2
            elif n <= 6:
                cols = 3
        cols = max(1, min(n, int(cols)))
        rows = math.ceil(n / cols)
        gap = 0.3
        card_w = (self.content_w - gap * (cols - 1)) / cols
        if card_w <= 0:
            raise ValueError("cards layout: too many columns for slide width")
        y0 = 1.6
        total_h = self.height_in - 2.4
        card_h = (total_h - gap * (rows - 1)) / rows
        pad = self.card_padding
        for i, it in enumerate(items):
            r = i // cols
            c = i % cols
            x = self.margin + c * (card_w + gap)
            y = y0 + r * (card_h + gap)
            self._card(slide, x, y, card_w, card_h, self.theme["surface"])
            iy = y + 0.2
            if it.get("icon"):
                self._add_icon(slide, x + pad, iy, card_w - 2 * pad, 0.6, it["icon"], it.get("icon_color"))
                iy += 0.65
            _, tf = self._textbox(slide, x + pad, iy, card_w - 2 * pad, 0.5)
            run = tf.paragraphs[0].add_run()
            run.text = str(it.get("title", ""))
            self._style_run(run, self.sizes["body"] + 1, self.theme["text"], bold=True)
            body = it.get("body", "")
            bullets = it.get("bullets", [])
            if not isinstance(bullets, (list, tuple)):
                bullets = [bullets]
            body_y = iy + 0.55
            if body:
                _, tf = self._textbox(slide, x + pad, body_y, card_w - 2 * pad, 0.9)
                run = tf.paragraphs[0].add_run()
                run.text = str(body)
                self._style_run(run, self.sizes["body"] - 1, self.theme["muted"])
                body_y += 0.95
            if bullets:
                self._add_bullets(
                    slide, bullets, x + pad, body_y, card_w - 2 * pad, y + card_h - body_y - 0.15,
                    self.sizes["body"] - 2, self.theme["text"],
                )
        self._notes(slide, slide_spec.get("notes"))

    def add_problem_solution_impact(self, slide_spec):
        slide = self._new_slide()
        self._heading(slide, slide_spec.get("title", ""), self.sizes["title"], self.theme["text"])
        # accept either nested dict or three keys
        psi = slide_spec.get("psi", {}) or {}
        problem = slide_spec.get("problem", psi.get("problem", {}))
        solution = slide_spec.get("solution", psi.get("solution", {}))
        impact = slide_spec.get("impact", psi.get("impact", {}))
        items = [
            ("Problem", problem, self.theme["accent3"]),
            ("Solution", solution, self.theme["accent"]),
            ("Impact", impact, self.theme["accent2"]),
        ]
        n = 3
        gap = 0.3
        col_w = (self.content_w - gap * (n - 1)) / n
        y = 1.6
        header_h = 0.5
        body_y = y + header_h + 0.1
        body_h = self.height_in - body_y - 0.7
        pad = self.card_padding
        for idx, (label, data, color) in enumerate(items):
            x = self.margin + idx * (col_w + gap)
            title = label
            body = ""
            bullets = []
            if isinstance(data, dict):
                title = data.get("title", data.get("heading", label))
                body = data.get("body", data.get("text", data.get("description", "")))
                bullets = data.get("bullets", data.get("items", data.get("points", [])))
            elif isinstance(data, str):
                body = data
            elif isinstance(data, (list, tuple)):
                bullets = list(data)
            if not isinstance(bullets, (list, tuple)):
                bullets = [bullets] if bullets else []
            self._rect(slide, x, y, col_w, header_h, color)
            _, tf = self._textbox(slide, x + pad, y, col_w - 2 * pad, header_h)
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            run = tf.paragraphs[0].add_run()
            run.text = str(title)
            _tc = "1A1A1A" if _hex_luminance(color) > 0.35 else "FFFFFF"
            self._style_run(run, self.sizes["body"], _tc, bold=True)
            self._card(slide, x, body_y, col_w, body_h, self.theme["surface"])
            by = body_y + 0.2
            if body:
                _, tf = self._textbox(slide, x + pad, by, col_w - 2 * pad, 0.9)
                run = tf.paragraphs[0].add_run()
                run.text = str(body)
                self._style_run(run, self.sizes["body"] - 1, self.theme["muted"])
                by += 0.95
            if bullets:
                self._add_bullets(slide, bullets, x + pad, by, col_w - 2 * pad, body_y + body_h - by - 0.15,
                                  self.sizes["body"] - 2, self.theme["text"])
        self._notes(slide, slide_spec.get("notes"))

    def add_before_after(self, slide_spec):
        slide = self._new_slide()
        self._heading(slide, slide_spec.get("title", ""), self.sizes["title"], self.theme["text"])
        before = slide_spec.get("before", {})
        after = slide_spec.get("after", {})
        if not isinstance(before, dict):
            before = {"title": "Before", "items": before if isinstance(before, (list, tuple)) else [before]}
        if not isinstance(after, dict):
            after = {"title": "After", "items": after if isinstance(after, (list, tuple)) else [after]}
        before.setdefault("title", "Before")
        after.setdefault("title", "After")
        before_items = before.get("items", before.get("bullets", before.get("points", [])))
        after_items = after.get("items", after.get("bullets", after.get("points", [])))
        if isinstance(before_items, str):
            before_items = [before_items]
        if isinstance(after_items, str):
            after_items = [after_items]
        n = 2
        gap = 0.4
        col_w = (self.content_w - gap) / n
        y = 1.6
        header_h = 0.5
        body_y = y + header_h + 0.15
        body_h = self.height_in - body_y - 0.7
        pad = self.card_padding
        for idx, (data, title, hdr_color) in enumerate((
            (before, before.get("title", "Before"), self.theme["accent3"]),
            (after, after.get("title", "After"), self.theme["accent2"]),
        )):
            x = self.margin + idx * (col_w + gap)
            items = before_items if idx == 0 else after_items
            self._rect(slide, x, y, col_w, header_h, hdr_color)
            _, tf = self._textbox(slide, x + pad, y, col_w - 2 * pad, header_h)
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            run = tf.paragraphs[0].add_run()
            run.text = str(title)
            _tc = "1A1A1A" if _hex_luminance(hdr_color) > 0.35 else "FFFFFF"
            self._style_run(run, self.sizes["body"], _tc, bold=True)
            self._card(slide, x, body_y, col_w, body_h, self.theme["surface"])
            self._add_bullets(slide, items or [], x + pad, body_y + 0.2, col_w - 2 * pad, body_h - 0.4,
                              self.sizes["body"] - 1, self.theme["text"])
        self._notes(slide, slide_spec.get("notes"))

    def build(self, spec: dict) -> None:
        handlers = {
            "title": self.add_title,
            "section": self.add_section,
            "bullets": self.add_bullets,
            "two_column": self.add_two_column,
            "image": self.add_image,
            "table": self.add_table,
            "quote": self.add_quote,
            "chart": self.add_chart,
            "closing": self.add_closing,
            "stats": self.add_stats,
            "timeline": self.add_timeline,
            "comparison": self.add_comparison,
            "cards": self.add_cards,
            "before_after": self.add_before_after,
            "problem_solution_impact": self.add_problem_solution_impact,
            "flow": self.add_flow,
            "process_vertical": self.add_process_vertical,
        }
        slides = spec.get("slides", [])
        if not slides:
            raise ValueError("deck spec has no slides")
        for slide_spec in slides:
            layout = slide_spec.get("layout", "bullets")
            layout = LAYOUT_ALIASES.get(layout, layout)
            if layout not in handlers:
                raise ValueError(
                    f"unknown layout {layout!r}; choose from {sorted(LAYOUTS)}"
                )
            self._current_slide_spec = slide_spec
            handlers[layout](slide_spec)
            slide = self.prs.slides[-1]
            # logo: per-slide override or deck default
            if "logo" in slide_spec:
                logo_spec = slide_spec.get("logo")
            else:
                logo_spec = self.logo
            if logo_spec:
                self._add_logo(slide, logo_spec)
            self._add_footer(slide)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build a .pptx deck from a JSON spec.")
    parser.add_argument("spec", help="path to the JSON deck spec")
    parser.add_argument("-o", "--output", required=True, help="output .pptx path")
    parser.add_argument("--force", action="store_true", help="overwrite an existing file")
    args = parser.parse_args(argv)

    spec_path = Path(args.spec)
    if not spec_path.is_file():
        print(f"error: spec not found: {spec_path}", file=sys.stderr)
        return 2
    out_path = Path(args.output)
    if out_path.exists() and not args.force:
        print(
            f"error: {out_path} exists; pass --force to overwrite",
            file=sys.stderr,
        )
        return 2

    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in {spec_path}: {exc}", file=sys.stderr)
        return 2

    try:
        builder = DeckBuilder(spec)
        builder.build(spec)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        builder.prs.save(str(out_path))
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    n = len(builder.prs.slides._sldIdLst)  # noqa: SLF001 - documented slide count
    print(f"Wrote {n} slides to {out_path} (theme: {builder.theme_name}, {spec.get('aspect', '16:9')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
