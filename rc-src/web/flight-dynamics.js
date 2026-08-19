const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
export function createRotorcraftDynamics() {
  const state = { velocity: { x: 0, y: 0, z: -18 }, collective: .52, fuel: 100, verticalSpeed: 0, airspeed: 65, wind: 0 };
  function update(input = {}, dt = 1 / 60) {
    state.collective = clamp(state.collective + ((input.up ? 1 : 0) - (input.down ? 1 : 0)) * dt * .32, 0, 1);
    const proceduralWind = Math.sin((input.time || 0) * .00019) * 6 + Math.sin((input.time || 0) * .000047) * 3;
    const wind = Number.isFinite(input.windSpeed) ? input.windSpeed / 3.6 : proceduralWind;
    state.velocity.y += (state.collective * 15.8 - 8.9 - state.velocity.y * .7) * dt;
    state.velocity.x += (((input.left ? 1 : 0) - (input.right ? 1 : 0)) * 7 + wind * .08 - state.velocity.x * .55) * dt;
    state.velocity.z += (-18 - state.velocity.z) * dt * .35;
    state.fuel = Math.max(0, state.fuel - dt * (.018 + state.collective * .026)); if (!state.fuel) state.collective = Math.max(0, state.collective - dt * .2);
    state.verticalSpeed = state.velocity.y; state.airspeed = Math.hypot(state.velocity.x, state.velocity.z) * 3.6; state.wind = wind;
    return { ...state, velocity: { ...state.velocity } };
  }
  return { state, update };
}
