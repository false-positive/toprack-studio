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
}
