(function (global) {
  const OPERATIONS = [
    { id: "medical", name: "Corredor médico urgente", roles: ["truck", "air"], target: { x: 80, z: -180 }, reward: 2400 },
    { id: "wildfire", name: "Incendio en zona forestal", roles: ["helicopter", "truck"], target: { x: -145, z: -260 }, reward: 3100 },
    { id: "harbour", name: "Emergencia en terminal marítima", roles: ["ship", "helicopter"], target: { x: 190, z: 310 }, reward: 2800 },
    { id: "intermodal", name: "Entrega intermodal contrarreloj", roles: ["truck", "train", "plane", "ship"], target: { x: 25, z: 390 }, reward: 5200 },
  ];
  const normalize = row => ({ ...row, role: row.vehicle || ({ air: "plane", sea: "ship", rail: "train" }[row.game] || row.game), z: Number(row.z ?? row.y ?? 0) });
  const hash = value => [...String(value)].reduce((sum, char) => ((sum * 31) + char.charCodeAt(0)) >>> 0, 2166136261);
  function create({ duration = 300 } = {}) {
    function get(state, now = Date.now()) {
      if (!state?.joined || !state.room) return null;
      const cycle = Math.floor(now / (duration * 1000)), operation = OPERATIONS[(hash(state.room) + cycle) % OPERATIONS.length];
      const participants = [...(state.players || []), ...(state.ai || [])].map(normalize);
      const roleState = operation.roles.map(role => { const candidates = participants.filter(row => row.role === role || (role === "air" && ["plane", "helicopter"].includes(row.role))); const nearest = candidates.sort((a,b)=>Math.hypot(a.x-operation.target.x,a.z-operation.target.z)-Math.hypot(b.x-operation.target.x,b.z-operation.target.z))[0]; const distance = nearest ? Math.hypot(nearest.x-operation.target.x,nearest.z-operation.target.z) : Infinity; return { role, ready: distance < 90, distance, player: nearest || null }; });
      const ready = roleState.filter(item => item.ready).length, remaining = duration - Math.floor((now / 1000) % duration);
      return { ...operation, cycle, remaining, roleState, ready, complete: ready === operation.roles.length, progress: ready / operation.roles.length };
    }
    return { operations: OPERATIONS, get };
  }
  global.MoonSharedOperations = { create, operations: OPERATIONS };
})(window);
