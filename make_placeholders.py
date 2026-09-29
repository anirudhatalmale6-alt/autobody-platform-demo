"""
Generates the two PLACEHOLDER before/after images for the demo page.

These exist only so the comparison slider can be demonstrated before the shop's
real photo pairs arrive. They are deliberately labelled as placeholders.

The important property: both frames share identical geometry (same background,
same car position, same crop). That is exactly the constraint real before/after
pairs must satisfy for the slider to look right, so the placeholders double as
an illustration of the shooting guide.
"""
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W, H = 1600, 1000

BODY = (28, 62, 108)        # car paint
BODY_DARK = (18, 42, 76)
GLASS = (138, 162, 186)
FLOOR = (58, 58, 62)
FLOOR_LIGHT = (78, 78, 84)
WALL_TOP = (36, 38, 44)
WALL_BOTTOM = (54, 57, 66)
TYRE = (22, 22, 24)
RIM = (176, 180, 188)
CHROME = (198, 204, 212)


def _font(size):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def workshop_background(img, d):
    """Vertical gradient wall plus a floor with perspective bay lines."""
    horizon = int(H * 0.62)
    for y in range(horizon):
        t = y / horizon
        d.line(
            [(0, y), (W, y)],
            fill=tuple(
                int(WALL_TOP[i] + (WALL_BOTTOM[i] - WALL_TOP[i]) * t) for i in range(3)
            ),
        )
    for y in range(horizon, H):
        t = (y - horizon) / (H - horizon)
        d.line(
            [(0, y), (W, y)],
            fill=tuple(
                int(FLOOR[i] + (FLOOR_LIGHT[i] - FLOOR[i]) * t) for i in range(3)
            ),
        )

    # overhead strip lights, reflected faintly on the floor
    for cx in (W * 0.28, W * 0.72):
        d.rounded_rectangle(
            [cx - 210, 54, cx + 210, 86], radius=16, fill=(228, 232, 240)
        )
        d.ellipse([cx - 300, 92, cx + 300, 150], fill=(70, 74, 86))

    # bay lines converging toward a vanishing point
    for x in range(-600, W + 900, 300):
        d.line([(x, H), (int(W * 0.5 + (x - W * 0.5) * 0.18), horizon)],
               fill=(72, 74, 80), width=3)
    d.line([(0, horizon), (W, horizon)], fill=(70, 72, 80), width=4)


def car(img, damaged):
    """Side-profile car. Identical geometry in both frames."""
    d = ImageDraw.Draw(img)
    left, right = 210, 1400
    roof_y, belt_y, sill_y = 430, 560, 760

    # ground shadow
    d.ellipse([left - 40, sill_y + 40, right + 40, sill_y + 130], fill=(30, 30, 34))

    # lower body
    d.polygon(
        [(left, sill_y), (left + 34, belt_y + 6), (right - 40, belt_y + 6),
         (right, sill_y)],
        fill=BODY,
    )
    d.rectangle([left + 10, belt_y, right - 10, sill_y], fill=BODY)

    # cabin / greenhouse
    d.polygon(
        [(left + 300, belt_y), (left + 420, roof_y), (right - 430, roof_y),
         (right - 300, belt_y)],
        fill=BODY_DARK,
    )
    # windows
    d.polygon(
        [(left + 340, belt_y - 14), (left + 438, roof_y + 22), (left + 700, roof_y + 22),
         (left + 700, belt_y - 14)],
        fill=GLASS,
    )
    d.polygon(
        [(left + 726, belt_y - 14), (left + 726, roof_y + 22), (right - 452, roof_y + 22),
         (right - 330, belt_y - 14)],
        fill=GLASS,
    )

    # beltline highlight + door shutlines
    d.line([(left + 24, belt_y + 4), (right - 30, belt_y + 4)], fill=CHROME, width=5)
    for x in (left + 300, left + 712, right - 300):
        d.line([(x, belt_y + 10), (x, sill_y - 16)], fill=BODY_DARK, width=4)

    # handles
    for x in (left + 500, left + 900):
        d.rounded_rectangle([x, belt_y + 54, x + 84, belt_y + 76], radius=10,
                            fill=CHROME)

    # lights
    d.rounded_rectangle([right - 96, belt_y + 40, right - 12, belt_y + 104],
                        radius=14, fill=(242, 238, 214))
    d.rounded_rectangle([left + 12, belt_y + 44, left + 86, belt_y + 104],
                        radius=14, fill=(178, 38, 38))

    # wheels
    for cx in (left + 250, right - 250):
        d.ellipse([cx - 112, sill_y - 112, cx + 112, sill_y + 112], fill=TYRE)
        d.ellipse([cx - 58, sill_y - 58, cx + 58, sill_y + 58], fill=RIM)
        d.ellipse([cx - 18, sill_y - 18, cx + 18, sill_y + 18], fill=(120, 124, 132))

    if damaged:
        # Damage is painted on its own layer and then masked to the flank, so a
        # dent or scratch can never bleed onto a wheel or the background. The
        # mask is the door/quarter area between the beltline and the sill.
        dmg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dmg)
        panel = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(panel)
        md.rectangle([left + 20, belt_y + 8, right - 20, sill_y - 8], fill=255)
        # punch the wheel arches back out of the panel area
        for cx in (left + 250, right - 250):
            md.ellipse([cx - 124, sill_y - 124, cx + 124, sill_y + 124], fill=0)

        # crumpled front quarter panel
        dd.polygon(
            [(right - 300, belt_y + 6), (right - 120, belt_y + 20),
             (right - 60, belt_y + 150), (right - 210, sill_y - 20),
             (right - 320, sill_y - 60)],
            fill=(86, 74, 62),
        )
        dd.polygon(
            [(right - 250, belt_y + 60), (right - 140, belt_y + 96),
             (right - 190, belt_y + 210), (right - 280, belt_y + 150)],
            fill=(126, 112, 92),
        )
        # scraped primer showing through
        for i in range(9):
            y = belt_y + 40 + i * 26
            dd.line([(right - 330 + i * 6, y), (right - 110 - i * 4, y + 10)],
                    fill=(158, 146, 126), width=5)
        # door dent + deep scratch running back along the flank
        dd.ellipse([left + 600, belt_y + 90, left + 800, belt_y + 200],
                   fill=(20, 46, 82))
        dd.line([(left + 420, belt_y + 150), (left + 980, belt_y + 176)],
                fill=(196, 190, 176), width=7)

        # Only the pixels that are BOTH painted damage and inside the panel
        # survive - intersecting the layer's own alpha with the panel area.
        img.paste(dmg, (0, 0), ImageChops.multiply(dmg.split()[3], panel))

        # cracked headlight - drawn after the paste, directly on the lens
        d.line([(right - 92, belt_y + 46), (right - 20, belt_y + 100)],
               fill=(150, 146, 124), width=6)
        d.line([(right - 30, belt_y + 46), (right - 84, belt_y + 100)],
               fill=(150, 146, 124), width=6)
    else:
        # Fresh clearcoat: a soft specular sweep high on the flank. Kept
        # translucent and above the handle line so it reads as a reflection
        # rather than hiding the trim underneath it.
        sweep = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sweep).polygon(
            [(left + 120, belt_y + 20), (right - 160, belt_y + 12),
             (right - 190, belt_y + 46), (left + 150, belt_y + 56)],
            fill=(120, 168, 224, 105),
        )
        img.paste(
            Image.alpha_composite(img.convert("RGBA"), sweep).convert("RGB"),
            (0, 0),
        )


def label(img, text, accent):
    """Footer strip only.

    No burnt-in BEFORE/AFTER badge: the page draws its own captions over the
    frames, and a second label baked into the pixels collides with them.
    """
    d = ImageDraw.Draw(img, "RGBA")
    small = _font(24)
    d.rectangle([0, H - 62, W, H], fill=(0, 0, 0, 190))
    d.text((24, H - 46), "PLACEHOLDER IMAGE - replace with the shop's own photo pair",
           font=small, fill=(214, 214, 220))


def build(damaged, text, accent, out):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    workshop_background(img, d)
    car(img, damaged)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    label(img, text, accent)
    img.save(out, "JPEG", quality=86, optimize=True)
    print("wrote", out)


if __name__ == "__main__":
    base = "/var/lib/freelancer/projects/40739456/demo/images/"
    build(True, "BEFORE", (176, 44, 44), base + "demo-before.jpg")
    build(False, "AFTER", (28, 132, 84), base + "demo-after.jpg")
