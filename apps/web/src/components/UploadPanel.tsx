import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, FileUp, LoaderCircle, UploadCloud, X } from "lucide-react";

import { uploadDocument } from "../lib/api";

const maxSizeBytes = 20 * 1024 * 1024;

function formatSize(bytes: number) {
  return `${(bytes / 1024 / 1024).toFixed(2)} МБ`;
}

export function UploadPanel() {
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const [files, setFiles] = useState<File[]>([]);
  const [progress, setProgress] = useState({ completed: 0, total: 0 });
  const [dragging, setDragging] = useState(false);
  const [clientError, setClientError] = useState<string | null>(null);

  const upload = useMutation({
    mutationFn: async (batch: File[]) => {
      const result = { success: 0, errors: [] as string[] };
      setProgress({ completed: 0, total: batch.length });
      for (const file of batch) {
        try {
          await uploadDocument(file);
          result.success += 1;
        } catch (error) {
          result.errors.push(`${file.name}: ${error instanceof Error ? error.message : "ошибка"}`);
        }
        setProgress((current) => ({ ...current, completed: current.completed + 1 }));
      }
      return result;
    },
    onSuccess: async () => {
      setFiles([]);
      setClientError(null);
      if (inputRef.current) inputRef.current.value = "";
      await queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  function chooseFiles(candidates: File[]) {
    upload.reset();
    if (!candidates.length) return;
    const oversized = candidates.filter((file) => file.size > maxSizeBytes);
    if (oversized.length) {
      setClientError(`Превышен лимит 20 МБ: ${oversized.map((file) => file.name).join(", ")}`);
      return;
    }
    setClientError(null);
    setFiles(candidates.slice(0, 20));
  }

  return (
    <section className="panel upload-card" id="upload">
      <div className="card-header">
        <div>
          <span className="section-label">Приём документов</span>
          <h2>Загрузить документы</h2>
        </div>
        <span className="header-icon">
          <FileUp size={19} />
        </span>
      </div>

      <button
        className={`dropzone${dragging ? " dropzone--active" : ""}`}
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragEnter={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragOver={(event) => event.preventDefault()}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          chooseFiles(Array.from(event.dataTransfer.files));
        }}
      >
        <span className="dropzone-icon">
          <UploadCloud size={26} />
        </span>
        <strong>Перетащите файлы сюда</strong>
        <span>или нажмите, чтобы выбрать до 20 документов</span>
        <small>PDF, JPG, PNG или TIFF · до 20 МБ каждый</small>
      </button>
      <input
        ref={inputRef}
        className="visually-hidden"
        type="file"
        multiple
        accept=".pdf,.jpg,.jpeg,.png,.tif,.tiff,application/pdf,image/jpeg,image/png,image/tiff"
        onChange={(event) => chooseFiles(Array.from(event.target.files ?? []))}
      />

      {files.length > 0 && (
        <div className="selected-files">
          {files.map((file, index) => (
            <div className="selected-file" key={`${file.name}-${file.lastModified}`}>
              <div><strong>{file.name}</strong><span>{formatSize(file.size)}</span></div>
              <button type="button" aria-label={`Убрать ${file.name}`} onClick={() => setFiles((current) => current.filter((_, itemIndex) => itemIndex !== index))}>
                <X size={16} />
              </button>
            </div>
          ))}
        </div>
      )}

      {(clientError || upload.error) && (
        <p className="form-message form-message--error">
          {clientError ?? upload.error?.message}
        </p>
      )}
      {upload.isSuccess && upload.data && (
        <p className="form-message form-message--success">
          <CheckCircle2 size={15} /> Принято документов: {upload.data.success}
        </p>
      )}
      {upload.data?.errors.map((message) => <p className="form-message form-message--error" key={message}>{message}</p>)}

      <button
        className="upload-action"
        type="button"
        disabled={!files.length || upload.isPending}
        onClick={() => files.length && upload.mutate(files)}
      >
        {upload.isPending ? <LoaderCircle className="spin" size={18} /> : <FileUp size={18} />}
        {upload.isPending ? `Загружено ${progress.completed} из ${progress.total}` : `Загрузить${files.length > 1 ? ` ${files.length} документов` : " документ"}`}
      </button>
    </section>
  );
}
