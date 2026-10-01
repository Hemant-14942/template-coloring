import { useEffect, useState } from "react";
import { HexColorInput, HexColorPicker } from "react-colorful";
import { shadesFor } from "@/lib/color";
import "./ColorPanel.css";

const SHAPE_PRESETS = ["#C00000", "#1F4E9A", "#0F7B6C", "#6A2C91", "#CA5000", "#2E7D32", "#B0005E", "#0E7490", "#374151"];
const BACKGROUND_PRESETS = ["#000000", "#0E1628", "#14181F", "#1A140C", "#0E1C16", "#1A1220", "#102028", "#24160F"];

interface Props {
  color: string;
  background: string;
  icon: File | null;
  onChange: (hex: string) => void;
  onBackgroundChange: (hex: string) => void;
  onIconChange: (file: File | null) => void;
  onDownload: () => void;
  onReset: () => void;
  busy: boolean;
  status: string;
}

export function ColorPanel({
  color, background, icon, onChange, onBackgroundChange, onIconChange, onDownload, onReset, busy, status,
}: Props) {
  const shades = shadesFor(color);
  const [iconUrl, setIconUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!icon) {
      setIconUrl(null);
      return;
    }
    const url = URL.createObjectURL(icon);
    setIconUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [icon]);

  return (
    <aside className="panel">
      <h1>Template color</h1>
      <p className="panel__sub">Shape color and slide background are chosen separately.</p>

      <section>
        <h2 className="panel__heading">Shape color</h2>
        <p className="panel__sub">Light shades are held back so the white text on the shapes stays readable.</p>
        <HexColorPicker className="panel__picker" color={color} onChange={onChange} />
        <label className="panel__label" htmlFor="hex-input">Hex code</label>
        <HexColorInput id="hex-input" className="panel__hex" color={color} onChange={onChange} prefixed />
        <div className="panel__shades" aria-hidden="true">
          <div style={{ background: `#${shades.dark}` }}>Dark</div>
          <div style={{ background: `#${shades.main}` }}>Main</div>
          <div style={{ background: `#${shades.bright}` }}>Bright</div>
        </div>
        <p className="panel__caption">Dark and bright are used for the pill gradients and outlines.</p>
        <div className="panel__presets" role="group" aria-label="Shape colors">
          {SHAPE_PRESETS.map((p) => (
            <button
              key={p}
              type="button"
              style={{ background: p }}
              aria-label={`Use shape color ${p}`}
              aria-pressed={p === color.toUpperCase()}
              onClick={() => onChange(p)}
            />
          ))}
        </div>
      </section>

      <section className="panel__bg">
        <h2 className="panel__heading">Slide background</h2>
        <p className="panel__sub">
          This dark color is written on each slide. Theme colors stay as they are, so anything else using them is left alone.
        </p>
        <HexColorPicker className="panel__picker panel__picker--short" color={background} onChange={onBackgroundChange} />
        <label className="panel__label" htmlFor="bg-hex">Hex code</label>
        <HexColorInput id="bg-hex" className="panel__hex" color={background} onChange={onBackgroundChange} prefixed />
        <div className="panel__presets" role="group" aria-label="Background colors">
          {BACKGROUND_PRESETS.map((p) => (
            <button
              key={p}
              type="button"
              style={{ background: p }}
              aria-label={`Use background ${p}`}
              aria-pressed={p === background.toUpperCase()}
              onClick={() => onBackgroundChange(p)}
            />
          ))}
        </div>
      </section>

      <section className="panel__bg">
        <h2 className="panel__heading">Heading icon</h2>
        <p className="panel__sub">
          Replaces the notepad and pencil on slides 1, 2, 3, 8, 9, and 12 in the download. It is not saved on the server.
        </p>
        <div className="panel__icon">
          {iconUrl && <img src={iconUrl} alt="Uploaded icon" />}
          <label className="btn btn--ghost panel__file">
            {icon ? "Change icon" : "Upload icon"}
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={(event) => {
                onIconChange(event.target.files?.[0] ?? null);
                event.target.value = "";
              }}
            />
          </label>
          {icon && (
            <button type="button" className="btn btn--ghost" onClick={() => onIconChange(null)}>
              Remove
            </button>
          )}
        </div>
      </section>

      <div className="panel__actions">
        <button type="button" className="btn btn--primary" onClick={onDownload} disabled={busy}>
          {busy ? "Building…" : "Download PowerPoint"}
        </button>
        <button type="button" className="btn btn--ghost" onClick={onReset}>Back to original</button>
      </div>
      <p className="panel__status" role="status">{status}</p>
      <p className="panel__note">The preview follows both colors. The downloaded file has the exact colors.</p>
    </aside>
  );
}
