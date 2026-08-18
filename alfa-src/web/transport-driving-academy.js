const LESSONS = [
  { id: "eco", name: "Conducción eficiente", duration: 150, maxSpeed: 82 },
  { id: "precision", name: "Precisión sin colisiones", duration: 120, maxSpeed: 55 },
  { id: "rain", name: "Control sobre mojado", duration: 135, maxSpeed: 65, weather: "rain" },
];
export function createDrivingAcademy() {
  let active = null;
  const best = JSON.parse(localStorage.getItem("moon.transport.academy.v1") || "{}");
  function start(id = "eco") { const lesson = LESSONS.find(item => item.id === id) || LESSONS[0]; active = { ...lesson, elapsed: 0, distance: 0, collisions: 0, speeding: 0, harsh: 0, interior: true, done: false }; return { ...active }; }
  function update(dt, state = {}) {
    if (!active || active.done) return active;
    active.elapsed += dt; active.distance += Math.max(0, state.speed || 0) * dt / 3.6;
    if ((state.speed || 0) > active.maxSpeed + 3) active.speeding += dt;
    if ((state.acceleration || 0) < -4.2 || Math.abs(state.lateralG || 0) > .42) active.harsh += dt;
    if (state.collision) active.collisions += 1; if (!state.interior) active.interior = false;
    if (active.elapsed >= active.duration) { active.stars = Math.max(0, 3 - Number(active.collisions > 0) - Number(active.speeding > 5) - Number(active.harsh > 4)); active.done = true; active.score = Math.max(0, Math.round(active.distance - active.speeding * 8 - active.harsh * 10 - active.collisions * 250)); best[active.id] = Math.max(best[active.id] || 0, active.stars); localStorage.setItem("moon.transport.academy.v1", JSON.stringify(best)); }
    return { ...active };
  }
  return { lessons: LESSONS, best, start, update, get state() { return active; } };
}
