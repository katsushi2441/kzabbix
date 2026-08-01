#!/usr/bin/env python3
"""koss.php用OGP画像(1200x630)。正規kurageさん(kurage-ecosystem-avatar.png)を右側に配置。"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
OUT = "/home/kojima/work/kzabbix/landing/assets/kzabbix-ogp.png"
AVATAR = "/home/kojima/work/kurage_web/images/kurage-ecosystem-avatar.png"

img = Image.new("RGB", (W, H), "#f4faf9")
dr = ImageDraw.Draw(img, "RGBA")

# 背景の淡いアクア
dr.ellipse([W - 560, -240, W + 240, 560], fill=(220, 244, 239, 255))
dr.ellipse([-260, H - 320, 220, H + 160], fill=(231, 247, 251, 160))

# 白カード
dr.rounded_rectangle([60, 70, W - 60, H - 70], radius=36, fill="#ffffff",
                     outline="#d9eae7", width=2)

# 正規kurageさん(上半身)を右側に
av = Image.open(AVATAR).convert("RGBA")
crop = av.crop((0, 0, av.width, int(av.height * 0.62)))  # 上半身
scale = 470 / crop.height
crop = crop.resize((int(crop.width * scale), 470))
img.paste(crop, (W - crop.width - 95, H - 70 - 470), crop)
dr = ImageDraw.Draw(img, "RGBA")

f_eyebrow = ImageFont.truetype(FONT, 26)
f_title = ImageFont.truetype(FONT, 72)
f_sub = ImageFont.truetype(FONT, 30)
f_tag = ImageFont.truetype(FONT, 24)

dr.text((120, 130), "● PRIVATE INCIDENT INTELLIGENCE", font=f_eyebrow, fill="#078fa8")
dr.text((116, 205), "Kurage", font=f_title, fill="#153f55")
dr.text((116, 295), "Zabbix", font=f_title, fill="#0799b4")
dr.text((118, 405), "Kurageさんが障害を見つけて、", font=f_sub, fill="#5f7a82")
dr.text((118, 448), "調べて、報告する。", font=f_sub, fill="#5f7a82")

# タグチップ
x = 118
for t in ("Zabbix 7.0", "Gemma4", "24/7"):
    w = dr.textlength(t, font=f_tag) + 36
    dr.rounded_rectangle([x, 508, x + w, 552], radius=22, fill="#e4f6f1", outline="#c8e9df", width=2)
    dr.text((x + 18, 517), t, font=f_tag, fill="#0b6e60")
    x += w + 14

img.save(OUT)
print("saved", OUT)
