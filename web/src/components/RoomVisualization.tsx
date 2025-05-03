import { useDroppable } from "@dnd-kit/core";
import { useEffect } from "react";
import { MapContainer, Polyline, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { ActiveModule, Module } from "../../types";
import PlacedModule from "./PlacedModule";
import "leaflet/dist/leaflet.css";
import { Button } from "@/components/ui/button";
import { Plus, Minus } from "lucide-react";

interface RoomVisualizationProps {
  roomDimensions: {
    width: number;
    height: number;
    walls: Array<{ start: [number, number]; end: [number, number] }>;
  };
  modules: Module[];
  mapRef: React.MutableRefObject<L.Map | null>;
  activeModules: Array<ActiveModule>;
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
}: RoomVisualizationProps) {
  const { setNodeRef } = useDroppable({
    id: "room",
  });

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

  return (
    <div className="h-full w-full bg-background relative" ref={setNodeRef}>
      {/* Custom Zoom Controls - now on the left above the toolbar */}
      <div className="absolute left-4 top-4 z-[1000] flex flex-col gap-2 bg-card/80 rounded-md shadow-lg p-2 border border-border">
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
      <MapContainer
        center={[roomDimensions.height / 2, roomDimensions.width / 2]}
        zoom={3}
        minZoom={-4}
        maxZoom={5}
        scrollWheelZoom={true}
        crs={L.CRS.Simple}
        className="h-full w-full"
        style={{ background: "#18181b" }}
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

        {/* Placed modules */}
        {activeModules.map((activeModule, i) => {
          return <PlacedModule key={i} activeModule={activeModule} />;
        })}

        {/* Event handlers */}
        <MapEventHandler />
      </MapContainer>
    </div>
  );
}
