(() => {
  if (document.getElementById('personal-rss-open')) return;
  const style = document.createElement('style'); style.textContent = `
#personal-rss-open{position:fixed;right:16px;bottom:calc(78px + env(safe-area-inset-bottom));z-index:9000;background:var(--grad,linear-gradient(120deg,#5dcaa5,#22d3ee));color:#04121f;border:1px solid #5dcaa566;border-radius:18px;padding:12px 20px;font:700 14px var(--body,sans-serif);box-shadow:0 8px 30px #0006;cursor:pointer}
#personal-rss-dialog{position:fixed;inset:18px 12px;max-width:860px;margin:0 auto;z-index:10000;overflow:auto;overscroll-behavior:contain;background:var(--bg,#070b14);color:var(--ink,#e9f0fb);color-scheme:dark;border:1px solid var(--line,#ffffff18);border-radius:24px;padding:22px;box-shadow:0 0 0 100vmax #020610c9,0 24px 90px #0009;font:14px/1.55 var(--body,system-ui,sans-serif)}
#personal-rss-dialog[hidden]{display:none}
#personal-rss-dialog h2{font:700 clamp(22px,5vw,30px) var(--display,system-ui,sans-serif);letter-spacing:-.03em;margin:8px 0}
#personal-rss-dialog h3{font-size:18px;margin:26px 0 12px}#personal-rss-dialog h4{grid-column:1/-1;color:var(--cyan,#22d3ee);font-size:12px;text-transform:uppercase;letter-spacing:.09em;margin:14px 0 0}
#personal-rss-dialog p{color:var(--muted,#9aaac2);margin:8px 0;font-size:13px}
#personal-rss-dialog .rss-kicker{color:var(--teal,#5dcaa5);font-size:11px;letter-spacing:.12em;font-weight:700;text-transform:uppercase}
#personal-rss-dialog button,#personal-rss-dialog input,#personal-rss-dialog select{font:inherit;padding:10px 12px;margin:4px 4px 4px 0;border:1px solid var(--line,#ffffff20);border-radius:12px;background:#101a2a;color:var(--ink,#e9f0fb);max-width:100%;box-sizing:border-box;min-height:42px}
#personal-rss-dialog button{cursor:pointer;font-weight:600;background:#5dcaa510;border-color:#5dcaa540;color:var(--teal,#5dcaa5)}
#personal-rss-dialog button:hover{background:#5dcaa528}#personal-rss-dialog button:disabled{opacity:.42;cursor:default}
#personal-rss-dialog :is(button,input,select,a):focus-visible{outline:2px solid var(--cyan,#22d3ee);outline-offset:3px}
#personal-rss-dialog input{width:100%}#personal-rss-dialog input::placeholder{color:#7c8ca6}#personal-rss-dialog select{width:100%}
#personal-rss-dialog label{display:block;color:var(--muted,#9aaac2);font-size:12px;margin-top:18px}
#personal-rss-dialog article{border:1px solid var(--line,#ffffff18);padding:16px;border-radius:16px;margin:4px 0;background:linear-gradient(135deg,#ffffff06,#ffffff02);overflow-wrap:anywhere}
#personal-rss-dialog article b{display:block;font-size:15px}#personal-rss-dialog article p{font-size:12px}
#personal-rss-dialog .rss-catalog{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
#personal-rss-dialog .rss-quota{padding:14px;border:1px solid #22d3ee30;border-radius:14px;background:#22d3ee08;color:var(--ink,#e9f0fb)}
#personal-rss-dialog progress{width:100%;height:7px;accent-color:#5dcaa5;display:block;margin:8px 0 14px}
#personal-rss-dialog form{padding:16px;margin-top:22px;background:#ffffff04;border:1px dashed #ffffff20;border-radius:16px}
#personal-rss-dialog a{color:var(--cyan,#22d3ee)}#personal-rss-dialog [role=alert]{padding:14px;color:#ffd69d;border:1px solid #ffb43c40;border-radius:14px;background:#ffb43c0b}
@media(max-width:540px){#personal-rss-dialog{inset:8px;padding:16px;border-radius:18px}#personal-rss-dialog .rss-catalog{grid-template-columns:1fr}}
@media(prefers-reduced-motion:reduce){#personal-rss-dialog{scroll-behavior:auto}}
`; document.head.append(style);
  const launch=document.createElement('button');launch.id='personal-rss-open';launch.textContent='Mis RSS';document.body.append(launch);
  const dialog=document.createElement('section');dialog.id='personal-rss-dialog';dialog.hidden=true;dialog.setAttribute('role','dialog');dialog.setAttribute('aria-label','Mis RSS');dialog.setAttribute('aria-modal','true');dialog.tabIndex=-1;document.body.append(dialog);
  let busy=false, channels=[], catalogFallback=[], target="me";
  const el=(tag,text,parent=dialog)=>{const n=document.createElement(tag);if(text)n.textContent=text;parent.append(n);return n;};
  async function load(body={}) {
    if(busy)return;busy=true;
    for(const b of dialog.querySelectorAll('button'))b.disabled=true;
    try {
      const r=await fetch(target==='me'?'/api/public/rss/mine':'/api/public/rss/channel',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...body,chat_id:target,initData:window.Telegram?.WebApp?.initData||''})});
      const data=await r.json();if(!r.ok||!data.ok)throw new Error(data.error||'RSS no disponible');render(data);
    }catch(error){if(catalogFallback.length)render({feeds:[],catalog:catalogFallback,quota:null,limit:20});const p=el('p',error.message);p.setAttribute('role','alert');}
    finally{busy=false;for(const b of dialog.querySelectorAll('button'))b.disabled=b.dataset.disabled==='true';}
  }
  function button(label,action,parent=dialog){const b=el('button',label,parent);b.type='button';b.onclick=action;return b;}
  function header(){
    button('Cerrar',()=>{dialog.hidden=true;launch.focus();});el('span','MOONBOT · RSS · BETA').className='rss-kicker';el('h2','Tu selección de noticias');el('p','Fuentes de confianza, organizadas a tu manera.');
    const label=el('label','Enviar novedades a ');const select=el('select',null,label);select.setAttribute('aria-label','Destino RSS');
    const own=el('option','Mi chat privado',select);own.value='me';
    for(const channel of channels){const option=el('option',channel.name,select);option.value=channel.id;}
    select.value=target;select.onchange=()=>{if(!busy){target=select.value;load();}};
  }
  function reader(data){
    const area=el('section');area.setAttribute('aria-label','Lector RSS integrado');el('h3','Leer noticias aquí',area);el('p','Lee sin consumir mensajes de Telegram. Comparte en tus canales con un enlace a nuestra WebApp.',area);
    const select=el('select',null,area);select.setAttribute('aria-label','Fuente del lector');el('option','Selecciona una fuente',select).value='';
    const sources=[...data.catalog,...data.feeds.map(f=>({...f,id:target==='me'?`own:${f.id}`:`channel:${target}:${f.id}`,title:`Suscripción · ${f.title||f.url}`}))];
    for(const source of sources)el('option',source.title,select).value=source.id;
    const actions=el('div',null,area);const status=el('p','',area);status.setAttribute('role','status');const results=el('div',null,area);results.style.maxHeight='60vh';results.style.overflow='auto';
    const readerRequest=async(body)=>{const r=await fetch('/api/public/rss/reader',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...body,initData:window.Telegram?.WebApp?.initData||''})});const payload=await r.json();if(!r.ok||!payload.ok)throw new Error(payload.error||'No se pudo completar la operación');return payload;};
    select.onchange=()=>results.replaceChildren();
    button('Ver noticias',async()=>{
      if(!select.value||busy)return;busy=true;status.textContent='Cargando noticias…';results.replaceChildren();const sourceId=select.value;select.disabled=true;
      try{const news=await readerRequest({action:'read',source_id:sourceId});status.textContent=`${news.entries.length} noticias · ${news.source.title}`;
        const dest=el('select',null,results);dest.setAttribute('aria-label','Canal para compartir noticias');el('option','Compartir en un canal…',dest).value='';for(const channel of channels)el('option',channel.name,dest).value=channel.id;
        if(!channels.length)el('p','Para publicar, añade el bot como administrador del canal con permiso de publicación.',results);
        for(const entry of news.entries){const card=el('article',null,results);el('p',entry.published_at||news.source.title,card);el('b',entry.title,card);if(entry.summary)el('p',entry.summary,card);const link=el('a','Leer original',card);link.href=entry.url;link.target='_blank';link.rel='noopener noreferrer';
          const send=button('Publicar en canal + WebApp',async()=>{if(busy)return;if(!dest.value){status.textContent='Selecciona un canal para publicar.';return;}const name=channels.find(c=>c.id===dest.value)?.name;
            if(!confirm(`Publicar en ${name}:\n\n${entry.title}\n${entry.url}\n\nIncluye un botón para abrir el lector RSS de la WebApp.`))return;
            busy=true;send.disabled=true;try{const result=await readerRequest({action:'share',source_id:sourceId,entry_id:entry.id,channel_id:dest.value});status.textContent=result.already_sent?'Ya estaba publicada en ese canal.':'Publicada con enlace a la WebApp.';}catch(error){status.textContent=error.message;}finally{busy=false;send.disabled=false;}
          },card);send.disabled=!channels.length;
        }
      }catch(error){status.textContent=error.message;}finally{busy=false;select.disabled=false;}
    },actions);
  }
  function render(data){
    dialog.replaceChildren();header();
    el('p',target==='me'?'Recibe novedades en tu chat privado. Las nuevas fuentes se guardan pausadas.':'Publica novedades en el canal seleccionado. Las nuevas fuentes se guardan pausadas.');
    const q=data.quota;if(q){el('p',`Cupo usado hoy: ${q.used} / ${q.limit} noticias · reinicio diario UTC.`).className='rss-quota';const progress=el('progress');progress.max=q.limit;progress.value=Math.min(q.used,q.limit);progress.setAttribute('aria-label','Cupo diario RSS utilizado');
    el('p',q.membership==='member'?'Pertenencia al canal verificada: puedes superar el cupo.':q.membership==='unavailable'?'No se pudo verificar tu pertenencia al canal.':`Para superar ${q.limit} noticias al día, únete a ${q.channel}.`);
    if(q.blocked)el('p','Entregas pausadas por el límite diario. Únete al canal y comprueba tu suscripción.');
    if(q.delivery_uncertain)el('p','Entrega pendiente de revisión por el administrador. No se reintentará automáticamente para evitar duplicados.');
    const a=el('a','Abrir @TodoSobreAllTech');a.href='https://t.me/TodoSobreAllTech';a.target='_blank';a.rel='noopener noreferrer';
    button('Comprobar suscripción',()=>load({action:'verify_membership'}));}
    reader(data);
    el('h3','Explorar RSS por categoría');const search=el('input');search.placeholder='Buscar fuente o tema';search.setAttribute('aria-label','Buscar RSS');const category=el('select');category.setAttribute('aria-label','Categoría RSS');const all=el('option','Todas las categorías',category);all.value='all';
    for(const name of [...new Set(data.catalog.map(i=>i.category))].sort()){const option=el('option',name,category);option.value=name;}
    const catalog=el('div');catalog.className='rss-catalog';function showCatalog(){catalog.replaceChildren();for(const name of [...new Set(data.catalog.map(i=>i.category))].sort()){
      if(category.value!=='all'&&category.value!==name)continue;
      const items=data.catalog.filter(i=>i.category===name&&`${i.title} ${i.category}`.toLowerCase().includes(search.value.toLowerCase()));if(!items.length)continue;el('h4',name,catalog);
      for(const item of items){const row=el('article',null,catalog);el('b',item.title,row);el('p',`${(item.language||'').toUpperCase()} · ${item.provider||'RSS oficial'}`,row);const exists=data.feeds.some(f=>f.url===item.url);const b=button(exists?'Ya añadido':'Suscribirme',()=>load({action:'add',url:item.url,title:item.title}),row);b.disabled=exists;b.dataset.disabled=String(exists);}}
    }search.oninput=showCatalog;category.onchange=showCatalog;showCatalog();
    const form=el('form');const title=el('input',null,form);title.placeholder='Nombre de la fuente';title.setAttribute('aria-label','Nombre de la fuente');title.maxLength=120;
    const url=el('input',null,form);url.type='url';url.required=true;url.maxLength=2000;url.placeholder='https://ejemplo.com/feed.xml';url.setAttribute('aria-label','URL RSS');const submit=el('button','Añadir mi RSS',form);submit.type='submit';form.onsubmit=e=>{e.preventDefault();load({action:'add',url:url.value.trim(),title:title.value.trim()});};
    el('h3',`Mis fuentes (${data.feeds.length}/${data.limit})`);
    if(!data.feeds.length)el('p','Todavía no tienes suscripciones. Selecciona una fuente o añade su URL.');
    for(const feed of data.feeds){const row=el('article');el('b',feed.title||'Fuente RSS',row);el('p',feed.url,row);el('p',`${feed.enabled?'Activa':'Pausada'} · ${feed.published_count||0} entregas · ${feed.error_count||0} errores`,row);button(feed.enabled?'Pausar':'Activar',()=>load({action:'toggle',feed_id:feed.id,enabled:!feed.enabled}),row);button('Eliminar',()=>{if(confirm('¿Eliminar esta suscripción?'))load({action:'delete',feed_id:feed.id});},row);}
    button('Actualizar',()=>load());
  }
  launch.onclick=async()=>{dialog.hidden=false;dialog.focus();dialog.replaceChildren();header();try{const r=await fetch('/api/public/rss/destinations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({initData:window.Telegram?.WebApp?.initData||''})});const data=await r.json();channels=data.channels||[];catalogFallback=data.catalog||[];}catch{channels=[];}dialog.replaceChildren();header();load();};
  if(window.Telegram?.WebApp?.initDataUnsafe?.start_param==='rss') launch.onclick();
  dialog.addEventListener('keydown',e=>{if(e.key==='Escape'){dialog.hidden=true;launch.focus();}if(e.key==='Tab'){const nodes=[...dialog.querySelectorAll('button:not(:disabled),input,a,select')];const first=nodes[0],last=nodes[nodes.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus();}}});
})();
