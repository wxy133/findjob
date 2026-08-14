"""Generate the same asset set and composition roles as 鼠鼠撤离.

mifei_original.jpg remains the editable source. The derived app_icon.jpg and
logo_circle.png deliberately retain Miffy's full body, matching 鼠鼠撤离.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


ASSETS = Path(__file__).resolve().parents[1] / "assets"
SOURCE = ASSETS / "mifei_original.jpg"
APP_ICON = ASSETS / "app_icon.jpg"
HEADER_SOURCE = ASSETS / "header_banner.jpg"
HEADER_FINAL = ASSETS / "header_banner_final.png"
LOGO = ASSETS / "logo_circle.png"
ICO = ASSETS / "app.ico"
CANVAS = (1280, 110)
CREAM = (240, 245, 255)
ACCENT = (138, 184, 232)


def fit_contain(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    copy = image.copy()
    copy.thumbnail(size, Image.LANCZOS)
    return copy


def fit_cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    scale = max(size[0] / image.width, size[1] / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    x = (resized.width - size[0]) // 2
    y = (resized.height - size[1]) // 2
    return resized.crop((x, y, x + size[0], y + size[1]))


def make_app_icon(original: Image.Image) -> Image.Image:
    size = 1024
    background = fit_cover(original, (size, size)).filter(ImageFilter.GaussianBlur(28))
    background = ImageEnhance.Brightness(background).enhance(1.12)
    overlay = Image.new("RGB", (size, size), (225, 235, 250))
    background = Image.blend(background, overlay, 0.36)
    body = fit_contain(original, (760, 940))
    background.paste(body, ((size - body.width) // 2, size - body.height - 32))
    return background


def make_header_source(original: Image.Image) -> Image.Image:
    width, height = 2560, 1440
    background = fit_cover(original, (width, height)).filter(ImageFilter.GaussianBlur(34))
    background = ImageEnhance.Brightness(background).enhance(1.15)
    background = Image.blend(background, Image.new("RGB", (width, height), CREAM), 0.60)
    hero = fit_contain(original, (960, 1320))
    background.paste(hero, (width - hero.width - 105, height - hero.height - 38))
    wash = Image.new("RGBA", (width, height), (*CREAM, 0))
    wash_draw = ImageDraw.Draw(wash)
    for x in range(int(width * 0.70)):
        alpha = round(245 * (1 - x / (width * 0.70)))
        wash_draw.line((x, 0, x, height), fill=(*CREAM, alpha))
    return Image.alpha_composite(background.convert("RGBA"), wash).convert("RGB")


def make_circle(full_body: Image.Image) -> Image.Image:
    image = full_body.resize((256, 256), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).ellipse((2, 2, 253, 253), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(0.35))
    result = Image.new("RGBA", image.size, (0, 0, 0, 0))
    result.paste(image, (0, 0), mask)
    return result


def make_header_final(source: Image.Image) -> Image.Image:
    width, height = CANVAS
    scaled = source.resize((round(source.width * height / source.height), height), Image.LANCZOS)
    right_scene = scaled.crop((scaled.width - 220, 0, scaled.width, height))
    banner = Image.new("RGB", CANVAS, CREAM)
    fade = Image.new("L", right_scene.size, 255)
    fade_draw = ImageDraw.Draw(fade)
    for x in range(42):
        fade_draw.line((x, 0, x, height), fill=round(255 * x / 42))
    banner.paste(right_scene, (width - right_scene.width, 0), fade)
    ImageDraw.Draw(banner).line((0, height - 1, width, height - 1), fill=ACCENT, width=1)
    return banner


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Missing source image: {SOURCE}")
    original = Image.open(SOURCE).convert("RGB")
    app_icon = make_app_icon(original)
    header_source = make_header_source(original)

    app_icon.save(APP_ICON, "JPEG", quality=95)
    header_source.save(HEADER_SOURCE, "JPEG", quality=95)
    make_circle(app_icon).save(LOGO, "PNG")
    make_header_final(header_source).save(HEADER_FINAL, "PNG")
    make_circle(app_icon).save(ICO, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("Created app_icon.jpg, header_banner.jpg, app.ico, logo_circle.png, and header_banner_final.png.")


if __name__ == "__main__":
    main()
