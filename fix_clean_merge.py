import re

with open("web/hub.html", "r", encoding="utf-8", errors="ignore") as f:
    hub = f.read()

# We need to find the layouts object and escape </script>
# Actually, the python script that built it is still here: clean_merge.py
# Let's just modify clean_merge.py to escape </script> and re-run it!

with open("clean_merge.py", "r", encoding="utf-8") as f:
    script = f.read()

# Add escaping for </script>
old_escape = "return text.replace('\\\\', '\\\\\\\\').replace('`', '\\\\`').replace('$', '\\\\$')"
new_escape = "return text.replace('\\\\', '\\\\\\\\').replace('`', '\\\\`').replace('$', '\\\\$').replace('</script>', '<\\\\/script>')"

script = script.replace(old_escape, new_escape)

# Also add the base tag injection inside clean_merge.py
old_blob = "const blob = new Blob([html], {{type: 'text/html'}});"
new_blob = """
  const origin = window.location.origin;
  const baseTag = `<base href="${origin}/">`;
  let fixedHtml = html.replace('<head>', '<head>' + baseTag);
  // Also replace relative fetch/api calls if they rely on window.location
  const blob = new Blob([fixedHtml], {{type: 'text/html'}});
"""

script = script.replace(old_blob, new_blob)

with open("clean_merge.py", "w", encoding="utf-8") as f:
    f.write(script)
