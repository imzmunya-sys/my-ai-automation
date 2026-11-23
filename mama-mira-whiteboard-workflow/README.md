# Mama Mira Farm — Whiteboard Video Workflow

A reusable starting point for making colourful 16:9 whiteboard explainers from **your approved narration audio and a numbered scene plan**.

> **Reconstructed on 23 November 2026.** The previously mentioned \`mama-mira-whiteboard-workflow.zip\` was not accessible, so these source files were recreated from the approved production brief. They are **not** represented as a copy of that missing ZIP. The approved Mama Mira image and the original drawing-hand asset were not available for upload.

## Production rules

- Use only the approved Mama Mira face, voluminous black curly hair, gold hoop earrings, yellow blouse and blue denim apron. **Never replace her image with a different woman.**
- Whiteboard: white background, black marker outlines, then progressive natural colours (garden greens, sunshine yellow, warm soil brown).
- Narration: use the owner's **existing recorded voice note exactly**, no AI narrator, background music or subtitles added by this program.
- Format: landscape 16:9; 1920×1080 by default. Preserve the script, sequence and audio timing.
- Each \`S01_Cxx\` entry in the scene JSON gives a fixed time range and specific picture/label. The engine renders exactly that plan; it does not automatically understand a 30-minute script.

## Folder contents

- \`render_whiteboard.py\` — script to make a progressively drawn MP4 with original narration.
- \`scenes_example.json\` — sample collards lesson storyboard; timings are **examples**, not the approved 30-minute narration.
- \`requirements.txt\` — Python requirements.
- \`assets/drawing_hand.svg\` — simple **new placeholder** marker-hand graphic. Replace with your original hand asset before final production.
- \`assets/README.md\` — instructions to add the **approved** Mama Mira reference image.

## Getting started

1. Install Python 3.10+ and FFmpeg, including \`ffprobe\`.
2. In this folder run: \`python -m pip install -r requirements.txt\`
3. Put your approved narration as \`narration.wav\`, \`narration.mp3\` or \`narration.m4a\` (do not upload private audio to a public GitHub repository).
4. Put your approved character PNG in \`assets/mama_mira.png\` — if this is missing, the renderer will **not** invent Mama Mira.
5. Prepare \`scenes.json\` based on the example with **all** of your numbered scenes and accurate timecodes. Paths for \`illustration\` are optional; where present they are shown without changing the original face/art.
6. Run: \`python render_whiteboard.py --scenes scenes.json --audio narration.m4a --output mama_mira_episode_02.mp4 --character assets/mama_mira.png\`
7. Preview the MP4, check the scene timing, hand movement, voice sync, character identity, spelling, text margins and illustration quality; approve before publishing.

Test without the character picture by removing \`--character\`. The result contains labels and simple botanical diagrams, **not** a substitute Mama Mira actor.

## Scene structure

Each scene contains:
- \`id\` — a unique clip ID such as \`S01_C01\`
- \`start\`, \`end\` — seconds relative to the beginning of the narration
- \`label\` — short handwritten-style diagram label; leave empty for no words on the picture
- \`visual\` — \`soil\`, \`seedling\`, \`collards\`, \`watering\` or \`sun\`, or \`none\`
- \`illustration\` — optional PNG/JPG to use in the illustration area; relative to the JSON file
- \`accent\` — optional hex colour

The scene plan must start at 0, have no overlaps or gaps and use increasing clip IDs in story order. The program warns if the planned timeline differs from narration duration.

## Quality and continuity limitations

This is a practical storyboard-driven renderer, **not** an AI script-to-video service. It cannot independently choose scene compositions or produce a photorealistic moving human hand. The placeholder SVG is there so the project can run. High-end whiteboard animation will benefit from a professional hand PNG and custom drawn panel images. No visual or script changes are made silently.

## Local files you should not push to GitHub

Narration recordings, unpublished scripts, approved character image assets (unless you intend to license/share them), render caches, finished MP4s and any API keys. Keep master copies privately backed up.

## Mama Mira production checklist

- [ ] Approved script unchanged
- [ ] Original narrator audio loaded and not rewritten
- [ ] Every scene has a unique ID and exact narration time range
- [ ] Approved Mama Mira image used wherever she appears
- [ ] White background, black outlines, progressively filled colours
- [ ] 16:9 framing, no cropped heads
- [ ] Voice in sync with visuals; no unexpected captions, music or new people
- [ ] Full length, play-through and export checked
