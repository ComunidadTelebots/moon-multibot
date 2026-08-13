(function (global) {
  const id = sessionStorage.getItem("moon.convoy.player") || `local-${Math.random().toString(36).slice(2, 9)}`;
  sessionStorage.setItem("moon.convoy.player", id);
  const channel = "BroadcastChannel" in global ? new BroadcastChannel("moon-games-convoy") : null;
  const state = { joined: false, room: localStorage.getItem("moon.convoy.room") || "", you: id, players: [], ai: [], mode: "local", error: "" };
  let snapshot = { game: "hub", x: 0, y: 0, speed: 0, heading: 0, cargo: "" }, timer = null, listener = null;
  const initData = () => { try { return parent.Telegram?.WebApp?.initData || global.Telegram?.WebApp?.initData || ""; } catch { return ""; } };
  channel && (channel.onmessage = event => { const row = event.data; if (row?.room === state.room && row.id !== id) { const found = state.players.find(p => p.id === row.id); found ? Object.assign(found, row) : state.players.push(row); listener?.(state); } });
  async function remote(action) { const response = await fetch("/api/public/games/convoy", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action, room: state.room, initData: initData(), ...snapshot }) }); const data = await response.json(); if (!data.ok) throw new Error(data.error || "Convoy no disponible"); Object.assign(state, data, { joined: true, mode: "online", error: "" }); localStorage.setItem("moon.convoy.room", data.room); listener?.(state); }
  function localTick() { const row = { id, name: "Jugador local", room: state.room, ...snapshot, seen: Date.now() }; channel?.postMessage(row); state.players = [row, ...state.players.filter(p => p.id !== id && Date.now()-(p.seen||0)<5000)]; const t=Date.now()/1000; state.ai=[0,1,2,3].map((n)=>({id:`local-ai-${n}`,name:["Aster IA","Expreso IA","CargoJet IA","Marina IA"][n],game:["truck","rail","air","sea"][n],x:Math.sin(t*(.18+n*.03)+n)*260,y:Math.cos(t*.14+n)*420,speed:55+n*18,heading:t*.2+n,ai:true})); listener?.(state); }
  async function join(room = "") { state.room = String(room || state.room || Math.random().toString(36).slice(2,8)).toUpperCase(); try { if (initData()) await remote("join"); else { state.joined=true; state.mode="local"; localStorage.setItem("moon.convoy.room",state.room); localTick(); } } catch(error) { state.error=error.message; state.joined=true; state.mode="local"; localTick(); } clearInterval(timer); timer=setInterval(()=>{ if(!state.joined)return; state.mode==="online"?remote("update").catch(e=>{state.error=e.message}):localTick(); },700); return state; }
  function update(data) { Object.assign(snapshot, data); }
  function onChange(fn) { listener=fn; fn(state); }
  function leave(){clearInterval(timer);timer=null;state.joined=false;state.players=[];state.ai=[];listener?.(state)}
  global.MoonConvoy={state,join,update,onChange,leave};
})(window);
