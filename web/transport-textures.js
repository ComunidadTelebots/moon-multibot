function textureCanvas(size, base, painter) {
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext("2d", { alpha: false });
  ctx.fillStyle = base;
  ctx.fillRect(0, 0, size, size);
  painter(ctx, size);
  return canvas;
}

// Reproducible noise keeps the road from changing every time the camera reloads.
function randomFactory(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function speckles(ctx, size, random, count, colors, radius = 1) {
  for (let i = 0; i < count; i += 1) {
    const r = 0.25 + random() * radius;
    ctx.fillStyle = colors[(random() * colors.length) | 0];
    ctx.fillRect(random() * size, random() * size, r, r);
  }
}

function scalarMap(size, base, seed, detail, streaks = false) {
  const random = randomFactory(seed);
  return textureCanvas(size, `rgb(${base},${base},${base})`, (ctx, s) => {
    speckles(ctx, s, random, detail, ["#686868", "#808080", "#929292", "#ababab"], 2.2);
    if (!streaks) return;
    ctx.globalAlpha = 0.22;
    ctx.lineWidth = Math.max(1, s / 512);
    for (let i = 0; i < 16; i += 1) {
      ctx.strokeStyle = random() > 0.5 ? "#555" : "#bbb";
      ctx.beginPath();
      const x = random() * s;
      ctx.moveTo(x, 0);
      ctx.bezierCurveTo(x + (random() - 0.5) * 35, s * 0.35, x + (random() - 0.5) * 55, s * 0.7, x, s);
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
  });
}

export function createProceduralTransportTextures(T, qualityLevel = 2) {
  const quality = Math.max(0, Math.min(3, Number(qualityLevel) || 0));
  const size = quality >= 3 ? 1024 : quality >= 2 ? 512 : quality >= 1 ? 256 : 128;
  const detail = Math.round(size * (quality >= 2 ? 9 : 5));
  const textures = [];
  const make = (canvas, repeatX, repeatY = repeatX, color = true) => {
    const texture = new T.CanvasTexture(canvas);
    texture.wrapS = texture.wrapT = T.RepeatWrapping;
    texture.repeat.set(repeatX, repeatY);
    if (color && T.SRGBColorSpace) texture.colorSpace = T.SRGBColorSpace;
    else if (!color && T.NoColorSpace) texture.colorSpace = T.NoColorSpace;
    texture.anisotropy = quality >= 3 ? 12 : quality >= 2 ? 8 : quality >= 1 ? 4 : 1;
    texture.generateMipmaps = quality > 0;
    textures.push(texture);
    return texture;
  };

  const asphaltRandom = randomFactory(7142);
  const asphalt = make(textureCanvas(size, "#383b3d", (ctx, s) => {
    speckles(ctx, s, asphaltRandom, detail, ["#202326", "#2c3032", "#4b4d4d", "#65625c"], 2.4);
    ctx.globalAlpha = 0.28;
    ctx.lineWidth = Math.max(0.7, s / 700);
    for (let i = 0; i < 13; i += 1) {
      ctx.strokeStyle = i % 3 ? "#171a1b" : "#77746b";
      ctx.beginPath();
      const x = asphaltRandom() * s;
      ctx.moveTo(x, 0);
      ctx.bezierCurveTo(x - 15, s * 0.3, x + 24, s * 0.66, x + (asphaltRandom() - 0.5) * 40, s);
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
  }), 3, 45);
  const asphaltRoughness = make(scalarMap(size, 205, 9981, detail, true), 3, 45, false);
  const asphaltBump = make(scalarMap(size, 126, 5931, detail, true), 3, 45, false);

  const grassRandom = randomFactory(4419);
  const grass = make(textureCanvas(size, "#527a3c", (ctx, s) => {
    speckles(ctx, s, grassRandom, detail, ["#294f2a", "#3f6932", "#658847", "#859b54", "#7b7139"], 2.8);
    ctx.globalAlpha = 0.35;
    for (let i = 0; i < s; i += 3) {
      ctx.fillStyle = i % 2 ? "#314f2b" : "#88a45c";
      ctx.fillRect(grassRandom() * s, grassRandom() * s, 1, 3 + grassRandom() * 7);
    }
    ctx.globalAlpha = 1;
  }), 18, 48);
  const groundRoughness = make(scalarMap(size, 222, 2271, detail, false), 18, 48, false);

  const metalRandom = randomFactory(8137);
  const metal = make(textureCanvas(size, "#c9ced0", (ctx, s) => {
    const gradient = ctx.createLinearGradient(0, 0, s, 0);
    gradient.addColorStop(0, "#758087"); gradient.addColorStop(0.18, "#e3e8e9");
    gradient.addColorStop(0.55, "#aeb6b9"); gradient.addColorStop(0.82, "#eef1f1"); gradient.addColorStop(1, "#707b80");
    ctx.fillStyle = gradient; ctx.fillRect(0, 0, s, s);
    ctx.globalAlpha = 0.2;
    for (let x = 0; x < s; x += 5) { ctx.fillStyle = x % 10 ? "#fff" : "#26343b"; ctx.fillRect(x, 0, 1, s); }
    speckles(ctx, s, metalRandom, size * 2, ["#ffffff", "#263238", "#8a512f"], 1.2);
    ctx.globalAlpha = 1;
  }), 2, 4);
  const metalRoughness = make(scalarMap(size, 105, 7348, size * 3, true), 2, 4, false);

  const paintRandom = randomFactory(1024);
  const paint = make(textureCanvas(size, "#18a99f", (ctx, s) => {
    const gradient = ctx.createLinearGradient(0, 0, s, 0);
    gradient.addColorStop(0, "#075e61"); gradient.addColorStop(0.38, "#21c4b8");
    gradient.addColorStop(0.62, "#2bd1c3"); gradient.addColorStop(1, "#064f54");
    ctx.fillStyle = gradient; ctx.fillRect(0, 0, s, s);
    ctx.globalAlpha = 0.08;
    speckles(ctx, s, paintRandom, size * 3, ["#fff", "#003c3c"], 1.4);
    ctx.globalAlpha = 1;
  }), 1, 1);
  const paintRoughness = make(scalarMap(size, 65, 3255, size * 2), 1, 1, false);

  const tyreRandom = randomFactory(9027);
  const tyre = make(textureCanvas(size, "#17191a", (ctx, s) => {
    ctx.strokeStyle = "#343738"; ctx.lineWidth = Math.max(2, s / 32);
    for (let x = -s; x < s * 2; x += s / 8) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x + s * 0.5, s); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(x + s * 0.5, 0); ctx.lineTo(x, s); ctx.stroke();
    }
    speckles(ctx, s, tyreRandom, size * 2, ["#090a0a", "#292b2b", "#4b443c"], 1.3);
  }), 4, 2);
  const tyreBump = make(scalarMap(size, 116, 4871, size * 4, true), 4, 2, false);

  const concreteRandom = randomFactory(6630);
  const concrete = make(textureCanvas(size, "#999b96", (ctx, s) => {
    speckles(ctx, s, concreteRandom, detail, ["#747672", "#8b8c87", "#b3b1a8", "#cbc7ba"], 2.8);
    ctx.strokeStyle = "#5c5d59"; ctx.globalAlpha = 0.35; ctx.lineWidth = Math.max(1, s / 380);
    for (let i = 0; i < 5; i += 1) { const p = (i * s) / 4; ctx.beginPath(); ctx.moveTo(p, 0); ctx.lineTo(p, s); ctx.stroke(); }
    ctx.globalAlpha = 1;
  }), 6, 12);
  const concreteRoughness = make(scalarMap(size, 218, 9001, detail), 6, 12, false);

  const sign = make(textureCanvas(size, "#1d6297", (ctx, s) => {
    const edge = Math.max(5, s * 0.045);
    ctx.strokeStyle = "#f4f6ef"; ctx.lineWidth = edge; ctx.strokeRect(edge, edge, s - edge * 2, s - edge * 2);
    const shine = ctx.createLinearGradient(0, 0, s, s);
    shine.addColorStop(0, "rgba(255,255,255,.24)"); shine.addColorStop(0.45, "rgba(255,255,255,0)"); shine.addColorStop(1, "rgba(0,20,45,.18)");
    ctx.fillStyle = shine; ctx.fillRect(0, 0, s, s);
  }), 1, 1);

  return {
    // Original keys remain intact for existing callers.
    asphalt, grass, metal, paint,
    asphaltRoughness, asphaltBump, groundRoughness,
    metalRoughness, paintRoughness, tyre, tyreBump,
    concrete, concreteRoughness, sign,
    maps: {
      asphalt: { map: asphalt, roughnessMap: asphaltRoughness, bumpMap: asphaltBump, bumpScale: 0.055 },
      ground: { map: grass, roughnessMap: groundRoughness },
      metal: { map: metal, roughnessMap: metalRoughness },
      paint: { map: paint, roughnessMap: paintRoughness },
      tyre: { map: tyre, bumpMap: tyreBump, bumpScale: 0.035 },
      concrete: { map: concrete, roughnessMap: concreteRoughness },
      sign: { map: sign },
    },
    dispose() { textures.forEach((texture) => texture.dispose()); },
  };
}
