/**
 * Setting type toggle — prong vs bezel.
 * Bezel is disabled in MVP (Phase 2).
 */

import React from "react";
import type { SettingType } from "../../types/jewelry";
import { useProjectStore } from "../../store/useProjectStore";

const btnStyle = (active: boolean): React.CSSProperties => ({
  flex: 1,
  padding: "6px 12px",
  border: "1px solid #444",
  background: active ? "#a78bfa" : "#1a1a1a",
  color: active ? "#000" : "#888",
  fontSize: 12,
  fontWeight: active ? 600 : 400,
  cursor: "pointer",
  borderRadius: 6,
  transition: "all 0.15s",
});

export default function SettingToggle() {
  const { currentParams, updateParams } = useProjectStore();

  return (
    <div>
      <h4 style={{ fontSize: 13, color: "#a78bfa", marginBottom: 12 }}>
        Setting Type
      </h4>
      <div style={{ display: "flex", gap: 8 }}>
        <button
          style={btnStyle(currentParams.setting_type === "prong")}
          onClick={() => updateParams({ setting_type: "prong" as SettingType })}
        >
          Prong
        </button>
        <button
          style={{
            ...btnStyle(currentParams.setting_type === "bezel"),
            opacity: 0.4,
            cursor: "not-allowed",
          }}
          disabled
          title="Bezel setting — coming in Phase 2"
        >
          Bezel (Phase 2)
        </button>
      </div>
    </div>
  );
}
