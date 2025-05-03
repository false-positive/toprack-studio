import type { Module } from "../../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function fetchModules(): Promise<Module[]> {
  const response = await fetch(`${API_BASE_URL}/api/modules/`);
  if (!response.ok) throw new Error("Failed to fetch modules");
  const json = await response.json();
  return json.data.map((mod: any) => {
    // Pick the first numeric attribute as amount/unit for display
    let unit = "";
    let amount = 0;
    if (mod.attributes) {
      const firstKey = Object.keys(mod.attributes).find(
        (k) => typeof mod.attributes[k] === "number"
      );
      if (firstKey) {
        unit = firstKey;
        amount = mod.attributes[firstKey];
      }
    }
    const dims = getModuleDimensions(mod.name);
    return {
      id: String(mod.id),
      name: mod.name,
      type: getModuleType(mod.name),
      width: mod.attributes?.Space_X?.value || dims.width,
      depth: mod.attributes?.Space_Y?.value || dims.depth,
      height: dims.height,
      power: mod.attributes?.Usable_Power?.value || 0,
      weight: mod.attributes?.Weight?.value || 0,
      color: getModuleColor(mod.name),
      icon: undefined,
      isInput: mod.is_input,
      isOutput: mod.is_output,
      unit,
      amount,
    };
  });
}

// Helper function to determine module type from name
function getModuleType(name: string): string {
  if (name.includes("Rack")) return "Rack";
  if (name.includes("Cooling") || name.includes("CRAC")) return "Cooling";
  if (name.includes("UPS") || name.includes("Power")) return "Power";
  if (name.includes("Network") || name.includes("Switch")) return "Network";
  if (name.includes("Storage")) return "Storage";
  if (name.includes("Security")) return "Security";
  return "Other";
}

// Helper function to determine module dimensions from name
function getModuleDimensions(name: string): {
  width: number;
  depth: number;
  height: number;
} {
  // Default dimensions
  const defaults = { width: 0.6, depth: 1.0, height: 2.0 };

  // Customize based on module type
  if (name.includes("Rack")) {
    return { width: 0.6, depth: 1.2, height: 2.0 };
  }
  if (name.includes("Cooling")) {
    return { width: 0.8, depth: 1.0, height: 2.0 };
  }
  if (name.includes("UPS")) {
    return { width: 0.8, depth: 0.9, height: 1.8 };
  }
  if (name.includes("PDU") || name.includes("Power")) {
    return { width: 0.4, depth: 0.6, height: 1.8 };
  }

  return defaults;
}

// Helper function to determine module color from name
function getModuleColor(name: string): string {
  if (name.includes("Rack")) return "#3b82f6";
  if (name.includes("Cooling") || name.includes("CRAC")) return "#06b6d4";
  if (name.includes("UPS") || name.includes("Power")) return "#f59e0b";
  if (name.includes("Network") || name.includes("Switch")) return "#10b981";
  if (name.includes("Storage")) return "#8b5cf6";
  if (name.includes("Security")) return "#ec4899";
  return "#a1a1aa";
}

// Create a placeholder modules array that will be populated when the data is loaded
const modules: Module[] = [];

// Export an empty array as default, which will be replaced when data is loaded
export default modules;
