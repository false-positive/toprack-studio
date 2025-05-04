import { atom } from "jotai";

export interface DataCenterComponent {
  id: number;
  name: string;
  attributes: Array<{
    unit: string;
    amount: number;
    below_amount: number;
    above_amount: number;
    minimize: number;
    maximize: number;
    unconstrained: number;
  }>;
}

export const selectedComponentAtom = atom<DataCenterComponent | null>(null);
