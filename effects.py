import os
from PIL import Image

# Functions adapted from hw3/functions.py

def apply_grayscale(full_path):
    im = Image.open(full_path).convert("RGB")
    pixels = list(im.getdata())
    new_list = [((a[0]*299 + a[1]*587 + a[2]*114) // 1000,) * 3 for a in pixels]
    im.putdata(new_list)
    base, _ = os.path.splitext(full_path)
    out_path = f"{base}_grayscale.png"
    im.save(out_path)
    return out_path


def apply_sepia(full_path):
    im = Image.open(full_path).convert("RGB")

    def sepia_tint(p):
        if p[0] < 63:
            r, g, b = int(p[0] * 1.1), p[1], int(p[2] * 0.9)
        elif p[0] < 192:
            r, g, b = int(p[0] * 1.15), p[1], int(p[2] * 0.85)
        else:
            r, g, b = int(p[0] * 1.08), p[1], int(p[2] * 0.5)
        return (min(r, 255), min(g, 255), min(b, 255))

    im.putdata([sepia_tint(p) for p in im.getdata()])
    base, _ = os.path.splitext(full_path)
    out_path = f"{base}_sepia.png"
    im.save(out_path)
    return out_path


def apply_negative(full_path):
    im = Image.open(full_path).convert("RGB")
    im.putdata([(255 - p[0], 255 - p[1], 255 - p[2]) for p in im.getdata()])
    base, _ = os.path.splitext(full_path)
    out_path = f"{base}_negative.png"
    im.save(out_path)
    return out_path


EFFECTS = {
    "grayscale": apply_grayscale,
    "sepia": apply_sepia,
    "negative": apply_negative,
}
