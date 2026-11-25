import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Clock,
  History,
  Layers,
  ListChecks,
  Loader2,
  RefreshCw,
  Search,
  Trash2,
  X,
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

export default function SessionHistoryDrawer({
  isOpen,
  onClose,
  sessions,
  activeSessionId,
  isLoadingList,
  loadingSessionId,
  deletingSessionId,
  onRefresh,
  onSelectSession,
  onDeleteSession,
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);

  useEffect(() => {
    if (!isOpen) {
      setConfirmDeleteId(null);
    }
  }, [isOpen]);

  if (!isOpen) {
    return null;
  }

  const normalizedQuery = searchQuery.trim().toLocaleLowerCase("tr-TR");
  const filteredSessions = sessions.filter((item) => {
    if (!normalizedQuery) return true;
    const titleMatch = (item.title || "")
      .toLocaleLowerCase("tr-TR")
      .includes(normalizedQuery);
    const summaryMatch = (item.summary || "")
      .toLocaleLowerCase("tr-TR")
      .includes(normalizedQuery);
    return titleMatch || summaryMatch;
  });

  return (
    <div
      className="fixed inset-0 z-40 flex justify-end bg-slate-900/40 backdrop-blur-[1px]"
      role="dialog"
      aria-modal="true"
      aria-label="Geçmiş Analiz Oturumları"
      onClick={onClose}
    >
      <aside
        className="flex h-full w-full max-w-md flex-col border-l border-slate-200 bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
              <History className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900">
                Geçmiş Analiz Oturumları
              </h2>
              <p className="text-xs text-slate-500">
                Kayıtlı {sessions.length} oturum
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={onRefresh}
              disabled={isLoadingList}
              title="Listeyi Yenile"
              className="inline-flex cursor-pointer items-center justify-center rounded-lg border border-slate-200 p-1.5 text-slate-600 transition hover:bg-slate-50 disabled:opacity-50"
            >
              <RefreshCw
                className={`h-4 w-4 ${isLoadingList ? "animate-spin" : ""}`}
              />
            </button>
            <button
              type="button"
              onClick={onClose}
              aria-label="Çekmeceyi Kapat"
              className="inline-flex cursor-pointer items-center justify-center rounded-lg p-1.5 text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="border-b border-slate-100 px-5 py-3">
          <div className="relative">
            <Search className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Başlık veya özet içinde ara..."
              className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2 pr-3 pl-9 text-xs text-slate-800 placeholder:text-slate-400 focus:border-indigo-500 focus:bg-white focus:outline-none"
            />
          </div>
        </div>

        <div className="flex-1 space-y-3 overflow-y-auto p-4 sm:p-5">
          {isLoadingList && sessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center text-xs text-slate-500">
              <Loader2 className="h-5 w-5 animate-spin text-indigo-600" />
              <p className="mt-2">Oturum geçmişi yükleniyor...</p>
            </div>
          ) : filteredSessions.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/70 p-6 text-center">
              <p className="text-xs font-medium text-slate-600">
                {sessions.length === 0
                  ? "Henüz kayıtlı analiz oturumu bulunmuyor."
                  : "Arama kriterine uyan oturum bulunamadı."}
              </p>
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery("")}
                  className="mt-2 cursor-pointer text-xs font-semibold text-indigo-600 hover:underline"
                >
                  Aramayı Temizle
                </button>
              )}
            </div>
          ) : (
            filteredSessions.map((item) => {
              const isActive = item.id === activeSessionId;
              const isLoadingItem = loadingSessionId === item.id;
              const isDeletingItem = deletingSessionId === item.id;
              const isConfirming = confirmDeleteId === item.id;

              return (
                <article
                  key={item.id}
                  className={`rounded-xl border p-3.5 transition ${
                    isActive
                      ? "border-indigo-300 bg-indigo-50/40 ring-1 ring-indigo-200"
                      : "border-slate-200 bg-white hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <button
                      type="button"
                      disabled={isLoadingItem || isDeletingItem}
                      onClick={() => onSelectSession(item.id)}
                      className="min-w-0 flex-1 cursor-pointer text-left disabled:cursor-wait"
                    >
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="text-[11px] font-bold text-slate-400">
                          #{item.id}
                        </span>
                        {isActive && (
                          <span className="rounded-md bg-indigo-600 px-1.5 py-0.5 text-[10px] font-bold text-white">
                            Açık
                          </span>
                        )}
                        <span
                          className={`rounded-md px-1.5 py-0.5 text-[10px] font-semibold ${
                            item.source_mode === "demo"
                              ? "bg-amber-50 text-amber-800 ring-1 ring-amber-200"
                              : "bg-slate-100 text-slate-700"
                          }`}
                        >
                          {item.source_mode === "demo" ? "Demo" : "Gemini AI"}
                        </span>
                      </div>

                      <h3 className="mt-1.5 line-clamp-1 text-sm font-bold text-slate-900">
                        {item.title}
                      </h3>
                      {item.summary && (
                        <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-slate-600">
                          {item.summary}
                        </p>
                      )}
                    </button>

                    <div className="flex shrink-0 items-center gap-1">
                      {isLoadingItem ? (
                        <Loader2 className="h-4 w-4 animate-spin text-indigo-600" />
                      ) : (
                        <button
                          type="button"
                          title="Oturumu Sil"
                          disabled={isDeletingItem}
                          onClick={() =>
                            setConfirmDeleteId(isConfirming ? null : item.id)
                          }
                          className="inline-flex cursor-pointer items-center rounded-lg p-1.5 text-slate-400 transition hover:bg-rose-50 hover:text-rose-600 disabled:opacity-50"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="mt-2.5 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
                    <span className="inline-flex items-center gap-1">
                      <Layers className="h-3 w-3 text-indigo-500" />
                      {item.requirement_count} Gereksinim
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <ListChecks className="h-3 w-3 text-indigo-500" />
                      {item.user_story_count} Hikâye
                    </span>
                    {item.ambiguity_count > 0 && (
                      <span className="inline-flex items-center gap-1 rounded bg-amber-50 px-1.5 py-0.5 font-semibold text-amber-800">
                        <AlertTriangle className="h-3 w-3 text-amber-600" />
                        {item.ambiguity_count} Belirsizlik
                      </span>
                    )}
                    <span className="ml-auto inline-flex items-center gap-1 text-[10px] text-slate-400">
                      <Clock className="h-3 w-3" />
                      {formatShortDate(item.created_at)}
                    </span>
                  </div>

                  {isConfirming && (
                    <div className="mt-3 flex items-center justify-between gap-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs">
                      <span className="font-semibold text-rose-800">
                        Kalıcı olarak silinsin mi?
                      </span>
                      <div className="flex items-center gap-1.5">
                        <button
                          type="button"
                          disabled={isDeletingItem}
                          onClick={() => setConfirmDeleteId(null)}
                          className="cursor-pointer rounded-md border border-slate-200 bg-white px-2 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-50"
                        >
                          Vazgeç
                        </button>
                        <button
                          type="button"
                          disabled={isDeletingItem}
                          onClick={() => onDeleteSession(item.id)}
                          className="inline-flex cursor-pointer items-center gap-1 rounded-md bg-rose-600 px-2.5 py-1 text-[11px] font-semibold text-white hover:bg-rose-700 disabled:opacity-60"
                        >
                          {isDeletingItem ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : null}
                          Sil
                        </button>
                      </div>
                    </div>
                  )}
                </article>
              );
            })
          )}
        </div>
      </aside>
    </div>
  );
}
