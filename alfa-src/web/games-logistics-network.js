(function (global) {
  const KEY = "moon.games.logistics.v1", stages = ["warehouse", "rail", "airport", "seaport", "delivered"];
  const labels = { warehouse: "Almacén", rail: "Terminal ferroviaria", airport: "Aeropuerto", seaport: "Puerto marítimo", delivered: "Destino final" };
  const cargoNames = ["Componentes tecnológicos", "Medicinas", "Alimentos refrigerados", "Maquinaria", "Material de emergencia"];
  const read = () => { try { return JSON.parse(localStorage.getItem(KEY)) || { shipments: [], delivered: 0 }; } catch { return { shipments: [], delivered: 0 }; } };
  const write = data => { localStorage.setItem(KEY, JSON.stringify(data)); global.dispatchEvent(new CustomEvent("moon-logistics-change", { detail: data })); return data; };
  function create(origin = "Puerto Logístico") { const data = read(), shipment = { id: `cargo_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`, cargo: cargoNames[Math.floor(Math.random() * cargoNames.length)], origin, stage: "warehouse", progress: 0, createdAt: Date.now() }; data.shipments.push(shipment); write(data); return shipment; }
  function available(stage) { return read().shipments.filter(item => item.stage === stage); }
  function advance(id, expectedStage) { const data = read(), item = data.shipments.find(row => row.id === id); if (!item || item.stage !== expectedStage) return null; const index = stages.indexOf(item.stage); item.stage = stages[index + 1] || "delivered"; item.progress = index + 1; item.updatedAt = Date.now(); if (item.stage === "delivered") data.delivered = (data.delivered || 0) + 1; write(data); return item; }
  function summary() { const data = read(); return { ...data, active: data.shipments.filter(x => x.stage !== "delivered").length, labels }; }
  global.MoonLogistics = { create, available, advance, summary, labels, stages };
})(window);
