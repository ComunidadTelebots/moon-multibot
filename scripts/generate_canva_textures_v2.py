"""
Generador Maestro de Texturas Pixel-Perfect basado en las fotos reales de Canva.
Extrae la diagramación exacta de cada diapositiva:
- page-077: Manifiesto de 2 columnas + Sello Incompleto + Precinto Alterado
- page-080: Tablet táctil con lectura Temp 112°C, Presión 1.2 bar, P0562
- page-093: Cartel ZONA DE PROTECCIÓN / FAUNA SILVESTRE con silueta de ciervo
- page-023: Cartel de TRANSPORTE ESPECIAL reflectante
- page-079: Testigo luminoso Check Engine
"""

import os
import math
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = r"C:\Users\adria\OneDrive\Documentos\Visual Studio\Telegram\DBTeamV2\Todosobrealltech\.moon-insideads-panel\web\generated-textures\canva-assets"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_font(name, size):
    font_path = os.path.join(r"C:\Windows\Fonts", name)
    if os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except:
            pass
    return ImageFont.load_default()

def generate_box07a_manifest():
    w, h = 1024, 1024
    img = Image.new("RGBA", (w, h), (228, 218, 198, 255))
    draw = ImageDraw.Draw(img)

    # Fondo envejecido con gradiente sutil
    for y in range(h):
        shade = int(8 * math.sin(y / h * math.pi))
        draw.line([(0, y), (w, y)], fill=(228 - shade, 218 - shade, 198 - shade, 255))

    # Borde exterior de documento
    draw.rectangle([(20, 20), (w - 20, h - 20)], outline=(140, 130, 115, 255), width=3)

    f_title = get_font("segoeuib.ttf", 32)
    f_lbl = get_font("segoeuib.ttf", 20)
    f_val = get_font("arialbd.ttf", 21)
    f_mono = get_font("consolab.ttf", 20)
    f_note = get_font("segoeui.ttf", 20)
    f_stamp = get_font("impact.ttf", 76)

    # Cabecera
    draw.rectangle([(36, 36), (w - 180, 100)], fill=(205, 195, 175, 255), outline=(130, 120, 105, 255), width=2)
    draw.text((50, 48), "MANIFIESTO DE TRANSPORTE", font=f_title, fill=(35, 30, 25, 255))

    # Tabla en 2 columnas exactas a Canva page-077
    table_x1, table_y1 = 36, 115
    table_x2, table_y2 = w - 180, 620
    split_x = 540  # Separador entre columna izquierda y derecha

    draw.rectangle([(table_x1, table_y1), (table_x2, table_y2)], outline=(120, 110, 95, 255), width=3)
    draw.line([(split_x, table_y1), (split_x, table_y2)], fill=(120, 110, 95, 255), width=2)

    # Filas de la Columna Izquierda
    left_rows = [
        (115, "Remitente:", "Rutas del Continente"),
        (215, "Destino:", "Puerto de Inírida"),
        (315, "Contenido declarado:", "Equipos y documentos"),
        (415, "Peso declarado:", "32,4 kg       Bultos: 1/1"),
        (515, "Observaciones:", "---")
    ]
    for y_pos, label, val in left_rows:
        draw.line([(table_x1, y_pos), (split_x, y_pos)], fill=(150, 140, 125, 255), width=1)
        draw.text((50, y_pos + 12), label, font=f_lbl, fill=(85, 75, 65, 255))
        draw.text((50, y_pos + 48), val, font=f_val, fill=(25, 20, 15, 255))

    # Filas de la Columna Derecha
    right_rows = [
        (115, "Fecha:", "18/04"),
        (215, "Guía:", "RC-8841"),
        (315, "Transportista:", "---"),
        (415, "Conductor:", "---"),
        (515, "Firma:", "---")
    ]
    for y_pos, label, val in right_rows:
        draw.line([(split_x, y_pos), (table_x2, y_pos)], fill=(150, 140, 125, 255), width=1)
        draw.text((split_x + 20, y_pos + 12), label, font=f_lbl, fill=(85, 75, 65, 255))
        draw.text((split_x + 20, y_pos + 48), val, font=f_mono, fill=(25, 20, 15, 255))

    # Nota de Aurora en la parte inferior
    draw.rectangle([(36, 650), (w - 180, 840)], fill=(238, 230, 212, 255), outline=(170, 160, 140, 255), width=2)
    draw.text((55, 665), "NOTA DE AURORA:", font=f_lbl, fill=(100, 75, 55, 255))
    draw.text((55, 705), '"Si estás leyendo esto, es porque algo salió del camino.\nConfía en tu criterio. No todas las respuestas vienen en los papeles."', font=f_note, fill=(45, 35, 25, 255))
    draw.text((560, 790), "- Aurora", font=get_font("segoeuib.ttf", 24), fill=(35, 25, 15, 255))

    # Sello rojo INCOMPLETO
    stamp_w, stamp_h = 440, 130
    stamp = Image.new("RGBA", (stamp_w, stamp_h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(stamp)
    s_draw.rectangle([(6, 6), (stamp_w - 6, stamp_h - 6)], outline=(205, 35, 25, 235), width=8)
    s_draw.rectangle([(16, 16), (stamp_w - 16, stamp_h - 16)], outline=(205, 35, 25, 160), width=2)
    s_draw.text((stamp_w // 2, stamp_h // 2), "INCOMPLETO", font=f_stamp, fill=(205, 35, 25, 235), anchor="mm")

    rot_stamp = stamp.rotate(-14, expand=True, resample=Image.BICUBIC)
    img.paste(rot_stamp, (420, 410), rot_stamp)

    # Cinta lateral PRECINTO ALTERADO en el lateral derecho
    tape_w = 140
    tape_x = w - tape_w
    draw.rectangle([(tape_x, 0), (w, h)], fill=(245, 80, 35, 255))
    draw.rectangle([(tape_x + 6, 6), (w - 6, h - 6)], outline=(160, 30, 10, 255), width=4)

    tape_txt = Image.new("RGBA", (h, tape_w), (0, 0, 0, 0))
    t_draw = ImageDraw.Draw(tape_txt)
    t_draw.text((h // 2, tape_w // 2), "PRECINTO ALTERADO  ·  07-A", font=get_font("impact.ttf", 46), fill=(25, 5, 0, 255), anchor="mm")
    rot_tape = tape_txt.rotate(90, expand=True)
    img.paste(rot_tape, (tape_x, 0), rot_tape)

    path = os.path.join(OUTPUT_DIR, "box07a_manifest.png")
    img.save(path, "PNG")
    print(f"Master Render: {path}")

def generate_diagnostic_tablet():
    w, h = 1024, 768
    # Fondo idéntico a panel 02 de page-080
    img = Image.new("RGBA", (w, h), (11, 26, 38, 255))
    draw = ImageDraw.Draw(img)

    # Marco tablet de goma rugerizada con empuñaduras laterales
    draw.rectangle([(0, 0), (w, h)], outline=(20, 30, 40, 255), width=28)
    draw.rectangle([(28, 28), (w - 28, h - 28)], outline=(23, 67, 88, 255), width=6)

    f_title = get_font("segoeuib.ttf", 36)
    f_lbl = get_font("segoeuib.ttf", 24)
    f_status_red = get_font("segoeuib.ttf", 26)
    f_val_red = get_font("impact.ttf", 64)
    f_rec = get_font("segoeui.ttf", 22)

    # Título central
    draw.text((w // 2, 70), "DIAGNÓSTICO INICIAL", font=f_title, fill=(85, 234, 217, 255), anchor="mm")

    # Contenedor central azul marino con bordes redondeados
    box_x1, box_y1 = 80, 120
    box_x2, box_y2 = w - 80, 640
    draw.rounded_rectangle([(box_x1, box_y1), (box_x2, box_y2)], radius=18, fill=(8, 20, 30, 255), outline=(23, 67, 88, 255), width=3)

    # Fila 1: Temperatura
    row1_y = 160
    # Icono termómetro
    draw.rectangle([(120, row1_y), (135, row1_y + 45)], fill=(255, 60, 45, 255))
    draw.ellipse([(112, row1_y + 40), (143, row1_y + 70)], fill=(255, 60, 45, 255))
    draw.text((180, row1_y + 8), "TEMPERATURA", font=f_lbl, fill=(180, 210, 225, 255))
    draw.text((180, row1_y + 42), "ALTA", font=f_status_red, fill=(255, 60, 45, 255))
    draw.text((w - 140, row1_y + 35), "112 °C", font=f_val_red, fill=(255, 75, 50, 255), anchor="rm")
    draw.line([(100, row1_y + 100), (w - 100, row1_y + 100)], fill=(20, 48, 65, 255), width=2)

    # Fila 2: Presión de Aceite
    row2_y = 290
    # Icono aceitera
    draw.polygon([(110, row2_y + 35), (145, row2_y + 20), (145, row2_y + 60), (110, row2_y + 60)], fill=(255, 170, 45, 255))
    draw.text((180, row2_y + 8), "PRESIÓN DE ACEITE", font=f_lbl, fill=(180, 210, 225, 255))
    draw.text((180, row2_y + 42), "BAJA", font=f_status_red, fill=(255, 170, 45, 255))
    draw.text((w - 140, row2_y + 35), "1.2 bar", font=f_val_red, fill=(255, 170, 45, 255), anchor="rm")
    draw.line([(100, row2_y + 100), (w - 100, row2_y + 100)], fill=(20, 48, 65, 255), width=2)

    # Fila 3: Falla Eléctrica
    row3_y = 420
    # Icono batería
    draw.rectangle([(110, row3_y + 15), (145, row3_y + 55)], outline=(255, 60, 45, 255), width=3)
    draw.rectangle([(118, row3_y + 8), (124, row3_y + 15)], fill=(255, 60, 45, 255))
    draw.rectangle([(131, row3_y + 8), (137, row3_y + 15)], fill=(255, 60, 45, 255))
    draw.text((180, row3_y + 8), "FALLA ELÉCTRICA", font=f_lbl, fill=(180, 210, 225, 255))
    draw.text((180, row3_y + 42), "DETECTADA", font=f_status_red, fill=(255, 60, 45, 255))
    draw.text((w - 140, row3_y + 15), "CÓDIGO", font=get_font("segoeuib.ttf", 20), fill=(255, 60, 45, 255), anchor="rm")
    draw.text((w - 140, row3_y + 52), "P0562", font=get_font("impact.ttf", 36), fill=(85, 234, 217, 255), anchor="rm")

    # Pie: Recomendación
    draw.text((w // 2, 595), "Recomendación: Inspección manual", font=f_rec, fill=(140, 185, 205, 255), anchor="mm")

    path = os.path.join(OUTPUT_DIR, "diagnostic_tablet.png")
    img.save(path, "PNG")
    print(f"Master Render: {path}")

def generate_wildlife_sign():
    w, h = 512, 512
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fondo verde bosque idéntico a Canva page-093
    draw.rounded_rectangle([(12, 12), (w - 12, h - 12)], radius=28, fill=(25, 63, 44, 255), outline=(255, 255, 255, 255), width=10)
    draw.rounded_rectangle([(24, 24), (w - 24, h - 24)], radius=20, outline=(15, 42, 28, 255), width=3)

    f_top = get_font("impact.ttf", 46)
    f_bot = get_font("impact.ttf", 38)

    draw.text((w // 2, 68), "ZONA DE", font=f_top, fill=(255, 255, 255, 255), anchor="mm")
    draw.text((w // 2, 118), "PROTECCIÓN", font=f_top, fill=(255, 255, 255, 255), anchor="mm")

    # Silueta de Ciervo Rojo perfil caminando de alta fidelidad
    stag_body = [
        (185, 255), (170, 262), (185, 275), (210, 285), (225, 310),
        (220, 340), (215, 360),
        # Pata delantera 1
        (210, 420), (222, 420), (232, 365),
        # Pata delantera 2
        (242, 415), (254, 415), (252, 360),
        # Vientre
        (275, 355), (305, 350),
        # Pata trasera 1
        (312, 420), (324, 420), (332, 355),
        # Pata trasera 2
        (340, 415), (352, 415), (356, 340),
        # Grupa y cola
        (365, 320), (375, 305), (365, 298),
        # Lomo y cruz
        (315, 290), (255, 285),
        # Cuello y nuca
        (235, 245), (225, 230),
        # Oreja
        (238, 210), (228, 225),
        # Frente
        (205, 245)
    ]
    draw.polygon(stag_body, fill=(255, 255, 255, 255))

    # Cornamenta majestuosa ramificada
    # Haz delantero
    draw.line([(212, 238), (195, 175)], fill=(255, 255, 255, 255), width=5)
    draw.line([(195, 175), (170, 145)], fill=(255, 255, 255, 255), width=4)
    draw.line([(205, 210), (180, 200)], fill=(255, 255, 255, 255), width=3)
    draw.line([(195, 185), (175, 175)], fill=(255, 255, 255, 255), width=3)
    draw.line([(180, 160), (165, 155)], fill=(255, 255, 255, 255), width=3)

    # Haz trasero
    draw.line([(220, 235), (245, 175)], fill=(255, 255, 255, 255), width=5)
    draw.line([(245, 175), (275, 145)], fill=(255, 255, 255, 255), width=4)
    draw.line([(235, 205), (260, 195)], fill=(255, 255, 255, 255), width=3)
    draw.line([(255, 175), (275, 170)], fill=(255, 255, 255, 255), width=3)
    draw.line([(265, 158), (285, 155)], fill=(255, 255, 255, 255), width=3)

    draw.text((w // 2, 460), "FAUNA SILVESTRE", font=f_bot, fill=(255, 255, 255, 255), anchor="mm")

    path = os.path.join(OUTPUT_DIR, "wildlife_protection_sign.png")
    img.save(path, "PNG")
    print(f"Master Render: {path}")

def generate_special_banner():
    w, h = 1024, 256
    img = Image.new("RGBA", (w, h), (255, 210, 0, 255))
    draw = ImageDraw.Draw(img)

    # Franjas diagonales negras reflectantes en ambos extremos
    stripe_w = 34
    for x in range(-50, 180, stripe_w * 2):
        draw.polygon([(x, 0), (x + stripe_w, 0), (x + stripe_w - 45, h), (x - 45, h)], fill=(18, 18, 18, 255))
    for x in range(w - 180, w + 60, stripe_w * 2):
        draw.polygon([(x, 0), (x + stripe_w, 0), (x + stripe_w - 45, h), (x - 45, h)], fill=(18, 18, 18, 255))

    # Marco negro y remaches
    draw.rectangle([(6, 6), (w - 6, h - 6)], outline=(18, 18, 18, 255), width=10)

    f_banner = get_font("impact.ttf", 92)
    draw.text((w // 2, h // 2 + 6), "TRANSPORTE ESPECIAL", font=f_banner, fill=(18, 18, 18, 255), anchor="mm")

    path = os.path.join(OUTPUT_DIR, "special_v21_banner.png")
    img.save(path, "PNG")
    print(f"Master Render: {path}")

def generate_check_engine():
    w, h = 256, 256
    img = Image.new("RGBA", (w, h), (12, 14, 18, 255))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([(8, 8), (w - 8, h - 8)], radius=20, outline=(255, 120, 20, 255), width=6)
    draw.rounded_rectangle([(16, 16), (w - 16, h - 16)], radius=14, fill=(30, 16, 6, 255))

    # Icono motor
    draw.rounded_rectangle([(65, 80), (190, 160)], radius=10, fill=(255, 145, 25, 255))
    draw.rectangle([(42, 100), (65, 140)], fill=(255, 145, 25, 255))
    draw.rectangle([(190, 100), (214, 140)], fill=(255, 145, 25, 255))
    draw.polygon([(105, 52), (150, 52), (140, 80), (115, 80)], fill=(255, 145, 25, 255))

    f_txt = get_font("impact.ttf", 26)
    draw.text((w // 2, 202), "CHECK ENGINE", font=f_txt, fill=(255, 160, 40, 255), anchor="mm")

    path = os.path.join(OUTPUT_DIR, "dash_check_engine.png")
    img.save(path, "PNG")
    print(f"Master Render: {path}")

if __name__ == "__main__":
    generate_box07a_manifest()
    generate_diagnostic_tablet()
    generate_wildlife_sign()
    generate_special_banner()
    generate_check_engine()
    print("Master pixel-perfect Canva textures compiled successfully!")
