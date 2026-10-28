"""Render the covers as standing 3D paperbacks with a visible spine, lighting and a contact shadow."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import numpy as np

BG = (15, 19, 22)
RED = (215, 38, 30)
WHITE = (244, 242, 238)

def coeffs(dst, src):
    """PIL PERSPECTIVE coefficients mapping output points dst -> input points src."""
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()

def warp(img, quad, size):
    w, h = img.size
    return img.transform(size, Image.PERSPECTIVE, coeffs(quad, [(0, 0), (w, 0), (w, h), (0, h)]),
                         Image.BICUBIC, fillcolor=(0, 0, 0, 0))

def shade(img, left, right, top=1.0, bottom=1.0):
    """Multiply by a horizontal (and slight vertical) light falloff."""
    a = np.asarray(img).astype(np.float32)
    h, w = a.shape[:2]
    gx = np.linspace(left, right, w)[None, :]
    gy = np.linspace(top, bottom, h)[:, None]
    a[..., :3] *= (gx * gy)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype("uint8"))

def spine_texture(h, w, title_main, title_red, sub):
    sp = Image.new("RGBA", (h, w), BG + (255,))          # drawn sideways, rotated later
    d = ImageDraw.Draw(sp)
    f = ImageFont.truetype("fonts/BebasNeue-Regular.ttf", int(w * 0.62))
    fs = ImageFont.truetype("fonts/BebasNeue-Regular.ttf", int(w * 0.36))
    x = int(h * 0.07)
    y = (w - (f.getbbox("H")[3] - f.getbbox("H")[1])) // 2 - f.getbbox("H")[1]
    for part, col in title_main:
        d.text((x, y), part, font=f, fill=col + (255,))
        x += d.textlength(part, font=f) + d.textlength(" ", font=f)
    ys = (w - (fs.getbbox("H")[3] - fs.getbbox("H")[1])) // 2 - fs.getbbox("H")[1]
    d.text((h - d.textlength(sub, font=fs) - int(h * 0.06), ys), sub, font=fs, fill=(150, 152, 154, 255))
    return sp.rotate(-90, expand=True)

def book(cover, spine, H=1500, angle=36, depth_ratio=0.072, scale=2):
    """Return an RGBA image of a standing paperback, spine on the left."""
    H *= scale
    cw, ch = cover.size
    true_w = H * cw / ch
    rad = np.radians(angle)
    fw = true_w * np.cos(rad)                 # projected front width
    sw = true_w * depth_ratio * np.sin(rad) * 2.2   # projected spine width (slightly exaggerated for legibility)
    drop = H * 0.032                          # perspective: far edge shorter
    pad = int(H * 0.16)
    W_ = int(sw + fw + pad * 2); H_ = int(H + pad * 2.2)
    x0 = pad + sw; y0 = pad * 0.6
    front_q = [(x0, y0), (x0 + fw, y0 + drop), (x0 + fw, y0 + H - drop), (x0, y0 + H)]
    spine_q = [(x0 - sw, y0 + drop * 0.35), (x0, y0), (x0, y0 + H), (x0 - sw, y0 + H - drop * 0.35)]

    canvas = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))

    # contact shadow on the floor
    sh = Image.new("L", (W_, H_), 0)
    sd = ImageDraw.Draw(sh)
    sd.ellipse([x0 - sw * 1.2, y0 + H - H * 0.02, x0 + fw * 1.12, y0 + H + H * 0.06], fill=200)
    sh = sh.filter(ImageFilter.GaussianBlur(H * 0.022))
    shadow = Image.new("RGBA", (W_, H_), (0, 0, 0, 255)); shadow.putalpha(sh)
    canvas = Image.alpha_composite(canvas, shadow)

    # front: light from the left, falling off to the right; hinge groove near the spine
    f = cover.convert("RGBA")
    f = shade(f, 1.05, 0.80, 1.02, 0.94)
    fd = ImageDraw.Draw(f)
    hx = int(cw * 0.028)
    fd.rectangle([hx, 0, hx + int(cw * 0.006), ch], fill=(0, 0, 0, 90))
    fd.rectangle([hx + int(cw * 0.006), 0, hx + int(cw * 0.011), ch], fill=(255, 255, 255, 28))
    front = warp(f, front_q, (W_, H_))
    # a soft sheen across the front
    sheen = Image.new("L", (W_, H_), 0)
    ImageDraw.Draw(sheen).polygon([(x0 + fw * 0.08, y0), (x0 + fw * 0.42, y0), (x0 + fw * 0.10, y0 + H), (x0 - fw * 0.22, y0 + H)], fill=26)
    sheen = sheen.filter(ImageFilter.GaussianBlur(H * 0.05))
    mask = front.split()[3]
    sheen = ImageChops.multiply(sheen, mask)
    white = Image.new("RGBA", (W_, H_), (255, 255, 255, 0)); white.putalpha(sheen)

    # spine: further from the light
    s = shade(spine.convert("RGBA"), 0.62, 0.78)
    sp = warp(s, spine_q, (W_, H_))

    canvas = Image.alpha_composite(canvas, sp)
    canvas = Image.alpha_composite(canvas, front)
    canvas = Image.alpha_composite(canvas, white)

    # rim light along the top and far edge, where a lamp behind would catch it
    rim = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rim)
    rd.line([front_q[0], front_q[1]], fill=(255, 250, 240, 120), width=max(2, int(scale * 1.5)))
    rd.line([front_q[1], front_q[2]], fill=(255, 250, 240, 70), width=max(2, int(scale * 1.5)))
    rd.line([spine_q[0], spine_q[1]], fill=(255, 250, 240, 60), width=max(1, int(scale)))
    canvas = Image.alpha_composite(canvas, rim)
    return canvas.resize((W_ // scale, H_ // scale), Image.LANCZOS)

flag_cover = Image.open("assets/cover-flagship.png").convert("RGB")
sm_cover = Image.open("assets/smoke-method-cover.png").convert("RGB").crop((48, 0, 1608, 2339))

flag_spine = spine_texture(2339, 175, [("MAKE ANY", WHITE), ("BULLSHIT", RED), ("SOUND BRILLIANT", WHITE)], None, "CASE FILE № 002")
sm_spine = spine_texture(2339, 120, [("THE", WHITE), ("SMOKE", RED), ("METHOD", WHITE)], None, "CASE FILE № 001")

flag = book(flag_cover, flag_spine, H=1500, angle=34, depth_ratio=0.075)
flag.save("assets/book-flagship.png")
print("flagship mockup", flag.size)

sm = book(sm_cover, sm_spine, H=1500, angle=34, depth_ratio=0.045)
sm.save("assets/book-smoke.png")
print("smoke mockup", sm.size)

# bundle: the field guide stands in front of the manual, lower and to the right
k = 0.70
sm_small = sm.resize((int(sm.width * k), int(sm.height * k)), Image.LANCZOS)
BW = int(flag.width + sm_small.width * 0.55); BH = flag.height
bundle = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
bundle.alpha_composite(flag, (0, 0))
bundle.alpha_composite(sm_small, (BW - sm_small.width, BH - sm_small.height - int(BH * 0.005)))
bundle.save("assets/book-bundle.png")
print("bundle", bundle.size)
