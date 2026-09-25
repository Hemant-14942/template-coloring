import { useEffect, useState } from "react";
import { fetchTemplate } from "@/api/templates";
import type { TemplateDetail } from "@/types/template";

type State =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; template: TemplateDetail };

export function useTemplate(id: string): State {
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading" });
    fetchTemplate(id)
      .then((template) => !cancelled && setState({ status: "ready", template }))
      .catch((e: Error) => !cancelled && setState({ status: "error", message: e.message }));
    return () => { cancelled = true; };
  }, [id]);

  return state;
}
