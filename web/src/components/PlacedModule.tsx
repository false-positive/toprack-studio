import { useEffect } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";
import type { Module } from "../../types";

interface PlacedModuleProps {
  id: string;
  position: [number, number];
  rotation: number;
  module: Module;
  onRemove: (id: string) => void;
  onRotate: (id: string) => void;
}

export default function PlacedModule({
  id,
  position,
  rotation,
  module,
  onRemove,
  onRotate,
}: PlacedModuleProps) {
  const map = useMap();

  useEffect(() => {
    // Create module representation
    const moduleElement = document.createElement("div");
    moduleElement.className = "placed-module";
    moduleElement.style.width = `${module.width * 20}px`;
    moduleElement.style.height = `${module.depth * 20}px`;
    moduleElement.style.backgroundColor = module.color || "#cccccc";
    moduleElement.style.transform = `rotate(${rotation}deg)`;

    // Add module name
    const nameElement = document.createElement("div");
    nameElement.className = "module-name";
    nameElement.textContent = module.name;
    moduleElement.appendChild(nameElement);

    // Add IO indicators if applicable
    if (module.isInput || module.isOutput) {
      const ioElement = document.createElement("div");
      ioElement.className = "module-io-indicator";

      if (module.isInput && module.isOutput) {
        ioElement.textContent = "I/O";
        ioElement.className += " io-both";
      } else if (module.isInput) {
        ioElement.textContent = "IN";
        ioElement.className += " io-input";
      } else if (module.isOutput) {
        ioElement.textContent = "OUT";
        ioElement.className += " io-output";
      }

      moduleElement.appendChild(ioElement);
    }

    // Add control buttons
    const controlsElement = document.createElement("div");
    controlsElement.className = "module-controls";

    const rotateButton = document.createElement("button");
    rotateButton.className = "rotate-button";
    rotateButton.innerHTML = "↻";
    rotateButton.onclick = (e) => {
      e.stopPropagation();
      onRotate(id);
    };

    const removeButton = document.createElement("button");
    removeButton.className = "remove-button";
    removeButton.innerHTML = "×";
    removeButton.onclick = (e) => {
      e.stopPropagation();
      onRemove(id);
    };

    controlsElement.appendChild(rotateButton);
    controlsElement.appendChild(removeButton);
    moduleElement.appendChild(controlsElement);

    // Create custom icon
    const moduleIcon = L.divIcon({
      html: moduleElement,
      className: "module-icon",
      iconSize: [module.width * 20, module.depth * 20],
      iconAnchor: [module.width * 10, module.depth * 10],
    });

    // Create marker
    const marker = L.marker(position, {
      icon: moduleIcon,
      draggable: true,
    }).addTo(map);

    // Handle drag end
    marker.on("dragend", () => {
      const newPos = marker.getLatLng();
      console.log(`Module ${id} moved to:`, [newPos.lat, newPos.lng]);
    });

    return () => {
      map.removeLayer(marker);
    };
  }, [map, id, position, rotation, module, onRemove, onRotate]);

  return null;
}
