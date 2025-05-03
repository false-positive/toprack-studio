import { Card } from "@/components/ui/card";
import { useState } from "react";
import { useDrag } from "react-dnd";
import type { Module } from "../../types";

interface ModuleLibraryProps {
  modules: Module[];
  onModulePlaced: (moduleId: string, position: [number, number]) => void;
}

interface ModuleItemProps {
  module: Module;
}

function ModuleItem({ module }: ModuleItemProps) {
  const [{ isDragging }, drag] = useDrag(() => ({
    type: "MODULE",
    item: { id: module.id },
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging(),
    }),
  }));

  // Use a callback ref to attach drag to the Card
  const setDragRef = (node: HTMLDivElement | null) => {
    if (node) drag(node);
  };

  return (
    <Card
      ref={setDragRef}
      className={`flex items-center gap-4 p-4 mb-2 shadow transition-opacity ${
        isDragging ? "opacity-50" : "opacity-100"
      }`}
    >
      <div
        className="flex items-center justify-center w-12 h-12 rounded bg-gray-100 text-lg font-bold"
        style={{ backgroundColor: module.color }}
      >
        {module.icon || module.name.charAt(0)}
      </div>
      <div className="flex-1">
        <h3 className="font-semibold text-base leading-tight">{module.name}</h3>
        <p className="text-xs text-muted-foreground">
          {module.width}m × {module.depth}m
        </p>
        <div className="flex gap-2 mt-1 text-xs">
          <span className="bg-muted px-2 py-0.5 rounded">{module.type}</span>
          <span className="bg-muted px-2 py-0.5 rounded">
            {module.amount} {module.unit}
          </span>
        </div>
        <div className="flex gap-2 mt-1 text-xs">
          {module.isInput && (
            <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
              Input
            </span>
          )}
          {module.isOutput && (
            <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded">
              Output
            </span>
          )}
        </div>
      </div>
    </Card>
  );
}

export default function ModuleLibrary({ modules }: ModuleLibraryProps) {
  const [filter, setFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState<string | null>(null);

  // Get unique module types for filter
  const moduleTypes = Array.from(new Set(modules.map((m) => m.type)));

  // Filter modules based on search and type filter
  const filteredModules = modules.filter((module) => {
    const matchesSearch = module.name
      .toLowerCase()
      .includes(filter.toLowerCase());
    const matchesType = !typeFilter || module.type === typeFilter;
    return matchesSearch && matchesType;
  });

  return (
    <div className="flex flex-col gap-4 p-4">
      <h2 className="text-xl font-bold mb-2">Module Library</h2>

      <div className="flex gap-2 mb-2">
        <input
          type="text"
          placeholder="Search modules..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="input input-bordered w-full max-w-xs"
        />
        <select
          value={typeFilter || ""}
          onChange={(e) => setTypeFilter(e.target.value || null)}
          className="select select-bordered"
        >
          <option value="">All Types</option>
          {moduleTypes.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-2">
        {filteredModules.length > 0 ? (
          filteredModules.map((module) => (
            <ModuleItem key={module.id} module={module} />
          ))
        ) : (
          <div className="text-muted-foreground text-center py-4">
            No modules match your search criteria
          </div>
        )}
      </div>
    </div>
  );
}
