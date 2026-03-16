export type SourceItem = {
  nama: string;
  lokasi: string;
};

export type ChatResponse = {
  answer: string;
  sources: SourceItem[];
  follow_up_suggestions?: string[];
  fallback_type?: "too_generic" | "out_of_scope" | null;
};

export type Message = {
  id: string;
  role: "user" | "assistant";
  text: string;
  sources?: SourceItem[];
  followUpSuggestions?: string[];
  fallbackType?: "too_generic" | "out_of_scope" | null;
};
