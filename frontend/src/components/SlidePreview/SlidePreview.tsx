import { useEffect, useRef, useState } from "react";
import { apiUrl } from "@/api/client";
import type { Slide } from "@/types/template";

interface Prepared {
  ctx: CanvasRenderingContext2D;
  frame: ImageData;
  original: Uint8ClampedArray;
  indices: Uint32Array;
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`Could not load ${src}`));
    img.src = src;
  });
}

interface Props {
  slide: Slide;
  lut: Float32Array; // shade lookup from buildShadeLut
}

export function SlidePreview({ slide, lut }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const prepared = useRef<Prepared | null>(null);
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);

  // Load preview + mask once, remember which pixels are recolorable
  useEffect(() => {
    let cancelled = false;
    Promise.all([loadImage(apiUrl(slide.preview_url)), loadImage(apiUrl(slide.mask_url))])
      .then(([img, mask]) => {
        const canvas = canvasRef.current;
        if (cancelled || !canvas) return;
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext("2d", { willReadFrequently: true })!;
        ctx.drawImage(mask, 0, 0, img.width, img.height);
        const m = ctx.getImageData(0, 0, img.width, img.height).data;
        ctx.drawImage(img, 0, 0);
        const frame = ctx.getImageData(0, 0, img.width, img.height);
        const idx: number[] = [];
        if (slide.recolor) for (let p = 0; p < m.length; p += 4) if (m[p] > 127) idx.push(p);
        prepared.current = { ctx, frame, original: new Uint8ClampedArray(frame.data), indices: Uint32Array.from(idx) };
        setReady(true);
      })
      .catch(() => !cancelled && setFailed(true));
    return () => { cancelled = true; };
  }, [slide]);

  // Repaint masked pixels whenever the color changes
  useEffect(() => {
    const p = prepared.current;
    if (!ready || !p) return;
    const d = p.frame.data, o = p.original, idx = p.indices;
    for (let n = 0; n < idx.length; n++) {
      const i = idx[n];
      const white = Math.min(o[i + 1], o[i + 2]);         // white/grey part (anti-aliased text edges)
      const k = Math.max(0, o[i] - white) * 3;             // red intensity -> LUT row
      d[i] = white + lut[k];
      d[i + 1] = white + lut[k + 1];
      d[i + 2] = white + lut[k + 2];
    }
    p.ctx.putImageData(p.frame, 0, 0);
  }, [lut, ready]);

  return (
    <figure className="slide">
      <canvas ref={canvasRef} role="img" aria-label={`Slide ${slide.number}: ${slide.name}`} />
      {failed && <p className="slide__error">Preview could not load.</p>}
      <figcaption>
        <b>{slide.number}</b>
        <div>
          {slide.name}
          <span> · {slide.recolor ? slide.change : "Unchanged"}</span>
        </div>
      </figcaption>
    </figure>
  );
}
