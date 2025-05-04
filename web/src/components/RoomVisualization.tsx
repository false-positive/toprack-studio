import { useDroppable } from "@dnd-kit/core";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import {
  Minus,
  Plus,
  RectangleHorizontal,
  RectangleVertical,
} from "lucide-react";
import { useEffect, useState } from "react";
import { MapContainer, Polyline, useMap } from "react-leaflet";
import type { ActiveModule, Module } from "../../types";
import PlacedModule from "./PlacedModule";
import { Button } from "./ui/button";
import WallDimensions from "./WallDimensions";
import { useAtomValue } from "jotai";
import { selectedToolAtom } from "@/projectsAtom";
import { fetchDisplayControl, toggleDisplayControl } from "@/data/modules";

interface RoomVisualizationProps {
  roomDimensions: {
    width: number;
    height: number;
    walls: Array<{ start: [number, number]; end: [number, number] }>;
  };
  modules: Module[];
  mapRef: React.MutableRefObject<L.Map | null>;
  activeModules: Array<ActiveModule>;
  onDeleteModule?: (id: number) => void;
  mapZIndex?: string;
  zoomZIndex?: string;
}

// Component to handle map events and interactions
function MapEventHandler() {
  const map = useMap();

  useEffect(() => {
    const handleClick = (e: L.LeafletMouseEvent) => {
      // This is just for debugging
      console.log("Map clicked at:", e.latlng);
    };

    map.on("click", handleClick);

    return () => {
      map.off("click", handleClick);
    };
  }, [map]);

  return null;
}

export default function RoomVisualization({
  roomDimensions,
  activeModules,
  mapRef,
  onDeleteModule,
  mapZIndex = "z-0",
  zoomZIndex = "z-40",
}: RoomVisualizationProps) {
  const { setNodeRef } = useDroppable({
    id: "room",
  });

  // Get the currently selected tool
  const selectedTool = useAtomValue(selectedToolAtom);

  // Map tool to cursor style
  const toolToCursor: Record<string, string> = {
    hand: "grab",
    select: "pointer",
    move: "move",
    crop: "crosshair",
    brush: "cell",
    eraser: "not-allowed",
    shapes: "copy",
  };
  const mapCursor = toolToCursor[selectedTool] || "grab";

  // Imperatively update the map container's cursor when the tool changes
  useEffect(() => {
    if (mapRef.current) {
      const container = mapRef.current.getContainer();
      container.style.cursor = mapCursor;
    }
  }, [mapCursor, mapRef]);

  // Convert walls to polylines
  const wallPolylines = roomDimensions.walls.map((wall, index) => {
    return {
      positions: [
        [wall.start[1], wall.start[0]],
        [wall.end[1], wall.end[0]],
      ],
      id: `wall-${index}`,
    };
  });

  // Custom zoom handlers
  const handleZoomIn = () => {
    if (mapRef.current) {
      mapRef.current.setZoom(mapRef.current.getZoom() + 1);
    }
  };
  const handleZoomOut = () => {
    if (mapRef.current) {
      mapRef.current.setZoom(mapRef.current.getZoom() - 1);
    }
  };

  const [displayMode, setDisplayMode] = useState<"vr" | "website">("website");
  const [isToggling, setIsToggling] = useState(false);

  useEffect(() => {
    fetchDisplayControl()
      .then(setDisplayMode)
      .catch(() => {});
  }, []);

  async function handleToggleVR() {
    setIsToggling(true);
    try {
      const mode = await toggleDisplayControl();
      setDisplayMode(mode);
    } catch {
      // Intentionally ignore errors for toggle
    }
    setIsToggling(false);
  }

  return (
    <div
      className={`h-full w-full bg-background relative ${mapZIndex}`}
      ref={setNodeRef}
    >
      {/* Custom Zoom Controls - now on the left above the toolbar */}
      <div
        className={`absolute left-4 top-4 flex flex-col gap-2 bg-card/80 rounded-md shadow-lg p-2 border border-border ${zoomZIndex}`}
      >
        <Button
          size="icon"
          variant="outline"
          aria-label="Zoom in"
          onClick={handleZoomIn}
        >
          <Plus className="w-5 h-5" />
        </Button>
        <Button
          size="icon"
          variant="outline"
          aria-label="Zoom out"
          onClick={handleZoomOut}
        >
          <Minus className="w-5 h-5" />
        </Button>
      </div>
      {/* VR Toggle Button - top right */}
      <div className="absolute bottom-4 right-4 z-50">
        <Button
          variant="outline"
          size="sm"
          className="flex items-center gap-2 shadow-md"
          onClick={handleToggleVR}
          disabled={isToggling}
        >
          {displayMode === "vr" ? (
            <>
              <RectangleVertical className="w-5 h-5" />
              Back to Editor
            </>
          ) : (
            <>
              <RectangleHorizontal className="w-5 h-5" />
              Edit in VR
            </>
          )}
        </Button>
      </div>
      <MapContainer
        center={[roomDimensions.height / 2, roomDimensions.width / 2]}
        zoom={3}
        minZoom={-4}
        maxZoom={5}
        scrollWheelZoom={true}
        crs={L.CRS.Simple}
        className="h-full w-full"
        style={{ background: "#18181b", cursor: mapCursor }}
        attributionControl={false}
        zoomControl={false}
        whenReady={
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          ((event: any) => {
            mapRef.current = event.target;
            // Force center and zoom after map is ready
            if (mapRef.current) {
              mapRef.current.setView(
                [roomDimensions.height / 2, roomDimensions.width / 2],
                3
              );
            }
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
          }) as any
        }
      >
        {/* Room walls */}
        {wallPolylines.map((wall) => (
          <Polyline
            key={wall.id}
            positions={wall.positions as L.LatLngExpression[]}
            color="#fff"
            weight={3}
          />
        ))}

        {/* Wall length overlays */}
        <WallDimensions walls={roomDimensions.walls} />

        {/* Placed modules */}
        {activeModules.map((activeModule, i) => {
          return (
            <PlacedModule
              key={i}
              activeModule={activeModule}
              onDelete={onDeleteModule}
            />
          );
        })}

        {/* Event handlers */}
        <MapEventHandler />
      </MapContainer>
    </div>
  );
}
