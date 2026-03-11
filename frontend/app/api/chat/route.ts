import { NextRequest, NextResponse } from "next/server";

const BACKEND_API_URL =
  process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000/api/chat";
const BACKEND_API_TOKEN = process.env.BACKEND_API_TOKEN ?? "";
const MAX_QUESTION_LENGTH = 500;

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as { question?: string };
    const question = (body.question ?? "").trim();

    if (!question) {
      return NextResponse.json(
        { detail: "Question tidak boleh kosong." },
        { status: 422 },
      );
    }

    if (question.length > MAX_QUESTION_LENGTH) {
      return NextResponse.json(
        { detail: `Question maksimal ${MAX_QUESTION_LENGTH} karakter.` },
        { status: 422 },
      );
    }

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (BACKEND_API_TOKEN) {
      headers.Authorization = `Bearer ${BACKEND_API_TOKEN}`;
    }

    const upstream = await fetch(BACKEND_API_URL, {
      method: "POST",
      headers,
      body: JSON.stringify({ question }),
      cache: "no-store",
    });

    const payload = await upstream.json().catch(() => ({
      detail: "Respons backend tidak valid.",
    }));

    return NextResponse.json(payload, { status: upstream.status });
  } catch {
    return NextResponse.json(
      { detail: "Gagal memproses permintaan." },
      { status: 500 },
    );
  }
}
