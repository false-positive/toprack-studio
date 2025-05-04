import { useQuery } from "@tanstack/react-query";
import { useAtom } from "jotai";
import {
  selectedComponentAtom,
  DataCenterComponent,
} from "../selectedComponentAtom";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@radix-ui/react-scroll-area";
import { useParams } from "react-router";

function fetchComponents(dataCenterId: number): Promise<DataCenterComponent[]> {
  return fetch(
    `${
      import.meta.env.VITE_API_BASE_URL
    }/api/datacenter-components/?data_center_id=${dataCenterId}`
  )
    .then((res) => res.json())
    .then((data) => data.data);
}

export function ComponentSelectorPanel() {
  const { projectId } = useParams();
  const {
    data: components,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["datacenter-components"],
    queryFn: () => fetchComponents(projectId ? Number(projectId) : -69),
  });
  const [selected, setSelected] = useAtom(selectedComponentAtom);

  return (
    <Card className="h-full flex flex-col bg-card border-border">
      <CardHeader>
        <CardTitle className="text-base">Component Selector</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col p-0">
        {isLoading && (
          <div className="p-4 text-muted-foreground">Loading...</div>
        )}
        {error && (
          <div className="p-4 text-destructive">Error loading components.</div>
        )}
        <ScrollArea className="flex-1">
          <ul>
            {components?.map((component) => (
              <li key={component.id}>
                <Button
                  variant={
                    selected?.id === component.id ? "default" : "outline"
                  }
                  className="w-full justify-start my-1"
                  onClick={() => setSelected(component)}
                >
                  {component.name}
                </Button>
              </li>
            ))}
          </ul>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
