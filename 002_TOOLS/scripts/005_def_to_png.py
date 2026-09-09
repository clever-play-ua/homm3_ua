#!/usr/bin/env python3
"""
Problem this solves: HoMM3 .DEF sprite/animation files are not a viewable
image format. This decodes every frame of a .DEF into a transparent PNG.

Ported to Python 3 from josch/lodextract's defextract.py (GPLv2):
https://github.com/josch/lodextract

Usage:
    python 005_def_to_png.py file.DEF ./outdir          # single file
    python 005_def_to_png.py ./some_folder ./outdir      # every .DEF in a folder

Output: <outdir>/<name>.dir/<group>_<frame>.png (+ <name>.json describing
the animation groups/frame order).
"""
import argparse
import json
import os
import struct
import sys
from collections import defaultdict

import numpy as np
from PIL import Image


def extract_def(infile, outdir):
    """Decodes one .DEF sprite/animation file's every frame group to PNG
    (ported from josch/lodextract's defextract.py - see module docstring).
    In: infile (a .DEF path), outdir (parent output folder). Out: None
    (writes `<outdir>/<name>.dir/<group>_<frame>.png` per frame plus
    `<outdir>/<name>.json` describing the animation groups/frame order -
    the same manifest shape read_header_segments-adjacent tooling
    elsewhere in this project doesn't consume, this is purely for human/
    image-editor consumption)."""
    f = open(infile, "rb")
    bn = os.path.splitext(os.path.basename(infile))[0]

    t, _, _, blocks = struct.unpack("<IIII", f.read(16))

    palette = []
    for _i in range(256):
        r, g, b = struct.unpack("<BBB", f.read(3))
        palette.extend((r, g, b))

    offsets = defaultdict(list)
    for _i in range(blocks):
        bid, entries, _, _ = struct.unpack("<IIII", f.read(16))
        for _j in range(entries):
            f.read(13)  # frame name, unused
        for _j in range(entries):
            offs, = struct.unpack("<I", f.read(4))
            offsets[bid].append(offs)

    outpath = os.path.join(outdir, f"{bn}.dir")
    os.makedirs(outpath, exist_ok=True)

    out_json = {"sequences": [], "type": t, "format": -1}
    firstfw, firstfh = -1, -1

    for bid, frame_offsets in offsets.items():
        frames = []
        for j, offs in enumerate(frame_offsets):
            f.seek(offs)
            pixeldata = bytearray()
            _, fmt, fw, fh, w, h, lm, tm = struct.unpack("<IIIIIIii", f.read(32))
            outname = os.path.join(outdir, f"{bn}.dir", f"{bid:02d}_{j:02d}.png")

            if lm > fw or tm > fh:
                print(f"  skip frame {bid}_{j}: margins ({lm}x{tm}) > dimensions ({fw}x{fh})")
                continue

            if firstfw == -1 and firstfh == -1:
                firstfw, firstfh = fw, fh
            else:
                fw = max(fw, firstfw)
                fh = max(fh, firstfh)

            if out_json["format"] == -1:
                out_json["format"] = fmt

            frames.append(os.path.join(f"{bn}.dir", f"{bid:02d}_{j:02d}.png"))

            if w != 0 and h != 0:
                if fmt == 0:
                    pixeldata = f.read(w * h)
                elif fmt == 1:
                    lineoffs = struct.unpack("<" + "I" * h, f.read(4 * h))
                    for lineoff in lineoffs:
                        f.seek(offs + 32 + lineoff)
                        totalrowlength = 0
                        while totalrowlength < w:
                            code, length = struct.unpack("<BB", f.read(2))
                            length += 1
                            if code == 0xff:
                                pixeldata += f.read(length)
                            else:
                                pixeldata += bytes([code]) * length
                            totalrowlength += length
                elif fmt == 2:
                    lineoffs = struct.unpack(f"<{h}H", f.read(2 * h))
                    f.read(2)  # unknown
                    for lineoff in lineoffs:
                        if f.tell() != offs + 32 + lineoff:
                            f.seek(offs + 32 + lineoff)
                        totalrowlength = 0
                        while totalrowlength < w:
                            segment, = struct.unpack("<B", f.read(1))
                            code = segment >> 5
                            length = (segment & 0x1f) + 1
                            if code == 7:
                                pixeldata += f.read(length)
                            else:
                                pixeldata += bytes([code]) * length
                            totalrowlength += length
                elif fmt == 3:
                    lineoffs = [struct.unpack("<" + "H" * (w // 32), f.read(w // 16)) for _ in range(h)]
                    for lineoff in lineoffs:
                        for off_i in lineoff:
                            if f.tell() != offs + 32 + off_i:
                                f.seek(offs + 32 + off_i)
                            totalblocklength = 0
                            while totalblocklength < 32:
                                segment, = struct.unpack("<B", f.read(1))
                                code = segment >> 5
                                length = (segment & 0x1f) + 1
                                if code == 7:
                                    pixeldata += f.read(length)
                                else:
                                    pixeldata += bytes([code]) * length
                                totalblocklength += length
                else:
                    print(f"  unknown format {fmt} in {infile}")
                    continue

                imp = Image.frombytes('P', (w, h), bytes(pixeldata))
                imp.putpalette(palette)
                imrgb = imp.convert("RGBA")
                pixrgb = np.array(imrgb)
                pixp = np.array(imp)
                # HoMM3 special palette indices: 0/5=transparent, 1/7=shadow
                # border, 4/6=shadow body (see community DEF format notes)
                pixrgb[pixp == 0] = (0, 0, 0, 0)
                pixrgb[pixp == 1] = (0, 0, 0, 0x40)
                pixrgb[pixp == 4] = (0, 0, 0, 0x80)
                pixrgb[pixp == 5] = (0, 0, 0, 0)
                pixrgb[pixp == 6] = (0, 0, 0, 0x80)
                pixrgb[pixp == 7] = (0, 0, 0, 0x40)
                imrgb = Image.fromarray(pixrgb)
                im = Image.new('RGBA', (fw, fh), (0, 0, 0, 0))
                im.paste(imrgb, (lm, tm))
            else:
                im = Image.new('RGBA', (fw, fh), (0, 0, 0, 0))
            im.save(outname)
        out_json["sequences"].append({"group": bid, "frames": frames})

    with open(os.path.join(outdir, f"{bn}.json"), "w") as o:
        json.dump(out_json, o, indent=2)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="A .DEF file, or a folder to batch-convert every .DEF in it")
    ap.add_argument("outdir", help="Output folder")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    if os.path.isdir(args.input):
        def_files = [os.path.join(args.input, f) for f in os.listdir(args.input) if f.lower().endswith(".def")]
    else:
        def_files = [args.input]

    ok, failed = 0, []
    for path in def_files:
        print(f"{os.path.basename(path)} ...")
        try:
            if extract_def(path, args.outdir):
                ok += 1
            else:
                failed.append(path)
        except Exception as e:
            print(f"  FAILED: {e}")
            failed.append(path)

    print(f"\nConverted {ok}/{len(def_files)}")
    if failed:
        print("Failed:")
        for p in failed:
            print("  -", p)
        sys.exit(1)


if __name__ == "__main__":
    main()
