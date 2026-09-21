import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Check,
  CheckCircle2,
  ClipboardCheck,
  FileWarning,
  LoaderCircle,
  Save,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";
import { useState } from "react";

import { PageHeader } from "../components/PageHeader";
import { useDocuments } from "../hooks/useDocuments";
import {
  approveDocumentRevision,
  correctDocumentRevision,
  listDocumentRevisions,
  resolveExactDuplicate,
  type DocumentRecord,
  type ResultRevisionRecord,
} from "../lib/api";
import { formatDate, statusLabel } from "../lib/documents";

const reviewRules = [
  { code: "R-01", title: "Низкая уверенность", description: "Confidence ниже порога автоприёмки." },
  { code: "R-02", title: "Обязательное поле", description: "Не заполнен обязательный реквизит." },
  { code: "R-03", title: "Проверка значения", description: "Нарушено детерминированное бизнес-правило." },
];

const fieldLabels: Record<string, string> = {
  doc_number: "Номер документа",
  doc_date: "Дата документа",
  supplier_inn: "ИНН поставщика",
  supplier_name: "Поставщик",
  buyer_inn: "ИНН покупателя",
  buyer_name: "Покупатель",
  amount_without_vat: "Сумма без НДС",
  vat_rate: "Ставка НДС",
  vat_amount: "Сумма НДС",
  total_amount: "Итого",
  currency: "Валюта",
};

const serviceActFieldLabels: Record<string, string> = {
  ...fieldLabels,
  doc_number: "Номер акта",
  doc_date: "Дата акта",
  supplier_inn: "ИНН исполнителя",
  supplier_name: "Исполнитель",
  buyer_inn: "ИНН заказчика",
  buyer_name: "Заказчик",
  total_amount: "Стоимость работ",
};

export function ReviewPage() {
  const documents = useDocuments();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const items = documents.data?.items ?? [];
  const queue = items.filter((item) => ["needs_review", "duplicate_file"].includes(item.status));
  const activeId = queue.some((item) => item.id === selectedId) ? selectedId : queue[0]?.id;
  const activeDocument = queue.find((item) => item.id === activeId);

  return (
    <>
      <PageHeader
        kicker="DF / Контроль"
        title="Ручная проверка"
        description="Исправление извлечённых реквизитов и подтверждение решения оператором."
      />

      <section className="review-summary panel" aria-label="Состояние очереди">
        <div className="review-stat"><span>В очереди</span><strong>{queue.length}</strong><small>требуют решения</small></div>
        <div className="review-stat"><span>Правил контроля</span><strong>{reviewRules.length}</strong><small>объяснимые проверки</small></div>
        <div className="review-stat review-stat--note">
          <ShieldCheck size={22} />
          <div><span>Ревизии неизменяемы</span><small>Любое исправление сохраняется новой версией результата.</small></div>
        </div>
      </section>

      <section className="review-layout">
        <article className="queue-panel panel">
          <div className="card-header">
            <div><span className="section-label">Очередь оператора</span><h2>Документы</h2></div>
            <span className="panel-counter">{queue.length.toString().padStart(2, "0")}</span>
          </div>
          {documents.isLoading && <div className="review-empty">Загружаем очередь…</div>}
          {documents.error && (
            <div className="review-empty review-empty--error"><FileWarning size={28} /><strong>Очередь недоступна</strong><span>{documents.error.message}</span></div>
          )}
          {!documents.isLoading && !documents.error && queue.length === 0 && (
            <div className="review-empty"><CheckCircle2 size={32} /><strong>Очередь пуста</strong><span>Все документы обработаны или ещё не запускались.</span></div>
          )}
          {queue.length > 0 && (
            <div className="queue-list">
              {queue.map((document) => (
                <button
                  className={document.id === activeId ? "queue-item queue-item--active" : "queue-item"}
                  type="button"
                  onClick={() => setSelectedId(document.id)}
                  key={document.id}
                >
                  <span className="queue-icon"><ClipboardCheck size={18} /></span>
                  <span className="queue-copy"><strong>{document.original_filename}</strong><small>{formatDate(document.created_at)} · {statusLabel(document.status)}</small></span>
                  <span className="queue-confidence">{document.confidence === null ? "—" : `${Math.round(document.confidence * 100)}%`}</span>
                </button>
              ))}
            </div>
          )}
        </article>

        {activeDocument ? (
          activeDocument.status === "duplicate_file" ? <ExactDuplicateReview document={activeDocument} /> : <ReviewWorkspace document={activeDocument} />
        ) : <RulesPanel />}
      </section>
    </>
  );
}

function ExactDuplicateReview({ document }: { document: DocumentRecord }) {
  const queryClient = useQueryClient();
  const decision = useMutation({
    mutationFn: (value: "keep" | "reject") => resolveExactDuplicate(document.id, value),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["documents"] }),
        queryClient.invalidateQueries({ queryKey: ["audit-events"] }),
      ]);
    },
  });

  return (
    <aside className="review-workspace panel">
      <div className="card-header"><div><span className="section-label">Точный дубль</span><h2>{document.original_filename}</h2></div><span className="revision-badge">SHA-256</span></div>
      <div className="duplicate-review">
        <FileWarning size={28} />
        <strong>Файл полностью совпадает с уже загруженным</strong>
        <p>Исходный документ: <span>{document.is_duplicate_of?.slice(0, 8)}</span>. Выберите, нужно ли сохранить копию как самостоятельный документ.</p>
      </div>
      {decision.error && <p className="run-error">{decision.error.message}</p>}
      <div className="review-actions">
        <button className="secondary-button" type="button" disabled={decision.isPending} onClick={() => decision.mutate("reject")}>Не обрабатывать</button>
        <button className="primary-button" type="button" disabled={decision.isPending} onClick={() => decision.mutate("keep")}>
          {decision.isPending ? <LoaderCircle className="spin" size={14} /> : <Check size={14} />} Оставить отдельно
        </button>
      </div>
    </aside>
  );
}

function ReviewWorkspace({ document }: { document: DocumentRecord }) {
  const revisions = useQuery({
    queryKey: ["document-revisions", document.id],
    queryFn: () => listDocumentRevisions(document.id),
  });
  const latest = revisions.data?.items[0];

  return (
    <aside className="review-workspace panel">
      <div className="card-header">
        <div><span className="section-label">Рабочая область</span><h2>{document.original_filename}</h2></div>
        {latest && <span className="revision-badge">REV {latest.revision_number}</span>}
      </div>
      {revisions.isLoading && <div className="review-editor-state">Загружаем результат…</div>}
      {revisions.error && <div className="review-editor-state review-empty--error">{revisions.error.message}</div>}
      {!revisions.isLoading && !revisions.error && !latest && (
        <div className="review-editor-state">Для документа ещё нет извлечённой ревизии.</div>
      )}
      {latest && <RevisionEditor document={document} revision={latest} key={latest.id} />}
    </aside>
  );
}

function RevisionEditor({ document, revision }: { document: DocumentRecord; revision: ResultRevisionRecord }) {
  const queryClient = useQueryClient();
  const labels = revision.schema_code === "service_act" ? serviceActFieldLabels : fieldLabels;
  const [fields, setFields] = useState<Record<string, string>>(() =>
    Object.fromEntries(Object.entries(revision.fields_json).map(([key, value]) => [key, value === null ? "" : String(value)])),
  );
  const failedChecks = revision.validation_json.filter((item) => !item.passed);
  const correction = useMutation({
    mutationFn: () => correctDocumentRevision(document.id, revision.id, fields),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["document-revisions", document.id] }),
        queryClient.invalidateQueries({ queryKey: ["document-runs", document.id] }),
        queryClient.invalidateQueries({ queryKey: ["audit-events"] }),
      ]);
    },
  });
  const approval = useMutation({
    mutationFn: () => approveDocumentRevision(document.id, revision.id),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["documents"] }),
        queryClient.invalidateQueries({ queryKey: ["document-revisions", document.id] }),
        queryClient.invalidateQueries({ queryKey: ["audit-events"] }),
      ]);
    },
  });

  return (
    <>
      <div className="review-meta"><span>{revision.schema_code} / schema v{revision.schema_version}</span><span>{revision.extraction_model}</span></div>
      <div className="review-form">
        {Object.keys(labels).map((key) => (
          <label className="review-field" key={key}>
            <span>{labels[key]}</span>
            <input value={fields[key] ?? ""} onChange={(event) => setFields((current) => ({ ...current, [key]: event.target.value }))} />
          </label>
        ))}
      </div>
      <div className={failedChecks.length ? "validation-box validation-box--failed" : "validation-box validation-box--passed"}>
        <div>{failedChecks.length ? <TriangleAlert size={16} /> : <CheckCircle2 size={16} />}<strong>{failedChecks.length ? `Нарушений: ${failedChecks.length}` : "Все проверки пройдены"}</strong></div>
        {failedChecks.length > 0 && <ul>{failedChecks.map((item, index) => <li key={`${item.code}-${index}`}>{item.message}</li>)}</ul>}
      </div>
      {(correction.error || approval.error) && <p className="run-error">{correction.error?.message ?? approval.error?.message}</p>}
      <div className="review-actions">
        <button className="secondary-button" type="button" disabled={correction.isPending || approval.isPending} onClick={() => correction.mutate()}>
          {correction.isPending ? <LoaderCircle className="spin" size={14} /> : <Save size={14} />} Сохранить новой ревизией
        </button>
        <button className="primary-button" type="button" disabled={correction.isPending || approval.isPending} onClick={() => approval.mutate()}>
          {approval.isPending ? <LoaderCircle className="spin" size={14} /> : <Check size={14} />} Подтвердить
        </button>
      </div>
    </>
  );
}

function RulesPanel() {
  return (
    <aside className="rules-panel panel">
      <div className="card-header"><div><span className="section-label">Логика маршрутизации</span><h2>Почему нужна проверка</h2></div></div>
      <p className="panel-intro">Документ направляется оператору только после срабатывания понятного правила.</p>
      <div className="rule-list">
        {reviewRules.map((rule) => <div className="rule-row" key={rule.code}><span className="rule-code">{rule.code}</span><div><strong>{rule.title}</strong><p>{rule.description}</p></div></div>)}
      </div>
    </aside>
  );
}
