/**
 * Customizer panel — container for all parameter controls.
 * Shows type-specific sliders based on the selected jewelry type.
 */

import "./Customizer.css";
import { useProjectStore } from "../../store/useProjectStore";
import DimensionSliders from "./DimensionSliders";
import EarringSliders from "./EarringSliders";
import JewelryTypeSelector from "./JewelryTypeSelector";
import MaterialSelect from "./MaterialSelect";
import PendantSliders from "./PendantSliders";
import SettingToggle from "./SettingToggle";
import SideStoneControls from "./SideStoneControls";
import StoneControls from "./StoneControls";

const TYPE_LABELS: Record<string, string> = {
  ring: "Ring",
  pendant: "Pendant",
  earring: "Earring",
};

export default function CustomizerPanel() {
  const jewelryType = useProjectStore((s) => s.currentParams.type) ?? "ring";

  return (
    <div className="customizer-panel">
      <h3>Customize {TYPE_LABELS[jewelryType] ?? "Jewelry"}</h3>

      <JewelryTypeSelector />

      {/* Type-specific dimension controls */}
      {jewelryType === "ring" && <DimensionSliders />}
      {jewelryType === "pendant" && <PendantSliders />}
      {jewelryType === "earring" && <EarringSliders />}

      <StoneControls />
      <MaterialSelect />

      {/* Setting controls — only for rings */}
      {jewelryType === "ring" && (
        <>
          <SettingToggle />
          <SideStoneControls />
        </>
      )}
    </div>
  );
}
