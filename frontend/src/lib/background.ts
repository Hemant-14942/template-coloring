const DARK = 32;

function isDark(data: Uint8ClampedArray, shape: Uint8Array, pixel: number): boolean {
  if (shape[pixel]) return false;
  const o = pixel * 4;
  return data[o] <= DARK && data[o + 1] <= DARK && data[o + 2] <= DARK;
}

function neighbors(pixel: number, width: number, height: number): number[] {
  const x = pixel % width;
  const y = (pixel / width) | 0;
  const found: number[] = [];
  if (x > 0) found.push(pixel - 1);
  if (x + 1 < width) found.push(pixel + 1);
  if (y > 0) found.push(pixel - width);
  if (y + 1 < height) found.push(pixel + width);
  return found;
}

/** Byte offsets of the slide background, including small holes inside letters. */
export function findBackgroundOffsets(
  data: Uint8ClampedArray,
  width: number,
  height: number,
  shape: Uint8Array,
): Uint32Array {
  const count = width * height;
  const seen = new Uint8Array(count);
  const pixels: number[] = [];

  const collect = (start: number, into: number[]) => {
    const pending = [start];
    seen[start] = 1;
    while (pending.length) {
      const pixel = pending.pop()!;
      into.push(pixel);
      for (const next of neighbors(pixel, width, height)) {
        if (seen[next] || !isDark(data, shape, next)) continue;
        seen[next] = 1;
        pending.push(next);
      }
    }
  };

  for (let x = 0; x < width; x++) {
    if (!seen[x] && isDark(data, shape, x)) collect(x, pixels);
    const bottom = (height - 1) * width + x;
    if (!seen[bottom] && isDark(data, shape, bottom)) collect(bottom, pixels);
  }
  for (let y = 0; y < height; y++) {
    const left = y * width;
    const right = left + width - 1;
    if (!seen[left] && isDark(data, shape, left)) collect(left, pixels);
    if (!seen[right] && isDark(data, shape, right)) collect(right, pixels);
  }

  // Counters in letters are dark, enclosed, and small. Larger dark shapes stay as they are.
  const maxHole = Math.round(count * 0.002);
  for (let pixel = 0; pixel < count; pixel++) {
    if (seen[pixel] || !isDark(data, shape, pixel)) continue;
    const hole: number[] = [];
    collect(pixel, hole);
    if (hole.length <= maxHole) for (const p of hole) pixels.push(p);
  }

  const offsets = new Uint32Array(pixels.length);
  for (let i = 0; i < pixels.length; i++) offsets[i] = pixels[i] * 4;
  return offsets;
}
