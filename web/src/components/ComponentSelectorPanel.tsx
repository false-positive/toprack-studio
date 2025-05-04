import { useQuery } from "@tanstack/react-query";
import { useAtom } from "jotai";
import {
  selectedComponentAtom,
  DataCenterComponent,
} from "../selectedComponentAtom";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useParams } from "react-router";

function fetchComponents(dataCenterId: number): Promise<DataCenterComponent[]> {
  return fetch(
    `${
      import.meta.env.VITE_API_BASE_URL
    }/api/datacenter-components/?data_center=${dataCenterId}`
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
        <div className="flex-1 flex flex-col justify-center">
          <Select
            value={selected ? String(selected.id) : undefined}
            onValueChange={(val) => {
              const comp = components?.find((c) => String(c.id) === val);
              if (comp) setSelected(comp);
            }}
            disabled={isLoading || !components}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select a component..." />
            </SelectTrigger>
            <SelectContent>
              {components?.map((component) => (
                <SelectItem key={component.id} value={String(component.id)}>
                  {component.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  );
}
