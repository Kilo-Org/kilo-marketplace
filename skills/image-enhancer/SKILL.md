---
name: image-enhancer
description: "Upscales, sharpens, and removes compression artifacts from images and screenshots, optimizing output for web, print, or social media. Use when improving image quality, upscaling low-resolution screenshots, or preparing visuals for publication."
metadata:
  category: creative-media
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: image-enhancer
---

## Workflow

### 1. Analyze

Inspect the source image to determine enhancement strategy:

```python
from PIL import Image

img = Image.open("screenshot.png")
print(f"Resolution: {img.size[0]}x{img.size[1]}")
print(f"Format: {img.format} | Mode: {img.mode}")
print(f"File size: {os.path.getsize('screenshot.png') / 1024:.1f} KB")
```

Check for: resolution < target, visible blur or softness, compression artifacts (blocky areas in JPEGs), noise in dark regions.

### 2. Enhance

Apply enhancements using Pillow or OpenCV depending on the task:

**Upscale (Pillow — basic bicubic)**:
```python
from PIL import Image, ImageFilter

img = Image.open("input.png")
target = (img.width * 2, img.height * 2)
upscaled = img.resize(target, Image.LANCZOS)
upscaled.save("output.png")
```

**Sharpen (OpenCV — unsharp mask)**:
```python
import cv2
import numpy as np

img = cv2.imread("input.png")
blurred = cv2.GaussianBlur(img, (0, 0), 3)
sharpened = cv2.addWeighted(img, 1.5, blurred, -0.5, 0)
cv2.imwrite("output.png", sharpened)
```

**Remove JPEG artifacts (OpenCV — bilateral filter)**:
```python
img = cv2.imread("input.jpg")
cleaned = cv2.bilateralFilter(img, 9, 75, 75)
cv2.imwrite("output.png", cleaned)  # Save as PNG to avoid re-compression
```

For high-quality AI upscaling, use `realesrgan-ncnn-vulkan`:
```bash
realesrgan-ncnn-vulkan -i input.png -o output.png -s 4 -n realesrgan-x4plus
```

### 3. Optimize for Target

| Target | Action |
|--------|--------|
| **Web** | Compress with `pillow` quality 85, max width 1920px |
| **Print** | Ensure 300 DPI: `img.save("out.png", dpi=(300, 300))` |
| **Social** | Resize to platform specs (e.g., 1200x630 for Open Graph) |
| **Retina** | Output at 2x display resolution |

### 4. Save and Verify

```python
import shutil, os

# Preserve original
shutil.copy2("screenshot.png", "screenshot-original.png")

# Save enhanced version
enhanced.save("screenshot.png", optimize=True)

# Verify output
result = Image.open("screenshot.png")
assert result.size[0] >= img.size[0], "Output should not be smaller than input"
print(f"Before: {os.path.getsize('screenshot-original.png')/1024:.0f}KB → After: {os.path.getsize('screenshot.png')/1024:.0f}KB")
```

## Example

**Prompt:** "Upscale screenshot-2024.png to retina resolution and sharpen it"

```
Analyzing screenshot-2024.png...
  Resolution: 1920x1080 | Format: PNG | Issue: slight blur, standard DPI

Steps applied:
  1. Upscaled 2x via LANCZOS → 3840x2160
  2. Applied unsharp mask (amount=1.5, radius=3)
  3. Verified: output resolution 3840x2160, no visible artifacts

Saved: screenshot-2024.png (enhanced)
Backup: screenshot-2024-original.png
```

