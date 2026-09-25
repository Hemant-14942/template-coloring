import { request } from "./client";
import type { TemplateDetail } from "@/types/template";

export async function fetchTemplate(id: string): Promise<TemplateDetail> {
  const res = await request(`/api/v1/templates/${encodeURIComponent(id)}`);
  return res.json();
}

export async function downloadRecolored(id: string, color: string): Promise<{ blob: Blob; filename: string }> {
  const res = await request(`/api/v1/templates/${encodeURIComponent(id)}/recolor`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ color }),
  });
  const disposition = res.headers.get("Content-Disposition") ?? "";
  const filename = /filename="?([^"]+)"?/.exec(disposition)?.[1] ?? `${id}-${color.replace("#", "")}.pptx`;
  return { blob: await res.blob(), filename };
}
