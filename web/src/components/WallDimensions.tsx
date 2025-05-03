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

    walls.forEach((wall) => {
      // Calculate midpoint of the wall
      const midX = (wall.start[0] + wall.end[0]) / 2;
      const midY = (wall.start[1] + wall.end[1]) / 2;

      // Calculate length of the wall
      const length = Math.sqrt(
        Math.pow(wall.end[0] - wall.start[0], 2) +
          Math.pow(wall.end[1] - wall.start[1], 2)
      );

      // Calculate angle of the wall
      const angle =
        Math.atan2(wall.end[1] - wall.start[1], wall.end[0] - wall.start[0]) *
        (180 / Math.PI);

      // Create a custom div for the dimension label
      const dimensionDiv = L.DomUtil.create("div", "dimension-label");
      dimensionDiv.innerHTML = `${length.toFixed(1)}m`;
      dimensionDiv.style.transform = `rotate(${angle}deg)`;

      // Create a custom icon using the div
      const dimensionIcon = L.divIcon({
        html: dimensionDiv,
        className: "dimension-icon",
        iconSize: [80, 20],
        iconAnchor: [40, 10],
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

  return null;
}
