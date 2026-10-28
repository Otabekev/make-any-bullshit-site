"""Render the flagship cover as an exact sibling of The Smoke Method cover.
All positions are measured from the Smoke Method's own layout (content area 1560 x 2339)."""
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageEnhance
import numpy as np

BG = (15, 19, 22)
RED = (215, 38, 30)
WHITE = (244, 242, 238)
GREY = (138, 140, 142)

W, H = 1560, 2339
SRC = Image.open("assets/smoke-method-cover.png").convert("RGB")
SW, SH = SRC.size

def bebas(size):
    return ImageFont.truetype("fonts/BebasNeue-Regular.ttf", size)

def oswald(size, wght=500):
    f = ImageFont.truetype("fonts/Oswald[wght].ttf", size)
    f.set_variation_by_axes([wght])
    return f

def inter(size, wght=400):
    f = ImageFont.truetype("fonts/Inter[opsz,wght].ttf", size)
    f.set_variation_by_axes([min(32, max(14, size / 2)), wght])
    return f

def tracked(d, x, y, text, font, fill, track):
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + track
    return x

def tracked_width(d, text, font, track):
    return sum(d.textlength(ch, font=font) + track for ch in text) - track

# ---------- smoke: the cover's own photographic smoke, flipped so the sibling isn't a copy ----------
canvas = Image.new("RGB", (W, H), BG)
col = SRC.crop((int(0.784 * SW), int(0.205 * SH), int(0.964 * SW), int(0.975 * SH)))
a = np.asarray(col).astype(np.int16)
floor = np.percentile(a.reshape(-1, 3), 55, axis=0) + 2
a = np.clip(a - floor, 0, 255).astype("uint8")           # isolate smoke from its own black
smoke = Image.fromarray(a).transpose(Image.FLIP_LEFT_RIGHT)
smoke = smoke.resize((round(smoke.width * H / smoke.height * 1.02), round(H * 1.02)), Image.LANCZOS)
smoke = ImageEnhance.Brightness(smoke).enhance(1.15)
layer = Image.new("RGB", (W, H), (0, 0, 0))
layer.paste(smoke, (W - smoke.width - 40, -20))
# a second, fainter wisp higher up, as the original has
wisp = SRC.crop((int(0.784 * SW), int(0.60 * SH), int(0.964 * SW), int(0.975 * SH)))
wraw = np.asarray(wisp).astype(np.int16)
wa = np.clip(wraw - (np.percentile(wraw.reshape(-1,3), 60, axis=0) + 2), 0, 255).astype("uint8")
wisp = Image.fromarray(wa).rotate(-28, expand=True, resample=Image.BICUBIC)
wisp = ImageEnhance.Brightness(wisp.resize((round(wisp.width * 1.3), round(wisp.height * 1.3)))).enhance(0.55)
layer2 = Image.new("RGB", (W, H), (0, 0, 0))
layer2.paste(wisp, (int(W * 0.48), -int(H * 0.05)))
def feather(im, px=110):
    w, h = im.size
    m = np.ones((h, w), np.float32)
    ramp = np.linspace(0, 1, px)
    m[:px, :] *= ramp[:, None]; m[-px:, :] *= ramp[::-1][:, None]
    m[:, :px] *= ramp[None, :]; m[:, -px:] *= ramp[::-1][None, :]
    return Image.fromarray((np.asarray(im).astype(np.float32) * m[..., None]).astype("uint8"))
smoke = feather(smoke, 90)
wisp = feather(wisp, 140)
layer = Image.new("RGB", (W, H), (0, 0, 0)); layer.paste(smoke, (W - smoke.width - 40, -20))
layer2 = Image.new("RGB", (W, H), (0, 0, 0)); layer2.paste(wisp, (int(W * 0.48), -int(H * 0.05)))
canvas = ImageChops.add(canvas, ImageChops.lighter(layer, layer2))

d = ImageDraw.Draw(canvas)
L, R = 163, 1396                     # the Smoke Method's text margins

# ---------- top rule + labels ----------
d.rectangle([L, 221, R, 223], fill=(62, 66, 70))
lab = oswald(30, 500)
tracked(d, L, 252, "CASE FILE № 002", lab, GREY, 11)
wr = tracked_width(d, "FIELD MANUAL", lab, 11)
tracked(d, R - wr, 252, "FIELD MANUAL", lab, GREY, 11)

# ---------- stamp, where FREE sits on the sibling ----------
st = Image.new("RGBA", (330, 120), (0, 0, 0, 0))
sd = ImageDraw.Draw(st)
sd.rectangle([4, 4, 325, 115], outline=RED + (255,), width=7)
sf = oswald(46, 600)
sw = tracked_width(sd, "FULL EDITION", sf, 7)
tracked(sd, (330 - sw) / 2, 30, "FULL EDITION", sf, RED + (255,), 7)
st = st.rotate(8, expand=True, resample=Image.BICUBIC)
canvas.paste(st, (R - st.width + 18, 330), st)

# ---------- title: four equal lines, cap height sized to the sibling's title block ----------
title = [("MAKE ANY", WHITE), ("BULLSHIT", RED), ("SOUND", WHITE), ("BRILLIANT", WHITE)]
size = 400
while True:
    f = bebas(size)
    if max(d.textlength(t, font=f) for t, _ in title) <= (R - L) * 0.96:
        break
    size -= 4
f = bebas(size)
cap = f.getbbox("H")[3] - f.getbbox("H")[1]
top_of_first_cap = 590
pitch = int(cap * 1.12)
for i, (t, c) in enumerate(title):
    y = top_of_first_cap + i * pitch - f.getbbox("H")[1]
    d.text((L - 4, y), t, font=f, fill=c)
title_bottom = top_of_first_cap + 3 * pitch + cap

# ---------- subtitle: bold first clause, then regular, wrapped like the sibling ----------
sub_bold = "The art of making weak arguments,"
sub_reg = "crazy ideas and unpopular opinions sound convincing."
fb, fr = inter(44, 620), inter(44, 400)
maxw = 1180 - L
words = [(w, fb, WHITE) for w in sub_bold.split()] + [(w, fr, (205, 205, 202)) for w in sub_reg.split()]
x, y = L, title_bottom + 104
space = d.textlength(" ", font=fr)
for w, font, col_ in words:
    ww = d.textlength(w, font=font)
    if x + ww > L + maxw:
        x, y = L, y + 62
    d.text((x, y), w, font=font, fill=col_)
    x += ww + space

# ---------- red rule + bottom labels ----------
d.rectangle([L, 2019, L + 140, 2028], fill=RED)
bl = oswald(30, 500)
tracked(d, L, 2072, "THE COMPLETE FIELD MANUAL", bl, GREY, 11)
tracked(d, L, 2120, "INCLUDES THE SMOKE METHOD", oswald(30, 600), WHITE, 11)

canvas.save("assets/cover-flagship.png")
print("cover", canvas.size, "title size", size, "cap", cap, "title bottom", title_bottom, "sub end y", y)
