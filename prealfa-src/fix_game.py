import sys

with open('c:/Users/adria/OneDrive/Cintiabot/Codigo multibot/web/cenizas-quimera.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace specific words first to avoid conflicts
text = text.replace('EDICIÃ*N', 'EDICIÓN')
text = text.replace('CazÃ¡bamos', 'Cazábamos')
text = text.replace('ǟ?A', 'ÍA')
text = text.replace('ǟ?o', 'ío')
text = text.replace('ǟ?a', 'ía')
text = text.replace('ǟ?e', 'íe')

# Replace strange quotation marks and em dashes
text = text.replace('ǽ\'??', '"')
text = text.replace('ǽ\'?', '"')
text = text.replace('ǽ\'', '"')
text = text.replace('ǟ€', '—')

# Replace standard mojibake
replacements = {
    'Ã¡': 'á',
    'Ã©': 'é',
    'Ã*': 'í',
    'Ã³': 'ó',
    'Ãº': 'ú',
    'Ã±': 'ñ',
    'Ã‘': 'Ñ',
    'Ã': 'Á',
    'ǟa': 'ía',
    'ǟe': 'íe',
    'ǟo': 'ío',
    'ǟu': 'íu',
    'ǟA': 'ÍA',
    'ǟE': 'ÍE',
    'ǟO': 'ÍO',
    'ǟU': 'ÍU',
    'ǟ?': 'Í',
    'ǟ': 'í'
}

for k, v in replacements.items():
    text = text.replace(k, v)

with open('c:/Users/adria/OneDrive/Cintiabot/Codigo multibot/web/cenizas-quimera.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Done")
