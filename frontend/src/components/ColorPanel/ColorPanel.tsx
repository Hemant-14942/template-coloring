import { HexColorInput, HexColorPicker } from "react-colorful";
import { luminance, shadesFor } from "@/lib/color";
import "./ColorPanel.css";

const PRESETS = ["#C00000", "#1F4E9A", "#0F7B6C", "#6A2C91", "#D35400", "#2E7D32", "#B0005E", "#0E7490", "#374151"];

interface Props {
  color: string;
  onChange: (hex: string) => void;
  onDownload: () => void;
  onReset: () => void;
  busy: boolean;
  status: string;
}

export function ColorPanel({ color, onChange, onDownload, onReset, busy, status }: Props) {
  const shades = shadesFor(color);
  const tooLight = luminance(color) > 0.35;

  return (
    <aside className="panel">
      <h1>Template color</h1>
      <p className="panel__sub">
        Pick one color. Every highlighted shape in the deck switches to it, with matching darker and brighter shades.
      </p>

      <HexColorPicker className="panel__picker" color={color} onChange={onChange} />

      <label className="panel__label" htmlFor="hex-input">Hex code</label>
      <HexColorInput id="hex-input" className="panel__hex" color={color} onChange={onChange} prefixed />

      <div className="panel__shades" aria-hidden="true">
        <div style={{ background: `#${shades.dark}` }}>Dark</div>
        <div style={{ background: `#${shades.main}` }}>Main</div>
        <div style={{ background: `#${shades.bright}` }}>Bright</div>
      </div>
      <p className="panel__caption">Dark and bright are used for the pill gradients and outlines.</p>

      <div className="panel__presets" role="group" aria-label="Preset colors">
        {PRESETS.map((p) => (
          <button
            key={p}
            type="button"
            style={{ background: p }}
            aria-label={`Use ${p}`}
            aria-pressed={p === color.toUpperCase()}
            onClick={() => onChange(p)}
          />
        ))}
      </div>

      <p className="panel__warn">{tooLight ? "This color is light, so the white text on the pills may be hard to read." : ""}</p>

      <div className="panel__actions">
        <button type="button" className="btn btn--primary" onClick={onDownload} disabled={busy}>
          {busy ? "Building…" : "Download PowerPoint"}
        </button>
        <button type="button" className="btn btn--ghost" onClick={onReset}>Back to original red</button>
      </div>
      <p className="panel__status" role="status">{status}</p>
      <p className="panel__note">Preview is a close approximation. The downloaded file has the exact colors.</p>
    </aside>
  );
}
