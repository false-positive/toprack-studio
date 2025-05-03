import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Hand, MousePointer, Crop, Brush, Eraser, Shapes, Move } from "lucide-react";
import { useState } from "react";

const TOOLS = [
    { value: "hand", icon: Hand, label: "Hand (Move)" },
    { value: "select", icon: MousePointer, label: "Select" },
    { value: "crop", icon: Crop, label: "Crop" },
    { value: "brush", icon: Brush, label: "Brush" },
    { value: "eraser", icon: Eraser, label: "Eraser" },
    { value: "shapes", icon: Shapes, label: "Shapes" },
    { value: "move", icon: Move, label: "Move Tool" },
];

export default function Toolbar() {
    // Only one tool can be selected at a time, default to 'hand'
    const [selected, setSelected] = useState<string>("hand");

    return (
        <aside className="absolute left-0 top-45 ml-6 mt-6 z-20 flex flex-col items-center gap-2 bg-card/80 rounded-r-xl shadow-lg border-r border-border p-2 w-10 mx-auto">
            <TooltipProvider>
                <ToggleGroup type="single" value={selected} onValueChange={(v) => setSelected(v || "hand")} className="flex flex-col gap-2 w-full items-center justify-center">
                    {TOOLS.map((tool) => (
                        <Tooltip key={tool.value}>
                            <TooltipTrigger asChild>
                                <ToggleGroupItem
                                    value={tool.value}
                                    aria-label={tool.label}
                                    className={`w-10 h-10 aspect-square flex items-center justify-center rounded-md ${
                                        selected === tool.value ? "bg-primary text-primary-foreground" : ""
                                    }`}
                                >
                                    <tool.icon className="w-5 h-5" />
                                </ToggleGroupItem>
                            </TooltipTrigger>
                            <TooltipContent side="right">{tool.label}</TooltipContent>
                        </Tooltip>
                    ))}
                </ToggleGroup>
            </TooltipProvider>
        </aside>
    );
}
