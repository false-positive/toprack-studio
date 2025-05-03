import { Card } from "@/components/ui/card";
import type { Module } from "../../types";

interface ModuleLibraryProps {
  modules: Module[];
  onModulePlaced: (moduleId: string, position: [number, number]) => void;
}

export default function ModuleLibrary({ modules }: ModuleLibraryProps) {
  return (
    <div className="flex flex-col gap-4">
      {modules.length > 0 ? (
        modules.map((module) => (
          <Card
            key={module.id}
            className="flex items-center gap-4 p-4 bg-card border border-border shadow-sm rounded-lg transition-transform hover:scale-[1.02] hover:shadow-md cursor-pointer"
          >
            <div className="flex items-center justify-center w-12 h-12 rounded bg-primary text-primary-foreground text-lg font-bold">
              {module.icon || module.name.charAt(0)}
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-base leading-tight text-foreground">
                {module.name}
              </h3>
              <p className="text-xs text-muted-foreground">
                {module.width}m × {module.depth}m
              </p>
              <div className="flex gap-2 mt-1 text-xs">
                <span className="bg-muted px-2 py-0.5 rounded text-foreground">
                  {module.type}
                </span>
                <span className="bg-muted px-2 py-0.5 rounded text-foreground">
                  {module.amount} {module.unit}
                </span>
              </div>
              <div className="flex gap-2 mt-1 text-xs">
                {module.isInput && (
                  <span className="bg-primary/20 text-primary px-2 py-0.5 rounded">
                    Input
                  </span>
                )}
                {module.isOutput && (
                  <span className="bg-green-900/30 text-green-400 px-2 py-0.5 rounded">
                    Output
                  </span>
                )}
              </div>
            </div>
          </Card>
        ))
      ) : (
        <div className="text-muted-foreground text-center py-4">
          No modules match your search criteria
        </div>
      )}
    </div>
  );
}
