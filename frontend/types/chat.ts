export type SourceItem = {
  nama: string;
  lokasi: string;
};

export type ChatResponse = {
  answer: string;
  sources: SourceItem[];
};

export type Message = {
  id: string;
  role: "user" | "assistant";
  text: string;
  sources?: SourceItem[];
};
