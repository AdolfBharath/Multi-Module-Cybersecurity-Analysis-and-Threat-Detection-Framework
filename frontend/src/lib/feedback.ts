export function notify(message: string, kind: "error" | "success" = "error") {
  window.dispatchEvent(new CustomEvent("cybershield:toast", { detail: { message, kind } }));
}
