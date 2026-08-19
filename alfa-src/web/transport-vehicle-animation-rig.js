/** Animates vehicle parts that are not already owned by the detailed cabin,
 * physics or enhancement systems. It consumes their state without re-simulating it. */
export function createVehicleAnimationRig(vehicle) {
  const parts = { steering: [], seats: [], busDoors: [], stretcher: [], shutters: [] };
  const managedCabin = Boolean(vehicle?.userData?.updateCabinControls);
  vehicle?.traverse?.(object => {
    if (!managedCabin && object.name === "steering_wheel") parts.steering.push(object);
    if (/driver_seat|passenger_seat|patient_bench/.test(object.name)) parts.seats.push(object);
    if (/bus_front_door_(glass|vertical_frame)/.test(object.name)) parts.busDoors.push(object);
    if (object.name === "stretcher") parts.stretcher.push(object);
    if (object.name === "fire_roller_shutter") parts.shutters.push(object);
    object.userData.animationRest ??= { x: object.position.x, y: object.position.y, z: object.position.z, rz: object.rotation.z };
  });
  let doorAmount = 0;
  function update({ dt = 0, time = 0, steering = 0, speed = 0, suspension = 0, parking = false, siren = false } = {}) {
    const blend = Math.min(1, Math.max(0, dt) * 8), vibration = Math.sin(time * .045) * Math.min(.012, speed * .00011);
    parts.steering.forEach(part => { part.rotation.z += (-steering * .72 - part.rotation.z) * blend; });
    parts.seats.forEach((part, index) => { const rest=part.userData.animationRest; part.position.y += (rest.y+suspension*.42+vibration*(index?-.45:1)-part.position.y)*blend; });
    doorAmount += ((parking && speed < .5 ? 1 : 0) - doorAmount) * Math.min(1, dt * 3.5);
    parts.busDoors.forEach((part, index) => { const rest=part.userData.animationRest, side=index%2?1:-1; part.position.z += (rest.z+side*doorAmount*.48-part.position.z)*blend; part.rotation.y=side*doorAmount*.32; });
    parts.stretcher.forEach(part => { const rest=part.userData.animationRest; part.position.z=rest.z+(siren?Math.sin(time*.008)*.025:0); });
    parts.shutters.forEach((part,index) => { const rest=part.userData.animationRest; part.position.y=rest.y+(parking&&speed<.5&&index===0?Math.sin(Math.min(1,doorAmount)*Math.PI)*.5:0); });
  }
  return { update, get counts(){ return Object.fromEntries(Object.entries(parts).map(([key,value])=>[key,value.length])); } };
}
