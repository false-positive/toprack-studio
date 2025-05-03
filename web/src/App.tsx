import { useState, useEffect } from "react";
import { DndProvider } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";
import ModuleLibrary from "./components/ModuleLibrary";
import RoomVisualization from "./components/RoomVisualization";
import "./App.css";
import { fetchModules } from "./data/modules";

function App() {
  const [loadedModules, setLoadedModules] = useState<Array<any>>([]);
  const [loading, setLoading] = useState(true);

  const [placedModules, setPlacedModules] = useState<
    Array<{
      id: string;
      moduleId: string;
      position: [number, number];
      rotation: number;
    }>
  >([]);

  const [roomDimensions, setRoomDimensions] = useState({
    width: 20, // meters
    height: 15, // meters
    walls: [
      { start: [0, 0], end: [60, 0] },
      { start: [60, 0], end: [60, 45] },
      { start: [60, 45], end: [0, 45] },
      { start: [0, 45], end: [0, 0] },
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
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading modules data...</p>
      </div>
    );
  }

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="app-container">
        <header className="app-header">
          <h1>Data Center Visualization</h1>
        </header>
        <main className="app-content">
          <div className="visualization-container">
            <RoomVisualization
              roomDimensions={roomDimensions}
              placedModules={placedModules}
              modules={loadedModules}
              onModuleRemoved={handleModuleRemoved}
              onModuleRotated={handleModuleRotated}
            />
          </div>
          <div className="library-container">
            <ModuleLibrary
              modules={loadedModules}
              onModulePlaced={handleModulePlaced}
            />
          </div>
        </main>
      </div>
    </DndProvider>
  );
}

export default App;
