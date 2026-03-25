---
name: slack-gif-creator
description: "Creates animated GIFs optimized for Slack's message (2MB) and emoji (64KB) size constraints using composable animation primitives (shake, bounce, spin, pulse, fade, zoom, explode, wiggle, slide, flip, morph, move, kaleidoscope), validators, and optimization utilities built on Pillow and imageio. Use when creating Slack reaction GIFs, custom emoji animations, message GIFs, or any animated GIF that must meet Slack's file size and dimension requirements."
license: Complete terms in LICENSE.txt
metadata:
  category: creative-media
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: slack-gif-creator
    license_path: slack-gif-creator/LICENSE.txt
---

# Slack GIF Creator - Flexible Toolkit

A toolkit for creating animated GIFs optimized for Slack. Provides validators for Slack's constraints, composable animation primitives, and optional helper utilities. **Apply these tools however needed to achieve the creative vision.**

## Slack's Requirements

Slack has specific requirements for GIFs based on their use:

**Message GIFs:**
- Max size: ~2MB
- Optimal dimensions: 480x480
- Typical FPS: 15-20
- Color limit: 128-256
- Duration: 2-5s

**Emoji GIFs:**
- Max size: 64KB (strict limit)
- Optimal dimensions: 128x128
- Typical FPS: 10-12
- Color limit: 32-48
- Duration: 1-2s

**Emoji GIFs are challenging** - the 64KB limit is strict. Strategies that help:
- Limit to 10-15 frames total
- Use 32-48 colors maximum
- Keep designs simple
- Avoid gradients
- Validate file size frequently

## Toolkit Structure

This skill provides three types of tools:

1. **Validators** - Check if a GIF meets Slack's requirements
2. **Animation Primitives** - Composable building blocks for motion (shake, bounce, move, kaleidoscope)
3. **Helper Utilities** - Optional functions for common needs (text, colors, effects)

**Complete creative freedom is available in how these tools are applied.**

## Core Validators

To ensure a GIF meets Slack's constraints, use these validators:

```python
from core.gif_builder import GIFBuilder

# After creating your GIF, check if it meets requirements
builder = GIFBuilder(width=128, height=128, fps=10)
# ... add your frames however you want ...

# Save and check size
info = builder.save('emoji.gif', num_colors=48, optimize_for_emoji=True)

# The save method automatically warns if file exceeds limits
# info dict contains: size_kb, size_mb, frame_count, duration_seconds
```

**File size validator**:
```python
from core.validators import check_slack_size

# Check if GIF meets size limits
passes, info = check_slack_size('emoji.gif', is_emoji=True)
# Returns: (True/False, dict with size details)
```

**Dimension validator**:
```python
from core.validators import validate_dimensions

# Check dimensions
passes, info = validate_dimensions(128, 128, is_emoji=True)
# Returns: (True/False, dict with dimension details)
```

**Complete validation**:
```python
from core.validators import validate_gif, is_slack_ready

# Run all validations
all_pass, results = validate_gif('emoji.gif', is_emoji=True)

# Or quick check
if is_slack_ready('emoji.gif', is_emoji=True):
    print("Ready to upload!")
```

## Animation Primitives

Composable building blocks for motion. Apply to any object in any combination. Each primitive returns a list of frames.

| Primitive | Module | Key function | Parameters |
|-----------|--------|-------------|------------|
| **Shake** | `templates.shake` | `create_shake_animation()` | `object_type`, `object_data`, `num_frames`, `shake_intensity`, `direction` (both/horizontal/vertical) |
| **Bounce** | `templates.bounce` | `create_bounce_animation()` | `object_type`, `object_data`, `num_frames`, `bounce_height` |
| **Spin** | `templates.spin` | `create_spin_animation()` | `rotation_type` (clockwise/wobble), `full_rotations`. Also: `create_loading_spinner(spinner_type)` |
| **Pulse** | `templates.pulse` | `create_pulse_animation()` | `pulse_type` (smooth/heartbeat), `scale_range`. Also: `create_attention_pulse(emoji, num_frames)` |
| **Fade** | `templates.fade` | `create_fade_animation()` | `fade_type` (in/out). Also: `create_crossfade(object1_data, object2_data)` |
| **Zoom** | `templates.zoom` | `create_zoom_animation()` | `zoom_type` (in/out), `scale_range`, `add_motion_blur`. Also: `create_explosion_zoom(emoji)` |
| **Explode** | `templates.explode` | `create_explode_animation()` | `explode_type` (burst/shatter/dissolve), `num_pieces`. Also: `create_particle_burst(particle_count)` |
| **Wiggle** | `templates.wiggle` | `create_wiggle_animation()` | `wiggle_type` (jello/wave), `intensity`, `cycles`. Also: `create_excited_wiggle(emoji)` |
| **Slide** | `templates.slide` | `create_slide_animation()` | `direction`, `slide_type` (in/across), `overshoot`. Also: `create_multi_slide(objects, stagger_delay)` |
| **Flip** | `templates.flip` | `create_flip_animation()` | `object1_data`, `object2_data`, `flip_axis` (horizontal/vertical). Also: `create_quick_flip(emoji1, emoji2)` |
| **Morph** | `templates.morph` | `create_morph_animation()` | `morph_type` (crossfade/scale/spin_morph) |
| **Move** | `templates.move` | `create_move_animation()` | `start_pos`, `end_pos`, `motion_type` (linear/arc/circle/wave), `easing`, `motion_params` |
| **Kaleidoscope** | `templates.kaleidoscope` | `create_kaleidoscope_animation()` | `base_frame`, `num_frames`, `segments`, `rotation_speed`. Also: `apply_simple_mirror(frame, mode)` |

### Composing Primitives

Combine primitives by iterating frames and applying multiple effects per frame:

```python
# Bounce + shake on impact
for i in range(num_frames):
    frame = create_blank_frame(480, 480, bg_color)
    t_bounce = i / (num_frames - 1)
    y = interpolate(start_y, ground_y, t_bounce, 'bounce_out')
    if y >= ground_y - 5:
        x = center_x + math.sin(i * 2) * 10  # shake on impact
    else:
        x = center_x
    draw_emoji(frame, '⚽', (x, y), size=60)
    builder.add_frame(frame)
```

## Helper Utilities

Optional helpers — use, modify, or replace with custom implementations as needed.

### GIF Builder

```python
from core.gif_builder import GIFBuilder

builder = GIFBuilder(width=480, height=480, fps=20)
for frame in my_frames:
    builder.add_frame(frame)
builder.save('output.gif', num_colors=128, optimize_for_emoji=False)
```

Features: automatic color quantization, duplicate frame removal, size warnings for Slack limits, emoji mode (aggressive optimization).

### Text, Color, Effects, and Easing

| Utility | Module | Key functions |
|---------|--------|--------------|
| **Text rendering** | `core.typography` | `draw_text_with_outline(frame, text, position, font_size, text_color, outline_color, outline_width, centered)`. Use `TYPOGRAPHY_SCALE['h1']` for sizing. For larger GIFs, PIL's `ImageDraw.text()` works directly. |
| **Color palettes** | `core.color_palettes` | `get_palette('vibrant')` — options: vibrant, pastel, dark, neon, professional. Returns dict with `background`, `primary`, `accent` keys. |
| **Visual effects** | `core.visual_effects` | `ParticleSystem()` (sparkles, confetti), `create_impact_flash(frame, position, radius)`, `create_shockwave_rings(frame, position, radii)` |
| **Easing** | `core.easing` | `interpolate(start, end, t, easing)` — easings: `linear`, `ease_in`, `ease_out`, `ease_in_out`, `bounce_out`, `elastic_out`, `back_out`. Also: `calculate_arc_motion()` |
| **Frame composition** | `core.frame_composer` | `create_gradient_background()`, `draw_emoji_enhanced()` (with optional shadow), `draw_circle_with_shadow()`, `draw_star()` |

## Optimization Strategies

When your GIF is too large:

**For Message GIFs (>2MB):**
1. Reduce frames (lower FPS or shorter duration)
2. Reduce colors (128 → 64 colors)
3. Reduce dimensions (480x480 → 320x320)
4. Enable duplicate frame removal

**For Emoji GIFs (>64KB) - be aggressive:**
1. Limit to 10-12 frames total
2. Use 32-40 colors maximum
3. Avoid gradients (solid colors compress better)
4. Simplify design (fewer elements)
5. Use `optimize_for_emoji=True` in save method

## Example Composition Patterns

### Emoji Reaction (Pulsing) — Emoji GIF

```python
builder = GIFBuilder(128, 128, 10)
for i in range(12):
    frame = Image.new('RGB', (128, 128), (240, 248, 255))
    scale = 1.0 + math.sin(i * 0.5) * 0.15
    size = int(60 * scale)
    draw_emoji_enhanced(frame, '😱', position=(64-size//2, 64-size//2), size=size, shadow=False)
    builder.add_frame(frame)
builder.save('reaction.gif', num_colors=40, optimize_for_emoji=True)
check_slack_size('reaction.gif', is_emoji=True)
```

### Action with Impact (Bounce + Flash) — Message GIF

```python
builder = GIFBuilder(480, 480, 20)
# Phase 1: fall
for i in range(15):
    frame = create_gradient_background(480, 480, (240, 248, 255), (200, 230, 255))
    y = interpolate(0, 350, i / 14, 'ease_in')
    draw_emoji_enhanced(frame, '⚽', position=(220, int(y)), size=80)
    builder.add_frame(frame)
# Phase 2: impact + flash + text
for i in range(8):
    frame = create_gradient_background(480, 480, (240, 248, 255), (200, 230, 255))
    if i < 3:
        frame = create_impact_flash(frame, (240, 350), radius=120, intensity=0.6)
    draw_emoji_enhanced(frame, '⚽', position=(220, 350), size=80)
    if i > 2:
        draw_text_with_outline(frame, "GOAL!", position=(240, 150), font_size=60,
                              text_color=(255, 68, 68), outline_color=(0, 0, 0),
                              outline_width=4, centered=True)
    builder.add_frame(frame)
builder.save('goal.gif', num_colors=128)
```

## Philosophy

This toolkit provides building blocks, not rigid recipes. To work with a GIF request:

1. **Understand the creative vision** - What should happen? What's the mood?
2. **Design the animation** - Break it into phases (anticipation, action, reaction)
3. **Apply primitives as needed** - Shake, bounce, move, effects - mix freely
4. **Validate constraints** - Check file size, especially for emoji GIFs
5. **Iterate if needed** - Reduce frames/colors if over size limits

**The goal is creative freedom within Slack's technical constraints.**

## Dependencies

To use this toolkit, install these dependencies only if they aren't already present:

```bash
pip install pillow imageio numpy
```
