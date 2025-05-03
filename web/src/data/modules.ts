import type { ActiveModule, Module } from "../../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function fetchModules(): Promise<Module[]> {
  const response = await fetch(`${API_BASE_URL}/api/modules/`);
  if (!response.ok) throw new Error("Failed to fetch modules");
  const json = await response.json();
  return json.data.map((mod: Module) => {
    // Pick the first numeric attribute as amount/unit for display
    let unit = "";
    let amount = 0;
    if (mod.attributes) {
      const firstKey = Object.keys(mod.attributes).find(
        (k) => typeof mod.attributes[k] === "number"
      );
      if (firstKey) {
        unit = firstKey;
        const amountIdk = mod.attributes[firstKey].amount;
        if (typeof amountIdk === "number") {
          amount = amountIdk;
        }
      }
    }
    const dims = getModuleDimensions(mod.name);
    return {
      id: String(mod.id),
      name: mod.name,
      type: getModuleType(mod.name),
      width: mod.attributes?.Space_X?.amount || dims.width,
      depth: mod.attributes?.Space_Y?.amount || dims.depth,
      height: dims.height,
      power: mod.attributes?.Usable_Power?.amount || 0,
      weight: mod.attributes?.Weight?.amount || 0,
      color: getModuleColor(mod.name),
      icon: undefined,
      isInput: mod.attributes?.is_input,
      isOutput: mod.attributes?.is_output,
      unit,
      amount,
      attributes: mod.attributes,
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

export async function fetchActiveModules() {
  const response = await fetch(`${API_BASE_URL}/api/active-modules/`);
  if (!response.ok) throw new Error("Failed to fetch active modules");
  const json = await response.json();
  return json as {
    data: ActiveModule[];
    data_center: {
      id: number;
      name: string;
      space_x: number;
      space_y: number;
    };
  };
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export async function addActiveModuleFake(_unused: {
  moduleId: string;
  x: number;
  y: number;
  moduleDetails: {
    id: number;
    name: string;
    attributes: Record<string, unknown>;
  };
}): Promise<Awaited<ReturnType<typeof fetchActiveModules>>> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 1000));
  // In a real implementation, you would POST to the backend here
  // For now, just return the current active modules (simulate backend update)
  return fetchActiveModules();
}

export async function addActiveModule({
  x,
  y,
  moduleId,
  dataCenterComponentId,
}: {
  x: number;
  y: number;
  moduleId: string | number;
  dataCenterComponentId?: number;
}): Promise<ActiveModule> {
  const body: Record<string, unknown> = {
    x,
    y,
    module: moduleId,
  };
  if (dataCenterComponentId) {
    body.data_center_component = dataCenterComponentId;
  }
  const response = await fetch(`${API_BASE_URL}/api/active-modules/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error("Failed to add active module");
  return response.json();
}

export async function deleteActiveModule(id: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/active-modules/${id}/`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error("Failed to delete active module");
}
