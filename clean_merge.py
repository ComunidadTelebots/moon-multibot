import subprocess
import re
import os

GIT_EXE = r"C:\Users\adria\AppData\Local\GitHubDesktop\app-3.6.3\resources\app\git\cmd\git.exe"

def get_git_content(commit_ref):
    result = subprocess.run([GIT_EXE, "show", f"{commit_ref}:web/hub.html"], capture_output=True)
    return result.stdout.decode('utf-8', errors='ignore')

# Load the historical files directly from git
html_estable = get_git_content("master")
html_new = get_git_content("d6c0a31")
html_clasico = get_git_content("4c61352")

# Read the current hub
with open("web/hub.html", "r", encoding="utf-8", errors="ignore") as f:
    hub = f.read()

# Fix encoding issues in current hub
fixes = {
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
for bad, good in fixes.items():
    hub = re.sub(r'\b' + bad + r'\b', good, hub)

hub = hub.replace("DISE'O", "DISEÑO")
hub = hub.replace("CL?SICO", "CLÁSICO")
hub = hub.replace("Diseo", "Diseño")
hub = hub.replace("Dise", "Diseño")

# Redo the layout switcher settings panel
old_sec = r'<div class="sec">Tema de Interfaz & Plataforma Móvil</div>'
new_sec = """<div class="sec">Apariencia (Arquitectura UI)</div>
        <div class="themeopt" onclick="switchLayout('aurora')"><div class="ra"></div><div class="to-t"><b>🚀 Alfa Definitivo (Aurora)</b><span>El diseño actual con todas las nuevas funciones.</span></div></div>
        <div class="themeopt" onclick="switchLayout('new')"><div class="ra"></div><div class="to-t"><b>✨ New Hub</b><span>Arquitectura con Perfil y Ajustes nativos.</span></div></div>
        <div class="themeopt" onclick="switchLayout('estable')"><div class="ra"></div><div class="to-t"><b>✅ Clásico Estable</b><span>El diseño de la release v16.85.0.</span></div></div>
        <div class="themeopt" onclick="switchLayout('clasico')"><div class="ra"></div><div class="to-t"><b>📺 Clásico Puro</b><span>La maqueta original de tarjetas apiladas.</span></div></div>

        <div class="sec">Tema de Color</div>"""
hub = re.sub(old_sec, new_sec, hub, count=1)

def escape_js_template(text):
    return text.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$').replace('</script>', '<\\/script>')

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
  
  const origin = window.location.origin;
  const baseTag = "<base href=\"" + origin + "/\">";
  let fixedHtml = html.replace('<head>', '<head>' + baseTag);
  // Also replace relative fetch/api calls if they rely on window.location
  const blob = new Blob([fixedHtml], {{type: 'text/html'}});

  const url = URL.createObjectURL(blob);
  
  document.documentElement.innerHTML = `<head><title>Panel Histórico</title></head>
  <body style="margin:0;padding:0;overflow:hidden;background:#000;">
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

print("Safely merged cleanly from Git")
