import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  History,
  Plus,
  Sparkles,
} from "lucide-react";

export default function Header({
  health,
  hasActiveSession,
  sessionCount,
  onNewAnalysis,
  onOpenHistory,
  onRecheckHealth,
}) {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur-xs">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3.5 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-sm">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-slate-900">
                ReqSense
              </h1>
              <span className="hidden rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600 sm:inline-block">
                v{health.version || "0.1.0"}
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Yapay Zekâ Destekli Yazılım Gereksinim Analizi Sistemi
            </p>
          </div>
        </div>

        <div className="hidden items-center gap-2 text-xs text-slate-500 lg:flex">
          <span
            className={`rounded-full px-2.5 py-1 font-medium ${
              !hasActiveSession
                ? "bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200"
                : "text-slate-500"
            }`}
          >
            1. Metin Gir
          </span>
          <span className="text-slate-300">→</span>
          <span className="px-1 font-medium text-slate-500">2. Analiz Et</span>
          <span className="text-slate-300">→</span>
          <span
            className={`rounded-full px-2.5 py-1 font-medium ${
              hasActiveSession
                ? "bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200"
                : "text-slate-500"
            }`}
          >
            3. Düzenle & Dışa Aktar
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={onOpenHistory}
            className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-2xs transition hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700"
          >
            <History className="h-3.5 w-3.5" />
            <span>Geçmiş Oturumlar</span>
            <span className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-bold text-slate-700">
              {sessionCount}
            </span>
          </button>

          {hasActiveSession && (
            <button
              type="button"
              onClick={onNewAnalysis}
              className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-semibold text-indigo-700 shadow-2xs transition hover:bg-indigo-100"
            >
              <Plus className="h-3.5 w-3.5" />
              Yeni Analiz
            </button>
          )}

          {health.status === "checking" && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
              <Activity className="h-3.5 w-3.5 animate-pulse" />
              API kontrol ediliyor...
            </span>
          )}
          {health.status === "online" && (
            <button
              type="button"
              onClick={onRecheckHealth}
              title="Bağlantı durumunu yenile"
              className="inline-flex cursor-pointer items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200 transition hover:bg-emerald-100"
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              Backend Bağlı {health.demoMode ? "(Demo Modu)" : ""}
            </button>
          )}
          {health.status === "offline" && (
            <button
              type="button"
              onClick={onRecheckHealth}
              title="Bağlantıyı yeniden kontrol et"
              className="inline-flex cursor-pointer items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-800 ring-1 ring-amber-200 transition hover:bg-amber-100"
            >
              <AlertTriangle className="h-3.5 w-3.5" />
              Backend Çevrimdışı (Port 8000)
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
