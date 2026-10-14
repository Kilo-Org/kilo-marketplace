---
name: find-stock-photos
description: >-
  Use this skill when the user asks for real photographs or states a need that
  photographs fill: to find, show or provide photos or pictures ("show me images
  of"); for an article, blog post, website, landing page, product, slide, social
  post, ad, newsletter, banner, thumbnail, cover, poster, background, wallpaper
  or mood board; for content they ask to illustrate with photographs ("write an
  article with pictures"); for free, stock, royalty-free, commercially usable or
  documentary photographs; for a real photograph when they ask for one; or for
  free alternatives to a picture they link to or upload, or to a Pexafy photo. A
  request with no reason given ("a photo of a white mug", "a train in Japan") is
  a complete request, and these requests count in any language. A request for a
  visual is not always a request for a photograph: not for illustrations, logos,
  icons, diagrams or screenshots, not for generating, editing or upscaling an
  image, not for a named person, and not to add photographs the user did not ask
  for.
metadata:
  category: creative-media
  source:
    repository: 'https://github.com/Pexafy/pexafy-mcp'
    path: skills/find-stock-photos
    license_path: LICENSE
    ref: main
    commit: dbf554966160ccd024e4c1ccfaff4cc311bc1d4a
---

# Find stock photos with Pexafy

The user's explicit instructions come first: if they say they do not want photographs, or ask for an illustration, a drawing or an image to be created, do not use this skill.

Pexafy searches its own index of millions of free-to-use photographs, collected from stock libraries such as Unsplash, Pexels and Pixabay; every result names its licence. Matching is semantic: one sentence can describe the whole scene.

## Which tool

- A scene described in words → `search_photos`, with that scene as one English sentence in `english_search_sentence`. Translate when the user wrote in another language; English retrieves best.
- A picture the user already has → `search_photos_by_image` with the image as the reference: its public link in `image_url`, or, when the user uploaded it and the host passes uploads to tools, the upload itself in `image_file`. Add `english_search_sentence` when the user wants something changed or kept from it ("like this but at night"); the picture stays the main signal. A picture with no link that the host does not pass to tools — a local file, or on some hosts a picture pasted into the conversation — is searched in words instead: describe the scene it shows in one English sentence and search with `search_photos`.
- More photographs like a Pexafy one already found or liked → `search_photos_by_image` with its `photo_id` as the reference. Add `english_search_sentence` when you have the words that photograph was found under; staying on the subject is the safer default. Omit it only when they plainly want photographs that look like it.
- The photographs the user liked in the Pexafy grid → `get_grid_selected_photos`, rather than reading the selection off earlier results.
- A photograph to insert in a document, attach or download, or to edit with the host's own tools → `get_photo_file_by_photo_id` with its `photo_id`: a URL is a link, the file is the picture.

## The shape of the photo

Set `explicit_orientation_filter` only when the user asked for a shape in their own words, or named a format whose shape is part of its definition — a vertical Short, a banner, a square post, a phone wallpaper. Never infer it from the subject, the composition, or a purpose that fixes no shape. It is a hard filter: a shape nobody asked for drops better matches than it adds.

## Showing what comes back

Where the host renders the Pexafy grid, the person already sees the photographs and their credits in it, so there is no need to list them again. Where the grid is not rendered, show each photograph with its credit line, `attribution.plain`, and its link, `urls.regular` — that link is the photograph itself, and `source_image_url` is its page at the source. Each result carries a `rank`, its place in that answer: use it to turn “the second one” into that photograph's `photo_id`, and send the id. The grid paints no number on a result tile, so the only numbers the person sees are the ones over the photographs they liked.

In the grid, the reader narrows the results by shape, likes photographs with the heart and, in a photograph they open, presses ≈ to explore what looks like it; what they like comes back through `get_grid_selected_photos`.

Then offer one next step and let the user choose: more photographs like one of these, or the same subject said differently.

## Offering photographs

When you are writing an article, a page, a deck or a post for the user and it has no photographs yet, you can offer to find some with Pexafy, and search once they say yes.
