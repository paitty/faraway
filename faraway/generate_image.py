from typing import Optional, Union
import tempfile
import os

from PIL import Image, ImageDraw, ImageFont

from faraway.data_structures import MainCard, BonusCard
from faraway.player_field import PlayerField
from faraway.load_cards import load_main_cards, load_bonus_cards

# Default visuals
DEFAULT_CARD_SIZE = 256
DEFAULT_BOTTOM_COLOR = (200, 50, 50)
DEFAULT_BG_COLOR = (240, 240, 240)


def create_image_from_maincard(
    card: MainCard,
    out_path: str = "card.png",
    card_size: int = DEFAULT_CARD_SIZE,
    font_path: Optional[str] = None,
) -> Image.Image:
    """Create and save a card image based on a `MainCard` instance.

    - Draws the card background and a bottom colored band.
    - Renders the card `id` in the top-left.
    - Renders small colored asset boxes in the top-right with counts.

    Returns the PIL Image object (also saves it to `out_path`).
    """
    BG_COLOR = DEFAULT_BG_COLOR
    BOTTOM_COLOR = DEFAULT_BOTTOM_COLOR

    img = Image.new("RGB", (card_size, card_size), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Font sizing (smaller to allow more room for icons)
    main_font_size = max(10, int(card_size * 0.14))
    small_font_size = max(8, int(card_size * 0.06))
    try:
        if font_path:
            main_font = ImageFont.truetype(font_path, main_font_size)
            small_font = ImageFont.truetype(font_path, small_font_size)
        else:
            # Try a system fallback; if it fails, fall back to default
            try:
                main_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/arial.ttf", main_font_size)
                small_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/arial.ttf", small_font_size)
            except Exception:
                main_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
    except Exception:
        main_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Use a slightly smaller font for the card id so the background icon shows through
    id_font_size = max(8, int(main_font_size * 0.65))
    try:
        if font_path:
            id_font = ImageFont.truetype(font_path, id_font_size)
        else:
            try:
                id_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/arial.ttf", id_font_size)
            except Exception:
                id_font = ImageFont.load_default()
    except Exception:
        id_font = ImageFont.load_default()

    # Draw the card id (top-left) and place a night/day icon behind it
    padding = int(card_size * 0.08)
    id_text = str(card.id)
    id_bbox = draw.textbbox((0, 0), id_text, font=id_font)
    id_tw = id_bbox[2] - id_bbox[0]
    id_th = id_bbox[3] - id_bbox[1]

    # decide which icon to show behind the id: night if card has night asset, otherwise day
    try:
        night_count = getattr(card.assets, "night", 0)
    except Exception:
        night_count = 0
    icon_name = "night" if night_count else "day"

    # icon sizing and placement (placed before drawing text so it appears behind)
    # make the icon much larger so it is visible behind the id
    ni_h = max(int(card_size * 0.28), main_font_size * 2)
    ni_w = ni_h
    gap = int(card_size * 0.02)

    # center the icon behind the id text
    text_center_x = padding + id_tw // 2
    text_center_y = padding + id_th // 2
    nx = int(text_center_x - ni_w // 2)
    ny = int(text_center_y - ni_h // 2)

    # clamp so the icon stays on-canvas
    nx = max(0, min(nx, card_size - ni_w))
    ny = max(0, min(ny, card_size - ni_h))

    try:
        icon = Image.open(f"icons/{icon_name}.png").convert("RGBA")
        icon = icon.resize((ni_w, ni_h))
        img.paste(icon, (nx, ny), icon)
    except Exception:
        # fallback: draw a subtle shape behind the id to indicate day/night
        bg_color = (50, 60, 80) if night_count else (255, 245, 200)
        draw.ellipse((nx, ny, nx + ni_w, ny + ni_h), fill=bg_color)

    # draw the id text on top of the icon (use smaller id font)
    draw.text((padding, padding), id_text, fill=(0, 0, 0), font=id_font)

    # bottom half: single color defined by the card's color asset
    colors_order = ["red", "green", "blue", "yellow"]
    color_values = {
        "red": (220, 20, 60),
        "green": (34, 139, 34),
        "blue": (30, 144, 255),
        "yellow": (255, 215, 0),
    }
    bottom_top = card_size // 2
    # choose color with highest asset count among the four colors
    counts = {name: getattr(card.assets, name, 0) for name in colors_order}
    chosen_name, chosen_count = max(counts.items(), key=lambda kv: kv[1])
    if chosen_count > 0:
        bottom_fill = color_values.get(chosen_name, DEFAULT_BOTTOM_COLOR)
    else:
        bottom_fill = DEFAULT_BOTTOM_COLOR
    draw.rectangle([(0, bottom_top), (card_size, card_size)], fill=bottom_fill)

    # Prerequisites icons: small icons aligned to the right at the top of the bottom half
    prereq_icons = ["rock", "animal", "vegetal"]
    # increase prereq icon size so assets are more visible
    small_icon_size = int(card_size * 0.10)
    small_icon_spacing = int(card_size * 0.025)
    prereqs = card.prerequisites.model_dump()
    prereq_to_draw = [(name, prereqs.get(name, 0)) for name in prereq_icons if prereqs.get(name, 0)]
    if prereq_to_draw:
        total_icons = sum(cnt for _, cnt in prereq_to_draw)
        total_width = total_icons * small_icon_size + max(0, total_icons - 1) * small_icon_spacing
        px = card_size - total_width - padding
        py = bottom_top - small_icon_size - int(card_size * 0.02)
        for name, cnt in prereq_to_draw:
            for _ in range(cnt):
                path = f"icons/{name}.png"
                try:
                    ic = Image.open(path).convert("RGBA")
                    ic = ic.resize((small_icon_size, small_icon_size))
                    img.paste(ic, (px, py), ic)
                except Exception:
                    draw.rectangle((px, py, px + small_icon_size, py + small_icon_size), fill=(160, 160, 160))
                px += small_icon_size + small_icon_spacing

    # Top-right: show rock, animal, vegetal and map icons (if present)
    top_right_icons = ["rock", "animal", "vegetal", "map"]
    # desired icon size (same for main and bonus cards) — make it bigger
    desired_icon_size = int(card_size * 0.16)
    icon_size = desired_icon_size
    icon_spacing = int(card_size * 0.04)
    icons_to_draw = []
    for name in top_right_icons:
        cnt = getattr(card.assets, name, 0)
        if cnt:
            icons_to_draw.append((name, cnt))

    total_width = len(icons_to_draw) * icon_size + max(0, len(icons_to_draw) - 1) * icon_spacing
    x = card_size - total_width - padding
    y = padding
    for name, cnt in icons_to_draw:
        path = f"icons/{name}.png"
        try:
            ic = Image.open(path).convert("RGBA")
            ic = ic.resize((icon_size, icon_size))
            img.paste(ic, (x, y), ic)
        except Exception:
            # fallback: colored box with count
            draw.rectangle((x, y, x + icon_size, y + icon_size), fill=(120, 120, 120))
            txt = str(cnt)
            bbox = draw.textbbox((0, 0), txt, font=small_font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            tx = x + (icon_size - tw) // 2
            ty = y + (icon_size - th) // 2
            draw.text((tx, ty), txt, fill=(255, 255, 255), font=small_font)
        x += icon_size + icon_spacing

    # Rewards visualization: larger icons (from assets when available) aligned to the right
    rewards = card.rewards.model_dump()
    reward_items = [(k, v) for k, v in rewards.items() if v]
    if reward_items:
        # make the rewards block larger
        reward_icon_size = int(card_size * 0.18)
        gap = int(card_size * 0.03)
        
        # Create a font for the reward values that matches the icon size
        reward_font_size = max(10, int(reward_icon_size * 0.8))
        try:
            if font_path:
                reward_font = ImageFont.truetype(font_path, reward_font_size)
            else:
                try:
                    reward_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/arial.ttf", reward_font_size)
                except Exception:
                    reward_font = ImageFont.load_default()
        except Exception:
            reward_font = ImageFont.load_default()

        # measure total width by simulating each item (icon + '=' + value)
        total_width = 0
        widths = []
        for name, val in reward_items:
            if name == "flat":
                # For flat rewards, only show the value
                val_bbox = draw.textbbox((0, 0), str(val), font=reward_font)
                val_w = val_bbox[2] - val_bbox[0]
                item_w = val_w
            else:
                # icon width
                iw = reward_icon_size
                # '=' width
                eq_bbox = draw.textbbox((0, 0), "=", font=reward_font)
                eq_w = eq_bbox[2] - eq_bbox[0]
                # value width
                val_bbox = draw.textbbox((0, 0), str(val), font=reward_font)
                val_w = val_bbox[2] - val_bbox[0]
                # larger spacing between icon and equals/value
                item_w = iw + gap + eq_w + int(card_size * 0.04) + val_w
            widths.append(item_w)
            total_width += item_w + int(card_size * 0.04)
        total_width -= int(card_size * 0.04)  # remove last spacing

        rx = card_size - padding - total_width
        
        # Vertically center rewards in the bottom half
        bottom_half_top = card_size // 2
        bottom_half_height = card_size - bottom_half_top
        ry = bottom_half_top + (bottom_half_height - reward_icon_size) // 2
        
        # draw each reward from left-to-right within the right-aligned block
        for (name, val), item_w in zip(reward_items, widths):
            if name == "flat":
                # For flat rewards, just draw the value, centered vertically
                val_bbox = draw.textbbox((0, 0), str(val), font=reward_font)
                val_h = val_bbox[3] - val_bbox[1]
                val_y = ry + (reward_icon_size - val_h) // 2
                draw.text((rx, val_y), str(val), fill=(0, 0, 0), font=reward_font)
            else:
                # draw icon if asset exists
                asset_path = f"icons/{name}.png"
                icon_top = ry
                drawn_icon = False
                try:
                    ic = Image.open(asset_path).convert("RGBA")
                    ic = ic.resize((reward_icon_size, reward_icon_size))
                    img.paste(ic, (rx, icon_top), ic)
                    drawn_icon = True
                except Exception:
                    drawn_icon = False

                if not drawn_icon:
                    # special cases
                    if name == "all_4_colors":
                        q = reward_icon_size // 2
                        colors = [(220, 20, 60), (34, 139, 34), (30, 144, 255), (255, 215, 0)]
                        for i in range(2):
                            for j in range(2):
                                cx = rx + j * q
                                cy = icon_top + i * q
                                draw.rectangle((cx, cy, cx + q, cy + q), fill=colors[i * 2 + j])
                    else:
                        draw.rectangle((rx, icon_top, rx + reward_icon_size, icon_top + reward_icon_size), fill=(120, 120, 120))
                        letter = name[0].upper()
                        lbbox = draw.textbbox((0, 0), letter, font=small_font)
                        ltw = lbbox[2] - lbbox[0]
                        lth = lbbox[3] - lbbox[1]
                        lx = rx + (reward_icon_size - ltw) // 2
                        ly = icon_top + (reward_icon_size - lth) // 2
                        draw.text((lx, ly), letter, fill=(255, 255, 255), font=small_font)

                # draw '=' and value to the right of the icon, vertically centered
                ex = rx + reward_icon_size + gap
                eq_bbox = draw.textbbox((0, 0), "=", font=reward_font)
                eq_h = eq_bbox[3] - eq_bbox[1]
                eq_w = eq_bbox[2] - eq_bbox[0]
                icon_center_y = ry + reward_icon_size // 2
                eq_y = icon_center_y - eq_h // 2
                draw.text((ex, eq_y), "=", fill=(0, 0, 0), font=reward_font)
                
                vx = ex + eq_w + gap
                val_bbox = draw.textbbox((0, 0), str(val), font=reward_font)
                val_h = val_bbox[3] - val_bbox[1]
                val_y = icon_center_y - val_h // 2
                draw.text((vx, val_y), str(val), fill=(0, 0, 0), font=reward_font)

            # advance rx by item width + small spacing
            rx += item_w + int(card_size * 0.04)

    img.save(out_path)
    return img

def create_image_from_bonuscard(
    card: BonusCard,
    out_path: str = "bonus_card.png",
    card_size: int = DEFAULT_CARD_SIZE,
    font_path: Optional[str] = None,
) -> Image.Image:
    """Create and save an image for a `BonusCard`.

    Similar to main cards but without an `id` or prerequisites. Adds a small 'B' badge.
    """
    BG_COLOR = DEFAULT_BG_COLOR

    # bonus cards are the same height but half the width
    width = max(1, card_size // 2)
    img = Image.new("RGB", (width, card_size), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Font sizing
    main_font_size = max(10, int(card_size * 0.12))
    small_font_size = max(8, int(card_size * 0.06))
    try:
        if font_path:
            main_font = ImageFont.truetype(font_path, main_font_size)
            small_font = ImageFont.truetype(font_path, small_font_size)
        else:
            try:
                main_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/arial.ttf", main_font_size)
                small_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/arial.ttf", small_font_size)
            except Exception:
                main_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
    except Exception:
        main_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # bottom half color selection (same logic as main cards)
    colors_order = ["red", "green", "blue", "yellow"]
    color_values = {
        "red": (220, 20, 60),
        "green": (34, 139, 34),
        "blue": (30, 144, 255),
        "yellow": (255, 215, 0),
    }
    bottom_top = card_size // 2
    counts = {name: getattr(card.assets, name, 0) for name in colors_order}
    chosen_name, chosen_count = max(counts.items(), key=lambda kv: kv[1])
    if chosen_count > 0:
        bottom_fill = color_values.get(chosen_name, DEFAULT_BOTTOM_COLOR)
    else:
        # no color defined -> use white background for the bottom half
        bottom_fill = (255, 255, 255)
    draw.rectangle([(0, bottom_top), (width, card_size)], fill=bottom_fill)

    padding = int(width * 0.06)

    # Top-right: draw asset icons (rock, animal, vegetal, map)
    top_right_icons = ["rock", "animal", "vegetal", "map"]
    # Use the same desired icon size as main cards; cap to available width
    desired_icon_size = int(card_size * 0.16)
    icon_size = min(desired_icon_size, max(6, width - padding * 2))
    icon_spacing = int(card_size * 0.04)
    icons_to_draw = []
    for name in top_right_icons:
        cnt = getattr(card.assets, name, 0)
        if cnt:
            icons_to_draw.append((name, cnt))

    total_width = len(icons_to_draw) * icon_size + max(0, len(icons_to_draw) - 1) * icon_spacing
    x = width - total_width - padding
    y = padding
    for name, cnt in icons_to_draw:
        path = f"icons/{name}.png"
        try:
            ic = Image.open(path).convert("RGBA")
            ic = ic.resize((icon_size, icon_size))
            img.paste(ic, (x, y), ic)
        except Exception:
            draw.rectangle((x, y, x + icon_size, y + icon_size), fill=(120, 120, 120))
            txt = str(cnt)
            bbox = draw.textbbox((0, 0), txt, font=small_font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            tx = x + (icon_size - tw) // 2
            ty = y + (icon_size - th) // 2
            draw.text((tx, ty), txt, fill=(255, 255, 255), font=small_font)
        x += icon_size + icon_spacing

    # Rewards (reuse main card logic but without icons fallback specifics)
    rewards = card.rewards.model_dump()
    reward_items = [(k, v) for k, v in rewards.items() if v]
    if reward_items:
        reward_icon_size = min(int(card_size * 0.18), max(8, width - padding * 2))
        gap = int(card_size * 0.03)
        reward_font_size = max(10, int(reward_icon_size * 0.8))
        try:
            if font_path:
                reward_font = ImageFont.truetype(font_path, reward_font_size)
            else:
                try:
                    reward_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/arial.ttf", reward_font_size)
                except Exception:
                    reward_font = ImageFont.load_default()
        except Exception:
            reward_font = ImageFont.load_default()

        total_width = 0
        widths = []
        for name, val in reward_items:
            if name == "flat":
                val_bbox = draw.textbbox((0, 0), str(val), font=reward_font)
                val_w = val_bbox[2] - val_bbox[0]
                item_w = val_w
            else:
                iw = reward_icon_size
                eq_bbox = draw.textbbox((0, 0), "=", font=reward_font)
                eq_w = eq_bbox[2] - eq_bbox[0]
                val_bbox = draw.textbbox((0, 0), str(val), font=reward_font)
                val_w = val_bbox[2] - val_bbox[0]
                item_w = iw + gap + eq_w + int(card_size * 0.04) + val_w
            widths.append(item_w)
            total_width += item_w + int(card_size * 0.04)
        total_width -= int(card_size * 0.04)

        rx = width - padding - total_width
        bottom_half_top = card_size // 2
        bottom_half_height = card_size - bottom_half_top
        ry = bottom_half_top + (bottom_half_height - reward_icon_size) // 2

        for (name, val), item_w in zip(reward_items, widths):
            if name == "flat":
                val_bbox = draw.textbbox((0, 0), str(val), font=reward_font)
                val_h = val_bbox[3] - val_bbox[1]
                val_y = ry + (reward_icon_size - val_h) // 2
                draw.text((rx, val_y), str(val), fill=(0, 0, 0), font=reward_font)
            else:
                asset_path = f"icons/{name}.png"
                icon_top = ry
                drawn_icon = False
                try:
                    ic = Image.open(asset_path).convert("RGBA")
                    ic = ic.resize((reward_icon_size, reward_icon_size))
                    img.paste(ic, (rx, icon_top), ic)
                    drawn_icon = True
                except Exception:
                    drawn_icon = False

                if not drawn_icon:
                    if name == "all_4_colors":
                        q = reward_icon_size // 2
                        colors = [(220, 20, 60), (34, 139, 34), (30, 144, 255), (255, 215, 0)]
                        for i in range(2):
                            for j in range(2):
                                cx = rx + j * q
                                cy = icon_top + i * q
                                draw.rectangle((cx, cy, cx + q, cy + q), fill=colors[i * 2 + j])
                    else:
                        draw.rectangle((rx, icon_top, rx + reward_icon_size, icon_top + reward_icon_size), fill=(120, 120, 120))
                        letter = name[0].upper()
                        lbbox = draw.textbbox((0, 0), letter, font=small_font)
                        ltw = lbbox[2] - lbbox[0]
                        lth = lbbox[3] - lbbox[1]
                        lx = rx + (reward_icon_size - ltw) // 2
                        ly = icon_top + (reward_icon_size - lth) // 2
                        draw.text((lx, ly), letter, fill=(255, 255, 255), font=small_font)

                ex = rx + reward_icon_size + gap
                eq_bbox = draw.textbbox((0, 0), "=", font=reward_font)
                eq_h = eq_bbox[3] - eq_bbox[1]
                eq_w = eq_bbox[2] - eq_bbox[0]
                icon_center_y = ry + reward_icon_size // 2
                eq_y = icon_center_y - eq_h // 2
                draw.text((ex, eq_y), "=", fill=(0, 0, 0), font=reward_font)

                vx = ex + eq_w + gap
                val_bbox = draw.textbbox((0, 0), str(val), font=reward_font)
                val_h = val_bbox[3] - val_bbox[1]
                val_y = icon_center_y - val_h // 2
                draw.text((vx, val_y), str(val), fill=(0, 0, 0), font=reward_font)

            rx += item_w + int(card_size * 0.04)

    # badge removed for bonus cards

    img.save(out_path)
    return img


def create_image_from_playerfield(
    player_field: PlayerField,
    out_path: str = "playerfield.png",
    card_size: int = DEFAULT_CARD_SIZE,
    cols: int = 5,
    spacing: int = 10,
    font_path: Optional[str] = None,
) -> Image.Image:
    """Create and save a grid image of all main cards in a PlayerField.
    
    Displays cards in a grid layout (default 4 columns).
    Returns the PIL Image object (also saves it to `out_path`).
    """
    cards = player_field.main_cards
    bonus_cards = player_field.bonus_cards

    if not cards:
        # Return empty image if no cards
        img = Image.new("RGB", (1, 1), DEFAULT_BG_COLOR)
        img.save(out_path)
        return img
    
    # Calculate grid dimensions
    rows = 1 + (len(cards) + cols - 1) // cols
    grid_width = cols * card_size + (cols - 1) * spacing
    grid_height = rows * card_size + (rows - 1) * spacing
    
    # Create grid image
    grid_img = Image.new("RGB", (grid_width, grid_height), DEFAULT_BG_COLOR)
    
    # Generate each card and place in grid
    for idx, card in enumerate(cards):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            card_img = create_image_from_maincard(card, out_path=tmp_path, card_size=card_size, font_path=font_path)
            
            # Calculate position in grid
            col = idx % cols
            row = 1 + idx // cols
            x = col * (card_size + spacing)
            y = row * (card_size + spacing)
            
            # Paste card into grid
            grid_img.paste(card_img, (x, y))
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    # Generate each card and place in grid
    for idx, card in enumerate(bonus_cards):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            card_img = create_image_from_bonuscard(card, out_path=tmp_path, card_size=card_size, font_path=font_path)
            
            # Calculate position in grid
            col = idx % (cols * 2)  # bonus cards take half width
            row = 0
            x = col * (card_size // 2 + spacing)
            y = row * (card_size + spacing)
            
            # Paste card into grid
            grid_img.paste(card_img, (x, y))
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    grid_img.save(out_path)
    return grid_img


def create_card_image(
    obj: Union[MainCard, PlayerField, BonusCard],
    out_path: str = "output.png",
    card_size: int = DEFAULT_CARD_SIZE,
    font_path: Optional[str] = None,
) -> Image.Image:
    """Create and save an image from either a MainCard or PlayerField.
    
    - If obj is a MainCard, creates a single card image
    - If obj is a PlayerField, creates a grid of all main cards
    
    Returns the PIL Image object (also saves it to `out_path`).
    """
    if isinstance(obj, MainCard):
        return create_image_from_maincard(obj, out_path=out_path, card_size=card_size, font_path=font_path)
    elif isinstance(obj, BonusCard):
        return create_image_from_bonuscard(obj, out_path=out_path, card_size=card_size, font_path=font_path)
    elif isinstance(obj, PlayerField):
        return create_image_from_playerfield(obj, out_path=out_path, card_size=card_size, font_path=font_path)
    else:
        raise TypeError(f"Expected MainCard or PlayerField, got {type(obj)}")

if __name__ == "__main__":
    import subprocess
    
    # Demo 1: Single card
    print("Generating single card image...")
    card_number = 30
    card = next(c for c in load_main_cards() if c.id == card_number)
    out_path = f"card.png"
    create_card_image(card, out_path=out_path, card_size=256)
    print(f"✓ Saved {out_path}")
    if os.path.exists(out_path):
        subprocess.run(["open", out_path])
    

    
    # Demo 2: Bonus card
    print("\nGenerating bonus card image (id 23)...")
    bonus_card_number = 7
    bonus_cards = load_bonus_cards()
    bonus_card = next((b for b in bonus_cards if getattr(b, "id", None) == bonus_card_number), None)
    if bonus_card:
        bonus_out = f"bonus_card.png"
        create_card_image(bonus_card, out_path=bonus_out, card_size=256)
        print(f"✓ Saved {bonus_out}")
        if os.path.exists(bonus_out):
            subprocess.run(["open", bonus_out])
    else:
        print("Bonus card 23 not found in data/bonus_cards.json")


    # Demo 3: Player field with multiple cards
    print("\nGenerating player field image...")
    card_ids = [20, 22, 30, 38, 13, 55, 1, 37]
    bonus_card_ids = [3, 9, 33, 44, 19]
    all_cards = load_main_cards()
    all_bonus_cards = load_bonus_cards()

    cards_dict = {card.id: card for card in all_cards}
    bonus_cards_dict = {card.id: card for card in all_bonus_cards}
    
    player_cards = [cards_dict[cid] for cid in card_ids if cid in cards_dict]
    bonus_player_cards = [bonus_cards_dict[cid] for cid in bonus_card_ids if cid in bonus_cards_dict]
    
    player_field = PlayerField(main_cards=player_cards, bonus_cards=bonus_player_cards)
    
    playerfield_path = "playerfield.png"
    create_card_image(player_field, out_path=playerfield_path, card_size=256)
    print(f"✓ Saved {playerfield_path}")
    if os.path.exists(playerfield_path):
        subprocess.run(["open", playerfield_path])
