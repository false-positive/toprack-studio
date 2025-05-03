import { useState, useEffect } from "react";
import { DndProvider } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";
import ModuleLibrary from "./components/ModuleLibrary";
import RoomVisualization from "./components/RoomVisualization";
import { fetchModules } from "./data/modules";
import type { Module } from "../types";

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
      <div className="flex flex-col min-h-screen bg-background">
        <header className="border-b bg-white/90 backdrop-blur supports-[backdrop-filter]:bg-white/60 px-8 py-4 flex items-center shadow-sm">
          <h1 className="text-base font-semibold tracking-tight text-gray-900">
            Data Center Editor
          </h1>
        </header>
        <main className="flex flex-1 overflow-hidden">
          <div className="flex-1 flex items-stretch">
            <div className="flex-1 relative">
              <RoomVisualization
                roomDimensions={roomDimensions}
                placedModules={placedModules}
                modules={loadedModules}
                onModuleRemoved={handleModuleRemoved}
                onModuleRotated={handleModuleRotated}
              />
            </div>
            <aside className="w-80 max-w-xs border-l bg-muted/50 h-full flex flex-col overflow-y-auto sticky top-0">
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
