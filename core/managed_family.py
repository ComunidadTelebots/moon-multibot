"""Verified managed-bot inventory. Credentials stay encrypted; no plugin execution."""
import threading
import time
from urllib.parse import urlencode

PLANS = (
    ('CintiaBot', 'CintiaGroupBackup01Bot', 'groups'),
    ('cintiaandrea_bot', 'CintiaAndreaGroupBackup01Bot', 'groups'),
)
TASKS = {'groups':'Administración de grupos', 'rss':'Noticias RSS', 'moderation':'Moderación', 'automation':'Bienvenidas y automatizaciones'}

class ManagedFamily:
    def __init__(self, db, get_bots, encrypt):
        self.db, self.get_bots, self.encrypt = db, get_bots, encrypt
        self.lock = threading.RLock()
        self.rows = []
        self.checked_at = None

    def sync(self):
        bots = {str(getattr(b,'bot_username','')).lstrip('@').lower():b for b in self.get_bots()}
        rows=[]
        for parent, username, task in PLANS:
            row={'parent':parent,'username':username,'task':task,'status':'parent_unavailable','verified_groups':0,'checked_groups':0,'total_groups':0,'automatic_failover':False}
            bot=bots.get(parent.lower())
            if bot:
                try:
                    chat=bot.api_call('getChat',{'chat_id':'@'+username})
                    identity=chat.get('result',{}).get('id') if chat.get('ok') else None
                    if not identity:row['status']='not_found'
                    else:
                        result=bot.api_call('getManagedBotToken',{'user_id':identity})
                        token=result.get('result') if result.get('ok') else None
                        if not isinstance(token,str) or not token.startswith(str(identity)+':'):
                            row['status']='relationship_unverified'
                        else:
                            # A successful export proves this parent manages this identity.
                            key='MANAGED_CHILD_SECRET_'+str(identity)
                            self.db.set(key,{'token':self.encrypt(token),'encrypted':True})
                            row.update(id=str(identity),status='registered_standby')
                            if parent.lower() == 'cintiabot' and identity == 8777193547:
                                from core.managed_group_onboarding import prepare_group
                                prepare_group(bot, self.db)
                            ids=sorted({str(x) for x in self.db.get('CHATS_'+bot.token,[]) if str(x).startswith('-')})
                            row['total_groups']=len(ids)
                            old=self.db.get('MANAGED_CHILD_PERMISSIONS_'+str(identity),{}) or {}
                            cursor=int(old.get('cursor',0))%max(1,len(ids))
                            checks=old.get('checks',{})
                            for cid in ids[cursor:cursor+8]:
                                member=bot.api_call('getChatMember',{'chat_id':cid,'user_id':identity})
                                rights=member.get('result',{}) if member.get('ok') else {}
                                checks[cid]={'ready':rights.get('status') in ('administrator','creator') and bool(rights.get('can_delete_messages')) and bool(rights.get('can_restrict_members')), 'at':time.time()}
                            checks={cid:value for cid,value in checks.items() if cid in ids and time.time()-value.get('at',0)<1800}
                            self.db.set('MANAGED_CHILD_PERMISSIONS_'+str(identity),{'cursor':cursor+8 if cursor+8<len(ids) else 0,'checks':checks})
                            row['checked_groups']=len(checks);row['verified_groups']=sum(bool(v.get('ready')) for v in checks.values())
                            row['status']='permissions_verified' if row['verified_groups'] else 'awaiting_group_permissions'
                except Exception:row['status']='verification_unavailable'
            rows.append(row)
        with self.lock:self.rows=rows;self.checked_at=time.time()

    def snapshot(self):
        with self.lock:
            return {'checked_at':self.checked_at,'children':[dict(r) for r in self.rows], 'automatic_failover':False}

    def start(self):
        def loop():
            while True:
                try:self.sync()
                except Exception:pass
                time.sleep(120)
        threading.Thread(target=loop,name='managed-family-inventory',daemon=True).start()

_family = None

def install_family(db,get_bots,encrypt):
    global _family
    _family=ManagedFamily(db,get_bots,encrypt);_family.start()
    return _family

def family_snapshot():
    return _family.snapshot() if _family else {'children':[], 'checked_at':None,'automatic_failover':False}
