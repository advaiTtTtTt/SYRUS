/**
 * Export helpers — trigger browser download of STL/GLB.
 */

export function downloadModel(buildId: string, format: "stl" | "glb", jewelryType: string = "ring") {
  const url = `/api/build/${buildId}/model.${format}`;
  const a = document.createElement("a");
  a.href = url;
  a.download = `${jewelryType}.${format}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}
