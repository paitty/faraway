from PIL import Image, ImageDraw
import os

# Ensure icons directory exists
os.makedirs("icons", exist_ok=True)

ICON_SIZE = 56

def create_day():
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    center = ICON_SIZE // 2
    radius = 14
    import math
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x1 = center + int(20 * math.cos(rad))
        y1 = center + int(20 * math.sin(rad))
        x2 = center + int(26 * math.cos(rad))
        y2 = center + int(26 * math.sin(rad))
        draw.line((x1, y1, x2, y2), fill=(255, 200, 0), width=2)
    draw.ellipse((center - radius, center - radius, center + radius, center + radius), fill=(255, 215, 0))
    img.save("icons/day.png")

def create_night():
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    center = ICON_SIZE // 2
    radius = 16
    draw.ellipse((center - radius, center - radius, center + radius, center + radius), fill=(255, 250, 200))
    draw.ellipse((center - 8, center - 6, center - 4, center - 2), fill=(200, 195, 160))
    draw.ellipse((center + 4, center + 2, center + 8, center + 6), fill=(200, 195, 160))
    draw.ellipse((center - 2, center + 8, center + 2, center + 12), fill=(200, 195, 160))
    img.save("icons/night.png")

def create_rock():
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    points = [(20, 8), (32, 12), (38, 24), (36, 40), (24, 44), (12, 38), (10, 22)]
    draw.polygon(points, fill=(80, 80, 90))
    draw.line((20, 8, 36, 40), fill=(100, 100, 110), width=1)
    draw.line((32, 12, 24, 44), fill=(100, 100, 110), width=1)
    draw.line((38, 24, 12, 38), fill=(60, 60, 70), width=1)
    draw.polygon([(20, 8), (26, 18), (22, 20)], fill=(120, 120, 130))
    img.save("icons/rock.png")

def create_animal():
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    center = ICON_SIZE // 2
    draw.ellipse((center - 10, center - 2, center + 10, center + 14), fill=(180, 140, 100))
    draw.polygon([(center - 8, center - 2), (center - 6, center - 12), (center - 4, center)], fill=(180, 140, 100))
    draw.polygon([(center + 8, center - 2), (center + 6, center - 12), (center + 4, center)], fill=(180, 140, 100))
    draw.polygon([(center - 7, center - 4), (center - 6, center - 10), (center - 5, center - 2)], fill=(200, 160, 120))
    draw.polygon([(center + 7, center - 4), (center + 6, center - 10), (center + 5, center - 2)], fill=(200, 160, 120))
    draw.ellipse((center - 5, center + 2, center - 2, center + 5), fill=(0, 0, 0))
    draw.ellipse((center + 2, center + 2, center + 5, center + 5), fill=(0, 0, 0))
    draw.ellipse((center - 4, center + 8, center + 4, center + 12), fill=(200, 160, 120))
    draw.line((center - 8, center - 4, center - 10, center - 18), fill=(120, 100, 80), width=2)
    draw.line((center + 8, center - 4, center + 10, center - 18), fill=(120, 100, 80), width=2)
    img.save("icons/animal.png")

def create_vegetal():
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    center = ICON_SIZE // 2
    pineapple_points = [
        (center, center - 14),
        (center + 10, center - 8),
        (center + 10, center + 6),
        (center, center + 12),
        (center - 10, center + 6),
        (center - 10, center - 8),
    ]
    draw.polygon(pineapple_points, fill=(200, 140, 40))
    for i in range(-2, 3):
        for j in range(-2, 3):
            x = center + i * 4
            y = center + j * 4
            draw.rectangle((x - 1, y - 1, x + 1, y + 1), fill=(160, 110, 20))
    leaf_points = [
        (center - 3, center - 14),
        (center - 5, center - 22),
        (center - 2, center - 18),
        (center, center - 20),
        (center + 2, center - 18),
        (center + 5, center - 22),
        (center + 3, center - 14),
    ]
    draw.polygon(leaf_points, fill=(100, 180, 60))
    img.save("icons/vegetal.png")

def create_color_icon(name, color):
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    center = ICON_SIZE // 2
    radius = 18
    draw.ellipse((center - radius, center - radius, center + radius, center + radius), fill=color, outline=(0, 0, 0), width=2)
    img.save(f"icons/{name}.png")

def create_all_4_colors():
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    half = ICON_SIZE // 2
    colors = [(220, 20, 60), (34, 139, 34), (30, 144, 255), (255, 215, 0)]
    for i in range(2):
        for j in range(2):
            x1 = i * half
            y1 = j * half
            x2 = x1 + half
            y2 = y1 + half
            draw.rectangle((x1, y1, x2, y2), fill=colors[i * 2 + j])
    img.save("icons/all_4_colors.png")

def create_map():
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    center = ICON_SIZE // 2
    draw.rectangle((6, 6, ICON_SIZE - 6, ICON_SIZE - 6), fill=(220, 200, 160))
    draw.ellipse((6, 2, ICON_SIZE - 6, 10), fill=(200, 180, 140))
    draw.ellipse((6, ICON_SIZE - 10, ICON_SIZE - 6, ICON_SIZE - 2), fill=(200, 180, 140))
    land_color = (100, 180, 60)
    water_color = (80, 140, 180)
    draw.rectangle((8, 8, ICON_SIZE - 8, ICON_SIZE - 8), fill=water_color)
    draw.polygon([(12, 18), (22, 16), (24, 26), (18, 30), (10, 28)], fill=land_color)
    draw.polygon([(30, 12), (40, 14), (42, 28), (36, 32), (28, 26)], fill=land_color)
    for i in range(2, ICON_SIZE - 6, 8):
        draw.line((i, 8, i, ICON_SIZE - 8), fill=(200, 180, 160), width=1)
        draw.line((8, i, ICON_SIZE - 8, i), fill=(200, 180, 160), width=1)
    compass_x = ICON_SIZE - 14
    compass_y = 12
    draw.polygon([
        (compass_x, compass_y - 3),
        (compass_x + 2, compass_y),
        (compass_x, compass_y + 3),
        (compass_x - 2, compass_y)
    ], fill=(220, 100, 60))
    img.save("icons/map.png")

if __name__ == "__main__":
    os.makedirs("icons", exist_ok=True)
    create_day()
    create_night()
    create_rock()
    create_animal()
    create_vegetal()
    create_color_icon("blue", (30, 144, 255))
    create_color_icon("red", (220, 20, 60))
    create_color_icon("yellow", (255, 215, 0))
    create_color_icon("green", (34, 139, 34))
    create_all_4_colors()
    create_map()
    print("Icons generated into icons/")
