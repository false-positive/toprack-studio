import { atomWithStorage } from "jotai/utils";
import { Project } from "./App";

// Jotai atom for projects, persisted to localStorage

export const projectsAtom = atomWithStorage<Project[]>("projects", []);
