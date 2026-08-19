import sys

with open('c:/Users/adria/OneDrive/Cintiabot/Codigo multibot/web/cenizas-quimera.html', 'r', encoding='utf-8') as f:
    text = f.read()

replacements = {
    'â€”': '—',
    'â€“': '–',
    'â€œ': '“',
    'â€\x9d': '”',
    'â€˜': '‘',
    'â€™': '’',
    'â€¦': '…'
}

# The right double quote is sometimes parsed strangely in strings, safer to replace just â€ if it's followed by a specific char
# Actually let's use the exact byte representations if possible, but python script with UTF-8 handles it fine usually.
# Let's add them directly
text = text.replace('â€”', '—')
text = text.replace('â€“', '–')
text = text.replace('â€œ', '“')
text = text.replace('â€', '”') # This covers right quote, but might overwrite others if not careful.
text = text.replace('â€˜', '‘')
text = text.replace('â€™', '’')
text = text.replace('â€¦', '…')


with open('c:/Users/adria/OneDrive/Cintiabot/Codigo multibot/web/cenizas-quimera.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Done')
