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
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [clientError, setClientError] = useState<string | null>(null);

  const upload = useMutation({
    mutationFn: uploadDocument,
    onSuccess: async () => {
      setFile(null);
      setClientError(null);
      await queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  function chooseFile(candidate: File | undefined) {
    upload.reset();
    if (!candidate) return;
    if (candidate.size > maxSizeBytes) {
      setClientError("Файл больше 20 МБ");
      setFile(null);
      return;
    }
    setClientError(null);
    setFile(candidate);
  }

  return (
    <section className="panel upload-card" id="upload">
      <div className="card-header">
        <div>
          <span className="section-label">Приём документов</span>
          <h2>Загрузить файл</h2>
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
          chooseFile(event.dataTransfer.files[0]);
        }}
      >
        <span className="dropzone-icon">
          <UploadCloud size={26} />
        </span>
        <strong>Перетащите файл сюда</strong>
        <span>или нажмите, чтобы выбрать</span>
        <small>PDF, JPG, PNG или TIFF · до 20 МБ</small>
      </button>
      <input
        ref={inputRef}
        className="visually-hidden"
        type="file"
        accept=".pdf,.jpg,.jpeg,.png,.tif,.tiff,application/pdf,image/jpeg,image/png,image/tiff"
        onChange={(event) => chooseFile(event.target.files?.[0])}
      />

      {file && (
        <div className="selected-file">
          <div>
            <strong>{file.name}</strong>
            <span>{formatSize(file.size)}</span>
          </div>
          <button type="button" aria-label="Убрать файл" onClick={() => setFile(null)}>
            <X size={16} />
          </button>
        </div>
      )}

      {(clientError || upload.error) && (
        <p className="form-message form-message--error">
          {clientError ?? upload.error?.message}
        </p>
      )}
      {upload.isSuccess && (
        <p className="form-message form-message--success">
          <CheckCircle2 size={15} /> Документ принят
        </p>
      )}

      <button
        className="upload-action"
        type="button"
        disabled={!file || upload.isPending}
        onClick={() => file && upload.mutate(file)}
      >
        {upload.isPending ? <LoaderCircle className="spin" size={18} /> : <FileUp size={18} />}
        {upload.isPending ? "Загружаем…" : "Загрузить документ"}
      </button>
    </section>
  );
}
