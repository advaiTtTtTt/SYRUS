/**
 * Keyboard shortcuts hook — Ctrl+Z / Ctrl+Shift+Z for undo/redo.
 * Uses zundo temporal store attached to useProjectStore.
 *
 * Respects input/textarea focus — doesn't intercept native undo in form fields.
 */

import { useEffect } from "react";
import { useProjectStore } from "../store/useProjectStore";

/** Tags where native undo/redo should take precedence */
const INPUT_TAGS = new Set(["INPUT", "TEXTAREA", "SELECT"]);

export function useKeyboardShortcuts() {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't intercept when user is typing in a form field
      const target = e.target as HTMLElement;
      if (INPUT_TAGS.has(target.tagName) || target.isContentEditable) return;

      const ctrl = e.ctrlKey || e.metaKey;
      if (!ctrl) return;

      if (e.key === "z" && !e.shiftKey) {
        e.preventDefault();
        useProjectStore.temporal.getState().undo();
      } else if ((e.key === "z" && e.shiftKey) || e.key === "y") {
        e.preventDefault();
        useProjectStore.temporal.getState().redo();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);
}
