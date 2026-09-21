export type HealthResponse = {
  status: "ok";
  service: string;
  version: string;
  environment: string;
};

export type SystemCapabilities = {
  environment: string;
  llm_provider: string;
  llm_model: string | null;
  demo_mode: boolean;
  ocr_available: boolean;
  ocr_command: string | null;
  ocr_languages_requested: string;
  ocr_languages_installed: string[];
  max_upload_size_mb: number;
  auto_accept_threshold: number;
  storage_backend: string;
  document_types: string[];
};

export type DocumentRecord = {
  id: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  page_count: number | null;
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

export type ProcessingRunRecord = {
  id: string;
  document_id: string;
  run_number: number;
  processor_version: string;
  status: "running" | "succeeded" | "awaiting_ocr" | "failed" | string;
  page_count: number | null;
  text_char_count: number;
  text_layer_pages: number;
  ocr_pages: number;
  ocr_pending_pages: number;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
};

export type ProcessingRunListResponse = {
  items: ProcessingRunRecord[];
  total: number;
};

export type ValidationCheck = {
  code: string;
  passed: boolean;
  message: string;
  field: string | null;
  severity: string;
};

export type ResultRevisionRecord = {
  id: string;
  document_id: string;
  processing_run_id: string;
  revision_number: number;
  schema_code: string;
  schema_version: number;
  extraction_model: string;
  status: "needs_review" | "approved" | string;
  fields_json: Record<string, unknown>;
  validation_json: ValidationCheck[];
  is_valid: boolean;
  created_at: string;
  approved_at: string | null;
};

export type ResultRevisionListResponse = {
  items: ResultRevisionRecord[];
  total: number;
};

export type AuditEventRecord = {
  id: string;
  document_id: string;
  original_filename: string;
  from_status: string | null;
  to_status: string;
  actor_type: "system" | "operator" | string;
  reason: string | null;
  created_at: string;
};

export type AuditEventListResponse = {
  items: AuditEventRecord[];
  total: number;
};

export type QualityMetrics = {
  case_count: number;
  classification_accuracy: number;
  field_accuracy: number;
  critical_field_accuracy: number;
  grounding_rate: number;
  stp_rate: number;
  stp_precision: number;
};

export type ThresholdPoint = {
  threshold: number;
  accepted: number;
  coverage: number;
  precision: number;
};

export type QualityReport = {
  available: boolean;
  dataset_version?: string;
  model_version?: string;
  generated_at?: string;
  case_count?: number;
  target_precision?: number;
  recommended_threshold?: number;
  overall?: QualityMetrics;
  splits?: Record<string, QualityMetrics>;
  threshold_curve?: ThresholdPoint[];
};

const apiUrl = import.meta.env.VITE_API_URL ?? "";

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${apiUrl}/api/v1/health`);

  if (!response.ok) {
    throw new Error(`API health check failed with ${response.status}`);
  }

  return response.json() as Promise<HealthResponse>;
}

export async function getCapabilities(): Promise<SystemCapabilities> {
  const response = await fetch(`${apiUrl}/api/v1/capabilities`);
  if (!response.ok) {
    throw await responseError(response);
  }
  return response.json() as Promise<SystemCapabilities>;
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

export async function startDocumentProcessing(documentId: string): Promise<ProcessingRunRecord> {
  const response = await fetch(`${apiUrl}/api/v1/documents/${documentId}/process`, {
    method: "POST",
  });
  if (!response.ok) {
    throw await responseError(response);
  }
  return response.json() as Promise<ProcessingRunRecord>;
}

export async function listDocumentRuns(documentId: string): Promise<ProcessingRunListResponse> {
  const response = await fetch(`${apiUrl}/api/v1/documents/${documentId}/runs`);
  if (!response.ok) {
    throw await responseError(response);
  }
  return response.json() as Promise<ProcessingRunListResponse>;
}

export async function listDocumentRevisions(
  documentId: string,
): Promise<ResultRevisionListResponse> {
  const response = await fetch(`${apiUrl}/api/v1/documents/${documentId}/revisions`);
  if (!response.ok) {
    throw await responseError(response);
  }
  return response.json() as Promise<ResultRevisionListResponse>;
}

export async function correctDocumentRevision(
  documentId: string,
  revisionId: string,
  fields: Record<string, unknown>,
): Promise<ResultRevisionRecord> {
  const response = await fetch(
    `${apiUrl}/api/v1/documents/${documentId}/revisions/${revisionId}/corrections`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fields }),
    },
  );
  if (!response.ok) {
    throw await responseError(response);
  }
  return response.json() as Promise<ResultRevisionRecord>;
}

export async function approveDocumentRevision(
  documentId: string,
  revisionId: string,
): Promise<ResultRevisionRecord> {
  const response = await fetch(
    `${apiUrl}/api/v1/documents/${documentId}/revisions/${revisionId}/approve`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason: "Проверено оператором в интерфейсе" }),
    },
  );
  if (!response.ok) {
    throw await responseError(response);
  }
  return response.json() as Promise<ResultRevisionRecord>;
}

export async function getQualityReport(): Promise<QualityReport> {
  const response = await fetch(`${apiUrl}/api/v1/quality/report`);
  if (!response.ok) {
    throw await responseError(response);
  }
  return response.json() as Promise<QualityReport>;
}

export async function runQualityEvaluation(): Promise<QualityReport> {
  const response = await fetch(`${apiUrl}/api/v1/quality/run`, { method: "POST" });
  if (!response.ok) {
    throw await responseError(response);
  }
  return response.json() as Promise<QualityReport>;
}

export async function downloadRevisionExport(format: "csv" | "xlsx"): Promise<Blob> {
  const response = await fetch(`${apiUrl}/api/v1/exports/revisions?format=${format}`);
  if (!response.ok) {
    throw await responseError(response);
  }
  return response.blob();
}

export async function resolveExactDuplicate(
  documentId: string,
  decision: "keep" | "reject",
): Promise<DocumentRecord> {
  const response = await fetch(`${apiUrl}/api/v1/documents/${documentId}/duplicate-decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision }),
  });
  if (!response.ok) {
    throw await responseError(response);
  }
  return response.json() as Promise<DocumentRecord>;
}

export async function listAuditEvents(): Promise<AuditEventListResponse> {
  const response = await fetch(`${apiUrl}/api/v1/audit/events`);
  if (!response.ok) {
    throw await responseError(response);
  }
  return response.json() as Promise<AuditEventListResponse>;
}
