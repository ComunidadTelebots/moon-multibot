import sys

def fix_mojibake(text):
    try:
        # If the string was double-encoded: UTF-8 read as CP1252 and saved as UTF-8
        return text.encode('cp1252').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text

# Test
test_str = "No cazÃ¡bamos monstruos. CazÃ¡bamos nuestro miedo a convertirnos en otra cosa."
print(fix_mojibake(test_str))
