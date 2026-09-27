"""Explicitly scoped group-backup onboarding; no automatic moderation or invitations."""
GROUP_ID = '-1001398334749'
CHILD_ID = 8777193547
CHILD_NAME = 'CintiaGroupBackup01Bot'
PARENT_NAME = 'cintiabot'
ADD_URL = 'https://t.me/CintiaGroupBackup01Bot?startgroup=backup&admin=delete_messages+restrict_members'


def prepare_group(parent, db, *, send_prompt=False):
    if str(getattr(parent,'bot_username','')).lstrip('@').lower() != PARENT_NAME:
        return 'wrong_parent'
    key='MANAGED_GROUP_PREPARATION_'+GROUP_ID
    def save(status):
        db.set(key,{'status':status,'child':CHILD_NAME,'automatic_failover':False})
        return status
    own=parent.api_call('getChatMember',{'chat_id':GROUP_ID,'user_id':str(parent.token).split(':',1)[0]})
    child=parent.api_call('getChatMember',{'chat_id':GROUP_ID,'user_id':CHILD_ID})
    if not own.get('ok') or not child.get('ok'):return save('verification_unavailable')
    rights=child.get('result',{});parent_rights=own.get('result',{})
    if rights.get('status') in ('left','kicked'):
        marker='MANAGED_GROUP_INVITATION_'+GROUP_ID
        if send_prompt and not db.get(marker):
            db.set(marker,{'state':'pending'})
            try:
                result=parent.api_call('sendMessage',{'chat_id':GROUP_ID,'text':'Preparación del respaldo de administración: añade a @CintiaGroupBackup01Bot con este botón. Después comprobaré sus permisos para borrar mensajes y restringir miembros. El relevo automático todavía no está activado.','reply_markup':{'inline_keyboard':[[{'text':'Añadir respaldo al grupo','url':ADD_URL}]]}})
                if result.get('ok'):db.set(marker,{'state':'sent','message_id':result.get('result',{}).get('message_id')})
            except Exception:pass
        return save('awaiting_addition')
    if rights.get('status') in ('administrator','creator') and rights.get('can_delete_messages') and rights.get('can_restrict_members'):
        return save('permissions_ready')
    if rights.get('status') != 'member':return save('manual_permissions_required')
    required=('can_promote_members','can_delete_messages','can_restrict_members')
    if parent_rights.get('status')!='administrator' or not all(parent_rights.get(p) for p in required):return save('parent_permissions_missing')
    # The caller must have verified this managed relationship before granting rights.
    token=parent.api_call('getManagedBotToken',{'user_id':CHILD_ID})
    if not token.get('ok') or not str(token.get('result','')).startswith(str(CHILD_ID)+':'):return save('relationship_unverified')
    grant=parent.api_call('promoteChatMember',{'chat_id':GROUP_ID,'user_id':CHILD_ID,'can_delete_messages':True,'can_restrict_members':True,'can_promote_members':False,'can_invite_users':False,'can_change_info':False,'can_pin_messages':False,'can_manage_video_chats':False,'can_manage_topics':False,'is_anonymous':False})
    if not grant.get('ok'):return save('promotion_unconfirmed')
    checked=parent.api_call('getChatMember',{'chat_id':GROUP_ID,'user_id':CHILD_ID})
    rights=checked.get('result',{}) if checked.get('ok') else {}
    return save('permissions_ready' if rights.get('status')=='administrator' and rights.get('can_delete_messages') and rights.get('can_restrict_members') else 'promotion_unconfirmed')
