import L from "leaflet";
import { useEffect } from "react";
import { useMap } from "react-leaflet";

interface WallDimensionsProps {
    walls: Array<{ start: [number, number]; end: [number, number] }>;
}

export default function WallDimensions({ walls }: WallDimensionsProps) {
    const map = useMap();

    useEffect(() => {
        const dimensionLayers: L.Layer[] = [];

        // Only show dimensions for the bottom and left walls (first and last in array)
        const showWalls = [0, walls.length - 1];

        showWalls.forEach((wallIdx) => {
            const wall = walls[wallIdx];
            if (!wall) return;
            // Calculate midpoint of the wall
            const midX = (wall.start[0] + wall.end[0]) / 2;
            const midY = (wall.start[1] + wall.end[1]) / 2;

            // Calculate length of the wall
            const length = Math.sqrt(Math.pow(wall.end[0] - wall.start[0], 2) + Math.pow(wall.end[1] - wall.start[1], 2));

            // Calculate angle of the wall
            const angle = Math.atan2(wall.end[1] - wall.start[1], wall.end[0] - wall.start[0]) * (180 / Math.PI);

            // Create a custom div for the dimension label
            const dimensionDiv = L.DomUtil.create("div", "dimension-label");
            dimensionDiv.innerHTML = `${length.toFixed(1)}m`;
            dimensionDiv.style.transform = `rotate(${angle}deg)`;

            // Create a custom icon using the div
            const dimensionIcon = L.divIcon({
                html: dimensionDiv,
                className: "dimension-icon dimension-center",
                iconSize: [80, 24],
                iconAnchor: [40, 12],
            });

            // Create a marker at the midpoint with the dimension label
            const dimensionMarker = L.marker([midY, midX], {
                icon: dimensionIcon,
                interactive: false,
            }).addTo(map);

            dimensionLayers.push(dimensionMarker);
        });

        return () => {
            dimensionLayers.forEach((layer) => {
                map.removeLayer(layer);
            });
        };
    }, [map, walls]);

    // Add styles for dimension labels for better contrast and centering
    const style = document.createElement("style");
    style.innerHTML = `
    .dimension-label {
      color: #fff !important;
      font-weight: bold;
      text-shadow: 0 0 4px #000, 0 0 2px #000;
      font-size: 1rem;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      height: 100%;
      text-align: center;
    }
    .dimension-icon {
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 80px;
      height: 24px;
    }
  `;
    if (typeof window !== "undefined" && !document.getElementById("dimension-label-style")) {
        style.id = "dimension-label-style";
        document.head.appendChild(style);
    }

    return null;
}
