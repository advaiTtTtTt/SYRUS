/**
 * Source image panel — shows 2D uploaded image alongside 3D viewport.
 *
 * Displays:
 *   - Uploaded image thumbnail with detection bbox overlay
 *   - AI confidence scores per detection component
 *   - Visual confidence bars for band/stone/setting/symmetry
 *
 * This is the "2D" half of the "2D → 3D" demo promise.
 */

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useProjectStore } from "../store/useProjectStore";
import type { DetectionRegion } from "../types/jewelry";

/** Colour per detection label */
const LABEL_COLOR: Record<string, string> = {
  ring_band: "#fbbf24",    // gold
  center_stone: "#60a5fa", // blue
  prong: "#a78bfa",        // purple
  bezel_rim: "#34d399",    // green
  side_stone: "#f472b6",   // pink
  bail: "#fb923c",         // orange
  pendant_body: "#2dd4bf", // teal
  earring_stud: "#e879f9", // fuchsia
};

const panelStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 8,
  padding: 12,
  background: "#111",
  borderRadius: 12,
  height: "100%",
  minHeight: 0,
  overflow: "hidden",
};

const heading: React.CSSProperties = {
  fontSize: 13,
  fontWeight: 600,
  color: "#fff",
  margin: 0,
};

const scoreRow: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  fontSize: 11,
  color: "#ccc",
};

const barBg: React.CSSProperties = {
  flex: 1,
  height: 4,
  background: "#333",
  borderRadius: 2,
  marginLeft: 8,
  marginRight: 6,
  overflow: "hidden",
};

/* ── Confidence bar ─────────────────────────────────────────── */

function ConfidenceBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 70 ? "#4ade80" : pct >= 40 ? "#fbbf24" : "#f87171";
  return (
    <div style={scoreRow}>
      <span style={{ minWidth: 60 }}>{label}</span>
      <div style={barBg}>
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: color,
            borderRadius: 2,
            transition: "width 0.3s",
          }}
        />
      </div>
      <span style={{ minWidth: 28, textAlign: "right", fontWeight: 600, color }}>
        {pct}%
      </span>
    </div>
  );
}

/* ── Bbox overlay canvas ────────────────────────────────────── */

function BboxOverlay({
  detections,
  imgEl,
}: {
  detections: DetectionRegion[];
  imgEl: HTMLImageElement | null;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !imgEl) return;
    const rect = imgEl.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    for (const det of detections) {
      const [nx1, ny1, nx2, ny2] = det.bbox;
      const x = nx1 * canvas.width;
      const y = ny1 * canvas.height;
      const w = (nx2 - nx1) * canvas.width;
      const h = (ny2 - ny1) * canvas.height;
      const color = LABEL_COLOR[det.label] ?? "#fff";

      // Box
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, w, h);

      // Label background
      const text = `${det.label.replace("_", " ")} ${Math.round(det.confidence * 100)}%`;
      ctx.font = "bold 10px Inter, sans-serif";
      const tm = ctx.measureText(text);
      const lh = 14;
      const lx = x;
      const ly = Math.max(y - lh, 0);
      ctx.fillStyle = color;
      ctx.globalAlpha = 0.85;
      ctx.fillRect(lx, ly, tm.width + 6, lh);
      ctx.globalAlpha = 1;

      // Label text
      ctx.fillStyle = "#000";
      ctx.fillText(text, lx + 3, ly + 10);
    }
  }, [detections, imgEl]);

  useEffect(() => {
    draw();
    window.addEventListener("resize", draw);
    return () => window.removeEventListener("resize", draw);
  }, [draw]);

  if (!imgEl) return null;

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
      }}
    />
  );
}

/* ── Main panel ─────────────────────────────────────────────── */

export default function SourceImagePanel() {
  const sourceImage = useProjectStore((s) => s.sourceImage);
  const parseResult = useProjectStore((s) => s.parseResult);
  const [imgEl, setImgEl] = useState<HTMLImageElement | null>(null);

  const imageUrl = useMemo(() => {
    if (!sourceImage) return null;
    return URL.createObjectURL(sourceImage);
  }, [sourceImage]);

  // Revoke object URL on cleanup to prevent memory leak
  useEffect(() => {
    return () => {
      if (imageUrl) URL.revokeObjectURL(imageUrl);
    };
  }, [imageUrl]);

  if (!sourceImage) return null;

  const detections = parseResult?.detections ?? [];

  return (
    <div style={panelStyle}>
      <h4 style={heading}>Source Image</h4>

      {/* Image + bbox overlay container */}
      <div style={{ position: "relative", width: "100%", maxHeight: "60%" }}>
        {imageUrl && (
          <img
            ref={(el) => setImgEl(el)}
            src={imageUrl}
            alt="Uploaded jewelry"
            style={{
              width: "100%",
              maxHeight: "100%",
              objectFit: "contain",
              borderRadius: 8,
              background: "#1a1a2e",
              display: "block",
            }}
            onLoad={() => {
              // Force canvas redraw after image dimensions are known
              setImgEl(document.querySelector<HTMLImageElement>('[alt="Uploaded jewelry"]'));
            }}
          />
        )}
        {detections.length > 0 && <BboxOverlay detections={detections} imgEl={imgEl} />}
      </div>

      {/* Detection legend */}
      {detections.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 2 }}>
          {detections.map((d, i) => (
            <span
              key={i}
              style={{
                fontSize: 10,
                padding: "1px 6px",
                borderRadius: 4,
                background: LABEL_COLOR[d.label] ?? "#555",
                color: "#000",
                fontWeight: 600,
              }}
            >
              {d.label.replaceAll("_", " ")}
            </span>
          ))}
        </div>
      )}

      {parseResult && (
        <div style={{ display: "flex", flexDirection: "column", gap: 4, marginTop: 4 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: "#a78bfa", marginBottom: 2 }}>
            AI Detection Confidence
          </div>
          <ConfidenceBar label="Band" value={parseResult.band_confidence} />
          <ConfidenceBar label="Stone" value={parseResult.stone_confidence} />
          <ConfidenceBar label="Setting" value={parseResult.setting_confidence} />
          <ConfidenceBar label="Symmetry" value={parseResult.symmetry_confidence} />
          <div
            style={{
              marginTop: 4,
              fontSize: 13,
              fontWeight: 700,
              color:
                parseResult.confidence_score >= 0.7
                  ? "#4ade80"
                  : parseResult.confidence_score >= 0.4
                  ? "#fbbf24"
                  : "#f87171",
              textAlign: "center",
            }}
          >
            Overall: {Math.round(parseResult.confidence_score * 100)}%
          </div>
        </div>
      )}
    </div>
  );
}
