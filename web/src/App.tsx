import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { DndContext, DragOverlay } from "@dnd-kit/core";
import { ScrollArea } from "@radix-ui/react-scroll-area";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAtom } from "jotai";
import L from "leaflet";
import {
  BookOpen,
  ChevronDown,
  ChevronUp,
  FileText,
  MoreVertical,
  Pencil,
  Plus,
  ScanLine,
  Settings,
  Sparkles,
  Trash2,
  UploadCloud,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, Route, Routes, useNavigate, useParams } from "react-router";
import LLogo from "./components/LLogo";
import ModuleCard from "./components/ModuleCard";
import ModuleLibrary from "./components/ModuleLibrary";
import RoomVisualization from "./components/RoomVisualization";
import Toolbar from "./components/Toolbar";
import { Input } from "./components/ui/input";
import {
  Menubar,
  MenubarContent,
  MenubarItem,
  MenubarMenu,
  MenubarSeparator,
  MenubarShortcut,
  MenubarTrigger,
} from "./components/ui/menubar";
import {
  addActiveModule,
  deleteActiveModule,
  fetchActiveModules,
  fetchModules,
} from "./data/modules";
import { projectsAtom } from "./projectsAtom";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";

// Units type for measurement units
interface Units {
  distance: string;
  currency: string;
  water: string;
  power: string;
}

// Project type
export interface Project {
  id: number;
  name: string;
  lastOpenedAt: string; // ISO string for serialization
  units: Units;
}

type ActiveModulesQueryResult = Awaited<ReturnType<typeof fetchActiveModules>>;

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
  const [newProjectName, setNewProjectName] = useState("Untitled Project");
  const [renameValue, setRenameValue] = useState("");
  const [showVRStep, setShowVRStep] = useState(false);
  const navigate = useNavigate();

  // Mock data for module libraries and rulesets
  const mockLibraries = [
    {
      id: 1,
      name: "Standard Library",
      description: "Default Siemens modules",
      icon: <BookOpen className="w-8 h-8 text-primary" />,
    },
    {
      id: 2,
      name: "Custom Library",
      description: "Your custom imported modules",
      icon: <BookOpen className="w-8 h-8 text-secondary" />,
    },
  ];
  const mockRulesets = [
    {
      id: 1,
      name: "Standard Rules",
      description: "Default Siemens ruleset",
      icon: <FileText className="w-8 h-8 text-primary" />,
    },
    {
      id: 2,
      name: "Green Rules",
      description: "Eco-friendly constraints",
      icon: <FileText className="w-8 h-8 text-green-600" />,
    },
  ];
  // Units state
  const [unitsOpen, setUnitsOpen] = useState(false);
  const [units, setUnits] = useState({
    distance: "m",
    currency: "EUR",
    water: "L",
    power: "kW",
  });
  // Multi-step dialog state
  const [projectStep, setProjectStep] = useState(0);
  const [selectedLibrary, setSelectedLibrary] = useState<number | null>(null);
  const [selectedRuleset, setSelectedRuleset] = useState<number | null>(null);

  useEffect(() => {
    console.log(units);
  }, [units]);

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

  async function handleBypassVRStep() {
    setProjectStep(0);
    setSelectedLibrary(null);
    setSelectedRuleset(null);
    setUnitsOpen(false);
    setUnits({
      distance: "m",
      currency: "EUR",
      water: "L",
      power: "kW",
    });
    try {
      const resp = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/create-data-center/`,
        {
          method: "POST",
          body: JSON.stringify({
            name: newProjectName.concat(new Date().getTime().toString()),
            _will_add_units_even_tho_this_field_is_ignored_by_the_backend:
              units,
          }),
          headers: {
            "Content-Type": "application/json",
          },
        }
      );
      if (!resp.ok) throw new Error("Failed to initialize values");
      // Create new project locally
      const newId = (await resp.json()).data.id;
      setProjects((prev) => [
        ...prev,
        {
          id: newId,
          name: newProjectName || "Untitled Project",
          lastOpenedAt: new Date().toISOString(),
          library: selectedLibrary,
          ruleset: selectedRuleset,
          units,
        },
      ]);
      setShowVRStep(false);
      navigate(`/projects/${newId}`);
    } catch (e) {
      alert(
        "Failed to initialize project: " + (e instanceof Error ? e.message : e)
      );
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background px-4">
      <div
        className="w-full max-w-2xl mx-auto flex flex-col gap-2 justify-center"
        style={{ minHeight: "100vh" }}
      >
        <header className="flex flex-col items-center gap-1 mt-6 mb-2">
          <span className="inline-flex items-center justify-center rounded-full bg-primary text-primary-foreground p-2 mb-1">
            <LLogo className="size-6" />
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
      {/* New Project Dialog (multi-step) */}
      <Dialog
        open={newProjectDialogOpen}
        onOpenChange={setNewProjectDialogOpen}
      >
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>New Project</DialogTitle>
            <DialogDescription>
              Set up your new project in a few easy steps.
            </DialogDescription>
          </DialogHeader>
          {/* Step 1: Name */}
          {projectStep === 0 && (
            <div className="flex flex-col gap-4">
              <label className="font-medium text-sm">Project Name</label>
              <Input
                autoFocus
                placeholder="Project name"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && newProjectName.trim())
                    setProjectStep(1);
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
                  onClick={() => setProjectStep(1)}
                  disabled={!newProjectName.trim()}
                >
                  Next
                </Button>
              </DialogFooter>
            </div>
          )}
          {/* Step 2: Module Library */}
          {projectStep === 1 && (
            <div className="flex flex-col gap-4">
              <label className="font-medium text-sm mb-1">
                Select Module Library
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {mockLibraries.map((lib) => (
                  <button
                    key={lib.id}
                    className={`flex flex-col items-center justify-center border-2 rounded-xl p-4 gap-2 transition-all cursor-pointer focus:outline-none ${
                      selectedLibrary === lib.id
                        ? "border-primary bg-primary/10"
                        : "border-border hover:border-primary/60"
                    }`}
                    onClick={() => setSelectedLibrary(lib.id)}
                  >
                    {lib.icon}
                    <span className="font-semibold text-base">{lib.name}</span>
                    <span className="text-xs text-muted-foreground text-center">
                      {lib.description}
                    </span>
                  </button>
                ))}
                <button
                  className="flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-4 gap-2 transition-all cursor-pointer hover:border-primary/60 focus:outline-none"
                  onClick={() => {}}
                >
                  <UploadCloud className="w-8 h-8 text-muted-foreground" />
                  <span className="font-semibold text-base">
                    Import from CSV
                  </span>
                  <span className="text-xs text-muted-foreground text-center">
                    Upload a new module library
                  </span>
                </button>
              </div>
              <DialogFooter>
                <Button variant="secondary" onClick={() => setProjectStep(0)}>
                  Back
                </Button>
                <Button
                  variant="default"
                  onClick={() => setProjectStep(2)}
                  disabled={selectedLibrary === null}
                >
                  Next
                </Button>
              </DialogFooter>
            </div>
          )}
          {/* Step 3: Ruleset */}
          {projectStep === 2 && (
            <div className="flex flex-col gap-4">
              <label className="font-medium text-sm mb-1">Select Ruleset</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {mockRulesets.map((rule) => (
                  <button
                    key={rule.id}
                    className={`flex flex-col items-center justify-center border-2 rounded-xl p-4 gap-2 transition-all cursor-pointer focus:outline-none ${
                      selectedRuleset === rule.id
                        ? "border-primary bg-primary/10"
                        : "border-border hover:border-primary/60"
                    }`}
                    onClick={() => setSelectedRuleset(rule.id)}
                  >
                    {rule.icon}
                    <span className="font-semibold text-base">{rule.name}</span>
                    <span className="text-xs text-muted-foreground text-center">
                      {rule.description}
                    </span>
                  </button>
                ))}
                <button
                  className="flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-4 gap-2 transition-all cursor-pointer hover:border-primary/60 focus:outline-none"
                  onClick={() => {}}
                >
                  <UploadCloud className="w-8 h-8 text-muted-foreground" />
                  <span className="font-semibold text-base">
                    Import from CSV
                  </span>
                  <span className="text-xs text-muted-foreground text-center">
                    Upload a new ruleset
                  </span>
                </button>
              </div>
              <DialogFooter>
                <Button variant="secondary" onClick={() => setProjectStep(1)}>
                  Back
                </Button>
                <Button
                  variant="default"
                  onClick={() => setProjectStep(3)}
                  disabled={selectedRuleset === null}
                >
                  Next
                </Button>
              </DialogFooter>
            </div>
          )}
          {/* Step 4: Units (collapsible) & Finish */}
          {projectStep === 3 && (
            <div className="flex flex-col gap-4">
              <div
                className="flex items-center justify-between cursor-pointer select-none"
                onClick={() => setUnitsOpen((v) => !v)}
              >
                <span className="font-medium text-sm flex items-center gap-2">
                  <Settings className="w-4 h-4" /> Advanced: Units
                </span>
                {unitsOpen ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </div>
              {unitsOpen && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 bg-muted/40 rounded-lg p-4">
                  <div className="flex flex-col gap-1">
                    <label className="text-xs font-medium">Distance</label>
                    <Input
                      value={units.distance}
                      onChange={(e) =>
                        setUnits((u) => ({ ...u, distance: e.target.value }))
                      }
                      placeholder="e.g. m, ft"
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-xs font-medium">Currency</label>
                    <Input
                      value={units.currency}
                      onChange={(e) =>
                        setUnits((u) => ({ ...u, currency: e.target.value }))
                      }
                      placeholder="e.g. EUR, USD"
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-xs font-medium">Water Volume</label>
                    <Input
                      value={units.water}
                      onChange={(e) =>
                        setUnits((u) => ({ ...u, water: e.target.value }))
                      }
                      placeholder="e.g. L, gal"
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-xs font-medium">Power</label>
                    <Input
                      value={units.power}
                      onChange={(e) =>
                        setUnits((u) => ({ ...u, power: e.target.value }))
                      }
                      placeholder="e.g. kW, MW"
                    />
                  </div>
                </div>
              )}
              <DialogFooter>
                <Button variant="secondary" onClick={() => setProjectStep(2)}>
                  Back
                </Button>
                <Button
                  variant="default"
                  onClick={() => {
                    setShowVRStep(true);
                    setNewProjectDialogOpen(false);
                  }}
                >
                  Create Project
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
      {/* VR Scan Step (unskippable, full-screen) */}
      {showVRStep && (
        <Dialog open={showVRStep}>
          <DialogContent className="flex flex-col items-center justify-center min-h-[60vh] max-w-lg gap-8">
            <div className="flex flex-col items-center gap-4 mt-8">
              <span className="inline-flex items-center justify-center rounded-full bg-primary text-primary-foreground p-6 mb-2 shadow-lg">
                <ScanLine className="w-20 h-20" />
              </span>
              <h2 className="text-3xl font-bold text-center">
                Scan Your Data Center in VR
              </h2>
              <p className="text-lg text-muted-foreground text-center max-w-md">
                Put on your VR headset and scan the room to begin designing your
                data center. This screen will wait for you to complete the scan
                in VR.
              </p>
            </div>
            <div className="flex flex-col items-center gap-2 mt-4">
              <span className="animate-pulse text-primary text-2xl font-semibold">
                Waiting for VR scan...
              </span>
              {/* TEMPORARY OVERRIDE BUTTON - REMOVE BEFORE PRODUCTION */}
              <Button
                variant="outline"
                className="mt-6"
                onClick={handleBypassVRStep}
              >
                Temporary: Skip VR Step
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
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
  const { projectId } = useParams();
  const { data: loadedModules = [], isLoading: modulesLoading } = useQuery({
    queryKey: ["modules", projectId],
    queryFn: () => fetchModules(Number(projectId)),
  });
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [projects, setProjects] = useAtom(projectsAtom);
  const currentProject = projects.find(
    (p) => String(p.id) === String(projectId)
  );
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

  const queryClient = useQueryClient();

  const { data: activeModules } = useQuery({
    queryKey: ["activeModules", projectId],
    queryFn: () => fetchActiveModules(Number(projectId)),
  });

  const addModuleMutation = useMutation({
    mutationFn: async ({
      x,
      y,
      moduleId,
    }: {
      x: number;
      y: number;
      moduleId: string;
    }) => {
      return addActiveModule({
        x,
        y,
        moduleId,
        dataCenterId: Number(projectId),
      });
    },
    onMutate: async (newModule) => {
      await queryClient.cancelQueries({ queryKey: ["activeModules"] });
      const previous = queryClient.getQueryData<ActiveModulesQueryResult>([
        "activeModules",
      ]);
      // Optimistically add the new module to the cache
      if (previous && previous.data) {
        queryClient.setQueryData(["activeModules"], {
          ...previous,
          data: [
            ...previous.data,
            {
              id: Math.random(),
              x: newModule.x,
              y: newModule.y,
              module_details: loadedModules.find(
                (m) => m.id === newModule.moduleId
              ),
            },
          ],
        });
      }
      return { previous };
    },
    onError: (_err, _newModule, context) => {
      if (context?.previous) {
        queryClient.setQueryData(["activeModules"], context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["activeModules"] });
    },
  });

  const deleteModuleMutation = useMutation({
    mutationFn: async (id: number) => deleteActiveModule(id, Number(projectId)),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ["activeModules"] });
      const previous = queryClient.getQueryData<ActiveModulesQueryResult>([
        "activeModules",
      ]);
      if (previous && previous.data) {
        queryClient.setQueryData(["activeModules"], {
          ...previous,
          data: previous.data.filter((mod) => mod.id !== id),
        });
      }
      return { previous };
    },
    onError: (_err, _id, context) => {
      if (context?.previous) {
        queryClient.setQueryData(["activeModules"], context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["activeModules"] });
    },
  });

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
          addModuleMutation.mutate({
            x: intCoords[0],
            y: intCoords[1],
            moduleId: activeModuleId,
          });
        }
        // handle drop logic here if needed
      }}
      onDragCancel={() => setActiveModuleId(null)}
    >
      <div className="flex flex-col min-h-screen bg-background text-foreground dark">
        <header
          className="w-full border-b bg-card/80 backdrop-blur supports-[backdrop-filter]:bg-card/60 shadow-sm sticky top-0 z-50 box-border"
          style={{
            height: "var(--header-height)",
            minHeight: "var(--header-height)",
            maxHeight: "var(--header-height)",
            paddingTop: 0,
            paddingBottom: 0,
            marginTop: 0,
            marginBottom: 0,
          }}
        >
          <div className="flex flex-col items-start w-full px-8 pt-2 pb-0 h-full">
            <div className="flex items-center gap-3 mb-1">
              <span className="inline-flex items-center justify-center rounded-full bg-primary text-primary-foreground p-1.5">
                <LLogo className="size-6" />
              </span>
              <h1 className="text-base font-semibold tracking-tight">
                {currentProject ? currentProject.name : "Data Center Editor"}
              </h1>
            </div>
            <nav className="flex flex-row gap-2 z-50 relative">
              <Menubar>
                <MenubarMenu>
                  <MenubarTrigger>File</MenubarTrigger>
                  <MenubarContent>
                    <MenubarItem>
                      New Tab <MenubarShortcut>⌘T</MenubarShortcut>
                    </MenubarItem>
                    <MenubarItem>New Window</MenubarItem>
                    <MenubarSeparator />
                    <MenubarItem>Share</MenubarItem>
                    <MenubarSeparator />
                    <MenubarItem>Print</MenubarItem>
                  </MenubarContent>
                </MenubarMenu>
                <MenubarMenu>
                  <MenubarTrigger>Edit</MenubarTrigger>
                  <MenubarContent>
                    <MenubarItem>
                      Undo <MenubarShortcut>⌘Z</MenubarShortcut>
                    </MenubarItem>
                    <MenubarItem>
                      Redo <MenubarShortcut>⇧⌘Z</MenubarShortcut>
                    </MenubarItem>
                    <MenubarSeparator />
                    <MenubarItem>
                      Cut <MenubarShortcut>⌘X</MenubarShortcut>
                    </MenubarItem>
                    <MenubarItem>
                      Copy <MenubarShortcut>⌘C</MenubarShortcut>
                    </MenubarItem>
                    <MenubarItem>
                      Paste <MenubarShortcut>⌘V</MenubarShortcut>
                    </MenubarItem>
                  </MenubarContent>
                </MenubarMenu>
                <MenubarMenu>
                  <MenubarTrigger>View</MenubarTrigger>
                  <MenubarContent>
                    <MenubarItem>
                      Zoom In <MenubarShortcut>⌘+</MenubarShortcut>
                    </MenubarItem>
                    <MenubarItem>
                      Zoom Out <MenubarShortcut>⌘-</MenubarShortcut>
                    </MenubarItem>
                    <MenubarItem>
                      Reset Zoom <MenubarShortcut>⌘0</MenubarShortcut>
                    </MenubarItem>
                    <MenubarSeparator />
                    <MenubarItem>Toggle Fullscreen</MenubarItem>
                  </MenubarContent>
                </MenubarMenu>
                <MenubarMenu>
                  <MenubarTrigger>Window</MenubarTrigger>
                  <MenubarContent>
                    <MenubarItem>Minimize</MenubarItem>
                    <MenubarItem>Zoom</MenubarItem>
                    <MenubarSeparator />
                    <MenubarItem>
                      Close Window <MenubarShortcut>⌘W</MenubarShortcut>
                    </MenubarItem>
                  </MenubarContent>
                </MenubarMenu>
                <MenubarMenu>
                  <MenubarTrigger>Help</MenubarTrigger>
                  <MenubarContent>
                    <MenubarItem>Documentation</MenubarItem>
                    <MenubarItem>About</MenubarItem>
                  </MenubarContent>
                </MenubarMenu>
              </Menubar>
            </nav>
          </div>
        </header>
        <main className="flex flex-col h-[calc(100vh-var(--header-height))] overflow-hidden">
          <ResizablePanelGroup
            direction="horizontal"
            className="flex-1 h-full w-full"
          >
            <ResizablePanel defaultSize={80} minSize={40}>
              <div className="relative h-full w-full">
                <RoomVisualization
                  roomDimensions={roomDimensions}
                  modules={loadedModules}
                  mapRef={mapRef}
                  activeModules={activeModules.data}
                  onDeleteModule={(id) => deleteModuleMutation.mutate(id)}
                />
                {/* Toolbar overlay */}
                <div className="absolute left-0 top-0 z-[500]">
                  <Toolbar />
                </div>
              </div>
            </ResizablePanel>
            <ResizableHandle withHandle />
            <ResizablePanel defaultSize={20} minSize={16} maxSize={32}>
              <aside className="h-full flex flex-col overflow-y-auto sticky top-0 shadow-md px-4 py-6 bg-card/90 border-l border-border">
                <div className="mb-6">
                  <h2 className="text-lg font-bold mb-4">Module Library</h2>
                  <Card>
                    <CardContent className="space-y-2">
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
                        <Select
                          value={typeFilter}
                          onValueChange={setTypeFilter}
                        >
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
            </ResizablePanel>
          </ResizablePanelGroup>
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
