/**
 * Toast notification system — lightweight, no external deps.
 *
 * Usage:
 *   import { toast } from "../utils/toast";
 *   toast.success("Exported GLB!");
 *   toast.error("Build failed");
 *   toast.info("Turntable on");
 */

let containerEl: HTMLDivElement | null = null;

function ensureContainer(): HTMLDivElement {
  if (!containerEl) {
    containerEl = document.createElement("div");
    containerEl.className = "toast-container";
    document.body.appendChild(containerEl);
  }
  return containerEl;
}

function show(message: string, variant: "success" | "error" | "info") {
  const container = ensureContainer();
  const el = document.createElement("div");
  el.className = `toast toast--${variant}`;
  el.textContent = message;
  container.appendChild(el);

  // Auto-remove after animation ends (~3s)
  setTimeout(() => {
    el.remove();
  }, 3100);
}

export const toast = {
  success: (msg: string) => show(msg, "success"),
  error: (msg: string) => show(msg, "error"),
  info: (msg: string) => show(msg, "info"),
};
