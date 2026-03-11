import type { ChatResponse } from "@/types/chat";

export async function askChat(question: string): Promise<ChatResponse> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    let detail = "Gagal memproses pertanyaan.";
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // Keep default error detail.
    }
    throw new Error(detail);
  }

  return (await response.json()) as ChatResponse;
}
