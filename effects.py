import math
import os
from PIL import Image

# Functions from hw3 functions.py

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

#needed to remove the effects suffix from the image name otherwise we would edit the edited image over and over
#and not the original image
def original_img_path(img_path):
    base, _ = os.path.splitext(img_path)
    changed = True
    while changed:
        changed = False
        for suffix in ["_grayscale", "_sepia", "_negative"]:
            if base.endswith(suffix):
                base = base[:-len(suffix)]
                changed = True
    for ext in [".jpg", ".jpeg", ".png"]:
        candidate = base + ext
        if os.path.exists(os.path.join("static", candidate)):
            return candidate
    return img_path

THUMB_SIZE = 300
COLS = 3
PADDING = 10


def make_album_collage(image_paths, output_path, cols=None):
    # nothing to do if no images were passed in
    if not image_paths:
        return None

    # figure out the grid size — max 3 columns, rows fill in as needed
    cols = cols if cols is not None else min(len(image_paths), COLS)
    rows = math.ceil(len(image_paths) / cols)

    # canvas needs to fit all thumbnails plus a little padding around each one
    canvas_w = cols * THUMB_SIZE + (cols + 1) * PADDING
    canvas_h = rows * THUMB_SIZE + (rows + 1) * PADDING

    # dark background so the album covers pop
    canvas = Image.new('RGB', (canvas_w, canvas_h), (20, 20, 20))

    for i, path in enumerate(image_paths):
        # resize every cover to the same size 
        src = Image.open(path).convert('RGB').resize((THUMB_SIZE, THUMB_SIZE))
        col = i % cols
        row = i // cols

        start_x = PADDING + col * (THUMB_SIZE + PADDING)
        start_y = PADDING + row * (THUMB_SIZE + PADDING)

        # pixel copy from lab 8
        for source_x in range(src.width):
            target_x = start_x + source_x
            for source_y in range(src.height):
                target_y = start_y + source_y
                p = src.getpixel((source_x, source_y))
                canvas.putpixel((target_x, target_y), p)

    canvas.save(output_path)
    return output_path
