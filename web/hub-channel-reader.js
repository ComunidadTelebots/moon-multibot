(() => {
  'use strict';
  const telegram = () => window.Telegram?.WebApp;
  function safeUrl(value) {
    try { const url = new URL(value, window.location.href); return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password ? url : null; } catch { return null; }
  }
  function open(value) {
    const url = safeUrl(value);
    if (!url) return false;
    if (url.origin === window.location.origin && url.pathname === '/hub.html' && url.searchParams.get('channel') === 'alltech') { showReader(); return true; }
    const tg = telegram();
    if (['t.me', 'www.t.me', 'telegram.me', 'www.telegram.me'].includes(url.hostname.toLowerCase())) {
      url.protocol = 'https:'; url.hostname = 't.me'; url.port = '';
      if (url.pathname.startsWith('/s/')) url.pathname = url.pathname.slice(2);
      try { if (tg?.openTelegramLink) { tg.openTelegramLink(url.href); return true; } } catch {}
    } else {
      try { if (tg?.openLink) { tg.openLink(url.href, { try_instant_view: false }); return true; } } catch {}
    }
    window.open(url.href, '_blank', 'noopener,noreferrer');
    return true;
  }
  window.MoonHubLinks = { open, safeUrl };
  let dialog, list, status, search, controller, previousFocus;
  function element(tag, text, className) { const node = document.createElement(tag); if (text) node.textContent = text; if (className) node.className = className; return node; }
  function closeReader() { controller?.abort(); dialog?.close(); previousFocus?.focus(); }
  function showReader() {
    if (!dialog) {
      const style = element('style');
      style.textContent = `.alltech-reader{width:min(680px,calc(100vw - 28px));max-height:88dvh;margin:auto;box-shadow:0 24px 80px #0008;box-sizing:border-box;border:1px solid #6579a4;border-radius:20px;padding:22px;color:var(--ink,#e7efff);background:var(--card-solid,var(--bg,#111a2d))}.alltech-reader::backdrop{background:#0009}.alltech-reader header{display:flex;justify-content:space-between;gap:12px}.alltech-reader h2{margin:0;font-size:22px}.alltech-reader button,.alltech-reader input{font:inherit;border:1px solid #6579a4;border-radius:10px;padding:10px;background:var(--bg,#111a2d);color:inherit}.alltech-reader input{box-sizing:border-box;width:100%;margin:14px 0}.alltech-reader article{padding:16px 0;border-top:1px solid #8190ad55}.alltech-reader article p{margin:10px 0;white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.6}.alltech-reader a{color:var(--accent,#60c8ff)}.alltech-reader small{opacity:.75}.alltech-reader-nav{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:16px 0}`;
      document.head.append(style);
      dialog = element('dialog', '', 'alltech-reader'); dialog.setAttribute('aria-label', 'Canal AllTech · lector del Hub');
      const header = element('header'); header.append(element('h2', 'Canal TodoSobreAllTech'));
      const close = element('button', 'Cerrar ×'); close.type='button'; close.onclick=closeReader; header.append(close); dialog.append(header);
      dialog.append(element('p', 'Publicaciones del canal sin salir del Hub.'));
      const nav=element('div','','alltech-reader-nav'), channel=element('a','Abrir canal en Telegram ↗'); channel.href='https://t.me/TodoSobreAllTech';channel.onclick=event=>{event.preventDefault();open(channel.href);};
      const reload=element('button','Actualizar');reload.type='button';reload.onclick=load;nav.append(channel,reload);dialog.append(nav);
      search=element('input');search.type='search';search.placeholder='Buscar publicaciones';search.setAttribute('aria-label','Buscar publicaciones de AllTech');dialog.append(search);
      status=element('p');status.setAttribute('role','status');list=element('section');dialog.append(status,list);
      dialog.addEventListener('cancel',()=>{controller?.abort();previousFocus?.focus();});document.body.append(dialog);
    }
    previousFocus=document.activeElement;
    if (!dialog.open) dialog.showModal();
    load();
  }
  async function load() {
    controller?.abort();controller=new AbortController();const active=controller;
    const timer=setTimeout(()=>active.abort(),15000);status.textContent='Cargando publicaciones…';list.replaceChildren();search.value='';search.oninput=null;
    try {
      const response=await fetch('/api/public/network/instant/alltech',{signal:active.signal,credentials:'omit'});
      const data=await response.json();if (!response.ok || !data.ok) throw new Error('unavailable');
      if(active.signal.aborted)return;
      const posts=data.posts || [];
      const render=()=>{
        const q=search.value.trim().toLocaleLowerCase();const rows=posts.filter(p=>String(p.text).toLocaleLowerCase().includes(q));list.replaceChildren();
        status.textContent=`${rows.length} publicaciones${data.stale?' · Copia guardada; el origen no responde':''}`;
        if(!rows.length)list.append(element('p','No hay publicaciones que coincidan.'));
        rows.forEach(post=>{const card=element('article');card.append(element('small',String(post.date||'')+(post.views?` · ${post.views} vistas`:'')),element('p',post.text || 'Publicación multimedia. Ábrela en Telegram para verla.'));const link=element('a','Abrir publicación en Telegram ↗');const url=safeUrl(post.url);if(url && url.hostname==='t.me' && /^\/todosobrealltech\/\d+$/i.test(url.pathname)){link.href=url.href;link.onclick=event=>{event.preventDefault();open(link.href);};card.append(link);}list.append(card);});
      };search.oninput=render;render();
    } catch {
      if(controller===active && dialog.open)status.textContent='No se pueden cargar las publicaciones ahora. Pulsa Actualizar o abre el canal en Telegram.';
    } finally {clearTimeout(timer);}
  }
  window.MoonHubChannelReader={open:showReader};
  document.addEventListener('click',event=>{if(event.defaultPrevented)return;const anchor=event.target.closest?.('a[href]');if(!anchor)return;const url=safeUrl(anchor.href);if(url && ['t.me','www.t.me','telegram.me','www.telegram.me'].includes(url.hostname.toLowerCase())){event.preventDefault();open(url.href);}});
  if(new URLSearchParams(window.location.search).get('channel')==='alltech')showReader();
})();
