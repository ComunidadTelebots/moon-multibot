(function (global) {
  const KEY = "moon.transport.achievements.v1";
  const definitions = [
    { id: "first_km", icon: "🛣️", name: "Primer kilómetro", test: s => s.distance >= 1 },
    { id: "road_veteran", icon: "🌍", name: "Ruta de 100 km", test: s => s.distance >= 100 },
    { id: "highway", icon: "⚡", name: "Velocidad de crucero", test: s => s.speed >= 90 },
    { id: "loader", icon: "📦", name: "Carga completa", test: s => s.loaded >= 3 },
    { id: "rain_driver", icon: "🌧️", name: "Conductor bajo la lluvia", test: s => s.rain && s.speed >= 40 },
    { id: "night_driver", icon: "🌙", name: "Ruta nocturna", test: s => s.night && s.speed >= 40 },
    { id: "convoy", icon: "🚛", name: "En compañía", test: s => s.convoyPlayers >= 2 },
    { id: "careful", icon: "🛡️", name: "Conducción impecable", test: s => s.distance >= 25 && s.damage === 0 },
  ];
  const load = () => { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch { return {}; } };
  let unlocked = load(), listener = null;
  function update(state) { const fresh=[]; for(const item of definitions)if(!unlocked[item.id]&&item.test(state)){unlocked[item.id]={at:Date.now()};fresh.push(item)}if(fresh.length){localStorage.setItem(KEY,JSON.stringify(unlocked));listener?.(fresh)}return fresh }
  function list(){return definitions.map(item=>({...item,unlocked:Boolean(unlocked[item.id]),at:unlocked[item.id]?.at||0}))}
  function onUnlock(fn){listener=fn}
  global.TransportAchievements={update,list,onUnlock};
})(window);
