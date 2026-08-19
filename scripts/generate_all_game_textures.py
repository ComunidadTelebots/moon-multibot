"""
Generador Integral de Todas las Texturas del Videojuego Moon Multibot (Canal Alfa).
Genera todas las libreas de vehículos, pantallas de cabina, europallets de carga
y señales de tráfico basadas estrictamente en el ecosistema Canva.
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

def draw_screws(draw, positions, radius=6):
    for x, y in positions:
        draw.ellipse([(x - radius, y - radius), (x + radius, y + radius)], fill=(80, 85, 90, 255), outline=(30, 35, 40, 255), width=2)
        draw.line([(x - radius + 2, y), (x + radius - 2, y)], fill=(40, 45, 50, 255), width=2)
        draw.line([(x, y - radius + 2), (x, y + radius - 2)], fill=(40, 45, 50, 255), width=2)

# ==============================================================================
# 1. LIBREAS DE EMPRESAS Y VEHÍCULOS (Canva págs 023, 024, 021)
# ==============================================================================

def generate_livery_rutas_continente():
    w, h = 1024, 512
    img = Image.new("RGBA", (w, h), (25, 28, 35, 255))
    draw = ImageDraw.Draw(img)

    # Franjas aerodinámicas corporativas (Naranja / Gris claro / Blanco)
    draw.polygon([(0, 320), (w, 180), (w, 360), (0, 500)], fill=(245, 110, 35, 255))
    draw.polygon([(0, 280), (w, 140), (w, 180), (0, 320)], fill=(220, 225, 230, 255))
    draw.polygon([(0, 250), (w, 110), (w, 135), (0, 275)], fill=(120, 130, 140, 255))

    # Logotipo
    draw.text((60, 60), "RUTAS DEL CONTINENTE", font=get_font("impact.ttf", 52), fill=(255, 255, 255, 255))
    draw.text((65, 125), "LOGÍSTICA INTEGRAL Y TRANSPORTE PESADO", font=get_font("segoeuib.ttf", 20), fill=(245, 130, 45, 255))

    # Identificación y matrícula de flota
    draw.text((w - 240, 65), "FLOTA Nº 408", font=get_font("consolab.ttf", 24), fill=(200, 210, 220, 255))
    draw.text((65, 430), "DIVISION TRANSPORTE INTERNACIONAL", font=get_font("segoeuib.ttf", 18), fill=(255, 255, 255, 255))

    path = os.path.join(OUTPUT_DIR, "livery_rutas_continente.png")
    img.save(path, "PNG")
    print(f"Generated: {path}")

def generate_livery_trans_iberica():
    w, h = 1024, 512
    img = Image.new("RGBA", (w, h), (10, 35, 60, 255))
    draw = ImageDraw.Draw(img)

    # Franjas azul cyan y blanco
    draw.polygon([(0, 0), (350, 0), (150, h), (0, h)], fill=(85, 234, 217, 255))
    draw.polygon([(350, 0), (450, 0), (250, h), (150, h)], fill=(255, 255, 255, 255))

    draw.text((480, 80), "TRANS-IBÉRICA", font=get_font("impact.ttf", 68), fill=(255, 255, 255, 255))
    draw.text((485, 160), "EXPRESS LOGISTICS · CARGA PALETIZADA", font=get_font("segoeuib.ttf", 22), fill=(85, 234, 217, 255))
    draw.text((485, 410), "MADRID · BARCELONA · MARSEILLE · LISBOA", font=get_font("segoeuib.ttf", 18), fill=(200, 225, 240, 255))

    path = os.path.join(OUTPUT_DIR, "livery_trans_iberica.png")
    img.save(path, "PNG")
    print(f"Generated: {path}")

def generate_livery_emergency_samur():
    w, h = 1024, 512
    img = Image.new("RGBA", (w, h), (235, 245, 50, 255)) # Amarillo fluor
    draw = ImageDraw.Draw(img)

    # Patrón Battenburg damero reflectante azul/fluor
    sq_size = 64
    for y in range(256, 448, sq_size):
        for x in range(0, w, sq_size * 2):
            offset = sq_size if (y // sq_size) % 2 == 1 else 0
            draw.rectangle([(x + offset, y), (x + offset + sq_size, y + sq_size)], fill=(15, 60, 150, 255))

    draw.text((80, 60), "EMERGENCIAS", font=get_font("impact.ttf", 76), fill=(15, 60, 150, 255))
    draw.text((85, 150), "SOPORTE VITAL AVANZADO · RESPUESTA RÁPIDA", font=get_font("segoeuib.ttf", 22), fill=(200, 20, 20, 255))
    draw.text((w - 180, 60), "112", font=get_font("impact.ttf", 92), fill=(200, 20, 20, 255))

    path = os.path.join(OUTPUT_DIR, "livery_emergency_samur.png")
    img.save(path, "PNG")
    print(f"Generated: {path}")

# ==============================================================================
# 2. CUADRO DE INSTRUMENTOS Y PANTALLAS DE CABINA (Canva pág 021)
# ==============================================================================

def generate_cockpit_tachometer():
    w, h = 1024, 512
    img = Image.new("RGBA", (w, h), (8, 14, 20, 255))
    draw = ImageDraw.Draw(img)

    # Marco de instrumentos
    draw.rectangle([(16, 16), (w - 16, h - 16)], outline=(25, 55, 75, 255), width=4)

    # Tacómetro Velocidad (Izquierda)
    cx1, cy1, r1 = 280, 256, 180
    draw.ellipse([(cx1 - r1, cy1 - r1), (cx1 + r1, cy1 + r1)], outline=(35, 75, 100, 255), width=6)
    draw.ellipse([(cx1 - r1 + 15, cy1 - r1 + 15), (cx1 + r1 - 15, cy1 + r1 - 15)], outline=(85, 234, 217, 180), width=4)
    draw.text((cx1, cy1 - 20), "78", font=get_font("impact.ttf", 96), fill=(255, 255, 255, 255), anchor="mm")
    draw.text((cx1, cy1 + 50), "km/h", font=get_font("segoeuib.ttf", 24), fill=(85, 234, 217, 255), anchor="mm")

    # Tacómetro RPM (Derecha)
    cx2, cy2, r2 = 744, 256, 180
    draw.ellipse([(cx2 - r2, cy2 - r2), (cx2 + r2, cy2 + r2)], outline=(35, 75, 100, 255), width=6)
    draw.ellipse([(cx2 - r2 + 15, cy2 - r2 + 15), (cx2 + r2 - 15, cy2 + r2 - 15)], outline=(245, 130, 45, 180), width=4)
    draw.text((cx2, cy2 - 20), "12", font=get_font("impact.ttf", 96), fill=(255, 255, 255, 255), anchor="mm")
    draw.text((cx2, cy2 + 50), "x100 RPM", font=get_font("segoeuib.ttf", 24), fill=(245, 130, 45, 255), anchor="mm")

    # Barra Combustible (Centro inferior)
    draw.rectangle([(420, 380), (604, 404)], fill=(18, 30, 40, 255), outline=(35, 75, 100, 255), width=2)
    draw.rectangle([(424, 384), (540, 400)], fill=(245, 130, 45, 255))
    draw.text((512, 355), "DIÉSEL: 63%", font=get_font("segoeuib.ttf", 18), fill=(220, 235, 245, 255), anchor="mm")
    draw.text((512, 440), "LIM: 80 km/h · 21:47", font=get_font("consolab.ttf", 20), fill=(85, 234, 217, 255), anchor="mm")

    path = os.path.join(OUTPUT_DIR, "cockpit_tachometer_cluster.png")
    img.save(path, "PNG")
    print(f"Generated: {path}")

def generate_cockpit_gps():
    w, h = 512, 512
    img = Image.new("RGBA", (w, h), (10, 20, 30, 255))
    draw = ImageDraw.Draw(img)

    draw.rectangle([(8, 8), (w - 8, h - 8)], outline=(35, 80, 105, 255), width=4)

    # Mapa perspectiva
    draw.polygon([(180, 480), (332, 480), (280, 120), (232, 120)], fill=(30, 50, 65, 255))
    # Ruta azul de guiado
    draw.line([(256, 460), (256, 320), (320, 220), (340, 130)], fill=(85, 234, 217, 255), width=16)

    # Flecha posición
    draw.polygon([(256, 440), (240, 470), (256, 460), (272, 470)], fill=(255, 255, 255, 255))

    # Señal límite de velocidad 80 km/h en esquina
    draw.ellipse([(380, 40), (460, 120)], fill=(255, 255, 255, 255), outline=(220, 30, 30, 255), width=10)
    draw.text((420, 80), "80", font=get_font("impact.ttf", 44), fill=(10, 10, 10, 255), anchor="mm")

    # Indicador de distancia de giro
    draw.text((50, 50), "2.4 km", font=get_font("impact.ttf", 52), fill=(255, 255, 255, 255))
    draw.text((50, 110), "Próxima salida A-2", font=get_font("segoeuib.ttf", 20), fill=(85, 234, 217, 255))

    path = os.path.join(OUTPUT_DIR, "cockpit_gps_screen.png")
    img.save(path, "PNG")
    print(f"Generated: {path}")

def generate_cb_radio_display():
    w, h = 512, 256
    img = Image.new("RGBA", (w, h), (18, 30, 24, 255)) # Verde LCD oscuro
    draw = ImageDraw.Draw(img)

    draw.rectangle([(8, 8), (w - 8, h - 8)], fill=(32, 58, 42, 255), outline=(60, 100, 75, 255), width=4)

    draw.text((40, 35), "CB TRANSCEIVER · CH 19", font=get_font("consolab.ttf", 22), fill=(120, 235, 160, 255))
    draw.text((40, 95), "27.185 MHz", font=get_font("impact.ttf", 58), fill=(160, 255, 190, 255))

    # Barra S-Meter
    draw.text((40, 185), "SIGNAL: [ ||||||||||||░░ ] S-9", font=get_font("consolab.ttf", 20), fill=(120, 235, 160, 255))
    draw.text((w - 110, 35), "AM / FM", font=get_font("consolab.ttf", 22), fill=(220, 255, 180, 255))

    path = os.path.join(OUTPUT_DIR, "cb_radio_display.png")
    img.save(path, "PNG")
    print(f"Generated: {path}")

# ==============================================================================
# 3. CARGAS, PALLETS Y MERCANCÍAS (Canva pág 023)
# ==============================================================================

def generate_cargo_pallet_electronics():
    w, h = 512, 512
    img = Image.new("RGBA", (w, h), (195, 150, 95, 255)) # Madera / Cartón
    draw = ImageDraw.Draw(img)

    # Franjas de cartón
    draw.rectangle([(16, 16), (w - 16, h - 16)], outline=(140, 100, 60, 255), width=4)

    # Etiqueta FRÁGIL roja
    draw.rectangle([(40, 40), (220, 120)], fill=(220, 35, 30, 255))
    draw.text((130, 80), "FRÁGIL", font=get_font("impact.ttf", 36), fill=(255, 255, 255, 255), anchor="mm")

    # Flechas "Este lado arriba"
    draw.polygon([(260, 100), (280, 60), (300, 100)], fill=(25, 25, 25, 255))
    draw.rectangle([(272, 100), (288, 120)], fill=(25, 25, 25, 255))

    # Código de barras GS1
    draw.rectangle([(40, 340), (w - 40, 460)], fill=(255, 255, 255, 255), outline=(50, 50, 50, 255), width=2)
    bar_x = 60
    for w_bar in [3, 6, 2, 8, 4, 3, 6, 2, 8, 4, 3, 6, 2, 8, 4, 3, 6, 2, 8, 4, 3, 6, 2, 8, 4, 3, 6, 2, 8, 4]:
        draw.rectangle([(bar_x, 355), (bar_x + w_bar, 425)], fill=(0, 0, 0, 255))
        bar_x += w_bar + 5
    draw.text((w // 2, 442), "(01) 8437001928410 (10) BATCH-449", font=get_font("consolab.ttf", 16), fill=(10, 10, 10, 255), anchor="mm")

    draw.text((40, 160), "ELECTRÓNICA DE PRECISIÓN", font=get_font("segoeuib.ttf", 22), fill=(25, 25, 25, 255))
    draw.text((40, 200), "PESO BRUTO: 450 KG · 120x80x110 cm", font=get_font("segoeuib.ttf", 18), fill=(60, 45, 30, 255))

    path = os.path.join(OUTPUT_DIR, "cargo_pallet_electronics.png")
    img.save(path, "PNG")
    print(f"Generated: {path}")

def generate_cargo_pallet_adr():
    w, h = 512, 512
    img = Image.new("RGBA", (w, h), (180, 185, 190, 255)) # Bidón metálico / IBC
    draw = ImageDraw.Draw(img)

    # Rombo ADR Clase 3 (Líquido Inflamable Rojo)
    cx, cy, s = 256, 200, 110
    draw.polygon([(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)], fill=(220, 30, 25, 255), outline=(255, 255, 255, 255), width=6)
    # Llama inflamable blanca
    draw.ellipse([(cx - 20, cy - 45), (cx + 20, cy + 15)], fill=(255, 255, 255, 255))
    draw.text((cx, cy + 60), "3", font=get_font("impact.ttf", 46), fill=(255, 255, 255, 255), anchor="mm")

    # Panel Naranja ADR (ONU 1202 - Diésel / Gasóleo)
    draw.rectangle([(80, 340), (432, 460)], fill=(255, 120, 10, 255), outline=(20, 20, 20, 255), width=6)
    draw.line([(80, 400), (432, 400)], fill=(20, 20, 20, 255), width=4)
    draw.text((256, 370), "30", font=get_font("impact.ttf", 44), fill=(10, 10, 10, 255), anchor="mm")
    draw.text((256, 430), "1202", font=get_font("impact.ttf", 44), fill=(10, 10, 10, 255), anchor="mm")

    path = os.path.join(OUTPUT_DIR, "cargo_pallet_adr_hazard.png")
    img.save(path, "PNG")
    print(f"Generated: {path}")

# ==============================================================================
# 4. SEÑALES DE CARRETERA Y ENTORNO (Canva págs 094, 023)
# ==============================================================================

def generate_road_warning_livestock():
    w, h = 512, 512
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Triángulo equilátero reflectante de advertencia
    p1 = (w // 2, 24)
    p2 = (w - 24, h - 36)
    p3 = (24, h - 36)
    draw.polygon([p1, p2, p3], fill=(255, 255, 255, 255), outline=(220, 30, 25, 255), width=28)

    # Silueta de Vaca / Ganado en el centro
    cow_pts = [
        (180, 300), (170, 260), (190, 250), (210, 270), (270, 270),
        (330, 280), (340, 340), (320, 340), (310, 400), (295, 400),
        (300, 350), (250, 350), (240, 400), (225, 400), (235, 330),
        (195, 330), (190, 400), (175, 400), (175, 320)
    ]
    draw.polygon(cow_pts, fill=(20, 20, 20, 255))
    # Cuernos
    draw.line([(180, 255), (170, 240)], fill=(20, 20, 20, 255), width=4)
    draw.line([(190, 255), (200, 240)], fill=(20, 20, 20, 255), width=4)

    path = os.path.join(OUTPUT_DIR, "road_warning_livestock.png")
    img.save(path, "PNG")
    print(f"Generated: {path}")

def generate_road_speed_limit_70():
    w, h = 512, 512
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Señal circular reglamentaria
    draw.ellipse([(16, 16), (w - 16, h - 16)], fill=(255, 255, 255, 255), outline=(220, 30, 25, 255), width=44)
    draw.text((w // 2, h // 2 + 5), "70", font=get_font("impact.ttf", 220), fill=(20, 20, 20, 255), anchor="mm")

    path = os.path.join(OUTPUT_DIR, "road_speed_limit_70.png")
    img.save(path, "PNG")
    print(f"Generated: {path}")

def generate_road_customs_toll_sign():
    w, h = 1024, 512
    img = Image.new("RGBA", (w, h), (20, 70, 150, 255)) # Azul autopista
    draw = ImageDraw.Draw(img)

    draw.rectangle([(16, 16), (w - 16, h - 16)], outline=(255, 255, 255, 255), width=10)

    draw.text((w // 2, 80), "CONTROL ADUANERO · TOLL · PEAJE", font=get_font("impact.ttf", 52), fill=(255, 255, 255, 255), anchor="mm")
    draw.line([(50, 130), (w - 50, 130)], fill=(255, 255, 255, 255), width=4)

    # Vías
    draw.text((200, 220), "VÍA 1: TELEPEAJE (TAG)", font=get_font("segoeuib.ttf", 28), fill=(85, 234, 217, 255))
    draw.text((200, 290), "VÍA 2: INSPECCIÓN ADUANA / ADR", font=get_font("segoeuib.ttf", 28), fill=(255, 200, 40, 255))
    draw.text((200, 360), "VÍA 3: TRANSPORTE PESADO / GÁLIBO", font=get_font("segoeuib.ttf", 28), fill=(255, 255, 255, 255))

    draw.text((w // 2, 450), "A 500 m  ·  REDUZCA A 30 km/h", font=get_font("impact.ttf", 36), fill=(255, 255, 255, 255), anchor="mm")

    path = os.path.join(OUTPUT_DIR, "road_customs_toll_sign.png")
    img.save(path, "PNG")
    print(f"Generated: {path}")

if __name__ == "__main__":
    generate_livery_rutas_continente()
    generate_livery_trans_iberica()
    generate_livery_emergency_samur()
    generate_cockpit_tachometer()
    generate_cockpit_gps()
    generate_cb_radio_display()
    generate_cargo_pallet_electronics()
    generate_cargo_pallet_adr()
    generate_road_warning_livestock()
    generate_road_speed_limit_70()
    generate_road_customs_toll_sign()
    print("Full video game Canva texture catalog generated successfully!")
