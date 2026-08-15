"""
Generador Local de Texturas en Disco a partir de las Referencias de Canva.
Crea archivos PNG reales de alta resolución para el simulador 3D.
"""

import os
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = r"C:\Users\adria\OneDrive\Documentos\Visual Studio\Telegram\DBTeamV2\Todosobrealltech\.moon-insideads-panel\web\generated-textures\canva-assets"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_box07a_manifest():
    w, h = 1024, 1024
    img = Image.new("RGBA", (w, h), (226, 216, 195, 255))
    draw = ImageDraw.Draw(img)

    # Borde envejecido
    draw.rectangle([(16, 16), (w - 16, h - 16)], outline=(130, 120, 103, 255), width=8)
    draw.rectangle([(28, 28), (w - 28, h - 28)], outline=(160, 150, 130, 255), width=3)

    # Texto
    draw.text((48, 60), "MANIFIESTO DE TRANSPORTE", fill=(44, 38, 30, 255))
    draw.text((48, 140), "Remitente:   Rutas del Continente", fill=(50, 45, 38, 255))
    draw.text((48, 200), "Destino:     Puerto Alba / Inirida", fill=(50, 45, 38, 255))
    draw.text((48, 260), "Guia Carga:  RC-8841", fill=(50, 45, 38, 255))
    draw.text((48, 320), "Contenido:   Equipos y documentos", fill=(50, 45, 38, 255))
    draw.text((48, 380), "Bultos:      1/1  |  Peso: 32.4 kg", fill=(50, 45, 38, 255))
    draw.text((48, 440), "Estado:      INSPECCION PENDIENTE", fill=(50, 45, 38, 255))

    # Sello rojo INCOMPLETO
    stamp = Image.new("RGBA", (480, 140), (0, 0, 0, 0))
    stamp_draw = ImageDraw.Draw(stamp)
    stamp_draw.rectangle([(8, 8), (472, 132)], outline=(200, 43, 29, 230), width=10)
    stamp_draw.text((30, 40), "INCOMPLETO", fill=(200, 43, 29, 230))
    rotated_stamp = stamp.rotate(-15, expand=True, resample=Image.BICUBIC)
    img.paste(rotated_stamp, (450, 520), rotated_stamp)

    # Cinta lateral PRECINTO ALTERADO
    draw.rectangle([(w - 140, 0), (w, h)], fill=(255, 106, 56, 255))
    draw.rectangle([(w - 130, 10), (w - 10, h - 10)], outline=(180, 40, 20, 255), width=4)
    
    seal_txt = Image.new("RGBA", (h, 120), (0, 0, 0, 0))
    seal_draw = ImageDraw.Draw(seal_txt)
    seal_draw.text((80, 30), "PRECINTO ALTERADO  ·  07-A  ·  ALERTA", fill=(40, 10, 5, 255))
    rot_seal = seal_txt.rotate(90, expand=True)
    img.paste(rot_seal, (w - 120, 0), rot_seal)

    path = os.path.join(OUTPUT_DIR, "box07a_manifest.png")
    img.save(path, "PNG")
    print(f"Generated: {path}")

def generate_diagnostic_tablet():
    w, h = 1024, 768
    img = Image.new("RGBA", (w, h), (4, 14, 22, 255))
    draw = ImageDraw.Draw(img)

    # Marco robusto de goma de taller
    draw.rectangle([(0, 0), (w, h)], outline=(20, 40, 50, 255), width=24)
    draw.rectangle([(24, 24), (w - 24, h - 24)], outline=(29, 77, 94, 255), width=6)

    # Cabecera
    draw.rectangle([(30, 30), (w - 30, 100)], fill=(8, 30, 43, 255))
    draw.text((60, 52), "DIAGNOSTICO INICIAL  ·  TALLER NOVA LIRIA", fill=(85, 234, 217, 255))

    # Tarjeta 1: Temperatura
    draw.rectangle([(50, 130), (w - 50, 260)], fill=(12, 34, 46, 255), outline=(35, 75, 90, 255), width=3)
    draw.text((80, 160), "TEMPERATURA DE MOTOR (ALTA)", fill=(255, 79, 56, 255))
    draw.text((700, 160), "112 C", fill=(255, 79, 56, 255))
    draw.rectangle([(80, 220), (w - 80, 235)], fill=(30, 45, 55, 255))
    draw.rectangle([(80, 220), (820, 235)], fill=(255, 79, 56, 255))

    # Tarjeta 2: Presión de Aceite
    draw.rectangle([(50, 290), (w - 50, 420)], fill=(12, 34, 46, 255), outline=(35, 75, 90, 255), width=3)
    draw.text((80, 320), "PRESION DE ACEITE (BAJA)", fill=(255, 170, 56, 255))
    draw.text((700, 320), "1.2 bar", fill=(255, 170, 56, 255))
    draw.rectangle([(80, 380), (w - 80, 395)], fill=(30, 45, 55, 255))
    draw.rectangle([(80, 380), (280, 395)], fill=(255, 170, 56, 255))

    # Tarjeta 3: Falla Eléctrica
    draw.rectangle([(50, 450), (w - 50, 580)], fill=(12, 34, 46, 255), outline=(35, 75, 90, 255), width=3)
    draw.text((80, 480), "FALLA ELECTRICA DETECTADA", fill=(255, 79, 56, 255))
    draw.text((650, 480), "CODIGO P0562", fill=(255, 210, 80, 255))
    draw.text((80, 535), "Tension de bateria baja o alternador irregular", fill=(140, 175, 190, 255))

    # Footer de recomendación
    draw.rectangle([(50, 620), (w - 50, 710)], fill=(7, 24, 34, 255), outline=(85, 234, 217, 100), width=2)
    draw.text((80, 650), "Recomendacion: Inspeccion manual de mangueras, correas y bornes.", fill=(120, 245, 230, 255))

    path = os.path.join(OUTPUT_DIR, "diagnostic_tablet.png")
    img.save(path, "PNG")
    print(f"Generated: {path}")

def generate_wildlife_sign():
    w, h = 512, 512
    img = Image.new("RGBA", (w, h), (30, 72, 50, 255))
    draw = ImageDraw.Draw(img)

    draw.rectangle([(16, 16), (w - 16, h - 16)], outline=(255, 255, 255, 255), width=12)
    draw.rectangle([(32, 32), (w - 32, h - 32)], outline=(18, 48, 32, 255), width=4)

    draw.text((120, 60), "ZONA DE", fill=(255, 255, 255, 255))
    draw.text((80, 120), "PROTECCION", fill=(255, 255, 255, 255))

    # Ciervo simplificado vectorial
    draw.polygon([(256, 220), (220, 320), (292, 320)], fill=(255, 255, 255, 255))
    draw.ellipse([(236, 190), (276, 230)], fill=(255, 255, 255, 255))
    # Cornamenta
    draw.line([(246, 195), (220, 160)], fill=(255, 255, 255, 255), width=6)
    draw.line([(266, 195), (292, 160)], fill=(255, 255, 255, 255), width=6)
    draw.line([(225, 175), (205, 170)], fill=(255, 255, 255, 255), width=4)
    draw.line([(287, 175), (307, 170)], fill=(255, 255, 255, 255), width=4)
    # Patas
    draw.line([(230, 320), (225, 410)], fill=(255, 255, 255, 255), width=8)
    draw.line([(282, 320), (287, 410)], fill=(255, 255, 255, 255), width=8)

    draw.text((60, 440), "FAUNA SILVESTRE", fill=(168, 224, 190, 255))

    path = os.path.join(OUTPUT_DIR, "wildlife_protection_sign.png")
    img.save(path, "PNG")
    print(f"Generated: {path}")

def generate_special_banner():
    w, h = 1024, 256
    img = Image.new("RGBA", (w, h), (255, 204, 0, 255))
    draw = ImageDraw.Draw(img)

    # Franjas negras diagonales en los laterales
    stripe_w = 28
    for x in range(-50, 160, stripe_w * 2):
        draw.polygon([(x, 0), (x + stripe_w, 0), (x + stripe_w - 40, h), (x - 40, h)], fill=(20, 20, 20, 255))
    for x in range(w - 160, w + 50, stripe_w * 2):
        draw.polygon([(x, 0), (x + stripe_w, 0), (x + stripe_w - 40, h), (x - 40, h)], fill=(20, 20, 20, 255))

    draw.rectangle([(8, 8), (w - 8, h - 8)], outline=(20, 20, 20, 255), width=10)
    draw.text((220, 90), "TRANSPORTE ESPECIAL", fill=(15, 15, 15, 255))

    path = os.path.join(OUTPUT_DIR, "special_v21_banner.png")
    img.save(path, "PNG")
    print(f"Generated: {path}")

def generate_check_engine():
    w, h = 256, 256
    img = Image.new("RGBA", (w, h), (12, 13, 16, 255))
    draw = ImageDraw.Draw(img)

    draw.rectangle([(8, 8), (w - 8, h - 8)], outline=(255, 127, 24, 255), width=8)
    draw.rectangle([(20, 20), (w - 20, h - 20)], fill=(30, 20, 10, 255))

    # Icono motor bloque
    draw.rectangle([(60, 90), (196, 170)], fill=(255, 149, 36, 255))
    draw.rectangle([(40, 110), (60, 150)], fill=(255, 149, 36, 255))
    draw.rectangle([(196, 110), (216, 150)], fill=(255, 149, 36, 255))
    draw.rectangle([(100, 60), (156, 90)], fill=(255, 149, 36, 255))

    draw.text((42, 190), "CHECK ENGINE", fill=(255, 160, 40, 255))

    path = os.path.join(OUTPUT_DIR, "dash_check_engine.png")
    img.save(path, "PNG")
    print(f"Generated: {path}")

if __name__ == "__main__":
    generate_box07a_manifest()
    generate_diagnostic_tablet()
    generate_wildlife_sign()
    generate_special_banner()
    generate_check_engine()
    print("All Canva texture maps physically generated in local disk!")
