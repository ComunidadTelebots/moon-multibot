import re

with open("web/hub.html", "r", encoding="utf-8") as f:
    hub = f.read()

# We need to escape all </script> tags that are inside the layouts block
# The layouts block starts at const layouts = { and ends at };
match = re.search(r'(const layouts = \{.*?\n\};)', hub, re.DOTALL)
if match:
    layouts_block = match.group(1)
    # Escape </script> securely to <\/script>
    safe_layouts_block = layouts_block.replace("</script>", "<\\/script>")
    hub = hub.replace(layouts_block, safe_layouts_block)
    
    with open("web/hub.html", "w", encoding="utf-8") as f:
        f.write(hub)
    print("Safely escaped all script tags inside templates!")
else:
    print("Could not find layouts block")
