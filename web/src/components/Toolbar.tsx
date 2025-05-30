import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Hand,
  MousePointer,
  Crop,
  Brush,
  Eraser,
  Shapes,
  Move,
} from "lucide-react";
import { useAtom } from "jotai";
import { selectedToolAtom } from "@/projectsAtom";

const TOOLS = [
  { value: "hand", icon: Hand, label: "Hand (Move)" },
  { value: "select", icon: MousePointer, label: "Select" },
  { value: "crop", icon: Crop, label: "Crop" },
  { value: "brush", icon: Brush, label: "Brush" },
  { value: "eraser", icon: Eraser, label: "Eraser" },
  { value: "shapes", icon: Shapes, label: "Shapes" },
  { value: "move", icon: Move, label: "Move Tool" },
];

export default function Toolbar({
  className = "",
  ...props
}: React.HTMLAttributes<HTMLElement>) {
  // Use global atom for selected tool
  const [selected, setSelected] = useAtom(selectedToolAtom);

  return (
    <aside
      className={`absolute left-0 top-45 ml-6 mt-6 z-[500] flex flex-col items-center gap-2 bg-card/80 rounded-r-xl shadow-lg border-r border-border p-2 w-10 mx-auto ${className}`}
      {...props}
    >
      <TooltipProvider>
        <ToggleGroup
          type="single"
          value={selected}
          onValueChange={(v) => setSelected(v || "hand")}
          className="flex flex-col gap-2 w-full items-center justify-center"
        >
          {TOOLS.map((tool) => (
            <Tooltip key={tool.value}>
              <TooltipTrigger asChild>
                <ToggleGroupItem
                  value={tool.value}
                  aria-label={tool.label}
                  className={`w-10 h-10 aspect-square flex items-center justify-center rounded-md transition-colors duration-150
                                        ${
                                          selected === tool.value
                                            ? "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground"
                                            : "bg-card text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                                        }
                                    `}
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
