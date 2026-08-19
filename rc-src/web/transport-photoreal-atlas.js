const QUADRANTS = {
  asphalt: [0, 0],
  ground: [1, 0],
  stone: [0, 1],
  foliage: [1, 1],
};

export function loadPhotorealAtlas(T, url, qualityLevel = 2) {
  const textures = {};
  const ready = new Promise((resolve, reject) => {
    new T.TextureLoader().load(url, source => {
      const image = source.image;
      const tileSize = Math.floor(Math.min(image.width, image.height) / 2);
      for (const [name, [column, row]] of Object.entries(QUADRANTS)) {
        const canvas = document.createElement("canvas");
        canvas.width = canvas.height = tileSize;
        canvas.getContext("2d", { alpha: false }).drawImage(
          image,
          column * tileSize, row * tileSize, tileSize, tileSize,
          0, 0, tileSize, tileSize,
        );
        const texture = new T.CanvasTexture(canvas);
        texture.name = `original_europe_${name}`;
        texture.colorSpace = T.SRGBColorSpace;
        texture.wrapS = texture.wrapT = T.RepeatWrapping;
        texture.anisotropy = qualityLevel >= 3 ? 16 : qualityLevel >= 2 ? 8 : 2;
        textures[name] = texture;
      }
      source.dispose();
      resolve(textures);
    }, undefined, reject);
  });
  return {
    textures,
    ready,
    dispose() { Object.values(textures).forEach(texture => texture.dispose()); },
  };
}
