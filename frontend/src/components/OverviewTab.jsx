import { Sparkles } from "lucide-react";
import { MAX_TITLE_LENGTH } from "../constants/reqsenseData";

function formatDateTime(isoValue) {
  if (!isoValue) return "-";
  try {
    return new Intl.DateTimeFormat("tr-TR", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(isoValue));
  } catch {
    return isoValue;
  }
}

export default function OverviewTab({
  session,
  onTitleChange,
  onSummaryChange,
  onReuseRawInput,
}) {
  return (
    <div className="grid gap-5 lg:grid-cols-3">
      <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-2xs lg:col-span-2">
        <div>
          <label
            htmlFor="overview-title"
            className="block text-xs font-semibold uppercase tracking-wide text-slate-600"
          >
            Proje Başlığı
          </label>
          <input
            id="overview-title"
            type="text"
            maxLength={MAX_TITLE_LENGTH}
            value={session.title}
            onChange={(e) => onTitleChange(e.target.value)}
            className="mt-1.5 w-full rounded-xl border border-slate-200 px-3.5 py-2 text-sm font-semibold text-slate-900 focus:border-indigo-500 focus:outline-none"
          />
        </div>

        <div>
          <label
            htmlFor="overview-summary"
            className="block text-xs font-semibold uppercase tracking-wide text-slate-600"
          >
            Proje Özeti
          </label>
          <textarea
            id="overview-summary"
            rows={4}
            value={session.summary || ""}
            onChange={(e) => onSummaryChange(e.target.value)}
            placeholder="Sistem özeti girin..."
            className="mt-1.5 w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm leading-relaxed text-slate-700 focus:border-indigo-500 focus:outline-none"
          />
        </div>

        <div className="border-t border-slate-100 pt-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Analiz Edilen Ham Girdi Metni
            </span>
            <button
              type="button"
              onClick={() => onReuseRawInput(session.title, session.raw_input)}
              className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-semibold text-slate-700 hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700"
            >
              <Sparkles className="h-3.5 w-3.5" />
              Bu Metinle Yeni Analiz Başlat
            </button>
          </div>
          <div className="mt-2 whitespace-pre-wrap rounded-xl border border-slate-200 bg-slate-50 p-3.5 text-xs leading-relaxed text-slate-700">
            {session.raw_input}
          </div>
        </div>
      </div>

      <aside className="space-y-3 rounded-xl border border-slate-200 bg-white p-5 shadow-2xs">
        <h3 className="text-sm font-bold text-slate-900">Oturum Bilgileri</h3>
        <dl className="space-y-3 text-xs">
          <div className="flex justify-between gap-2 border-b border-slate-100 pb-2">
            <dt className="text-slate-500">Oturum Kimliği</dt>
            <dd className="font-semibold text-slate-800">#{session.id}</dd>
          </div>
          <div className="flex justify-between gap-2 border-b border-slate-100 pb-2">
            <dt className="text-slate-500">Analiz Modu</dt>
            <dd className="font-semibold text-slate-800">
              {session.source_mode === "demo"
                ? "Demo Modu (Yerel)"
                : "Gemini Structured Output"}
            </dd>
          </div>
          <div className="flex justify-between gap-2 border-b border-slate-100 pb-2">
            <dt className="text-slate-500">Oluşturulma</dt>
            <dd className="font-medium text-slate-800">
              {formatDateTime(session.created_at)}
            </dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt className="text-slate-500">Son Güncelleme</dt>
            <dd className="font-medium text-slate-800">
              {formatDateTime(session.updated_at)}
            </dd>
          </div>
        </dl>
      </aside>
    </div>
  );
}
