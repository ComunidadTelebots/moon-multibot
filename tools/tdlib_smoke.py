"""Real-library routing check without logging in or reading bot tokens.

Mount the existing .env at /run/secrets/tdlib.env, read-only. No application
startup, bot store, user messages or production session directories are used.
"""
import json
import argparse
import os
import tempfile
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dotenv import dotenv_values


def main(bot_username=None):
    settings = dotenv_values('/run/secrets/tdlib.env')
    for key in ('TDLIB_API_ID', 'TDLIB_API_HASH'):
        if not settings.get(key):
            raise RuntimeError('Missing TDLib configuration')
        os.environ[key] = settings[key]
    from core.tdlib_client import TDLibClient
    token = None
    if bot_username:
        token = settings.get('TDLIB_TEST_BOT_TOKEN')
        if not token:
            raise RuntimeError('Configure TDLIB_TEST_BOT_TOKEN for the selected test bot')
        try:
            with urllib.request.urlopen(f'https://api.telegram.org/bot{token}/getMe', timeout=15) as response:
                profile = json.load(response)
        except Exception:
            raise RuntimeError('Could not verify the selected test bot') from None
        if not profile.get('ok') or profile.get('result', {}).get('username', '').lower() != bot_username.lstrip('@').lower():
            raise RuntimeError('Test token does not match the selected bot')
    clients = []
    with tempfile.TemporaryDirectory() as directory:
        try:
            for index in range(1 if token else 2):
                client = TDLibClient(settings['TDLIB_API_ID'], settings['TDLIB_API_HASH'], {},
                                     bot_token=token, db_dir=f'{directory}/session-{index}')
                if not client.start():
                    raise RuntimeError('TDLib library failed to start')
                clients.append(client)
            with ThreadPoolExecutor(max_workers=2) as pool:
                responses = list(pool.map(lambda client: client.send_await({'@type': 'getOption', 'name': 'version'}), clients))
            if any(not response or response.get('@type') != 'optionValueString' for response in responses):
                raise RuntimeError('TDLib version request failed')
            if any(response.get('@client_id') != client._client_id for response, client in zip(responses, clients)):
                raise RuntimeError('TDLib response routed to wrong account')
            if token:
                deadline = time.monotonic() + 60
                while not clients[0].is_ready and time.monotonic() < deadline:
                    time.sleep(0.1)
                if not clients[0].is_ready:
                    raise RuntimeError('Test bot did not reach TDLib authorizationStateReady')
                me = clients[0].send_await({'@type': 'getMe'})
                if not me or me.get('id') != profile['result']['id']:
                    raise RuntimeError('Authenticated account does not match the test bot')
            print(json.dumps({'ok': True, 'clients': len(clients), 'version': responses[0]['value'],
                              'routing_verified': True, 'authenticated': bool(token), 'messages_sent': 0}), flush=True)
        finally:
            for client in clients:
                client.stop()
            deadline = time.monotonic() + 15
            while any(client._auth_state != 'authorizationStateClosed' for client in clients) and time.monotonic() < deadline:
                time.sleep(0.1)
            if any(client._auth_state != 'authorizationStateClosed' for client in clients):
                raise RuntimeError('TDLib close was not confirmed')
            print(json.dumps({'closed_cleanly': True}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bot', help='Expected test bot username; uses only TDLIB_TEST_BOT_TOKEN')
    main(parser.parse_args().bot)
