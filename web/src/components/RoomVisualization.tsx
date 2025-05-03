import { useRef, useEffect } from "react";
import { MapContainer, ImageOverlay, Polyline, useMap } from "react-leaflet";
import L from "leaflet";
import { useDrop } from "react-dnd";
import type { Module } from "../../types";
import PlacedModule from "./PlacedModule";
import WallDimensions from "./WallDimensions";
import "leaflet/dist/leaflet.css";

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
}

// Component to handle map events and interactions
function MapEventHandler({ onDrop }: { onDrop: (position: [number, number]) => void }) {
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

// Drop target for modules
function DropLayer({ onModulePlaced }: { onModulePlaced: (moduleId: string, position: [number, number]) => void }) {
    const map = useMap();

    const [, drop] = useDrop({
        accept: "MODULE",
        drop: (item: { id: string }, monitor) => {
            const clientOffset = monitor.getClientOffset();
            if (clientOffset) {
                const point = L.point(clientOffset.x, clientOffset.y);
                const latlng = map.containerPointToLatLng(point);
                onModulePlaced(item.id, [latlng.lat, latlng.lng]);
            }
        },
    });

    useEffect(() => {
        const mapContainer = map.getContainer();
        drop(mapContainer);
    }, [map, drop]);

    return null;
}

export default function RoomVisualization({ roomDimensions, placedModules, modules, onModuleRemoved, onModuleRotated }: RoomVisualizationProps) {
    const mapRef = useRef<L.Map | null>(null);

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

    const handleModulePlaced = (moduleId: string, position: [number, number]) => {
        // Adjust position if needed
        const adjustedPosition: [number, number] = [position[0], position[1]];
        onModuleRemoved(moduleId);
    };

    return (
        <div className="room-visualization">
            <MapContainer
                center={[roomDimensions.height / 2, roomDimensions.width / 2]}
                zoom={1}
                minZoom={-2}
                maxZoom={2}
                scrollWheelZoom={true}
                crs={L.CRS.Simple}
                bounds={bounds}
                style={{ height: "100%", width: "100%" }}
                whenCreated={(map) => {
                    mapRef.current = map;
                    map.fitBounds(bounds);
                }}
            >
                {/* Background grid */}
                <ImageOverlay
                    bounds={bounds}
                    url="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
                    opacity={0.1}
                />

                {/* Room walls */}
                {wallPolylines.map((wall) => (
                    <Polyline key={wall.id} positions={wall.positions as L.LatLngExpression[]} color="#333" weight={3} />
                ))}

                {/* Wall dimensions */}
                <WallDimensions walls={roomDimensions.walls} />

                {/* Placed modules */}
                {placedModules.map((placedModule) => {
                    const moduleData = modules.find((m) => m.id === placedModule.moduleId);
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

                {/* Event handlers */}
                <MapEventHandler onDrop={(pos) => console.log("Dropped at", pos)} />
                <DropLayer onModulePlaced={handleModulePlaced} />
            </MapContainer>
        </div>
    );
}
