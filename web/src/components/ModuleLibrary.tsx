import type { Module } from "../../types";
import ModuleCard from "./ModuleCard";

interface ModuleLibraryProps {
  modules: Module[];
  onModulePlaced: (moduleId: string, position: [number, number]) => void;
}

export default function ModuleLibrary({ modules }: ModuleLibraryProps) {
  return (
    <div className="flex flex-col gap-4">
      {modules.length > 0 ? (
        modules.map((module) => <ModuleCard key={module.id} module={module} />)
      ) : (
        <div className="text-muted-foreground text-center py-4">
          No modules match your search criteria
        </div>
      )}
    </div>
  );
}
