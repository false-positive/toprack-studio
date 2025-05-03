import { useState } from "react";
import { useDrag } from "react-dnd";
import type { Module } from "../types";

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

    return (
        <div ref={drag} className={`module-item ${isDragging ? "dragging" : ""}`} style={{ opacity: isDragging ? 0.5 : 1 }}>
            <div className="module-icon" style={{ backgroundColor: module.color }}>
                {module.icon || module.name.charAt(0)}
            </div>
            <div className="module-details">
                <h3>{module.name}</h3>
                <p className="module-dimensions">
                    {module.width}m × {module.depth}m
                </p>
                <div className="module-info">
                    <span className="module-type">{module.type}</span>
                    <span className="module-price">
                        {module.amount} {module.unit}
                    </span>
                </div>
                <div className="module-io">
                    {module.isInput && <span className="module-input">Input</span>}
                    {module.isOutput && <span className="module-output">Output</span>}
                </div>
            </div>
        </div>
    );
}

export default function ModuleLibrary({ modules, onModulePlaced }: ModuleLibraryProps) {
    const [filter, setFilter] = useState("");
    const [typeFilter, setTypeFilter] = useState<string | null>(null);

    // Get unique module types for filter
    const moduleTypes = Array.from(new Set(modules.map((m) => m.type)));

    // Filter modules based on search and type filter
    const filteredModules = modules.filter((module) => {
        const matchesSearch = module.name.toLowerCase().includes(filter.toLowerCase());
        const matchesType = !typeFilter || module.type === typeFilter;
        return matchesSearch && matchesType;
    });

    return (
        <div className="module-library">
            <h2>Module Library</h2>

            <div className="library-filters">
                <input type="text" placeholder="Search modules..." value={filter} onChange={(e) => setFilter(e.target.value)} className="search-input" />

                <select value={typeFilter || ""} onChange={(e) => setTypeFilter(e.target.value || null)} className="type-filter">
                    <option value="">All Types</option>
                    {moduleTypes.map((type) => (
                        <option key={type} value={type}>
                            {type}
                        </option>
                    ))}
                </select>
            </div>

            <div className="modules-list">
                {filteredModules.length > 0 ? (
                    filteredModules.map((module) => <ModuleItem key={module.id} module={module} />)
                ) : (
                    <div className="no-modules">No modules match your search criteria</div>
                )}
            </div>
        </div>
    );
}
