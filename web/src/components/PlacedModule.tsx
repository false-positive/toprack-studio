import { Rectangle } from "react-leaflet";
import type { ActiveModule } from "../../types";

interface PlacedModuleProps {
  activeModule: ActiveModule;
}

export default function PlacedModule({ activeModule }: PlacedModuleProps) {
  const spaceXIdk = activeModule.module_details.attributes.Space_X.amount;
  const spaceYIdk = activeModule.module_details.attributes.Space_Y.amount;
  const spaceX = typeof spaceXIdk === "number" ? spaceXIdk : 10;
  const spaceY = typeof spaceYIdk === "number" ? spaceYIdk : 10;
  console.dir(JSON.stringify({ activeModule, spaceX, spaceY }, null, 2));
  return (
    <Rectangle
      bounds={[
        [activeModule.x - spaceX / 2, activeModule.y - spaceY / 2],
        [activeModule.x + spaceX / 2, activeModule.y + spaceY / 2],
      ]}
      pathOptions={{ color: "#38bdf8", weight: 2, fillOpacity: 0.3 }}
    />
  );
}
