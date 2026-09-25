import { useEffect, useState } from "react";
import { ColorPanel } from "@/components/ColorPanel/ColorPanel";
import { SlideGrid } from "@/components/SlideGrid/SlideGrid";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { useDownload } from "@/hooks/useDownload";
import { useTemplate } from "@/hooks/useTemplate";
import { isHex, normalizeHex } from "@/lib/color";

const TEMPLATE_ID = "red-final";
const DEFAULT_COLOR = "#C00000";

export default function App() {
  const state = useTemplate(TEMPLATE_ID);
  const [color, setColor] = useState(DEFAULT_COLOR);
  const previewColor = useDebouncedValue(color, 40); // keeps dragging the picker smooth
  const { download, busy, message } = useDownload(TEMPLATE_ID);

  useEffect(() => {
    document.documentElement.style.setProperty("--pick", color);
  }, [color]);

  const handleChange = (hex: string) => {
    if (isHex(hex)) setColor(normalizeHex(hex));
  };

  return (
    <div className="layout">
      <ColorPanel
        color={color}
        onChange={handleChange}
        onDownload={() => download(color)}
        onReset={() => setColor(DEFAULT_COLOR)}
        busy={busy || state.status !== "ready"}
        status={message}
      />
      {state.status === "loading" && <p className="state">Loading template…</p>}
      {state.status === "error" && (
        <p className="state state--error">
          Could not load the template: {state.message}. Check that the backend is running on port 8000.
        </p>
      )}
      {state.status === "ready" && <SlideGrid template={state.template} color={previewColor} />}
    </div>
  );
}
