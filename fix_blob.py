import re

with open("web/hub.html", "r", encoding="utf-8", errors="ignore") as f:
    hub = f.read()

# Replace the blob creation logic to inject a <base> tag
old_blob = "const blob = new Blob([html], {type: 'text/html'});"
new_blob = """
  // Inject base tag to fix relative links and fetch API calls inside the Blob iframe
  const origin = window.location.origin;
  const baseTag = `<base href="${origin}/">`;
  const fixedHtml = html.replace('<head>', '<head>' + baseTag);
  const blob = new Blob([fixedHtml], {type: 'text/html'});
"""

hub = hub.replace(old_blob, new_blob)

with open("web/hub.html", "w", encoding="utf-8") as f:
    f.write(hub)

print("Injected base tag")
