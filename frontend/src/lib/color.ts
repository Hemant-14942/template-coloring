/** Shade generation. Keep in sync with backend/app/services/color.py. */
import type { ColorSet } from "@/types/template";

const DARK_RATIO = 0.74;
const BRIGHT_RATIO = 1.33;

type RGB = [number, number, number];

export const isHex = (v: string) => /^#?[0-9a-f]{6}$/i.test(v);
export const normalizeHex = (v: string) => `#${v.replace("#", "").toUpperCase()}`;

export function hexToRgb(hex: string): RGB {
  const h = hex.replace("#", "");
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)) as RGB;
}

export function rgbToHex(r: number, g: number, b: number): string {
  return [r, g, b]
    .map((v) => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, "0"))
    .join("")
    .toUpperCase();
}

function rgbToHsl(r: number, g: number, b: number): RGB {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h = 0, s = 0;
  const l = (max + min) / 2;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    h = max === r ? (g - b) / d + (g < b ? 6 : 0) : max === g ? (b - r) / d + 2 : (r - g) / d + 4;
    h /= 6;
  }
  return [h, s, l];
}

function hslToRgb(h: number, s: number, l: number): RGB {
  if (s === 0) return [l * 255, l * 255, l * 255];
  const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
  const p = 2 * l - q;
  const f = (t: number) => {
    if (t < 0) t += 1;
    if (t > 1) t -= 1;
    if (t < 1 / 6) return p + (q - p) * 6 * t;
    if (t < 1 / 2) return q;
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
    return p;
  };
  return [f(h + 1 / 3) * 255, f(h) * 255, f(h - 1 / 3) * 255];
}

export function shadesFor(hex: string): ColorSet {
  const [h, s, l] = rgbToHsl(...hexToRgb(hex));
  return {
    dark: rgbToHex(...hslToRgb(h, s, l * DARK_RATIO)),
    main: hex.replace("#", "").toUpperCase(),
    bright: rgbToHex(...hslToRgb(h, s, Math.min(l * BRIGHT_RATIO, l + (1 - l) * 0.5))),
  };
}

/** Relative luminance (WCAG). Above ~0.35 white text starts losing contrast. */
export function luminance(hex: string): number {
  const [r, g, b] = hexToRgb(hex).map((v) => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/**
 * Lookup table: red intensity in the original render (0-255) -> new RGB.
 * Anchors match the template's shades: 0x8E dark, 0xC0 main, 0xFF bright.
 */
export function buildShadeLut(shades: ColorSet, base: ColorSet): Float32Array {
  const D = hexToRgb(shades.dark), M = hexToRgb(shades.main), B = hexToRgb(shades.bright);
  const dI = hexToRgb(base.dark)[0], mI = hexToRgb(base.main)[0], bI = hexToRgb(base.bright)[0];
  const lut = new Float32Array(256 * 3);
  for (let i = 0; i < 256; i++) {
    let c: number[];
    if (i <= dI) c = D.map((v) => (v * i) / dI);
    else if (i <= mI) { const t = (i - dI) / (mI - dI); c = D.map((v, j) => v + (M[j] - v) * t); }
    else { const t = Math.min(1, (i - mI) / (bI - mI)); c = M.map((v, j) => v + (B[j] - v) * t); }
    lut.set(c, i * 3);
  }
  return lut;
}
