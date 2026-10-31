#!/usr/bin/env python3
"""QA-validate a .pptx deck built by presentation-creator.

Usage:
    python3 validate_deck.py deck.pptx [--json]

Checks:
  * shapes outside the slide bounds (1% tolerance)
  * estimated text overflow (font size + box size vs. text length)
  * font floors (body >= 14pt, titles >= 28pt)
  * more than 6 bullets on a slide
  * a slide with no title text
  * duplicate slide titles
  * low text/background contrast (WCAG ratio)

Exit code: 1 if any errors were reported, 0 otherwise (warnings alone exit 0).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
except ModuleNotFoundError:  # pragma: no cover - environment guard
    sys.stderr.write(
        "error: python-pptx is not installed. See references/troubleshooting.md.\n"
    )
    raise SystemExit(2)


EMU_PER_PT = 12700
BODY_FLOOR_PT = 14.0
TITLE_FLOOR_PT = 28.0
BOUNDS_TOLERANCE = 0.01
OVERFLOW_TOLERANCE = 1.15
MAX_BULLETS = 6
CAPTION_BAND_IN = 0.9


def _emu_to_pt(value) -> float:
    return (value or 0) / EMU_PER_PT


def _rgb(shape_fill):
    try:
        rgb = shape_fill.fore_color.rgb
        return (rgb[0], rgb[1], rgb[2])
    except Exception:
        return None


def _solid_fill_color(shape):
    try:
        from pptx.enum.dml import MSO_FILL
    except Exception:  # pragma: no cover
        return None
    try:
        if shape.fill.type == MSO_FILL.SOLID:
            return _rgb(shape.fill)
    except Exception:
        return None
    return None


def _run_color(run):
    try:
        rgb = run.font.color.rgb
        return (rgb[0], rgb[1], rgb[2])
    except Exception:
        return None


def _relative_luminance(color) -> float:
    def channel(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in color)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(fg, bg) -> float:
    l1, l2 = _relative_luminance(fg), _relative_luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def _rects_overlap(a, b) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)


def _slide_bg_color(slide):
    try:
        bg = slide.background.fill
        from pptx.enum.dml import MSO_FILL

        if bg.type == MSO_FILL.SOLID:
            return _rgb(bg)
    except Exception:
        return None
    return None


def _shape_bbox(shape):
    return (shape.left or 0, shape.top or 0, shape.width or 0, shape.height or 0)


def _text_shapes(slide):
    result = []
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text_frame.text.strip():
            result.append(shape)
    return result


def _max_font_size(shape) -> float:
    sizes = []
    for p in shape.text_frame.paragraphs:
        for r in p.runs:
            if r.font.size is not None:
                sizes.append(r.font.size.pt)
    return max(sizes) if sizes else 18.0


def _estimate_overflow(shape):
    """Return (needed_pt, available_pt) or None when not applicable.

    Uses a word-wrap estimate (char width ~0.52em) instead of a raw
    character count, which is closer to how PowerPoint wraps text.
    """
    tf = shape.text_frame
    width_pt = _emu_to_pt(shape.width) - 14.4  # default L/R inset ~0.2in
    height_pt = _emu_to_pt(shape.height) - 7.2  # default T/B inset ~0.1in
    if width_pt <= 10 or height_pt <= 4:
        return None
    needed = 0.0
    for para in tf.paragraphs:
        text = "".join(r.text for r in para.runs)
        if not text.strip():
            continue
        size = max(
            (r.font.size.pt for r in para.runs if r.font.size is not None),
            default=18.0,
        )
        chars_per_line = max(8, int(width_pt / (size * 0.52)))
        # word-aware wrapping
        words = text.split()
        lines = 1
        cur = 0
        for w in words:
            if cur == 0:
                cur = len(w)
            elif cur + 1 + len(w) <= chars_per_line:
                cur += 1 + len(w)
            else:
                lines += 1
                cur = len(w)
                if len(w) > chars_per_line:
                    lines += len(w) // chars_per_line
                    cur = len(w) % chars_per_line
        needed += lines * size * 1.3
        if para.space_after is not None:
            needed += para.space_after.pt
        else:
            needed += size * 0.2
    return needed, height_pt


def _bullets_on_slide(slide) -> int:
    count = 0
    for shape in _text_shapes(slide):
        for p in shape.text_frame.paragraphs:
            text = "".join(r.text for r in p.runs).strip()
            if text.startswith("\u2022") or text.startswith("- ") or text.startswith("* "):
                count += 1
    return count


class Report:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.slide_summaries: list[dict] = []

    def error(self, slide_idx, msg):
        self.errors.append(f"slide {slide_idx}: {msg}")

    def warn(self, slide_idx, msg):
        self.warnings.append(f"slide {slide_idx}: {msg}")


def validate(path: Path) -> Report:
    prs = Presentation(str(path))
    sw = prs.slide_width
    sh = prs.slide_height
    tol_x = sw * BOUNDS_TOLERANCE
    tol_y = sh * BOUNDS_TOLERANCE
    report = Report()
    seen_titles: dict[str, int] = {}

    for idx, slide in enumerate(prs.slides, start=1):
        texts = _text_shapes(slide)
        fill_shapes = []
        for shape in slide.shapes:
            color = _solid_fill_color(shape)
            if color is None:
                continue
            _x, _y, _w, _h = _shape_bbox(shape)
            if _w < int(0.05 * 914400) or _h < int(0.05 * 914400):
                continue
            fill_shapes.append((shape, _shape_bbox(shape), color))

        # -- bounds -----------------------------------------------------
        for shape in slide.shapes:
            x, y, w, h = _shape_bbox(shape)
            if (
                x < -tol_x
                or y < -tol_y
                or x + w > sw + tol_x
                or y + h > sh + tol_y
            ):
                report.error(
                    idx,
                    f"shape '{shape.shape_type}' outside slide bounds "
                    f"(l={x / 914400:.2f}in t={y / 914400:.2f}in "
                    f"r={(x + w) / 914400:.2f}in b={(y + h) / 914400:.2f}in)",
                )

        # -- tables -----------------------------------------------------
        for shape in slide.shapes:
            if shape.has_table:
                tbl = shape.table
                n_rows = len(tbl.rows)
                n_cols = len(tbl.columns)
                if n_rows > 9:
                    report.warn(idx, f"table has {n_rows} rows (>8 body rows)")
                if n_cols > 6:
                    report.warn(idx, f"table has {n_cols} columns (>6)")

        # -- font floors, overflow, contrast ---------------------------
        bg_default = _slide_bg_color(slide) or (255, 255, 255)
        max_size = max((_max_font_size(s) for s in texts), default=0.0)
        title_text = None
        for shape in texts:
            size = _max_font_size(shape)
            is_footer = (shape.top or 0) >= sh - int(CAPTION_BAND_IN * 914400)
            text_value = shape.text_frame.text.strip()

            if max_size and size == max_size and title_text is None:
                title_text = text_value
                if size < TITLE_FLOOR_PT and (shape.top or 0) < int(2.0 * 914400):
                    report.error(
                        idx,
                        f"title font {size:.0f}pt is below the {TITLE_FLOOR_PT:.0f}pt floor",
                    )
            elif not is_footer:
                for p in shape.text_frame.paragraphs:
                    for r in p.runs:
                        if r.font.size is not None and r.font.size.pt < 12.0:
                            report.error(
                                idx,
                                f"body font {r.font.size.pt:.0f}pt is below the "
                                f"{BODY_FLOOR_PT:.0f}pt floor: {r.text[:40]!r}",
                            )
                            break

            over = _estimate_overflow(shape)
            if over is not None:
                needed, available = over
                if needed > available * OVERFLOW_TOLERANCE:
                    report.error(
                        idx,
                        f"estimated text overflow in '{text_value[:30]}…' "
                        f"(needs ~{needed:.0f}pt, box ~{available:.0f}pt)",
                    )

            # contrast: topmost solid fill below this text shape
            bbox = _shape_bbox(shape)
            bg = None
            for fshape, fbbox, color in fill_shapes:
                if fshape is shape:
                    continue
                if _rects_overlap(bbox, fbbox):
                    bg = color
            bg = bg or bg_default
            for p in shape.text_frame.paragraphs:
                for r in p.runs:
                    if not r.text.strip():
                        continue
                    fg = _run_color(r)
                    if fg is None:
                        continue
                    size = r.font.size.pt if r.font.size is not None else 18.0
                    bold = bool(r.font.bold)
                    large = size >= 24 or (size >= 18 and bold)
                    required = 3.0 if large else 4.5
                    ratio = _contrast(fg, bg)
                    if ratio < required:
                        report.error(
                            idx,
                            f"low contrast {ratio:.2f}:1 (need {required:.1f}:1) for "
                            f"{r.text[:30]!r}",
                        )

        # -- bullets ----------------------------------------------------
        bullets = _bullets_on_slide(slide)
        if bullets > MAX_BULLETS:
            report.error(idx, f"{bullets} bullets (max {MAX_BULLETS} per slide)")

        # -- density / wall-of-text heuristics -------------------------
        total_chars = sum(len(sh.text_frame.text) for sh in texts)
        if total_chars > 1100:
            report.warn(idx, f"slide is text-heavy ({total_chars} chars); consider splitting")
        est_lines = 0
        for _sh in texts:
            _ = _estimate_overflow(_sh)
        if bullets > 5:
            report.warn(idx, f"{bullets} bullets is dense; aim for <=5")
        # whitespace coverage
        slide_area = (sw / 914400) * (prs.slide_height / 914400)
        xs, ys, xe, ye = [], [], [], []
        for shape in slide.shapes:
            x, y, w, h = _shape_bbox(shape)
            xs.append(x / 914400); ys.append(y / 914400)
            xe.append((x + w) / 914400); ye.append((y + h) / 914400)
        if xs:
            covered = (max(xe) - min(xs)) * (max(ye) - min(ys))
        else:
            covered = 0.0
        coverage = covered / slide_area if slide_area else 0.0
        if coverage < 0.12:
            report.warn(idx, f"slide looks sparse (content covers ~{coverage:.0%}); add substance or remove")
        if coverage > 0.97:
            report.warn(idx, f"slide looks crowded (content covers ~{coverage:.0%}); add whitespace")

        # -- title presence / duplicates --------------------------------
        if title_text is None:
            report.error(idx, "slide has no title text")
        else:
            key = title_text.lower()
            if key in seen_titles:
                report.error(idx, f"duplicate title (also on slide {seen_titles[key]})")
            else:
                seen_titles[key] = idx

        # -- notes ------------------------------------------------------
        has_notes = bool(
            slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip()
        )
        if not has_notes:
            report.warn(idx, "slide has no speaker notes")

        report.slide_summaries.append(
            {"slide": idx, "title": title_text, "bullets": bullets, "notes": has_notes}
        )

    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate a .pptx deck.")
    parser.add_argument("deck", help="path to the .pptx file")
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args(argv)

    path = Path(args.deck)
    if not path.is_file():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    report = validate(path)

    if args.json:
        print(
            json.dumps(
                {
                    "file": str(path),
                    "errors": report.errors,
                    "warnings": report.warnings,
                    "slides": report.slide_summaries,
                    "ok": not report.errors,
                },
                indent=2,
            )
        )
    else:
        print(f"Deck: {path}")
        print(f"Slides: {len(report.slide_summaries)}")
        for line in report.errors:
            print(f"  ERROR   {line}")
        for line in report.warnings:
            print(f"  WARNING {line}")
        if report.errors:
            print(f"\nFAILED: {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
        else:
            print(f"\nPASSED: 0 errors, {len(report.warnings)} warning(s)")

    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
