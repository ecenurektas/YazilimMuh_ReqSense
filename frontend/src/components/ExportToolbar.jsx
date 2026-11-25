import {
  Check,
  Download,
  Loader2,
  RotateCcw,
  Save,
} from "lucide-react";

const EXPORT_BUTTONS = [
  { format: "md", label: "Markdown (.md)" },
  { format: "csv", label: "CSV (.csv)" },
  { format: "json", label: "JSON (.json)" },
];

export default function ExportToolbar({
  session,
  isDirty,
  isSaving,
  exportingFormat,
  onSave,
  onRevert,
  onExport,
}) {
  const isBusy = isSaving || Boolean(exportingFormat);

  return (
    <div className="flex flex-col justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm lg:flex-row lg:items-center">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700">
            Oturum #{session.id}
          </span>
          <span
            className={`rounded-md px-2 py-0.5 text-xs font-semibold ${
              session.source_mode === "demo"
                ? "bg-amber-50 text-amber-800 ring-1 ring-amber-200"
                : "bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200"
            }`}
          >
            {session.source_mode === "demo" ? "Demo Modu" : "Gemini Yapay Zekâ"}
          </span>
          {isDirty ? (
            <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-900">
              Kaydedilmemiş değişiklikler var
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700">
              <Check className="h-3 w-3" />
              Veritabanıyla güncel
            </span>
          )}
        </div>
        <h2 className="mt-2 truncate text-lg font-bold text-slate-900 sm:text-xl">
          {session.title}
        </h2>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          disabled={!isDirty || isBusy}
          onClick={onRevert}
          className="inline-flex cursor-pointer items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          Geri Al
        </button>

        <button
          type="button"
          disabled={!isDirty || isBusy}
          onClick={onSave}
          className="inline-flex cursor-pointer items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-xs transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-indigo-300"
        >
          {isSaving ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Kaydediliyor...
            </>
          ) : (
            <>
              <Save className="h-3.5 w-3.5" />
              Değişiklikleri Kaydet
            </>
          )}
        </button>

        <div className="mx-1 hidden h-6 w-px bg-slate-200 sm:block" />

        {EXPORT_BUTTONS.map(({ format, label }) => {
          const active = exportingFormat === format;
          return (
            <button
              key={format}
              type="button"
              disabled={isBusy}
              onClick={() => onExport(format)}
              className="inline-flex cursor-pointer items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {active ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Download className="h-3.5 w-3.5" />
              )}
              {label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
