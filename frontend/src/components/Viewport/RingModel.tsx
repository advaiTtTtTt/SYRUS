/**
 * GLB model loader with multi-material support + parametric fallbacks.
 */

import { useGLTF } from "@react-three/drei";
import { useEffect, useMemo } from "react";
import * as THREE from "three";
import { useProjectStore } from "../../store/useProjectStore";

const METAL_COLORS: Record<string, string> = {
  "18k_gold": "#d4af37",
  "14k_gold": "#c5a028",
  platinum: "#e5e4e2",
  silver: "#c0c0c0",
};

const GEM_COLORS: Record<string, string> = {
  diamond: "#b9f2ff",
  ruby: "#e0115f",
  sapphire: "#0f52ba",
  emerald: "#50c878",
  moissanite: "#f5e6b8",
};

/** Mesh names containing these tokens get gem material instead of metal. */
const STONE_TOKENS = ["stone", "gem", "halo_stones", "pave_stones"];

function isStoneNode(name: string): boolean {
  const lower = name.toLowerCase();
  return STONE_TOKENS.some((t) => lower.includes(t));
}

export default function RingModel() {
  const modelUrl = useProjectStore((s) => s.modelUrl);
  const jewelryType = useProjectStore((s) => s.currentParams.type);

  if (modelUrl) {
    return <LoadedModel url={modelUrl} />;
  }

  // Parametric fallback per type
  switch (jewelryType) {
    case "pendant":
      return <FallbackPendant />;
    case "earring":
      return <FallbackEarring />;
    default:
      return <FallbackRing />;
  }
}

function LoadedModel({ url }: { url: string }) {
  const { scene } = useGLTF(url);
  const customization = useProjectStore((s) => s.customization);
  const metalColor = METAL_COLORS[customization.metal_type] ?? "#d4af37";
  const gemColor = GEM_COLORS[customization.gemstone_material] ?? "#b9f2ff";

  const clonedScene = useMemo(() => scene.clone(), [scene]);

  useEffect(() => {
    const oldMaterials: THREE.Material[] = [];

    clonedScene.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        // Track old material for disposal
        if (child.material) {
          const mats = Array.isArray(child.material) ? child.material : [child.material];
          oldMaterials.push(...mats);
        }

        if (isStoneNode(child.name)) {
          child.material = new THREE.MeshPhysicalMaterial({
            color: gemColor,
            transparent: true,
            opacity: 0.82,
            roughness: 0.02,
            metalness: 0.0,
            clearcoat: 1.0,
            clearcoatRoughness: 0.03,
            ior: 2.4,
            thickness: 2.0,
          });
        } else {
          child.material = new THREE.MeshStandardMaterial({
            color: metalColor,
            metalness: 0.92,
            roughness: 0.12,
          });
        }
        child.castShadow = true;
        child.receiveShadow = true;
      }
    });

    return () => {
      oldMaterials.forEach((m) => m.dispose());
    };
  }, [clonedScene, metalColor, gemColor]);

  return <primitive object={clonedScene} />;
}

/** Parametric fallback ring — interactive 3D preview without CadQuery.
 *
 * Orientation: ring upright (hole along Z, like on a vertical finger).
 * Stone at 12 o'clock (top, +Y direction).
 * Three.js TorusGeometry: tube sweeps in XY plane around Z axis.
 *   - i=π/2 → tube center at (0, R, 0) → top of ring
 *   - Outer surface at top: (0, R+tubeR, 0)
 */
function FallbackRing() {
  const params = useProjectStore((s) => s.currentParams);
  const customization = useProjectStore((s) => s.customization);

  const metalColor = METAL_COLORS[customization.metal_type] ?? "#d4af37";
  const gemColor = GEM_COLORS[customization.gemstone_material] ?? "#b9f2ff";

  const R = params.ring_radius;
  const bt = params.band_thickness;
  const bw = params.band_width;
  const tubeR = bt / 2;
  // Scale Z axis to represent band width (depth along finger)
  const depthScale = bw / bt;

  const stone = params.center_stone;
  const stoneR = stone.diameter / 2;
  const stoneH = stone.height;
  const nProngs = stone.prongs;

  // Stone footprint for prong clearance (elliptical based on shape)
  const footprint = useMemo(() => {
    switch (stone.type) {
      case "oval":    return { rx: stoneR * 0.95, rz: stoneR * 0.65 };
      case "emerald": return { rx: stoneR * 0.75, rz: stoneR * 0.55 };
      case "pear":    return { rx: stoneR * 0.7,  rz: stoneR * 0.85 };
      default:        return { rx: stoneR * 0.8,  rz: stoneR * 0.8 };
    }
  }, [stone.type, stoneR]);

  // Top of outer band surface at 12 o'clock
  const seatY = R + tubeR;
  const prongH = stoneH * 0.75;
  const colletTopR = Math.max(footprint.rx, footprint.rz) + 0.2;
  const colletBotR = colletTopR + 0.5;

  // Gem material — shared across shapes
  const gemMaterial = (
    <meshPhysicalMaterial
      color={gemColor}
      transparent
      opacity={0.82}
      roughness={0.02}
      metalness={0.0}
      clearcoat={1.0}
      clearcoatRoughness={0.03}
      ior={2.4}
      thickness={stoneH * 0.5}
      envMapIntensity={2.0}
    />
  );

  return (
    <group rotation={[-0.25, 0.15, 0]}>
      {/* ── Ring Band — upright, hole along Z ─── */}
      <mesh scale={[1, 1, depthScale]}>
        <torusGeometry args={[R, tubeR, 32, 100]} />
        <meshStandardMaterial
          color={metalColor}
          metalness={0.92}
          roughness={0.12}
        />
      </mesh>

      {/* ── Stone Setting at 12 o'clock ────────── */}
      <group position={[0, seatY, 0]}>

        {/* Collet / setting base */}
        <mesh position={[0, 0.1, 0]}>
          <cylinderGeometry args={[colletTopR, colletBotR, 0.4, Math.max(nProngs * 4, 24)]} />
          <meshStandardMaterial color={metalColor} metalness={0.9} roughness={0.15} />
        </mesh>

        {/* Center stone */}
        <group position={[0, stoneH * 0.35, 0]}>
          {stone.type === "emerald" ? (
            <mesh>
              <boxGeometry args={[stoneR * 1.3, stoneH * 0.7, stoneR * 0.9]} />
              {gemMaterial}
            </mesh>
          ) : stone.type === "oval" ? (
            <mesh scale={[1.3, 1.0, 0.75]}>
              <sphereGeometry args={[stoneR * 0.75, 32, 24]} />
              {gemMaterial}
            </mesh>
          ) : stone.type === "pear" ? (
            <mesh scale={[0.75, 1.0, 1.15]}>
              <sphereGeometry args={[stoneR * 0.75, 32, 24]} />
              {gemMaterial}
            </mesh>
          ) : (
            <mesh>
              <sphereGeometry args={[stoneR * 0.75, 48, 32]} />
              {gemMaterial}
            </mesh>
          )}
        </group>

        {/* Prongs — positioned outside stone, taper up to grip edge */}
        {Array.from({ length: nProngs }, (_, i) => {
          const angle = (i / nProngs) * Math.PI * 2;
          const clearR =
            Math.sqrt(
              (footprint.rx * Math.cos(angle)) ** 2 +
              (footprint.rz * Math.sin(angle)) ** 2
            ) + 0.4;
          const px = Math.cos(angle) * clearR;
          const pz = Math.sin(angle) * clearR;

          return (
            <group key={i} position={[px, 0, pz]}>
              {/* Shaft — tapers from base to tip */}
              <mesh position={[0, prongH / 2, 0]}>
                <cylinderGeometry args={[0.12, 0.3, prongH, 8]} />
                <meshStandardMaterial color={metalColor} metalness={0.92} roughness={0.12} />
              </mesh>
              {/* Tip — grips the stone */}
              <mesh position={[0, prongH, 0]}>
                <sphereGeometry args={[0.18, 8, 6]} />
                <meshStandardMaterial color={metalColor} metalness={0.92} roughness={0.12} />
              </mesh>
            </group>
          );
        })}
      </group>
    </group>
  );
}

/** Parametric fallback pendant — disc/oval + bail + stone. */
function FallbackPendant() {
  const params = useProjectStore((s) => s.currentParams);
  const customization = useProjectStore((s) => s.customization);
  const metalColor = METAL_COLORS[customization.metal_type] ?? "#d4af37";
  const gemColor = GEM_COLORS[customization.gemstone_material] ?? "#b9f2ff";

  const pp = params.pendant_params;
  const baseW = pp?.base_width ?? 15;
  const baseH = pp?.base_height ?? 20;
  const baseT = pp?.base_thickness ?? 2;
  const bailD = pp?.bail_diameter ?? 5;
  const bailT = pp?.bail_thickness ?? 1.5;
  const isOval = pp?.base_shape === "oval";

  const stone = params.center_stone;
  const stoneR = stone.diameter / 2;

  // For oval: squash the cylinder on Y axis (base cylinder lies flat, height → thickness)
  // cylinder args: [radiusTop, radiusBottom, height, radialSegments]
  // We use the larger of baseW, baseH as the cylinder radius, then scale
  const baseRadius = baseW / 2;
  const ovalScaleZ = isOval ? baseH / baseW : 1.0;

  return (
    <group rotation={[-0.2, 0.15, 0]}>
      {/* Base plate — circular or oval */}
      <mesh scale={[1, 1, ovalScaleZ]}>
        <cylinderGeometry args={[baseRadius, baseRadius, baseT, 48]} />
        <meshStandardMaterial color={metalColor} metalness={0.92} roughness={0.12} />
      </mesh>

      {/* Bail loop at top */}
      <mesh position={[0, baseRadius * ovalScaleZ + bailD / 3, 0]}>
        <torusGeometry args={[bailD / 2, bailT / 2, 16, 32, Math.PI]} />
        <meshStandardMaterial color={metalColor} metalness={0.92} roughness={0.12} />
      </mesh>

      {/* Center stone */}
      <mesh position={[0, 0, baseT / 2 + stoneR * 0.3]}>
        <sphereGeometry args={[stoneR * 0.7, 48, 32]} />
        <meshPhysicalMaterial
          color={gemColor}
          transparent
          opacity={0.82}
          roughness={0.02}
          metalness={0.0}
          clearcoat={1.0}
          clearcoatRoughness={0.03}
          ior={2.4}
          thickness={stoneR * 0.5}
        />
      </mesh>
    </group>
  );
}

/** Parametric fallback earring — stud + pin + stone. */
function FallbackEarring() {
  const params = useProjectStore((s) => s.currentParams);
  const customization = useProjectStore((s) => s.customization);
  const metalColor = METAL_COLORS[customization.metal_type] ?? "#d4af37";
  const gemColor = GEM_COLORS[customization.gemstone_material] ?? "#b9f2ff";

  const ep = params.earring_params;
  const studD = ep?.stud_diameter ?? 6;
  const studT = ep?.stud_thickness ?? 1.5;
  const pinL = ep?.pin_length ?? 10;
  const pinD = ep?.pin_diameter ?? 0.8;

  const stone = params.center_stone;
  const stoneR = stone.diameter / 2;

  return (
    <group rotation={[-0.2, 0.15, 0]}>
      {/* Stud base disc */}
      <mesh>
        <cylinderGeometry args={[studD / 2, studD / 2, studT, 48]} />
        <meshStandardMaterial color={metalColor} metalness={0.92} roughness={0.12} />
      </mesh>

      {/* Back pin */}
      <mesh position={[0, -(studT / 2 + pinL / 2), 0]}>
        <cylinderGeometry args={[pinD * 0.3, pinD / 2, pinL, 12]} />
        <meshStandardMaterial color={metalColor} metalness={0.92} roughness={0.12} />
      </mesh>

      {/* Center stone on front face */}
      <mesh position={[0, studT / 2 + stoneR * 0.25, 0]}>
        <sphereGeometry args={[stoneR * 0.65, 48, 32]} />
        <meshPhysicalMaterial
          color={gemColor}
          transparent
          opacity={0.82}
          roughness={0.02}
          metalness={0.0}
          clearcoat={1.0}
          clearcoatRoughness={0.03}
          ior={2.4}
          thickness={stoneR * 0.5}
        />
      </mesh>
    </group>
  );
}
