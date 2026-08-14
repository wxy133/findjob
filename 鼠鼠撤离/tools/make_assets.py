"""一次性生成ICO和GUI所需的裁切版仓鼠PNG，运行一次即可，产物写入assets目录"""
import os
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
os.makedirs(ASSETS, exist_ok=True)

SRC_ICON = os.path.join(ASSETS, "app_icon.jpg")
SRC_BANNER = os.path.join(ASSETS, "header_banner.jpg")

ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def square_crop(img: Image.Image) -> Image.Image:
    w, h = img.size
    s = min(w, h)
    left = (w - s) // 2
    top = (h - s) // 2
    return img.crop((left, top, left + s, top + s))


def mask_circle(img: Image.Image) -> Image.Image:
    img = img.convert("RGBA")
    s = img.size[0]
    mask = Image.new("L", (s, s), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((2, 2, s - 2, s - 2), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=0.4))
    out = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def build_ico():
    assert os.path.exists(SRC_ICON), f"缺少源图片: {SRC_ICON}"
    src = Image.open(SRC_ICON).convert("RGBA")
    src = square_crop(src)
    images = []
    for size in ICO_SIZES:
        resized = src.resize(size, Image.LANCZOS)
        images.append(resized)
    out_path = os.path.join(ASSETS, "app.ico")
    images[0].save(
        out_path,
        format="ICO",
        sizes=[im.size for im in images],
        append_images=images[1:],
    )
    print(f"✅ 生成 ICO: {out_path}  尺寸: {ICO_SIZES}")


def build_logo_small():
    """GUI界面里标题左侧、各卡片左上角使用的圆形仓鼠头像（128x128 PNG，透明背景）"""
    src = Image.open(SRC_ICON).convert("RGBA")
    src = square_crop(src).resize((128, 128), Image.LANCZOS)
    out = mask_circle(src)
    out_path = os.path.join(ASSETS, "logo_circle.png")
    out.save(out_path, "PNG")
    print(f"✅ 生成圆形LOGO: {out_path}")


def build_banner_thumb(target_height=110):
    """GUI顶部横幅。取右侧仓鼠主体，左侧留柔和渐隐的奶油色给标题叠加"""
    assert os.path.exists(SRC_BANNER), f"缺少横幅源图: {SRC_BANNER}"
    src = Image.open(SRC_BANNER).convert("RGB")
    w, h = src.size
    new_w = int(w * target_height / h)
    src = src.resize((new_w, target_height), Image.LANCZOS)

    banner_w = 1280
    if new_w < banner_w:
        canvas = Image.new("RGB", (banner_w, target_height), (251, 243, 231))
        canvas.paste(src, (banner_w - new_w, 0))
        src = canvas
    else:
        # 从右侧裁出仓鼠主体
        src = src.crop((new_w - banner_w, 0, new_w, target_height))

    # 左侧添加奶油色渐隐遮罩，避免标题字糊在门上
    mask = Image.new("L", (banner_w, target_height), 0)
    fade_stop = int(banner_w * 0.55)
    for x in range(fade_stop):
        alpha = int(255 * (1 - x / fade_stop))
        for y in range(target_height):
            mask.putpixel((x, y), alpha)
    # 把遮罩作用到奶油色上
    cream = Image.new("RGB", (banner_w, target_height), (251, 243, 231))
    src = Image.composite(cream, src, mask)

    # 底部加1px橙色分隔线
    draw = ImageDraw.Draw(src)
    draw.line([(0, target_height - 1), (banner_w, target_height - 1)], fill=(210, 125, 60), width=1)

    out_path = os.path.join(ASSETS, "header_banner_final.png")
    src.save(out_path, "PNG")
    print(f"✅ 生成GUI横幅: {out_path} ({src.size[0]}x{src.size[1]})")


if __name__ == "__main__":
    build_ico()
    build_logo_small()
    build_banner_thumb()
    print("\n全部素材生成完毕 ✨")
