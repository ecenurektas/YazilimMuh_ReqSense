import {
  AlertTriangle,
  ArrowRight,
  Clock,
  History,
  Loader2,
} from "lucide-react";

function formatShortDate(isoValue) {
  if (!isoValue) return "";
  try {
    return new Intl.DateTimeFormat("tr-TR", {
      dateStyle: "short",
      timeStyle: "short",
    }).format(new Date(isoValue));
  } catch {
    return isoValue;
  }
}

export default function RecentSessionsCard({
  sessions,
  loadingSessionId,
  onSelectSession,
  onOpenHistory,
}) {
  if (!sessions || sessions.length === 0) {
    return null;
  }

  const recent = sessions.slice(0, 4);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
            <History className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              Son Analiz Oturumları
            </h3>
            <p className="text-xs text-slate-500">
              Önceki analizlerinize tek tıkla geri dönüp düzenleme veya dışa
              aktarma yapabilirsiniz.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={onOpenHistory}
          className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700"
        >
          Tüm Geçmişi Yönet ({sessions.length})
          <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {recent.map((item) => {
          const isLoading = loadingSessionId === item.id;
          return (
            <button
              key={item.id}
              type="button"
              disabled={Boolean(loadingSessionId)}
              onClick={() => onSelectSession(item.id)}
              className="group flex cursor-pointer flex-col justify-between rounded-xl border border-slate-200 bg-slate-50/60 p-4 text-left transition hover:border-indigo-300 hover:bg-indigo-50/40 disabled:cursor-wait"
            >
              <div>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[11px] font-bold text-slate-400">
                    #{item.id}
                  </span>
                  <span
                    className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                      item.source_mode === "demo"
                        ? "bg-amber-50 text-amber-800 ring-1 ring-amber-200"
                        : "bg-white text-slate-600 ring-1 ring-slate-200"
                    }`}
                  >
                    {item.source_mode === "demo" ? "Demo" : "Gemini AI"}
                  </span>
                </div>
                <h4 className="mt-2 line-clamp-2 text-sm font-bold text-slate-900 group-hover:text-indigo-700">
                  {item.title}
                </h4>
              </div>

              <div className="mt-3 space-y-1.5 border-t border-slate-200/70 pt-2.5 text-[11px] text-slate-600">
                <div className="flex items-center justify-between">
                  <span>
                    {item.requirement_count} Gereksinim · {item.user_story_count}{" "}
                    Hikâye
                  </span>
                  {isLoading ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-indigo-600" />
                  ) : (
                    item.ambiguity_count > 0 && (
                      <span className="inline-flex items-center gap-0.5 font-semibold text-amber-700">
                        <AlertTriangle className="h-3 w-3" />
                        {item.ambiguity_count}
                      </span>
                    )
                  )}
                </div>
                <div className="flex items-center gap-1 text-[10px] text-slate-400">
                  <Clock className="h-3 w-3" />
                  {formatShortDate(item.created_at)}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}
