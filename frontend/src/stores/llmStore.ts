import { create } from 'zustand';

export interface LLMModel {
  id: string;
  name: string;
  provider: string;
  available: boolean;
  configured: boolean;
}

interface LLMStore {
  models: LLMModel[];
  selectedModel: string | null;
  setModels: (models: LLMModel[]) => void;
  setSelectedModel: (modelId: string | null) => void;
}

export const useLLMStore = create<LLMStore>((set) => ({
  models: [],
  selectedModel: null,
  setModels: (models) => set({ models }),
  setSelectedModel: (modelId) => set({ selectedModel: modelId }),
}));
