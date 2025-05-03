import type { Module } from "../types";

// Function to fetch and parse the CSV data
async function fetchModules(): Promise<Module[]> {
    try {
        const response = await fetch("https://hebbkx1anhila5yf.public.blob.vercel-storage.com/modules-gAtcNlIudxiEmpgpmbdrgiguKL68oj.csv");
        const text = await response.text();

        // Parse CSV
        const rows = text.split("\n").filter((row) => row.trim() !== "");

        // Skip header row
        const modules: Module[] = [];

        for (let i = 1; i < rows.length; i++) {
            const columns = rows[i].split("\t");

            if (columns.length >= 6) {
                const id = columns[0].trim();
                const name = columns[1].trim();
                const isInput = columns[2].trim() === "1";
                const isOutput = columns[3].trim() === "1";
                const unit = columns[4].trim();
                const amount = Number.parseFloat(columns[5].trim());

                // Generate dimensions based on the module name
                // This is a simplification - in a real app, dimensions would come from the data
                const dimensions = getModuleDimensions(name);

                modules.push({
                    id,
                    name,
                    type: getModuleType(name),
                    width: dimensions.width,
                    depth: dimensions.depth,
                    height: dimensions.height,
                    power: isInput ? 100 : 0, // Simplified power calculation
                    weight: amount / 100, // Simplified weight calculation
                    color: getModuleColor(name),
                    isInput,
                    isOutput,
                    unit,
                    amount,
                });
            }
        }

        return modules;
    } catch (error) {
        console.error("Error fetching modules:", error);
        return [];
    }
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
function getModuleDimensions(name: string): { width: number; depth: number; height: number } {
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

// Export the fetch function so it can be called when the app initializes
export { fetchModules };

// Export an empty array as default, which will be replaced when data is loaded
export default modules;
