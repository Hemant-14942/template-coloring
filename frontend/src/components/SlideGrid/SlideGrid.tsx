import { useMemo } from "react";
import { SlidePreview } from "@/components/SlidePreview/SlidePreview";
import { buildShadeLut, shadesFor } from "@/lib/color";
import type { TemplateDetail } from "@/types/template";
import "./SlideGrid.css";

interface Props {
  template: TemplateDetail;
  color: string;
}

export function SlideGrid({ template, color }: Props) {
  const lut = useMemo(() => buildShadeLut(shadesFor(color), template.base_colors), [color, template.base_colors]);

  return (
    <main>
      <h2 className="grid__title">Preview, {template.slides.length} slides</h2>
      <div className="grid">
        {template.slides.map((s) => (
          <SlidePreview key={s.number} slide={s} lut={lut} />
        ))}
      </div>
    </main>
  );
}
