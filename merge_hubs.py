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

print("Merged all into hub.html")
