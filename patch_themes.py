import os
import re

with open("web/hub.html", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Inject CSS for iOS/Android themes if missing
css_to_inject = """
  /* ── 🍏 Tema iOS Día (Light Cupertino) ── */
  body.theme-ios-light {
    --bg: #f2f2f7; --ink: #000000; --muted: #6e6e73;
    --teal: #007aff; --cyan: #5856d6; --amber: #ff9500; --red: #ff3b30;
    --line: rgba(0,0,0,.09); --card: #ffffff; --card2: #f9f9fb;
    --grad: linear-gradient(120deg, #007aff, #5856d6);
  }
  body.theme-ios-light .topbar, body.theme-ios-light .tabbar { background: rgba(242,242,247,.88); border-color: rgba(0,0,0,.08); }
  body.theme-ios-light .card, body.theme-ios-light .c-card, body.theme-ios-light .stat { box-shadow: 0 2px 10px rgba(0,0,0,.04); border-color: rgba(0,0,0,.06); }
  body.theme-ios-light .badge-status-hub.alfa { background: rgba(255,149,0,.15); color: #d97706; border-color: rgba(255,149,0,.4); }

  /* ── 🍏 Tema iOS Noche (OLED Dark) ── */
  body.theme-ios-dark {
    --bg: #000000; --ink: #ffffff; --muted: #8e8e93;
    --teal: #0a84ff; --cyan: #5e5ce6; --amber: #ffd60a; --red: #ff453a;
    --line: #2c2c2e; --card: #1c1c1e; --card2: #141416;
    --grad: linear-gradient(120deg, #0a84ff, #5e5ce6);
  }
  body.theme-ios-dark .topbar, body.theme-ios-dark .tabbar { background: rgba(0,0,0,.85); border-color: rgba(255,255,255,.1); }
  body.theme-ios-dark .card, body.theme-ios-dark .c-card, body.theme-ios-dark .stat { box-shadow: none; border-color: rgba(255,255,255,.08); }

  /* ── 🤖 Tema Android Material 3 Día ── */
  body.theme-android-light {
    --bg: #fafdfc; --ink: #191c1b; --muted: #6f7975;
    --teal: #006b5a; --cyan: #006876; --amber: #b26c00; --red: #ba1a1a;
    --line: #e0e3e1; --card: #eff1ee; --card2: #e0e3e1;
    --grad: linear-gradient(120deg, #006b5a, #006876);
  }
  body.theme-android-light .card, body.theme-android-light .c-card, body.theme-android-light .stat { border-radius: 24px; border: none; }

  /* ── 🤖 Tema Android Material 3 Noche ── */
  body.theme-android-dark {
    --bg: #191c1b; --ink: #e0e3e1; --muted: #89938f;
    --teal: #51dbbf; --cyan: #4fd8eb; --amber: #ffb86b; --red: #ffb4ab;
    --line: #3f4945; --card: #1e2522; --card2: #191c1b;
    --grad: linear-gradient(120deg, #51dbbf, #4fd8eb);
  }
  body.theme-android-dark .card, body.theme-android-dark .c-card, body.theme-android-dark .stat { border-radius: 24px; border: none; }
"""

if "body.theme-ios-light" not in content:
    content = content.replace("</style>", css_to_inject + "\n</style>")

# 2. Update loadAjustes to have the full theme/platform selector
old_ajustes = r'<div class="sec">Tema</div>.*?<div class="themeopt" data-theme-opt="clasico">.*?</div></div>'
new_ajustes = """<div class="sec">Tema de Interfaz & Plataforma Móvil</div>
        <div class="themeopt" data-theme-opt="nuevo"><div class="ra"></div><div class="to-t"><b>✨ Moon Neón (Cyberpunk)</b><span>Diseño por defecto con acentos teal/cyan fluidos.</span></div></div>
        <div class="themeopt" data-theme-opt="ios-dark"><div class="ra"></div><div class="to-t"><b>🍏 iOS Cupertino Noche (OLED Dark)</b><span>Diseño nativo de Apple, negro puro y acentos azules.</span></div></div>
        <div class="themeopt" data-theme-opt="ios-light"><div class="ra"></div><div class="to-t"><b>🍏 iOS Cupertino Día (Light)</b><span>Diseño nativo de Apple en fondo blanco suave y gris.</span></div></div>
        <div class="themeopt" data-theme-opt="android-dark"><div class="ra"></div><div class="to-t"><b>🤖 Android Material 3 Noche</b><span>Material You Dark con esquinas de 24px y turquesa.</span></div></div>
        <div class="themeopt" data-theme-opt="android-light"><div class="ra"></div><div class="to-t"><b>🤖 Android Material 3 Día</b><span>Material You Light tonal con tarjetas elevadas.</span></div></div>
        <div class="themeopt" data-theme-opt="clasico"><div class="ra"></div><div class="to-t"><b>📺 Clásico Retro</b><span>La maqueta original de tarjetas apiladas.</span></div></div>
        
        <div class="sec">Canal / Estado de Versión</div>
        <div class="themeopt" data-channel-opt="alfa"><div class="ra"></div><div class="to-t"><b>🔥 ALFA</b><span>Canal de desarrollo activo (Simulador 3D).</span></div></div>
        <div class="themeopt" data-channel-opt="beta"><div class="ra"></div><div class="to-t"><b>🧪 BETA</b><span>Canal de estabilización previa.</span></div></div>
        <div class="themeopt" data-channel-opt="rc"><div class="ra"></div><div class="to-t"><b>🚀 RC (Release Candidate)</b><span>Candidata final de lanzamiento.</span></div></div>
        <div class="themeopt" data-channel-opt="estable"><div class="ra"></div><div class="to-t"><b>✅ ESTABLE</b><span>Rama principal estable verificada.</span></div></div>"""

content = re.sub(old_ajustes, new_ajustes, content, flags=re.DOTALL)

with open("web/hub.html", "w", encoding="utf-8", newline="\n") as f:
    f.write(content)

print("Patch applied")
