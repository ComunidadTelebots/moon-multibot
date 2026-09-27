import os
from dotenv import dotenv_values

settings = dotenv_values('/run/secrets/tdlib.env')
for source, target in [('TDLIB_API_ID', 'TELEGRAM_API_ID'), ('TDLIB_API_HASH', 'TELEGRAM_API_HASH')]:
    value = settings.get(source) or os.environ.get(target)
    if not value:
        raise SystemExit('Missing TDLib application credentials')
    os.environ[target] = value
os.execv('/usr/local/bin/telegram-bot-api', ['telegram-bot-api', '--http-port=8081',
           '--dir=/var/lib/telegram-bot-api', '--verbosity=0'])
