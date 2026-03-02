/**
 * Customizer panel — container for all parameter controls.
 */

import React from "react";
import DimensionSliders from "./DimensionSliders";
import MaterialSelect from "./MaterialSelect";
import SettingToggle from "./SettingToggle";
import StoneControls from "./StoneControls";

const panelStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 20,
  padding: 16,
  background: "#111",
  borderRadius: 12,
  overflowY: "auto",
  maxHeight: "100%",
};

export default function CustomizerPanel() {
  return (
    <div style={panelStyle}>
      <h3 style={{ fontSize: 15, fontWeight: 600, color: "#fff" }}>
        Customize Ring
      </h3>
      <DimensionSliders />
      <StoneControls />
      <MaterialSelect />
      <SettingToggle />
    </div>
  );
}
