import os
import re

def get_file_content(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

# Load the historical files
html_estable = get_file_content("web/hub-estable.html")
html_new = get_file_content("web/hub-new.html")
html_clasico = get_file_content("web/hub-clasico.html")

# Read the current hub
hub = get_file_content("web/hub.html")

# Fix the encoding using a safer mapping without touching HTML tags
# We will only target specific broken words
fixes = {
    "Diseo": "Diseño",
    "Dise": "Diseño", # Be careful with this one, could match "Diseñado" but "Dise" is usually the broken word
    "Aadir": "Añadir",
    "Clsico": "Clásico",
    "configuracin": "configuración",
    "versin": "versión",
    "Mvil": "Móvil",
    "Estadsticas": "Estadísticas",
    "Moderacin": "Moderación",
    "Gestin": "Gestión",
    "Automatizacin": "Automatización",
    "Bsqueda": "Búsqueda",
    "Ttulo": "Título",
    "sincronizacin": "sincronización",
    "Analticas": "Analíticas",
    "Mtricas": "Métricas",
    "Composicin": "Composición",
    "da": "día",
    "ms": "más",
    "seccin": "sección",
    "opcin": "opción",
    "botn": "botón",
    "accin": "acción",
    "informacin": "información",
    "redireccin": "redirección",
    "verificacin": "verificación",
    "proteccin": "protección",
    "eliminacin": "eliminación",
    "excepcin": "excepción",
    "direccin": "dirección",
    "conexin": "conexión",
    "nico": "único",
    "ltimo": "último",
    "rpida": "rápida",
    "pestaa": "pestaña",
    "pequeo": "pequeño",
    "tamao": "tamaño",
    "contrasea": "contraseña",
    "ao": "año",
    "compaa": "compañía",
    "categora": "categoría",
    "tecnologa": "tecnología",
    "economa": "economía",
    "gua": "guía",
    "das": "días",
    "desarrollar": "desarrollará",
    "estar": "estará",
    "podr": "podrá",
    "ser": "será",
    "habr": "habrá",
    "tendr": "tendrá",
    "aqu": "aquí",
    "as": "así",
    "slo": "sólo",
    "tambin": "también",
    "ningn": "ningún",
    "algn": "algún",
    "comn": "común",
    "segn": "según",
    "rabe": "árabe",
    "cirlico": "cirílico",
    "ldico": "lúdico",
    "ptimo": "óptimo",
    "grficos": "gráficos",
    "grficas": "gráficas",
    "dinmica": "dinámica",
    "efmera": "efímera",
    "automtica": "automática",
    "annima": "anónima",
    "annimo": "anónimo",
    "autenticacin": "autenticación",
    "prximas": "próximas",
    "trminos": "términos",
    "lmite": "límite",
    "expulsin": "expulsión",
    "auditora": "auditoría",
    "creacin": "creación",
    "inyeccin": "inyección",
    "tacgrafo": "tacógrafo",
    "fsica": "física",
    "nete": "únete",
    "Campaa": "Campaña",
    "nicamente": "únicamente",
    "envan": "envían",
    "Ordenacin": "Ordenación",
    "jerarqua": "jerarquía",
    "Pestaas": "Pestañas"
}

# The problem was replacing "s", "a", "i", "u", "o" globally which destroyed script tags and URLs!
# So we only replace the specific words above.

for bad, good in fixes.items():
    hub = re.sub(r'\b' + bad + r'\b', good, hub)

# Replace remaining common patterns manually without word boundaries
hub = hub.replace("DISE'O", "DISEÑO")
hub = hub.replace("CL?SICO", "CLÁSICO")
hub = hub.replace("Diseo", "Diseño")
hub = hub.replace("Dise", "Diseño")

# Fix the settings panel in hub.html to have "Apariencia" and "Tema"
old_sec = r'<div class="sec">Tema de Interfaz & Plataforma Móvil</div>'
new_sec = """<div class="sec">Apariencia (Arquitectura UI)</div>
        <div class="themeopt" onclick="switchLayout('aurora')"><div class="ra"></div><div class="to-t"><b>🚀 Alfa Definitivo (Aurora)</b><span>El diseño actual con todas las nuevas funciones.</span></div></div>
        <div class="themeopt" onclick="switchLayout('new')"><div class="ra"></div><div class="to-t"><b>✨ New Hub</b><span>Arquitectura con Perfil y Ajustes nativos.</span></div></div>
        <div class="themeopt" onclick="switchLayout('estable')"><div class="ra"></div><div class="to-t"><b>✅ Clásico Estable</b><span>El diseño de la release v16.85.0.</span></div></div>
        <div class="themeopt" onclick="switchLayout('clasico')"><div class="ra"></div><div class="to-t"><b>📺 Clásico Puro</b><span>La maqueta original de tarjetas apiladas.</span></div></div>

        <div class="sec">Tema de Color</div>"""
hub = re.sub(old_sec, new_sec, hub, count=1)

# Escape backticks and ${} to safely inject into a JS template literal
def escape_js_template(text):
    return text.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')

# Inject the layout switcher JS and the templates
switcher_script = f"""
<script>
const layouts = {{
  'estable': `{escape_js_template(html_estable)}`,
  'new': `{escape_js_template(html_new)}`,
  'clasico': `{escape_js_template(html_clasico)}`
}};

function switchLayout(id) {{
  if(id === 'aurora') {{ window.location.reload(); return; }}
  const html = layouts[id];
  const blob = new Blob([html], {{type: 'text/html'}});
  const url = URL.createObjectURL(blob);
  
  document.documentElement.innerHTML = `<head><title>Panel Histórico</title></head>
  <body style="margin:0;padding:0;overflow:hidden;">
    <iframe src="${{url}}" style="width:100vw;height:100vh;border:none;"></iframe>
    <button onclick="window.location.reload()" style="position:fixed;bottom:24px;right:24px;z-index:999999;background:var(--teal, #0a84ff);color:#fff;border:none;padding:14px 24px;border-radius:30px;box-shadow:0 8px 24px rgba(0,0,0,.4);cursor:pointer;font-weight:bold;font-family:sans-serif;font-size:15px;transition:transform 0.2s;">
      🔙 Volver al Alfa
    </button>
  </body>`;
}}
</script>
</body>
"""

hub = hub.replace("</body>", switcher_script)

with open("web/hub.html", "w", encoding="utf-8") as f:
    f.write(hub)

print("Safely merged and fixed encoding")
