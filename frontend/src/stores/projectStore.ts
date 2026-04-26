import { create } from 'zustand';

export interface Project {
  id: string;
  name: string;
  project_type: 'gaoxin' | 'xiaojuren';
  status: 'draft' | 'generating' | 'review' | 'done';
  company_name: string;
  updated_at: string;
}

interface ProjectStore {
  projects: Project[];
  currentProject: Project | null;
  setProjects: (projects: Project[]) => void;
  setCurrentProject: (project: Project | null) => void;
}

export const useProjectStore = create<ProjectStore>((set) => ({
  projects: [],
  currentProject: null,
  setProjects: (projects) => set({ projects }),
  setCurrentProject: (project) => set({ currentProject: project }),
}));
