import { Card } from "@/components/ui/card";
import { useDraggable } from "@dnd-kit/core";
import type { Module } from "../../types";
import { cn } from "@/lib/utils";
import { CSS } from "@dnd-kit/utilities";

interface ModuleCardProps {
  module: Module;
  onClick?: () => void;
  draggable?: boolean;
  highlight?: boolean;
}

export default function ModuleCard({
  module,
  onClick,
  draggable = true,
  highlight = false,
}: ModuleCardProps) {
  const dnd = useDraggable({ id: `module-${module.id}` });
  const setNodeRef = draggable ? dnd.setNodeRef : undefined;
  const listeners = draggable ? dnd.listeners : {};
  const attributes = draggable ? dnd.attributes : {};
  const transform = draggable ? dnd.transform : null;

  return (
    <Card
      className={cn(
        "flex items-center gap-4 p-4 bg-card border border-border shadow-sm transition-transform hover:scale-[1.02] hover:shadow-md cursor-grab",
        {
          "bg-accent cursor-grabbing": highlight,
        }
      )}
      style={{
        transform:
          transform && highlight
            ? CSS.Translate.toString(transform)
            : undefined,
      }}
      {...listeners}
      {...attributes}
      ref={setNodeRef}
      onClick={onClick}
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
  );
}
