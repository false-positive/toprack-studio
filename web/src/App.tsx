import { useState, useRef, useEffect } from "react";
import ModuleLibrary from "./components/ModuleLibrary";
import RoomVisualization from "./components/RoomVisualization";
import { fetchActiveModules, fetchModules } from "./data/modules";
import { Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@radix-ui/react-scroll-area";
import { useQuery } from "@tanstack/react-query";
import { DndContext, DragOverlay } from "@dnd-kit/core";
import ModuleCard from "./components/ModuleCard";
import L from "leaflet";
import { ActiveModule } from "types";
import Toolbar from "./components/Toolbar";

function App() {
  const { data: loadedModules = [], isLoading: modulesLoading } = useQuery({
    queryKey: ["modules"],
    queryFn: fetchModules,
  });
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  const [roomDimensions] = useState({
    width: 20, // meters
    height: 15, // meters
    walls: [
      { start: [0, 0] as [number, number], end: [60, 0] as [number, number] },
      { start: [60, 0] as [number, number], end: [60, 45] as [number, number] },
      { start: [60, 45] as [number, number], end: [0, 45] as [number, number] },
      { start: [0, 45] as [number, number], end: [0, 0] as [number, number] },
    ],
  });

  const [activeModuleId, setActiveModuleId] = useState<string | null>(null);

  const mapRef = useRef<L.Map | null>(null);
  const lastMousePosition = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  const { data: activeModules } = useQuery({
    queryKey: ["activeModules"],
    queryFn: () => fetchActiveModules(),
  });

  const [
    TEMPORARY_REMOVE_SOON_activeModules,
    setTEMPORARY_REMOVE_SOON_activeModules,
  ] = useState<Array<ActiveModule>>([]);

  useEffect(() => {
    function handleMouseMove(e: MouseEvent) {
      lastMousePosition.current = { x: e.clientX, y: e.clientY };
    }
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  // Compute unique types for the Select
  const moduleTypes = Array.from(
    new Set(loadedModules.map((m) => m.type).filter(Boolean))
  );

  // Filter modules based on search and type
  const filteredModules = loadedModules.filter((module) => {
    const matchesSearch =
      search.trim() === "" ||
      module.name.toLowerCase().includes(search.trim().toLowerCase());
    const matchesType = typeFilter === "all" || module.type === typeFilter;
    return matchesSearch && matchesType;
  });

  if (modulesLoading || !activeModules) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mb-4"></div>
        <p className="text-muted-foreground">Loading modules data...</p>
      </div>
    );
  }

  return (
    <DndContext
      onDragStart={(event) => {
        // event.active.id is like 'module-<id>'
        const id = String(event.active.id).replace(/^module-/, "");
        setActiveModuleId(id);
      }}
      onDragEnd={(event) => {
        setActiveModuleId(null);
        if (
          event.over &&
          event.over.id === "room" &&
          mapRef.current &&
          activeModuleId
        ) {
          const { x, y } = lastMousePosition.current;
          const mapContainer = mapRef.current.getContainer();
          const rect = mapContainer.getBoundingClientRect();
          const point = L.point(x - rect.left, y - rect.top);
          const latlng = mapRef.current.containerPointToLatLng(point);
          const intCoords: [number, number] = [
            Math.round(latlng.lat),
            Math.round(latlng.lng),
          ];
          const module = loadedModules.find((m) => m.id === activeModuleId);
          setTEMPORARY_REMOVE_SOON_activeModules((prev) => [
            ...prev,
            {
              id: prev.length > 0 ? prev[prev.length - 1].id + 1 : 1,
              x: intCoords[0],
              y: intCoords[1],
              module_details: {
                id: Math.random(),
                name: module?.name ?? "Hardcoded Foobar",
                attributes: module?.attributes ?? {},
              },
            },
          ]);
        }
        // handle drop logic here if needed
      }}
      onDragCancel={() => setActiveModuleId(null)}
    >
      <div className="flex flex-col min-h-screen bg-background text-foreground dark">
        <header className="w-full h-(--header-height) border-b flex items-center border-border bg-card/80 backdrop-blur supports-[backdrop-filter]:bg-card/60 shadow-sm px-0 py-0">
          <div className="flex items-center gap-3 px-8 py-3">
            <span className="inline-flex items-center justify-center rounded-full bg-primary text-primary-foreground p-1.5">
              <Sparkles className="h-4 w-4" />
            </span>
            <h1 className="text-base font-semibold tracking-tight">
              Data Center Editor
            </h1>
          </div>
        </header>
        <main className="flex flex-1 h-[calc(100vh-var(--header-height)-var(--footer-height))]">
          <Toolbar />
          <div className="flex-1 flex items-stretch">
            <div className="flex-1 bg-gradient-to-br from-background via-muted to-background">
              <RoomVisualization
                roomDimensions={roomDimensions}
                modules={loadedModules}
                mapRef={mapRef}
                activeModules={TEMPORARY_REMOVE_SOON_activeModules}
              />
            </div>
            <aside className="w-80 max-w-xs border-l border-border bg-card/90 h-full flex flex-col overflow-y-auto sticky top-0 shadow-md px-4 py-6">
              <div className="mb-6">
                <h2 className="text-lg font-bold mb-4">Module Library</h2>
                <Card>
                  <CardContent>
                    <div className="flex flex-col gap-2">
                      <Label
                        htmlFor="module-search"
                        className="text-xs text-muted-foreground"
                      >
                        Search modules
                      </Label>
                      <Input
                        id="module-search"
                        type="text"
                        placeholder="Search modules..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full text-sm bg-background text-foreground border-border"
                      />
                    </div>
                    <div className="flex flex-col gap-2">
                      <Label
                        htmlFor="type-filter"
                        className="text-xs text-muted-foreground"
                      >
                        Type
                      </Label>
                      <Select value={typeFilter} onValueChange={setTypeFilter}>
                        <SelectTrigger
                          id="type-filter"
                          className="w-full text-sm bg-background text-foreground border-border"
                        >
                          <SelectValue placeholder="All Types" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Types</SelectItem>
                          {moduleTypes.map((type) => (
                            <SelectItem key={type} value={type}>
                              {type}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </CardContent>
                </Card>
                <Separator className="mt-5 bg-border" />
              </div>
              <ScrollArea className="h-[200px]">
                <ModuleLibrary modules={filteredModules} />
              </ScrollArea>
            </aside>
          </div>
        </main>
      </div>
      <DragOverlay>
        {activeModuleId ? (
          <div className="opacity-80">
            {(() => {
              const module = loadedModules.find((m) => m.id === activeModuleId);
              return module ? (
                <ModuleCard
                  module={module}
                  draggable={false}
                  highlight={true}
                />
              ) : null;
            })()}
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}

export default App;
