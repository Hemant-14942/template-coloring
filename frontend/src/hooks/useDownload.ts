import { useCallback, useState } from "react";
import { downloadRecolored } from "@/api/templates";
import { saveBlob } from "@/lib/download";

export function useDownload(templateId: string) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  const download = useCallback(async (color: string) => {
    setBusy(true);
    setMessage("Building your file…");
    try {
      const { blob, filename } = await downloadRecolored(templateId, color);
      saveBlob(blob, filename);
      setMessage(`Downloaded ${filename}`);
    } catch (e) {
      setMessage(`Could not build the file: ${(e as Error).message}`);
    } finally {
      setBusy(false);
    }
  }, [templateId]);

  return { download, busy, message };
}
