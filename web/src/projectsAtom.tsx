import { atomWithStorage } from "jotai/utils";
import { Project } from "./App";
import { atom } from "jotai";

// Jotai atom for projects, persisted to localStorage

export const projectsAtom = atomWithStorage<Project[]>("projects", []);

// Atom for globally selected tool (default: 'hand')
export const selectedToolAtom = atom<string>("hand");
