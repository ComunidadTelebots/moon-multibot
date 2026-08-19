import sys
with open('c:/Users/adria/OneDrive/Cintiabot/Codigo multibot/web/cenizas-quimera.html', encoding='utf-8') as f:
    html = f.read()

print(f"File size: {len(html)}")
idx = html.find('<script type="module">')
print(f"Found at: {idx}")

if idx != -1:
    end_idx = html.find('</script>', idx)
    with open('script_0.js', 'w', encoding='utf-8') as f2:
        f2.write(html[idx+22:end_idx])
    print("Wrote script_0.js")
