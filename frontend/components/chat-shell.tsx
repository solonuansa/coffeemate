"use client";

import { FormEvent, useMemo, useState } from "react";

import { askChat } from "@/lib/api";
import type { Message } from "@/types/chat";

const MAX_QUESTION_LENGTH = 1000;

export default function ChatShell() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const remainingChars = useMemo(
    () => MAX_QUESTION_LENGTH - question.length,
    [question.length],
  );

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isLoading) return;

    const sanitized = question.trim();
    if (!sanitized) return;
    if (sanitized.length > MAX_QUESTION_LENGTH) {
      setError(`Pertanyaan maksimal ${MAX_QUESTION_LENGTH} karakter.`);
      return;
    }

    setError(null);
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      text: sanitized,
    };
    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setIsLoading(true);

    try {
      const result = await askChat(sanitized);
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        text: result.answer,
        sources: result.sources,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Terjadi kesalahan tidak terduga.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-4xl flex-col px-4 py-6 sm:px-6">
      <header className="mb-5 border-b border-stone-200 pb-4">
        <h1 className="text-2xl font-bold text-stone-900">
          Coffee Shop Assistant
        </h1>
        <p className="mt-1 text-sm text-stone-600">
          Tanyakan rekomendasi coffee shop di Yogyakarta.
        </p>
      </header>

      <main className="flex-1 space-y-3 overflow-y-auto rounded-xl border border-stone-200 bg-white p-4">
        {messages.length === 0 ? (
          <p className="text-sm text-stone-500">
            Mulai dengan pertanyaan seperti: &quot;Coffee shop untuk WFC di
            Sleman&quot;.
          </p>
        ) : (
          messages.map((message) => (
            <article
              key={message.id}
              className={`max-w-3xl rounded-xl px-4 py-3 ${
                message.role === "user"
                  ? "ml-auto bg-stone-900 text-white"
                  : "bg-stone-100 text-stone-900"
              }`}
            >
              <p className="whitespace-pre-wrap text-sm">{message.text}</p>
              {message.sources && message.sources.length > 0 ? (
                <ul className="mt-3 space-y-1 border-t border-stone-300/80 pt-2 text-xs">
                  {message.sources.map((source, index) => (
                    <li key={`${message.id}-${source.nama}-${index}`}>
                      {index + 1}. {source.nama} - {source.lokasi}
                    </li>
                  ))}
                </ul>
              ) : null}
            </article>
          ))
        )}

        {isLoading ? (
          <div className="w-fit rounded-xl bg-amber-100 px-4 py-2 text-sm text-amber-900">
            Sedang memproses jawaban...
          </div>
        ) : null}
      </main>

      <form
        onSubmit={onSubmit}
        className="mt-4 rounded-xl border border-stone-200 bg-white p-3"
      >
        <label htmlFor="question" className="mb-2 block text-sm text-stone-700">
          Pertanyaan
        </label>
        <textarea
          id="question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          rows={3}
          className="w-full resize-none rounded-lg border border-stone-300 px-3 py-2 text-sm outline-none transition focus:border-stone-500"
          placeholder="Contoh: rekomendasikan tempat ngopi yang nyaman untuk kerja"
          disabled={isLoading}
        />
        <div className="mt-2 flex items-center justify-between">
          <p
            className={`text-xs ${
              remainingChars >= 0 ? "text-stone-500" : "text-red-600"
            }`}
          >
            Sisa karakter: {remainingChars}
          </p>
          <button
            type="submit"
            disabled={isLoading || !question.trim() || remainingChars < 0}
            className="rounded-lg bg-stone-900 px-4 py-2 text-sm font-medium text-white transition disabled:cursor-not-allowed disabled:bg-stone-400"
          >
            {isLoading ? "Mengirim..." : "Kirim"}
          </button>
        </div>
        {error ? <p className="mt-2 text-sm text-red-600">{error}</p> : null}
      </form>
    </div>
  );
}
