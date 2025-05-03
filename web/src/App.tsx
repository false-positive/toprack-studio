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
import { Route, Routes, Link } from "react-router";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from "@/components/ui/popover";
import { CardHeader, CardTitle } from "@/components/ui/card";
import { Pencil, Plus, Trash2, MoreVertical } from "lucide-react";
import { useAtom } from "jotai";
import { atomWithStorage } from "jotai/utils";
import { useParams } from "react-router";

// Project type
interface Project {
  id: number;
  name: string;
  lastOpenedAt: string; // ISO string for serialization
}

// Jotai atom for projects, persisted to localStorage
const projectsAtom = atomWithStorage<Project[]>("projects", []);

function App() {
  return (
    <Routes>
      <Route path="/" element={<SplashScreen />} />
      <Route path="/projects/:projectId" element={<EditorPage />} />
    </Routes>
  );
}

function SplashScreen() {
  const [projects, setProjects] = useAtom(projectsAtom);
  const [newProjectDialogOpen, setNewProjectDialogOpen] = useState(false);
  const [renameDialogOpen, setRenameDialogOpen] = useState<number | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState<number | null>(null);
  const [newProjectName, setNewProjectName] = useState("");
  const [renameValue, setRenameValue] = useState("");

  function handleCreateProject() {
    if (newProjectName.trim()) {
      setProjects((prev) => [
        ...prev,
        {
          id: Date.now(),
          name: newProjectName.trim(),
          lastOpenedAt: new Date().toISOString(),
        },
      ]);
      setNewProjectName("");
      setNewProjectDialogOpen(false);
    }
  }

  function handleRenameProject(id: number) {
    setProjects((prev) =>
      prev.map((p) => (p.id === id ? { ...p, name: renameValue } : p))
    );
    setRenameDialogOpen(null);
    setRenameValue("");
  }

  function handleDeleteProject(id: number) {
    setProjects((prev) => prev.filter((p) => p.id !== id));
    setDeleteDialogOpen(null);
  }

  // Helper to format relative time
  function formatRelativeTime(dateString: string) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    if (minutes < 1) return rtf.format(0, "minute");
    if (minutes < 60) return rtf.format(-minutes, "minute");
    if (hours < 24) return rtf.format(-hours, "hour");
    return rtf.format(-days, "day");
  }

  // Split projects: first 2 are cards, rest are in the list
  const cardProjects = projects.slice(0, 2);
  const listProjects = projects.slice(2);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background px-4">
      <div
        className="w-full max-w-2xl mx-auto flex flex-col gap-2 justify-center"
        style={{ minHeight: "100vh" }}
      >
        <header className="flex flex-col items-center gap-1 mt-6 mb-2">
          <span className="inline-flex items-center justify-center rounded-full bg-primary text-primary-foreground p-2 mb-1">
            <Sparkles className="h-6 w-6" />
          </span>
          <h1 className="text-2xl font-bold tracking-tight">
            Welcome to Data Center Designer
          </h1>
          <p className="text-muted-foreground text-base">
            Design, manage, and visualize your data center projects.
          </p>
        </header>
        {/* Card row: 2 most recent + add */}
        <div className="flex justify-center w-full">
          <div className="flex flex-row gap-4">
            {cardProjects.map((project) => (
              <Card
                key={project.id}
                className="w-64 min-w-[240px] flex-shrink-0 relative group"
              >
                <div className="aspect-video bg-muted rounded-lg flex items-center justify-center mb-3">
                  <span className="text-muted-foreground text-5xl">
                    <Sparkles className="w-12 h-12 opacity-30" />
                  </span>
                </div>
                <CardHeader className="flex flex-row items-center justify-between px-4 pt-0 pb-2">
                  <CardTitle className="truncate max-w-[120px]">
                    {project.name}
                  </CardTitle>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="hover:bg-accent"
                      >
                        <MoreVertical className="w-5 h-5" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent
                      align="end"
                      sideOffset={8}
                      className="min-w-[140px] p-1"
                    >
                      <button
                        className="flex w-full items-center gap-2 rounded px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground transition-colors"
                        onClick={() => {
                          setRenameDialogOpen(project.id);
                          setRenameValue(project.name);
                        }}
                      >
                        <Pencil className="w-4 h-4 mr-2" /> Rename
                      </button>
                      <button
                        className="flex w-full items-center gap-2 rounded px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground text-destructive"
                        onClick={() => setDeleteDialogOpen(project.id)}
                      >
                        <Trash2 className="w-4 h-4 mr-2" /> Delete
                      </button>
                    </PopoverContent>
                  </Popover>
                </CardHeader>
                <CardContent className="px-4 pb-4">
                  <div className="flex flex-col gap-2">
                    <span className="text-xs text-muted-foreground">
                      Last opened: {formatRelativeTime(project.lastOpenedAt)}
                    </span>
                    <Button
                      asChild
                      variant="secondary"
                      size="sm"
                      className="w-full mt-2"
                    >
                      <Link to={`/projects/${project.id}`}>Open Project</Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
            {/* Add New Project Card */}
            <Card
              className="w-64 min-w-[240px] flex-shrink-0 flex flex-col items-center justify-center cursor-pointer hover:shadow-lg transition-shadow border-dashed border-2 border-primary/40 bg-muted/50"
              onClick={() => setNewProjectDialogOpen(true)}
            >
              <div className="flex flex-col items-center justify-center flex-1 py-8">
                <span className="inline-flex items-center justify-center rounded-full bg-primary text-primary-foreground p-3 mb-2">
                  <Plus className="h-8 w-8" />
                </span>
                <span className="text-lg font-semibold">
                  Create New Project
                </span>
              </div>
            </Card>
          </div>
        </div>
        {/* Minimalist List for remaining projects */}
        {listProjects.length > 0 && (
          <div className="mt-4 flex flex-col items-center w-full">
            <div className="text-xs text-muted-foreground font-semibold px-2 pb-1 w-full max-w-xl mx-auto">
              Other Projects
            </div>
            <ScrollArea className="max-h-40 w-full max-w-xl mx-auto rounded-md">
              <table className="w-full text-xs">
                <tbody>
                  {listProjects.map((project) => (
                    <tr
                      key={project.id}
                      className="border-b border-border hover:bg-muted/40 group transition-colors"
                    >
                      <td className="px-2 py-1 truncate max-w-[120px] align-middle font-medium">
                        {project.name}
                      </td>
                      <td className="px-2 py-1 text-[11px] text-muted-foreground align-middle whitespace-nowrap">
                        Last opened: {formatRelativeTime(project.lastOpenedAt)}
                      </td>
                      <td className="px-1 py-1 align-middle text-right">
                        <Popover>
                          <PopoverTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="hover:bg-accent"
                            >
                              <MoreVertical className="w-4 h-4" />
                            </Button>
                          </PopoverTrigger>
                          <PopoverContent
                            align="end"
                            sideOffset={8}
                            className="min-w-[100px] p-1"
                          >
                            <button
                              className="flex w-full items-center gap-2 rounded px-2 py-1 text-xs hover:bg-accent hover:text-accent-foreground transition-colors"
                              onClick={() => {
                                setRenameDialogOpen(project.id);
                                setRenameValue(project.name);
                              }}
                            >
                              <Pencil className="w-4 h-4 mr-2" /> Rename
                            </button>
                            <button
                              className="flex w-full items-center gap-2 rounded px-2 py-1 text-xs hover:bg-accent hover:text-accent-foreground text-destructive"
                              onClick={() => setDeleteDialogOpen(project.id)}
                            >
                              <Trash2 className="w-4 h-4 mr-2" /> Delete
                            </button>
                          </PopoverContent>
                        </Popover>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </ScrollArea>
          </div>
        )}
      </div>
      {/* New Project Dialog */}
      <Dialog
        open={newProjectDialogOpen}
        onOpenChange={setNewProjectDialogOpen}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New Project</DialogTitle>
            <DialogDescription>
              Enter a name for your new project.
            </DialogDescription>
          </DialogHeader>
          <Input
            autoFocus
            placeholder="Project name"
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleCreateProject();
            }}
          />
          <DialogFooter>
            <Button
              variant="secondary"
              onClick={() => setNewProjectDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="default"
              onClick={handleCreateProject}
              disabled={!newProjectName.trim()}
            >
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Rename Project Dialog */}
      <Dialog
        open={renameDialogOpen !== null}
        onOpenChange={() => setRenameDialogOpen(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename Project</DialogTitle>
            <DialogDescription>
              Enter a new name for your project.
            </DialogDescription>
          </DialogHeader>
          <Input
            autoFocus
            placeholder="New project name"
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && renameDialogOpen !== null)
                handleRenameProject(renameDialogOpen);
            }}
          />
          <DialogFooter>
            <Button
              variant="secondary"
              onClick={() => setRenameDialogOpen(null)}
            >
              Cancel
            </Button>
            <Button
              variant="default"
              onClick={() =>
                renameDialogOpen !== null &&
                handleRenameProject(renameDialogOpen)
              }
              disabled={!renameValue.trim()}
            >
              Rename
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Delete Project Dialog */}
      <Dialog
        open={deleteDialogOpen !== null}
        onOpenChange={() => setDeleteDialogOpen(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Project</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this project? This action cannot
              be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="secondary"
              onClick={() => setDeleteDialogOpen(null)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() =>
                deleteDialogOpen !== null &&
                handleDeleteProject(deleteDialogOpen)
              }
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function EditorPage() {
  const { data: loadedModules = [], isLoading: modulesLoading } = useQuery({
    queryKey: ["modules"],
    queryFn: fetchModules,
  });
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [, setProjects] = useAtom(projectsAtom);
  const { projectId } = useParams();
  useEffect(() => {
    if (projectId) {
      setProjects((prev) =>
        prev.map((p) =>
          String(p.id) === String(projectId)
            ? { ...p, lastOpenedAt: new Date().toISOString() }
            : p
        )
      );
    }
  }, [projectId, setProjects]);

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

  const [, setTEMPORARY_REMOVE_SOON_activeModules] = useState<
    Array<ActiveModule>
  >([]);

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
          <div className="flex-1 flex items-stretch">
            <div className="flex-1 bg-gradient-to-br from-background via-muted to-background">
              <RoomVisualization
                roomDimensions={roomDimensions}
                modules={loadedModules}
                mapRef={mapRef}
                activeModules={activeModules}
              />
            </div>
            {/* <ModuleCard
              module={loadedModules[0]}
              onClick={() => handleModulePlaced(loadedModules[0].id, [0, 0])}
            /> */}
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
