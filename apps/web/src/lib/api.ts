export type HealthResponse = {
  status: "ok";
  service: string;
  version: string;
  environment: string;
};

export type DocumentRecord = {
  id: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  status: "uploaded" | "duplicate_file" | string;
  doc_type: string | null;
  confidence: number | null;
  is_duplicate_of: string | null;
  created_at: string;
};

export type DocumentListResponse = {
  items: DocumentRecord[];
  total: number;
};

const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${apiUrl}/api/v1/health`);

  if (!response.ok) {
    throw new Error(`API health check failed with ${response.status}`);
  }

  return response.json() as Promise<HealthResponse>;
}

async function responseError(response: Response): Promise<Error> {
  const fallback = `Request failed with ${response.status}`;
  try {
    const body = (await response.json()) as { detail?: string };
    return new Error(body.detail ?? fallback);
  } catch {
    return new Error(fallback);
  }
}

export async function listDocuments(): Promise<DocumentListResponse> {
  const response = await fetch(`${apiUrl}/api/v1/documents`);
  if (!response.ok) {
    throw await responseError(response);
  }
  return response.json() as Promise<DocumentListResponse>;
}

export async function uploadDocument(file: File): Promise<DocumentRecord> {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch(`${apiUrl}/api/v1/documents`, {
    method: "POST",
    body,
  });
  if (!response.ok) {
    throw await responseError(response);
  }
  return response.json() as Promise<DocumentRecord>;
}
