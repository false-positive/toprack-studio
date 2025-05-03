import { useEffect } from "react";
import { MapContainer, Polyline, useMap, Marker } from "react-leaflet";
import L from "leaflet";
import type { Module } from "../../types";
import PlacedModule from "./PlacedModule";
import WallDimensions from "./WallDimensions";
import "leaflet/dist/leaflet.css";
import { useDroppable } from "@dnd-kit/core";

interface RoomVisualizationProps {
  roomDimensions: {
    width: number;
    height: number;
    walls: Array<{ start: [number, number]; end: [number, number] }>;
  };
  placedModules: Array<{
    id: string;
    moduleId: string;
    position: [number, number];
    rotation: number;
  }>;
  modules: Module[];
  onModuleRemoved: (id: string) => void;
  onModuleRotated: (id: string) => void;
  mapRef: React.MutableRefObject<L.Map | null>;
  TEMPORARY_REMOVE_SOON_tempMarkers: Array<{
    id: string;
    position: [number, number];
  }>;
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
  placedModules,
  modules,
  onModuleRemoved,
  onModuleRotated,
  mapRef,
  TEMPORARY_REMOVE_SOON_tempMarkers,
}: RoomVisualizationProps) {
  const { setNodeRef } = useDroppable({
    id: "room",
  });

  // Calculate bounds based on room dimensions
  const bounds: L.LatLngBoundsExpression = [
    [0, 0],
    [roomDimensions.height, roomDimensions.width],
  ];

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

  return (
    <div className="h-full w-full bg-background" ref={setNodeRef}>
      <MapContainer
        center={[roomDimensions.height / 2, roomDimensions.width / 2]}
        zoom={1}
        minZoom={-2}
        maxZoom={2}
        scrollWheelZoom={true}
        crs={L.CRS.Simple}
        bounds={bounds}
        className="h-full w-full"
        style={{ background: "#18181b" }}
        attributionControl={false}
        whenReady={
          ((event) => {
            mapRef.current = event.target;
            event.target.fitBounds(bounds);
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

        {/* Wall dimensions */}
        <WallDimensions walls={roomDimensions.walls} />

        {/* Placed modules */}
        {placedModules.map((placedModule) => {
          const moduleData = modules.find(
            (m) => m.id === placedModule.moduleId
          );
          if (!moduleData) return null;

          return (
            <PlacedModule
              key={placedModule.id}
              id={placedModule.id}
              position={placedModule.position}
              rotation={placedModule.rotation}
              module={moduleData}
              onRemove={onModuleRemoved}
              onRotate={onModuleRotated}
            />
          );
        })}

        {/* TEMPORARY_REMOVE_SOON: tempMarkers as grid-aligned 1x1 squares with module ID */}
        {TEMPORARY_REMOVE_SOON_tempMarkers.map((marker) => (
          <Marker
            key={`TEMPORARY_REMOVE_SOON_${marker.id}_${marker.position[0]}_${marker.position[1]}`}
            position={marker.position}
            icon={L.divIcon({
              html: `<div style="width: 20px; height: 20px; background: #fbbf24; color: #18181b; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 2px solid #92400e; border-radius: 2px;">${marker.id}</div>`,
              className: "",
              iconSize: [20, 20],
              iconAnchor: [10, 10],
            })}
            interactive={false}
          />
        ))}

        {/* Event handlers */}
        <MapEventHandler />
      </MapContainer>
    </div>
  );
}
