export interface ModuleAttribute {
  unit: string;
  amount: boolean | string | number;
  is_input: boolean;
  is_output: boolean;
}

export interface Module {
  id: string;
  name: string;
  type: string;
  width: number;
  depth: number;
  height: number;
  power: number;
  weight: number;
  color?: string;
  icon?: string;
  isInput: boolean;
  isOutput: boolean;
  unit: string;
  amount: number;
  attributes: ModuleAttribute[];
}

export interface ActiveModule {
  id: number;
  x: number;
  y: number;
  module_details: {
    id: number;
    name: string;
    attributes: ModuleAttribute[];
  };
}
