import { Rectangle, Popup, Marker } from "react-leaflet";
import type { ActiveModule } from "../../types";
import { getModuleColor } from "@/data/modules";
import L from "leaflet";
import { getContrastColor } from "./ModuleCard";

interface PlacedModuleProps {
  activeModule: ActiveModule;
  onDelete?: (id: number) => void;
}

export default function PlacedModule({
  activeModule,
  onDelete,
}: PlacedModuleProps) {
  const spaceXIdk = activeModule.module_details.attributes.Space_X.amount;
  const spaceYIdk = activeModule.module_details.attributes.Space_Y.amount;
  const spaceX = typeof spaceXIdk === "number" ? spaceXIdk / 10 : 1;
  const spaceY = typeof spaceYIdk === "number" ? spaceYIdk / 10 : 1;
  console.dir(JSON.stringify({ activeModule, spaceX, spaceY }, null, 2));

  // Calculate center of the rectangle
  const center: [number, number] = [activeModule.x, activeModule.y];

  // Create a custom divIcon for the label
  const labelIcon = L.divIcon({
    html: `<span class='ako-label' style="color: #fff; display: flex; align-items: center; justify-content: center; width: 100%; height: 100%;">${activeModule.module_details.name
      .split(/[ _-]/g)
      .map((word) =>
        word.match(/[0-9]+/) ? ` ${word}` : word.charAt(0).toUpperCase()
      )
      .join("")}</span>`,
    className: "", // Remove default leaflet styles
    iconSize: [spaceX * 10, spaceY * 10], // scale with rectangle size
    iconAnchor: [spaceX * 5, spaceY * 5], // center the label
  });

  // Add style for the label (only once)
  if (
    typeof window !== "undefined" &&
    !document.getElementById("ako-label-style")
  ) {
    const style = document.createElement("style");
    style.id = "ako-label-style";
    style.innerHTML = `
      .ako-label {
        font-family: 'Inter', 'sans-serif';
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        text-align: center;
        line-height: 1;
        padding: 0;
        margin: 0;
        background: none;
        border: none;
        box-shadow: none;
        pointer-events: none;
        user-select: none;
      }
    `;
    document.head.appendChild(style);
  }

  return (
    <>
      <Rectangle
        bounds={[
          [activeModule.x - spaceX / 2, activeModule.y - spaceY / 2],
          [activeModule.x + spaceX / 2, activeModule.y + spaceY / 2],
        ]}
        pathOptions={{
          color: getModuleColor(activeModule.module_details.name),
          weight: 2,
          fillOpacity: 0.3,
        }}
        eventHandlers={{
          click: (event) => {
            if (
              event.originalEvent &&
              event.originalEvent.ctrlKey &&
              onDelete
            ) {
              onDelete(activeModule.id);
            }
          },
        }}
      >
        <Popup>
          <div className="flex flex-col gap-2">
            <div className="font-bold text-lg">
              {activeModule.module_details.name.replace(/[ _-]/g, " ")}
            </div>
            {/* <div className="text-xs text-muted-foreground break-all">
              <pre className="whitespace-pre-wrap">
                {JSON.stringify(activeModule.module_details.attributes, null, 2)}
              </pre>
            </div> */}
          </div>
        </Popup>
      </Rectangle>
      {/* Label overlay at the center of the rectangle */}
      <Marker
        position={center}
        icon={labelIcon}
        interactive={false}
        keyboard={false}
      />
    </>
  );
}
