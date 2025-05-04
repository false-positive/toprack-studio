import type { ActiveModule, Module } from "../../types";
import type { ModuleAttribute } from "../../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function fetchModules(dataCenterId: number): Promise<Module[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/modules/?data_center=${dataCenterId}`
  );
  if (!response.ok) throw new Error("Failed to fetch modules");
  const json = await response.json();
  return json.data.map(
    (mod: {
      id: string | number;
      name: string;
      attributes: ModuleAttribute[];
    }) => {
      // Pick the first numeric attribute as amount/unit for display
      let unit = "";
      let amount = 0;
      if (Array.isArray(mod.attributes)) {
        const firstNumeric = mod.attributes.find(
          (attr: { amount: unknown }) => typeof attr.amount === "number"
        );
        if (firstNumeric) {
          unit = firstNumeric.unit;
          if (typeof firstNumeric.amount === "number") {
            amount = firstNumeric.amount;
          }
        }
      }
      const dims = getModuleDimensions(mod.name);
      const spaceXAttr = Array.isArray(mod.attributes)
        ? mod.attributes.find(
            (attr: { unit: string }) => attr.unit === "Space_X"
          )
        : undefined;
      const spaceYAttr = Array.isArray(mod.attributes)
        ? mod.attributes.find(
            (attr: { unit: string }) => attr.unit === "Space_Y"
          )
        : undefined;
      const usablePowerAttr = Array.isArray(mod.attributes)
        ? mod.attributes.find(
            (attr: { unit: string }) => attr.unit === "Usable_Power"
          )
        : undefined;
      const weightAttr = Array.isArray(mod.attributes)
        ? mod.attributes.find(
            (attr: { unit: string }) => attr.unit === "Weight"
          )
        : undefined;
      const isInput = Array.isArray(mod.attributes)
        ? mod.attributes.some((attr: { is_input: boolean }) => attr.is_input)
        : false;
      const isOutput = Array.isArray(mod.attributes)
        ? mod.attributes.some((attr: { is_output: boolean }) => attr.is_output)
        : false;
      return {
        id: String(mod.id),
        name: mod.name,
        type: getModuleType(mod.name),
        width:
          spaceXAttr && typeof spaceXAttr.amount === "number"
            ? spaceXAttr.amount
            : dims.width,
        depth:
          spaceYAttr && typeof spaceYAttr.amount === "number"
            ? spaceYAttr.amount
            : dims.depth,
        height: dims.height,
        power:
          usablePowerAttr && typeof usablePowerAttr.amount === "number"
            ? usablePowerAttr.amount
            : 0,
        weight:
          weightAttr && typeof weightAttr.amount === "number"
            ? weightAttr.amount
            : 0,
        color: getModuleColor(mod.name),
        icon: undefined,
        isInput,
        isOutput,
        unit,
        amount,
        attributes: Array.isArray(mod.attributes) ? mod.attributes : [],
      };
    }
  );
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
export function getModuleColor(name: string): string {
  if (name.includes("Network") || name.includes("Switch")) return "#10b981";
  if (name.includes("Data")) return "#22c55e"; // Added a fresh green for data-related items
  if (name.includes("Rack")) return "#ef4444"; // Changed to a vibrant red
  if (name.includes("Water_Chiller") || name.includes("CRAC")) return "#06b6d4";
  if (name.includes("Water")) return "#1e40af"; // supply - dark blue
  if (name.includes("Transformer") || name.includes("Power")) return "#f59e0b";
  if (name.includes("Storage")) return "#8b5cf6";
  if (name.includes("Security")) return "#ec4899";
  return "#a1a1aa";
}

export async function fetchActiveModules(dataCenterId: number) {
  const response = await fetch(
    `${API_BASE_URL}/api/active-modules/?data_center=${dataCenterId}`
  );
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

export async function addActiveModule({
  x,
  y,
  moduleId,
  dataCenterComponentId,
  dataCenterId,
}: {
  x: number;
  y: number;
  moduleId: string | number;
  dataCenterComponentId?: number;
  dataCenterId: number;
}): Promise<ActiveModule> {
  const body: Record<string, unknown> = {
    x,
    y,
    module: moduleId,
    data_center: dataCenterId,
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
  const payload = await response.json();
  return {
    ...payload,
    data: {
      ...payload.data,
      x: payload.data.y,
      y: payload.data.x,
    },
  };
}

export async function deleteActiveModule(
  id: number,
  dataCenterId: number
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/active-modules/${id}/?data_center=${dataCenterId}`,
    {
      method: "DELETE",
    }
  );
  if (!response.ok) throw new Error("Failed to delete active module");
}

export async function fetchValidationResults(dataCenterId: number) {
  const response = await fetch(
    `${API_BASE_URL}/api/validate-component-values/?data_center=${dataCenterId}`
  );
  if (!response.ok) throw new Error("Failed to fetch validation results");
  return response.json();
}

export async function fetchDataCenterDetails(dataCenterId: number) {
  const response = await fetch(
    `${API_BASE_URL}/api/datacenters/${dataCenterId}/`
  );
  if (!response.ok) throw new Error("Failed to fetch data center details");
  return response.json();
}

export async function fetchDisplayControl(): Promise<"vr" | "website"> {
  const response = await fetch(`${API_BASE_URL}/api/display-control/`);
  if (!response.ok) throw new Error("Failed to fetch display control");
  const json = await response.json();
  return json.data.current_display;
}

export async function toggleDisplayControl(): Promise<"vr" | "website"> {
  const response = await fetch(`${API_BASE_URL}/api/display-control/toggle/`);
  if (!response.ok) throw new Error("Failed to toggle display control");
  const json = await response.json();
  return json.data.current_display;
}
