import { useState, useEffect } from "react";
import { DndProvider } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";
import ModuleLibrary from "./components/ModuleLibrary";
import RoomVisualization from "./components/RoomVisualization";
import { fetchModules } from "./data/modules";
import type { Module } from "../types";
import { Sparkles } from "lucide-react";

function App() {
  const [loadedModules, setLoadedModules] = useState<Module[]>([]);
  const [loading, setLoading] = useState(true);

  const [placedModules, setPlacedModules] = useState<
    Array<{
      id: string;
      moduleId: string;
      position: [number, number];
      rotation: number;
    }>
  >([]);

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

  // Load modules data when component mounts
  useEffect(() => {
    async function loadModules() {
      setLoading(true);
      const data = await fetchModules();
      setLoadedModules(data);
      setLoading(false);
    }

    loadModules();
  }, []);

  const handleModulePlaced = (moduleId: string, position: [number, number]) => {
    setPlacedModules((prev) => [
      ...prev,
      {
        id: `${moduleId}-${Date.now()}`,
        moduleId,
        position,
        rotation: 0,
      },
    ]);
  };

  const handleModuleRemoved = (id: string) => {
    setPlacedModules((prev) => prev.filter((module) => module.id !== id));
  };

  const handleModuleRotated = (id: string) => {
    setPlacedModules((prev) =>
      prev.map((module) =>
        module.id === id
          ? { ...module, rotation: (module.rotation + 90) % 360 }
          : module
      )
    );
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mb-4"></div>
        <p className="text-muted-foreground">Loading modules data...</p>
      </div>
    );
  }

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="flex flex-col min-h-screen bg-background text-foreground dark">
        <header className="w-full border-b border-border bg-card/80 backdrop-blur supports-[backdrop-filter]:bg-card/60 shadow-sm px-0 py-0">
          <div className="flex items-center gap-3 px-8 py-3">
            <span className="inline-flex items-center justify-center rounded-full bg-primary text-primary-foreground p-1.5">
              <Sparkles className="h-4 w-4" />
            </span>
            <h1 className="text-base font-semibold tracking-tight">
              Data Center Editor
            </h1>
          </div>
        </header>
        <main className="flex flex-1 overflow-hidden">
          <div className="flex-1 flex items-stretch">
            <div className="flex-1 relative bg-gradient-to-br from-background via-muted to-background">
              <RoomVisualization
                roomDimensions={roomDimensions}
                placedModules={placedModules}
                modules={loadedModules}
                onModuleRemoved={handleModuleRemoved}
                onModuleRotated={handleModuleRotated}
              />
            </div>
            <aside className="w-80 max-w-xs border-l border-border bg-card/90 h-full flex flex-col overflow-y-auto sticky top-0 shadow-md px-4 py-6">
              <div className="mb-6">
                <h2 className="text-lg font-bold mb-4">Module Library</h2>
                <div className="flex flex-col gap-2 bg-muted/50 rounded-lg p-3 mb-4">
                  <input
                    type="text"
                    placeholder="Search modules..."
                    className="input input-bordered w-full text-sm bg-background text-foreground border-border"
                  />
                  <select className="select select-bordered w-full text-sm bg-background text-foreground border-border">
                    <option value="">All Types</option>
                    {/* Dynamically render types here if needed */}
                  </select>
                </div>
              </div>
              <ModuleLibrary
                modules={loadedModules}
                onModulePlaced={handleModulePlaced}
              />
            </aside>
          </div>
        </main>
      </div>
    </DndProvider>
  );
}

export default App;
