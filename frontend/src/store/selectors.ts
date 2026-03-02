/**
 * Derived selectors for the project store.
 */

import { useProjectStore, type ProjectState } from "./useProjectStore";

/** Check if params have changed since last build */
export const useIsDirty = () =>
  useProjectStore((s: ProjectState) => s.buildId === null || s.isBuilding);

/** Whether we have a model ready to display */
export const useHasModel = () =>
  useProjectStore((s: ProjectState) => s.modelUrl !== null);

/** Whether export is allowed (not REJECTED) */
export const useCanExport = () =>
  useProjectStore(
    (s: ProjectState) =>
      s.validationResult !== null &&
      s.validationResult.manufacturing_status !== "REJECTED" &&
      s.buildId !== null
  );
