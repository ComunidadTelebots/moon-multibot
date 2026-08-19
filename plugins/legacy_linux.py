"""Herramientas GNU/Linux recuperadas de los comandos históricos de TeleBots."""

import re


ALTERNATIVES = {
    "photoshop": "GIMP, Krita o Photopea",
    "office": "LibreOffice u OnlyOffice",
    "word": "LibreOffice Writer u OnlyOffice Documents",
    "excel": "LibreOffice Calc u OnlyOffice Spreadsheets",
    "premiere": "Kdenlive, Shotcut o DaVinci Resolve",
    "illustrator": "Inkscape",
    "winrar": "PeaZip, Ark o File Roller",
    "notepad": "Kate, Geany o VS Code",
    "outlook": "Thunderbird o Evolution",
}

DISTROS = {
    "ubuntu": "Ubuntu: distribución basada en Debian, enfocada en facilidad de uso. https://ubuntu.com/download",
    "debian": "Debian: distribución comunitaria estable y base de muchos sistemas. https://www.debian.org/distrib/",
    "fedora": "Fedora: tecnologías recientes respaldadas por su comunidad. https://fedoraproject.org/",
    "arch": "Arch Linux: sistema flexible de actualización continua para usuarios avanzados. https://archlinux.org/download/",
    "mint": "Linux Mint: escritorio accesible basado en Ubuntu/Debian. https://linuxmint.com/download.php",
}

ISOS = """Descargas oficiales de GNU/Linux:
• Ubuntu: https://ubuntu.com/download
• Debian: https://www.debian.org/distrib/
• Fedora: https://fedoraproject.org/
• Linux Mint: https://linuxmint.com/download.php
• Arch Linux: https://archlinux.org/download/
Verifica siempre la suma SHA256 publicada por el proyecto."""


def handle_command(bot, cid, uid, text, rank):
    parts = text.strip().split(maxsplit=1)
    cmd = parts[0].lower() if parts else ""
    argument = parts[1].strip().lower() if len(parts) > 1 else ""
    if cmd not in {"/alternativa", "/distro", "/isos", "/kernel", "/man"}:
        return False
    if cmd == "/alternativa":
        if not argument:
            answer = "Uso: /alternativa <programa>. Ejemplo: /alternativa Photoshop"
        else:
            match = next((value for key, value in ALTERNATIVES.items() if key in argument), None)
            answer = match or "No tengo una equivalencia verificada. Consulta https://alternativeto.net/platform/linux/"
    elif cmd == "/distro":
        if not argument:
            answer = "Uso: /distro <nombre>. Disponibles: " + ", ".join(sorted(DISTROS))
        else:
            answer = DISTROS.get(argument, "Distribución no incluida aún. Catálogo: https://distrowatch.com/")
    elif cmd == "/isos":
        answer = ISOS
    elif cmd == "/kernel":
        answer = "Versiones y avisos oficiales del kernel Linux:\nhttps://www.kernel.org/"
    else:
        command = argument.split()[0] if argument else ""
        if not command or not re.fullmatch(r"[a-zA-Z0-9_.+-]{1,64}", command):
            answer = "Uso: /man <comando>. Ejemplo: /man grep"
        else:
            answer = f"Manual de {command}:\nhttps://man7.org/linux/man-pages/dir_all_alphabetic.html\nEn GNU/Linux también puedes ejecutar: man {command}"
    bot.send_msg(cid, answer, parse_mode=None)
    return True
