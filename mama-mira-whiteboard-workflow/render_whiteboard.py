#!/usr/bin/env python3
"""Storyboard-driven Mama Mira whiteboard MP4 renderer.

This program does NOT write narration, invent character faces or interpret scripts.
It reveals approved diagrams and labels, then muxes the supplied narration unchanged.
Requires Pillow, CairoSVG, and the FFmpeg/FFprobe command-line tools.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WHITE = (255, 255, 255)
INK = (37, 38, 39)
ROOT = Path(__file__).resolve().parent


def font_at(size: int):
    for name in ("DejaVuSans.ttf", "Arial.ttf", "LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def hex_rgb(value: str):
    value = str(value or "#478b55").lstrip("#")
    if len(value) != 6:
        raise ValueError("Accent must be #RRGGBB")
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))


def read_scenes(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    scenes = data["scenes"]
    if not scenes:
        raise ValueError("Storyboard has no scenes")
    ids = set()
    prior_end = 0.0
    for item in scenes:
        sid = str(item["id"])
        start, end = float(item["start"]), float(item["end"])
        if sid in ids:
            raise ValueError(f"Duplicate clip ID: {sid}")
        if abs(start - prior_end) > 0.001:
            raise ValueError(f"Gap or overlap before {sid}: {prior_end} -> {start}")
        if not math.isfinite(end) or end <= start:
            raise ValueError(f"Invalid duration: {sid}")
        if len(str(item.get("label", ""))) > 100:
            raise ValueError(f"Keep labels short for the whiteboard: {sid}")
        ids.add(sid)
        prior_end = end
    return scenes


def narration_duration(audio: Path):
    command = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(audio)
    ]
    try:
        return float(subprocess.check_output(command, text=True).strip())
    except (ValueError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("Could not read narration duration with ffprobe") from exc


def fit_img(path: Path, max_w: int, max_h: int):
    image = Image.open(path).convert("RGBA")
    image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    return image


def make_hand(path: Path, size: int):
    if not path.exists():
        return None
    if path.suffix.lower() == ".svg":
        import cairosvg
        pixels = cairosvg.svg2png(url=str(path), output_width=size)
        return Image.open(io.BytesIO(pixels)).convert("RGBA")
    hand = Image.open(path).convert("RGBA")
    hand.thumbnail((size, size), Image.Resampling.LANCZOS)
    return hand


def draw_leaf(d, x, y, radius, outline, fill):
    d.ellipse((x-radius, y-radius*0.6, x+radius, y+radius*0.6),
              outline=outline, fill=fill, width=max(2, int(radius*0.065)))
    d.line((x-radius*0.65, y, x+radius*0.65, y), fill=outline, width=max(2, int(radius*0.04)))


def draw_botanical(d, name: str, size: tuple[int, int], colored: bool, accent):
    w, h = size
    x, y = int(w*0.72), int(h*0.56)
    thickness = max(4, w//360)
    green = accent if colored else WHITE
    soil = (151, 96, 60) if colored else WHITE
    blue = (98, 177, 215) if colored else WHITE
    yellow = (243, 197, 71) if colored else WHITE

    name = str(name or "none").lower()
    if name in ("soil", "seedling", "collards", "watering"):
        d.rounded_rectangle((x-int(w*.16), y+int(h*.13), x+int(w*.16), y+int(h*.24)),
                            radius=17, fill=soil, outline=INK, width=thickness)
        for dx in (-.12, -.055, .025, .105):
            px = x+int(w*dx)
            d.ellipse((px-7, y+int(h*.17), px+7, y+int(h*.18)), fill=INK)

    if name in ("seedling", "collards", "watering"):
        d.line((x, y+int(h*.14), x, y-int(h*.13)), fill=INK, width=thickness)
        spread = 1.0 if name == "seedling" else 1.5
        for sign in (-1, 1):
            draw_leaf(d, x+sign*int(w*.07*spread), y-int(h*.085),
                      int(w*.063*spread), INK, green)
            d.line((x, y, x+sign*int(w*.075*spread), y-int(h*.085)),
                   fill=INK, width=thickness)
        if name != "seedling":
            draw_leaf(d, x, y-int(h*.16), int(w*.07), INK, green)

    if name == "watering":
        bx, by = x-int(w*.20), y-int(h*.22)
        d.ellipse((bx-45,by-30,bx+50,by+32), fill=blue, outline=INK, width=thickness)
        d.line((bx+40,by,bx+120,by+40), fill=INK, width=thickness*2)
        for i in range(4):
            dx = int(w*.025*i)
            d.ellipse((bx+130+dx,by+60+dx//3,bx+136+dx,by+68+dx//3),
                      fill=blue, outline=INK)

    elif name == "sun":
        r = int(w*.092)
        d.ellipse((x-r,y-r,x+r,y+r), outline=INK, fill=yellow, width=thickness)
        for a in range(12):
            ang = a*math.pi/6
            d.line((x+int(r*1.2*math.cos(ang)),y+int(r*1.2*math.sin(ang)),
                    x+int(r*1.6*math.cos(ang)),y+int(r*1.6*math.sin(ang))),
                   fill=INK, width=thickness)

    elif name == "collards":
        for off in (-1, 0, 1):
            draw_leaf(d, x+off*int(w*.065), y-int(h*.13*abs(off)),
                      int(w*.085), INK, green)


def make_art(scene: dict, w: int, h: int, color: bool, scene_dir: Path,
             character: Path | None):
    image = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(image)
    margin = int(w*.09)
    max_text_width = int(w*.49)
    words = str(scene.get("label", "")).split()
    font = font_at(int(h*.07))
    y = int(h*.22)
    line = ""
    lines = []
    for word in words:
        test = (line+" "+word).strip()
        if d.textbbox((0,0), test, font=font)[2] > max_text_width and line:
            lines.append(line)
            line = word
        else:
            line = test
    if line:
        lines.append(line)
    for line in lines[:5]:
        d.text((margin, y), line, font=font, fill=INK,
               stroke_width=0)
        y += int(h*.09)
    accent = hex_rgb(scene.get("accent", "#478b55"))
    draw_botanical(d, scene.get("visual","none"), (w,h), color, accent)

    artwork = str(scene.get("illustration", "")).strip()
    if artwork and color:
        asset = (scene_dir / artwork).resolve()
        if not asset.is_file():
            raise FileNotFoundError(f"Missing illustration for {scene['id']}: {asset}")
        pic = fit_img(asset, int(w*.38), int(h*.53))
        image.paste(pic, (int(w*.54), int(h*.27)), pic)

    if character is not None and color:
        pic = fit_img(character, int(w*.14), int(h*.25))
        image.paste(pic, (int(w*.82), int(h*.70)), pic)
    return image


def emit_frames(scenes, audio, out, w, h, fps, out_fps, hand, character, scene_dir):
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("Install FFmpeg and ffprobe and add them to PATH")
    duration = narration_duration(audio)
    planned = float(scenes[-1]["end"])
    if abs(duration-planned) > 0.5:
        print(f"WARNING: storyboard ends at {planned:.2f}s; narration is {duration:.2f}s. "
              "Fix timecodes before final production.", file=sys.stderr)

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo",
           "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "pipe:0",
           "-i", str(audio), "-r", str(out_fps), "-c:v", "libx264",
           "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags",
           "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    hand_img = make_hand(hand, max(100, int(w*.13)))
    try:
        for scene in scenes:
            print(f"Rendering {scene['id']}", flush=True)
            start = float(scene["start"])
            end = float(scene["end"])
            total = max(1, int(round((end-start)*fps)))
            ink = make_art(scene, w, h, False, scene_dir, None)
            colored = make_art(scene, w, h, True, scene_dir, character)
            for f in range(total):
                progress = f / max(1, total-1)
                ink_progress = min(1.0, progress / .65)
                color_progress = min(1.0, max(0, progress-.65)/.35)
                ink_x = int(w*ink_progress)
                color_x = int(w*color_progress)
                frame = Image.new("RGB", (w,h), WHITE)
                if ink_x:
                    frame.paste(ink.crop((0,0,ink_x,h)), (0,0))
                if color_x:
                    frame.paste(colored.crop((0,0,color_x,h)), (0,0))
                if hand_img is not None and progress < .97:
                    cursor = ink_x if progress < .65 else color_x
                    hx = min(w-hand_img.width, max(0,cursor-hand_img.width//3))
                    hy = int(h*.60)
                    frame.paste(hand_img,(hx,hy),hand_img)
                proc.stdin.write(frame.tobytes())
        proc.stdin.close()
        status = proc.wait()
        if status != 0:
            raise RuntimeError(f"FFmpeg exited with status {status}")
    except Exception:
        if proc.stdin and not proc.stdin.closed:
            proc.stdin.close()
        proc.kill()
        proc.wait()
        raise
    print(f"Created {out} | planned {planned:.2f}s | audio {duration:.2f}s")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scenes", type=Path, required=True)
    p.add_argument("--audio", type=Path, required=True)
    p.add_argument("--output", type=Path, default=Path("mama_mira_whiteboard.mp4"))
    p.add_argument("--character", type=Path, help="Approved Mama Mira PNG only")
    p.add_argument("--hand", type=Path, default=ROOT/"assets/drawing_hand.svg")
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument("--fps", type=int, default=12)
    p.add_argument("--output-fps", type=int, default=24)
    a = p.parse_args()
    if a.width <= 0 or a.height <= 0 or a.fps <= 0 or a.output_fps <= 0:
        p.error("Dimensions and FPS must be positive")
    if abs(a.width/a.height-16/9) > 0.002:
        p.error("Use 16:9 output dimensions for Mama Mira")
    if not a.audio.is_file():
        p.error(f"Audio does not exist: {a.audio}")
    if a.character is not None and not a.character.is_file():
        p.error(f"Approved Mama Mira character image not found: {a.character}")
    scenes = read_scenes(a.scenes)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    emit_frames(scenes, a.audio, a.output, a.width, a.height,
                a.fps, a.output_fps, a.hand, a.character, a.scenes.resolve().parent)


if __name__ == "__main__":
    main()
