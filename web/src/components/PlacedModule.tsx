import { Rectangle, Popup } from "react-leaflet";
import type { ActiveModule } from "../../types";

interface PlacedModuleProps {
    activeModule: ActiveModule;
    onDelete?: (id: number) => void;
}

export default function PlacedModule({ activeModule, onDelete }: PlacedModuleProps) {
    const spaceXIdk = activeModule.module_details.attributes.Space_X.amount;
    const spaceYIdk = activeModule.module_details.attributes.Space_Y.amount;
    const spaceX = typeof spaceXIdk === "number" ? spaceXIdk / 10 : 1;
    const spaceY = typeof spaceYIdk === "number" ? spaceYIdk / 10 : 1;
    console.dir(JSON.stringify({ activeModule, spaceX, spaceY }, null, 2));
    return (
        <Rectangle
            bounds={[
                [activeModule.x - spaceX / 2, activeModule.y - spaceY / 2],
                [activeModule.x + spaceX / 2, activeModule.y + spaceY / 2],
            ]}
            pathOptions={{ color: "#38bdf8", weight: 2, fillOpacity: 0.3 }}
            eventHandlers={{
                click: (event) => {
                    if (event.originalEvent && event.originalEvent.ctrlKey && onDelete) {
                        onDelete(activeModule.id);
                    }
                },
            }}
        >
            <Popup>
                <div className="flex flex-col gap-2">
                    <div className="font-bold text-lg">{activeModule.module_details.name}</div>
                    {/* <div className="text-xs text-muted-foreground break-all">
            <pre className="whitespace-pre-wrap">
              {JSON.stringify(activeModule.module_details.attributes, null, 2)}
            </pre>
          </div> */}
                </div>
            </Popup>
        </Rectangle>
    );
}
