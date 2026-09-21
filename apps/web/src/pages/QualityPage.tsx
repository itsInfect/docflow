import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BarChart3, CheckCircle2, FlaskConical, LoaderCircle, Play, ShieldCheck } from "lucide-react";

import { PageHeader } from "../components/PageHeader";
import {
  getQualityReport,
  runQualityEvaluation,
  type QualityMetrics,
  type QualityReport,
} from "../lib/api";

const splitLabels: Record<string, string> = {
  development: "Development",
  holdout: "Holdout",
  stress: "Stress",
};

function percent(value: number | undefined) {
  return value === undefined ? "—" : `${(value * 100).toFixed(1)}%`;
}

export function QualityPage() {
  const queryClient = useQueryClient();
  const report = useQuery({ queryKey: ["quality-report"], queryFn: getQualityReport });
  const evaluation = useMutation({
    mutationFn: runQualityEvaluation,
    onSuccess: (data) => queryClient.setQueryData(["quality-report"], data),
  });
  const data = evaluation.data ?? report.data;

  return (
    <>
      <PageHeader
        kicker="DF / Evaluation"
        title="Качество моделей"
        description="Воспроизводимые показатели на development, holdout и stress-выборках."
        actions={
          <button className="primary-button" type="button" disabled={evaluation.isPending} onClick={() => evaluation.mutate()}>
            {evaluation.isPending ? <LoaderCircle className="spin" size={15} /> : <Play size={15} />}
            Запустить оценку
          </button>
        }
      />

      {report.isLoading && <QualityLoading />}
      {(report.error || evaluation.error) && (
        <div className="quality-message quality-message--error panel">
          Не удалось выполнить оценку: {report.error?.message ?? evaluation.error?.message}
        </div>
      )}
      {!report.isLoading && !report.error && !data?.available && <EmptyQuality />}
      {data?.available && data.overall && <QualityReportView report={data} />}
    </>
  );
}

function QualityLoading() {
  return <div className="quality-message panel"><LoaderCircle className="spin" size={18} /> Загружаем последний отчёт…</div>;
}

function EmptyQuality() {
  return (
    <section className="quality-empty panel">
      <FlaskConical size={34} />
      <strong>Контрольный прогон ещё не выполнен</strong>
      <p>Система сгенерирует 30 счетов в трёх макетах, отделит holdout и stress-наборы и рассчитает метрики без случайных demo-значений.</p>
    </section>
  );
}

function QualityReportView({ report }: { report: QualityReport }) {
  const metrics = report.overall as QualityMetrics;
  const cards = [
    { name: "Классификация", value: percent(metrics.classification_accuracy), key: "Accuracy", note: "Тип документа" },
    { name: "Извлечение", value: percent(metrics.field_accuracy), key: "Field accuracy", note: "Все реквизиты" },
    { name: "Автообработка", value: percent(metrics.stp_rate), key: "STP rate", note: `Precision ${percent(metrics.stp_precision)}` },
  ];

  return (
    <>
      <section className="quality-grid">
        {cards.map((metric, index) => (
          <article className="quality-metric panel" key={metric.name}>
            <span className="metric-index">0{index + 1}</span>
            <div><span>{metric.name}</span><strong>{metric.value}</strong><small>{metric.key} · {metric.note}</small></div>
            <span className="locked-tag quality-ready"><CheckCircle2 size={13} /> {report.case_count} примеров</span>
          </article>
        ))}
      </section>

      <section className="quality-layout">
        <article className="quality-panel quality-panel--chart panel">
          <div className="card-header">
            <div><span className="section-label">Calibration</span><h2>Порог автоприёмки</h2></div>
            <BarChart3 size={20} />
          </div>
          <div className="threshold-chart">
            {(report.threshold_curve ?? []).map((point) => (
              <div className={point.threshold === report.recommended_threshold ? "threshold-column threshold-column--active" : "threshold-column"} key={point.threshold}>
                <span className="threshold-value">{percent(point.coverage)}</span>
                <div className="threshold-track"><span style={{ height: `${Math.max(point.coverage * 100, 3)}%` }} /></div>
                <strong>{point.threshold.toFixed(2)}</strong>
              </div>
            ))}
          </div>
          <div className="calibration-note">
            <ShieldCheck size={18} />
            <div><strong>Рекомендуемый threshold: {report.recommended_threshold?.toFixed(2)}</strong><p>Максимальное покрытие при целевой precision не ниже {percent(report.target_precision)}.</p></div>
          </div>
        </article>

        <aside className="quality-panel panel">
          <div className="card-header">
            <div><span className="section-label">Evidence</span><h2>Состав отчёта</h2></div>
            <FlaskConical size={20} />
          </div>
          <dl className="quality-facts">
            <div><dt>Dataset</dt><dd>{report.dataset_version}</dd></div>
            <div><dt>Baseline</dt><dd>{report.model_version}</dd></div>
            <div><dt>Critical fields</dt><dd>{percent(metrics.critical_field_accuracy)}</dd></div>
            <div><dt>Grounding</dt><dd>{percent(metrics.grounding_rate)}</dd></div>
            <div><dt>Дата прогона</dt><dd>{report.generated_at}</dd></div>
          </dl>
        </aside>
      </section>

      <section className="split-panel panel">
        <div className="card-header"><div><span className="section-label">Dataset splits</span><h2>Устойчивость по выборкам</h2></div></div>
        <div className="split-table">
          <div className="split-row split-row--head"><span>Выборка</span><span>Примеров</span><span>Классификация</span><span>Поля</span><span>Critical</span><span>STP</span></div>
          {Object.entries(report.splits ?? {}).map(([name, split]) => (
            <div className="split-row" key={name}><strong>{splitLabels[name] ?? name}</strong><span>{split.case_count}</span><span>{percent(split.classification_accuracy)}</span><span>{percent(split.field_accuracy)}</span><span>{percent(split.critical_field_accuracy)}</span><span>{percent(split.stp_rate)}</span></div>
          ))}
        </div>
      </section>
    </>
  );
}
