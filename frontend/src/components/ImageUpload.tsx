/**
 * Image upload component with drag-and-drop support.
 *
 * Flow:
 *   1. User selects / drops image
 *   2. POST /api/parse (multipart/form-data, key="file")
 *   3. On success → store parseResult + currentParams → useBuild auto-triggers /api/build
 *   4. On failure → fallback to default params, confidence=0
 *   5. If confidence < 0.6 → show low-confidence warning
 */

import { useCallback, useRef, useState } from "react";
import { parseImage } from "../api/parseApi";
import { useProjectStore } from "../store/useProjectStore";
import "./ImageUpload.css";

const LOW_CONFIDENCE_THRESHOLD = 0.6;

export default function ImageUpload() {
  const {
    setProject,
    setSourceImage,
    setIsParsing,
    setParseFailure,
    isParsing,
    parseResult,
  } = useProjectStore();
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
        // POST /api/parse with FormData key "file"
        const res = await parseImage(file);

        // Store parse_result → updates currentParams → useBuild auto-triggers /api/build
        setProject(res.project_id, res.parse_result, res.customization);
      } catch (err) {
        // Fallback: default parametric JSON, confidence = 0
        setParseFailure();
        setError(err instanceof Error ? err.message : "Parsing failed — using defaults");
      } finally {
        setIsParsing(false);
      }
    },
    [setProject, setSourceImage, setIsParsing, setParseFailure]
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

  const confidence = parseResult?.confidence_score ?? null;
  const showLowConfidence =
    confidence !== null && confidence < LOW_CONFIDENCE_THRESHOLD;

  return (
    <div
      className={`upload-dropzone ${dragActive ? "upload-dropzone--active" : ""}`}
      role="button"
      tabIndex={0}
      aria-label="Upload jewelry image — click or drag and drop"
      onDragOver={(e) => {
        e.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          inputRef.current?.click();
        }
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        hidden
        aria-hidden="true"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) handleFile(f);
          // Reset so re-uploading the same file works
          e.target.value = "";
        }}
      />
      {isParsing ? (
        <span className="upload-status">
          <span className="spinner" style={{ marginRight: 8 }} />
          Analyzing image...
        </span>
      ) : parseResult ? (
        <span className="upload-label" style={{ color: "#4ade80" }}>
          ✓ Image analyzed — drop another to replace
        </span>
      ) : (
        <>
          <span className="upload-icon" aria-hidden="true">📷</span>
          <span className="upload-label">
            Drop a jewelry image or click to upload
          </span>
        </>
      )}
      {error && <span className="upload-error">{error}</span>}
      {showLowConfidence && (
        <span className="upload-warning">
          ⚠ Low confidence detection — defaults may be applied.
        </span>
      )}
    </div>
  );
}
