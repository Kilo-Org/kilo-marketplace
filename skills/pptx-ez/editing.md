# Editing Presentations

## Template-Based Workflow

When using an existing presentation as a template:

1. **Analyze the template**:
   ```bash
   python scripts/thumbnail.py template.pptx
   python -m markitdown template.pptx
   ```
   Review `thumbnails.jpg` for layouts; markitdown output for placeholder text.

2. **Plan slide mapping**: for each content section, choose a template slide.

   ⚠️ **Use varied layouts** — monotonous presentations are a common failure mode.
   Actively seek out:
   - Multi-column layouts (2-column, 3-column)
   - Image + text combinations
   - Full-bleed images with text overlay
   - Quote or callout slides
   - Section dividers
   - Stat / number callouts
   - Icon grids

   Avoid repeating the same text-heavy layout on every slide.

3. **Unpack**:
   ```bash
   python scripts/office/unpack.py template.pptx unpacked/
   ```

4. **Structural edits** (do yourself, not with subagents):
   - Delete unwanted slides: remove `<p:sldId>` from `<p:sldIdLst>` in `ppt/presentation.xml`
   - Duplicate slides: `python scripts/add_slide.py unpacked/ slide2.xml`
   - Reorder: rearrange `<p:sldId>` elements in `ppt/presentation.xml`
   - **Complete ALL structural changes before step 5**

5. **Edit content** (use subagents if available — slides are separate XML files):
   ```
   ppt/slides/slide1.xml
   ppt/slides/slide2.xml
   ...
   ```
   For each slide: read the XML, identify ALL placeholder content, replace with final content.
   **Use the Edit tool** — do not use sed, awk, or Python scripts for content edits.

6. **Clean orphaned parts**:
   ```bash
   python scripts/clean.py unpacked/
   ```

7. **Pack**:
   ```bash
   python scripts/office/pack.py unpacked/ output.pptx --original template.pptx
   ```

---

## Slide Operations

Slide order lives in `ppt/presentation.xml` → `<p:sldIdLst>`.

**Reorder**: rearrange `<p:sldId>` elements.

**Delete**: remove `<p:sldId>`, then run `clean.py` to remove the orphaned slide file and media.

**Add / duplicate**:
```bash
python scripts/add_slide.py unpacked/ slide2.xml         # duplicate
python scripts/add_slide.py unpacked/ slideLayout6.xml   # from layout
# Prints: <p:sldId id="..." r:id="..."/>
# → insert this element at the desired position in ppt/presentation.xml <p:sldIdLst>
```

Never manually copy slide files — `add_slide.py` handles Content_Types.xml, relationship IDs, and notes-slide cleanup that manual copies miss.

---

## Formatting Rules (XML editing)

- **Bold all headers, subheadings, and inline labels**: `b="1"` on `<a:rPr>`:
  ```xml
  <a:rPr lang="en-US" sz="2400" b="1" dirty="0"/>
  ```
  Applies to: slide titles, section headers, inline labels like "Status:", "Note:".

- **Never use unicode bullets (•)**: use `<a:buChar char="•"/>` or `<a:buAutoNum>` — unicode bullets create double-bullets when combined with list formatting.

- **Bullet inheritance**: let bullets inherit from the layout. Only specify `<a:buChar>` or `<a:buNone>` when overriding.

---

## Multi-item content pattern

Create separate `<a:p>` elements for each item — **never concatenate into one string**.

**❌ WRONG**:
```xml
<a:p>
  <a:r><a:rPr lang="en-US" sz="1800" dirty="0"/>
    <a:t>Step 1: Do the first thing. Step 2: Do the second thing.</a:t>
  </a:r>
</a:p>
```

**✅ CORRECT** — separate paragraphs, bold headers:
```xml
<a:p>
  <a:pPr algn="l"><a:lnSpc><a:spcPts val="3600"/></a:lnSpc></a:pPr>
  <a:r><a:rPr lang="en-US" sz="1800" b="1" dirty="0"/><a:t>Step 1</a:t></a:r>
</a:p>
<a:p>
  <a:pPr algn="l"><a:lnSpc><a:spcPts val="3600"/></a:lnSpc></a:pPr>
  <a:r><a:rPr lang="en-US" sz="1800" dirty="0"/><a:t>Do the first thing.</a:t></a:r>
</a:p>
```

Copy `<a:pPr>` from the original paragraph to preserve line spacing. Use `b="1"` on header runs.

---

## Template adaptation pitfalls

When the source has fewer items than the template:
- **Remove excess elements entirely** (images, shapes, text boxes) — do not just clear text
- Check for orphaned visuals after clearing text content
- Run visual QA to catch mismatched element counts

When replacing text with longer content:
- Longer text may overflow or wrap unexpectedly
- Test with visual QA after changes
- Consider truncating or splitting content to fit the template's design constraints

---

## Smart quotes (XML entities)

`unpack.py` encodes smart quotes as XML entities so plain-text editors don't corrupt them. `pack.py` restores them. When adding new text with the Edit tool, use entities explicitly:

| Character | Entity |
|-----------|--------|
| `"` (left double) | `&#x201C;` |
| `"` (right double) | `&#x201D;` |
| `'` (left single) | `&#x2018;` |
| `'` (right single) | `&#x2019;` |

```xml
<a:t>the &#x201C;Agreement&#x201D; between parties</a:t>
```

---

## Other XML pitfalls

- **Whitespace preservation**: use `xml:space="preserve"` on `<a:t>` with leading/trailing spaces:
  ```xml
  <a:t xml:space="preserve"> leading space</a:t>
  ```

- **Never use `xml.etree.ElementTree`** for parsing — it corrupts namespaces. Use `defusedxml.minidom` or `lxml.etree`.

- **Shape IDs must be unique** within a slide. When duplicating shapes, assign new `id` values on `<p:cNvPr>`.

- **`<a:off>` and `<a:ext>` values** are in EMU (914 400 per inch). Mis-set values cause invisible or off-screen elements.
