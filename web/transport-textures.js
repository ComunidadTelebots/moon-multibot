function textureCanvas(size, base, painter) {
  const canvas = document.createElement("canvas"); canvas.width = canvas.height = size;
  const ctx = canvas.getContext("2d"); ctx.fillStyle = base; ctx.fillRect(0, 0, size, size); painter(ctx, size);
  return canvas;
}

export function createProceduralTransportTextures(T, qualityLevel = 2) {
  const size = qualityLevel >= 3 ? 1024 : qualityLevel >= 2 ? 512 : 256;
  const make = (canvas, rx, ry = rx) => { const t = new T.CanvasTexture(canvas); t.wrapS = t.wrapT = T.RepeatWrapping; t.repeat.set(rx, ry); t.colorSpace = T.SRGBColorSpace; t.anisotropy = qualityLevel >= 2 ? 8 : 2; return t; };
  const asphalt = make(textureCanvas(size, "#35383b", (c, s) => {
    for (let i = 0; i < s * 7; i++) { const v = 35 + Math.random() * 45; c.fillStyle = `rgb(${v},${v},${v})`; const r = Math.random() * 2 + .3; c.fillRect(Math.random()*s, Math.random()*s, r, r); }
    c.globalAlpha=.22; c.strokeStyle="#0d1012"; for(let i=0;i<12;i++){c.beginPath();c.moveTo(Math.random()*s,0);c.bezierCurveTo(Math.random()*s,s*.3,Math.random()*s,s*.7,Math.random()*s,s);c.stroke();} c.globalAlpha=1;
  }), 3, 45);
  const grass = make(textureCanvas(size, "#517f3f", (c, s) => {
    for(let i=0;i<s*5;i++){c.fillStyle=Math.random()>.5?"#426d35":"#6b914d";c.fillRect(Math.random()*s,Math.random()*s,1,Math.random()*4+1);}
  }), 18, 48);
  const metal = make(textureCanvas(size, "#d4dadd", (c,s) => {
    c.globalAlpha=.25; for(let x=0;x<s;x+=6){c.fillStyle=x%12?"#fff":"#78858b";c.fillRect(x,0,1,s);} c.globalAlpha=1;
  }), 2, 4);
  const paint = make(textureCanvas(size, "#19a99f", (c,s) => {
    const g=c.createLinearGradient(0,0,s,0);g.addColorStop(0,"#08736f");g.addColorStop(.45,"#27c9bd");g.addColorStop(1,"#075f61");c.fillStyle=g;c.fillRect(0,0,s,s);
  }), 1, 1);
  return { asphalt, grass, metal, paint, dispose(){ asphalt.dispose(); grass.dispose(); metal.dispose(); paint.dispose(); } };
}
