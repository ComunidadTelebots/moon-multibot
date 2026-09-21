"""Exercise only the configured test bot against the official local gateway."""
import argparse
import json
import os
import time
import hashlib
from dotenv import dotenv_values
from core.telegram_api import telegram_api_call, create_telegram_session
from core.bot_endpoint import bot_api_url
from core.persistent_inbox import PersistentInbox


def main(expected, origin, migrate, plugin_test, inbox_path):
    settings = dotenv_values('/run/secrets/tdlib.env')
    token = settings.get('TDLIB_TEST_BOT_TOKEN')
    if not token:
        raise RuntimeError('Missing dedicated test bot token')
    session = create_telegram_session()
    cloud = f'https://api.telegram.org/bot{token}/'
    os.environ['MOON_LOCAL_BOT_IDS'] = token.split(':', 1)[0]
    os.environ['MOON_BOT_API_URL'] = origin
    local = bot_api_url(token)
    # Identity is checked before any migration or plugin response.
    profile = telegram_api_call(session, cloud if migrate else local, 'getMe', {}, timeout=60)
    if not profile.get('ok') or profile.get('result', {}).get('username', '').lower() != expected.lstrip('@').lower():
        raise RuntimeError('Test bot identity verification failed')
    if migrate:
        response = telegram_api_call(session, cloud, 'logOut', {}, timeout=15)
        if not response.get('ok'):
            raise RuntimeError('Test bot cloud logout failed')
        print(json.dumps({'test_bot_moved_from_cloud': True}), flush=True)
    result = telegram_api_call(session, local, 'getMe', {}, timeout=60)
    if not result.get('ok') or result.get('result', {}).get('id') != profile['result']['id']:
        raise RuntimeError('Local gateway identity verification failed')
    for method in ('getWebhookInfo', 'getMyCommands', 'getMyDescription'):
        result = telegram_api_call(session, local, method, {}, timeout=15)
        if not result.get('ok'):
            raise RuntimeError(f'Gateway contract failed for {method}')
    print(json.dumps({'gateway_identity_verified': True, 'read_contracts_verified': 4}), flush=True)
    if not plugin_test:
        return
    from plugins.calculator import handle_command
    class PluginBot:
        sends = 0
        def send_msg(self, chat_id, text):
            result = telegram_api_call(session, local, 'sendMessage', {
                'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}, timeout=15, _retries=1)
            if not result.get('ok'):
                raise RuntimeError('Plugin response was not confirmed; do not blindly retry')
            self.sends += 1
            return result
    bot = PluginBot()
    inbox = PersistentInbox(inbox_path)
    since = int(time.time())
    offset = 0
    deadline = time.monotonic() + 180
    print(json.dumps({'waiting_for_private_command': '/calculadora 2+2', 'timeout_seconds': 180}), flush=True)
    while time.monotonic() < deadline:
        result = telegram_api_call(session, local, 'getUpdates', {'offset': offset, 'timeout': 10, 'allowed_updates': ['message']}, timeout=20)
        if not result.get('ok'):
            raise RuntimeError('Gateway polling failed')
        for update in result.get('result', []):
            offset = max(offset, update['update_id'] + 1)
            message = update.get('message', {})
            if (message.get('date', 0) >= since and message.get('chat', {}).get('type') == 'private' and
                    message.get('text', '').strip() == '/calculadora 2+2'):
                partition = hashlib.sha256(f"{profile['result']['id']}:{message['chat']['id']}".encode()).hexdigest()
                inbox.enqueue(f"{profile['result']['id']}:{update['update_id']}", partition, message)
                job = inbox.claim('calculator-test-worker')
                if not job or not inbox.start(job['id'], 'calculator-test-worker', job['lease']):
                    raise RuntimeError('Queue has no runnable job; inspect pending or uncertain work')
                message = job['payload']
                try:
                    handled = handle_command(bot, str(message['chat']['id']), str(message['from']['id']), message['text'], 'user')
                except Exception:
                    inbox.finish(job['id'], 'calculator-test-worker', job['lease'], success=False)
                    raise
                if not handled or bot.sends != 1:
                    raise RuntimeError('Calculator plugin did not produce exactly one confirmed response')
                if not inbox.finish(job['id'], 'calculator-test-worker', job['lease']):
                    raise RuntimeError('Queue acknowledgement failed; do not replay without reconciliation')
                print(json.dumps({'plugin': 'calculator', 'received': True, 'handled': True, 'responses_confirmed': bot.sends,
                                  'queue': inbox.stats()}), flush=True)
                return
    raise RuntimeError('No private plugin test command received')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bot', required=True)
    parser.add_argument('--origin', required=True)
    parser.add_argument('--migrate', action='store_true')
    parser.add_argument('--plugin-test', action='store_true')
    parser.add_argument('--inbox', default='/tmp/gateway-test-inbox.db')
    args = parser.parse_args()
    main(args.bot, args.origin, args.migrate, args.plugin_test, args.inbox)
