/**
 * Image upload component with drag-and-drop support.
 */

import React, { useCallback, useRef, useState } from "react";
import { parseImage } from "../api/parseApi";
import { useProjectStore } from "../store/useProjectStore";

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    border: "2px dashed #555",
    borderRadius: 12,
    padding: 32,
    cursor: "pointer",
    transition: "border-color 0.2s",
    minHeight: 160,
  },
  active: {
    borderColor: "#a78bfa",
    background: "rgba(167, 139, 250, 0.05)",
  },
  label: { fontSize: 14, color: "#aaa", marginTop: 8 },
  error: { color: "#f87171", fontSize: 12, marginTop: 8 },
};

export default function ImageUpload() {
  const { setProject, setSourceImage, setIsParsing, isParsing } =
    useProjectStore();
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.type.startsWith("image/")) {
        setError("Please upload an image file (JPEG, PNG, WebP)");
        return;
      }
      setError(null);
      setSourceImage(file);
      setIsParsing(true);

      try {
        const res = await parseImage(file);
        setProject(res.project_id, res.parse_result, res.customization);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Parsing failed");
      } finally {
        setIsParsing(false);
      }
    },
    [setProject, setSourceImage, setIsParsing]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div
      style={{ ...styles.container, ...(dragActive ? styles.active : {}) }}
      onDragOver={(e) => {
        e.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        hidden
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) handleFile(f);
        }}
      />
      {isParsing ? (
        <span style={{ color: "#a78bfa" }}>Analyzing image...</span>
      ) : (
        <>
          <span style={{ fontSize: 28 }}>📷</span>
          <span style={styles.label}>
            Drop a jewelry image or click to upload
          </span>
        </>
      )}
      {error && <span style={styles.error}>{error}</span>}
    </div>
  );
}
