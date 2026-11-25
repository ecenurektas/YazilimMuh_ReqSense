import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  ClipboardList,
  Layers,
  ListChecks,
  X,
} from "lucide-react";
import ExportToolbar from "./components/ExportToolbar";
import Header from "./components/Header";
import MetricsSummary from "./components/MetricsSummary";
import OverviewTab from "./components/OverviewTab";
import RecentSessionsCard from "./components/RecentSessionsCard";
import RequirementForm from "./components/RequirementForm";
import RequirementsTab from "./components/RequirementsTab";
import SessionHistoryDrawer from "./components/SessionHistoryDrawer";
import UserStoriesTab from "./components/UserStoriesTab";
import { MIN_INPUT_LENGTH } from "./constants/reqsenseData";
import {
  analyzeRequirements,
  checkHealth,
  deleteSession,
  exportSessionFile,
  getSession,
  listSessions,
  updateSession,
} from "./services/api";
import {
  hydrateSessionForEditor,
  isSessionDirty,
  serializeSessionForUpdate,
  validateSessionDraft,
} from "./utils/sessionMapper";

const ACTIVE_SESSION_STORAGE_KEY = "reqsense_active_session_id";

const TABS = [
  { id: "requirements", label: "Gereksinimler (FR / NFR)", icon: Layers },
  {
    id: "stories",
    label: "Kullanıcı Hikâyeleri & Kabul Kriterleri",
    icon: ListChecks,
  },
  { id: "overview", label: "Proje Özeti & Ham Metin", icon: ClipboardList },
];

function toSessionSummary(detail) {
  const requirements = detail.requirements || [];
  const userStories = detail.user_stories || [];
  return {
    id: detail.id,
    title: detail.title,
    summary: detail.summary,
    source_mode: detail.source_mode,
    requirement_count: detail.requirement_count ?? requirements.length,
    user_story_count: detail.user_story_count ?? userStories.length,
    ambiguity_count:
      detail.ambiguity_count ??
      requirements.filter((r) => Boolean(r.ambiguity_warning?.trim())).length,
    created_at: detail.created_at,
    updated_at: detail.updated_at,
  };
}

export default function App() {
  const [health, setHealth] = useState({
    status: "checking",
    demoMode: false,
    version: "0.1.0",
  });

  const [formTitle, setFormTitle] = useState("");
  const [formRawInput, setFormRawInput] = useState("");
  const [useDemoMode, setUseDemoMode] = useState(false);
  const [analyzeError, setAnalyzeError] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const [savedSession, setSavedSession] = useState(null);
  const [draftSession, setDraftSession] = useState(null);
  const [isRestoring, setIsRestoring] = useState(false);

  const [sessions, setSessions] = useState([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [loadingSessionId, setLoadingSessionId] = useState(null);
  const [deletingSessionId, setDeletingSessionId] = useState(null);

  const [activeTab, setActiveTab] = useState("requirements");
  const [isSaving, setIsSaving] = useState(false);
  const [exportingFormat, setExportingFormat] = useState(null);
  const [banner, setBanner] = useState(null);

  const dirty = isSessionDirty(savedSession, draftSession);

  const loadSessionsList = useCallback(async () => {
    setIsLoadingSessions(true);
    try {
      const list = await listSessions();
      setSessions(Array.isArray(list) ? list : []);
    } catch {
      // Çevrimdışı durumda mevcut liste korunur
    } finally {
      setIsLoadingSessions(false);
    }
  }, []);

  const refreshHealthAndSessions = useCallback(async () => {
    setHealth((prev) => ({ ...prev, status: "checking" }));
    const [healthRes, sessionsRes] = await Promise.allSettled([
      checkHealth(),
      listSessions(),
    ]);

    if (healthRes.status === "fulfilled") {
      const data = healthRes.value;
      setHealth({
        status: data.status === "ok" ? "online" : "offline",
        demoMode: Boolean(data.demo_mode),
        version: data.version || "0.1.0",
      });
    } else {
      setHealth({ status: "offline", demoMode: false, version: "0.1.0" });
    }

    if (sessionsRes.status === "fulfilled") {
      setSessions(Array.isArray(sessionsRes.value) ? sessionsRes.value : []);
    }
  }, []);

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      await refreshHealthAndSessions();

      const storedSessionId = window.sessionStorage.getItem(
        ACTIVE_SESSION_STORAGE_KEY
      );
      if (!storedSessionId || !active) {
        return;
      }

      setIsRestoring(true);
      try {
        const restored = await getSession(storedSessionId);
        if (active && restored) {
          setSavedSession(hydrateSessionForEditor(restored));
          setDraftSession(hydrateSessionForEditor(restored));
        }
      } catch {
        window.sessionStorage.removeItem(ACTIVE_SESSION_STORAGE_KEY);
      } finally {
        if (active) {
          setIsRestoring(false);
        }
      }
    }

    bootstrap();
    return () => {
      active = false;
    };
  }, [refreshHealthAndSessions]);

  useEffect(() => {
    if (!dirty) return undefined;

    function handleBeforeUnload(event) {
      event.preventDefault();
      event.returnValue = "";
    }

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [dirty]);

  function upsertSessionInList(detail) {
    const summaryItem = toSessionSummary(detail);
    setSessions((prev) => [
      summaryItem,
      ...prev.filter((item) => item.id !== summaryItem.id),
    ]);
  }

  async function handleAnalyze(overrideDemo = false) {
    setBanner(null);
    const trimmed = formRawInput.trim();
    if (trimmed.length < MIN_INPUT_LENGTH) {
      setAnalyzeError(
        `Gereksinim metni en az ${MIN_INPUT_LENGTH} karakter olmalıdır.`
      );
      return;
    }

    const shouldUseDemo = Boolean(overrideDemo || useDemoMode || health.demoMode);
    if (overrideDemo) {
      setUseDemoMode(true);
    }

    setAnalyzeError(null);
    setIsAnalyzing(true);
    try {
      const created = await analyzeRequirements({
        title: formTitle,
        rawInput: trimmed,
        useDemo: shouldUseDemo,
      });
      setSavedSession(hydrateSessionForEditor(created));
      setDraftSession(hydrateSessionForEditor(created));
      upsertSessionInList(created);
      window.sessionStorage.setItem(
        ACTIVE_SESSION_STORAGE_KEY,
        String(created.id)
      );
      setHealth((prev) =>
        prev.status === "offline" ? { ...prev, status: "online" } : prev
      );
      setActiveTab("requirements");
      setBanner({
        type: "success",
        message: `"${created.title}" için gereksinim analizi tamamlandı ve veritabanına kaydedildi.`,
      });
    } catch (err) {
      setAnalyzeError(
        err.message || "Analiz sırasında beklenmeyen bir hata oluştu."
      );
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function persistDraft() {
    const validation = validateSessionDraft(draftSession);
    if (!validation.valid) {
      setActiveTab(validation.tab);
      setBanner({ type: "error", message: validation.message });
      return null;
    }

    setIsSaving(true);
    try {
      const payload = serializeSessionForUpdate(draftSession);
      const updated = await updateSession(draftSession.id, payload);
      setSavedSession(hydrateSessionForEditor(updated));
      setDraftSession(hydrateSessionForEditor(updated));
      upsertSessionInList(updated);
      return updated;
    } catch (err) {
      setBanner({
        type: "error",
        message: err.message || "Değişiklikler kaydedilemedi.",
      });
      return null;
    } finally {
      setIsSaving(false);
    }
  }

  async function handleSave() {
    setBanner(null);
    const updated = await persistDraft();
    if (updated) {
      setBanner({
        type: "success",
        message: "Değişiklikler veritabanına kalıcı olarak kaydedildi.",
      });
    }
  }

  function handleRevert() {
    if (!savedSession) return;
    setDraftSession(hydrateSessionForEditor(savedSession));
    setBanner({
      type: "info",
      message: "Kaydedilmemiş düzenlemeler geri alındı.",
    });
  }

  async function handleExport(format) {
    if (!draftSession) return;
    setBanner(null);

    let targetId = draftSession.id;
    if (dirty) {
      const updated = await persistDraft();
      if (!updated) {
        return;
      }
      targetId = updated.id;
    }

    setExportingFormat(format);
    try {
      const filename = await exportSessionFile(targetId, format);
      setBanner({
        type: "success",
        message: `Dışa aktarma tamamlandı: ${filename}`,
      });
    } catch (err) {
      setBanner({
        type: "error",
        message: err.message || "Dışa aktarma sırasında bir hata oluştu.",
      });
    } finally {
      setExportingFormat(null);
    }
  }

  async function handleSelectSession(sessionId) {
    if (draftSession?.id === sessionId) {
      setIsHistoryOpen(false);
      return;
    }

    if (
      dirty &&
      !window.confirm(
        "Kaydedilmemiş değişiklikleriniz var. Başka bir oturuma geçmek istiyor musunuz?"
      )
    ) {
      return;
    }

    setBanner(null);
    setLoadingSessionId(sessionId);
    try {
      const detail = await getSession(sessionId);
      setSavedSession(hydrateSessionForEditor(detail));
      setDraftSession(hydrateSessionForEditor(detail));
      upsertSessionInList(detail);
      window.sessionStorage.setItem(
        ACTIVE_SESSION_STORAGE_KEY,
        String(detail.id)
      );
      setActiveTab("requirements");
      setIsHistoryOpen(false);
      setBanner({
        type: "info",
        message: `#${detail.id} "${detail.title}" oturumu yüklendi.`,
      });
    } catch (err) {
      if (err.status === 404) {
        setSessions((prev) => prev.filter((item) => item.id !== sessionId));
      }
      setBanner({
        type: "error",
        message: err.message || "Oturum yüklenemedi.",
      });
    } finally {
      setLoadingSessionId(null);
    }
  }

  async function handleDeleteSession(sessionId) {
    setBanner(null);
    setDeletingSessionId(sessionId);
    try {
      await deleteSession(sessionId);
      setSessions((prev) => prev.filter((item) => item.id !== sessionId));
      if (draftSession?.id === sessionId) {
        setSavedSession(null);
        setDraftSession(null);
        window.sessionStorage.removeItem(ACTIVE_SESSION_STORAGE_KEY);
      }
      setBanner({
        type: "success",
        message: `#${sessionId} numaralı analiz oturumu kalıcı olarak silindi.`,
      });
    } catch (err) {
      if (err.status === 404) {
        setSessions((prev) => prev.filter((item) => item.id !== sessionId));
        if (draftSession?.id === sessionId) {
          setSavedSession(null);
          setDraftSession(null);
          window.sessionStorage.removeItem(ACTIVE_SESSION_STORAGE_KEY);
        }
      }
      setBanner({
        type: "error",
        message: err.message || "Oturum silinemedi.",
      });
    } finally {
      setDeletingSessionId(null);
    }
  }

  function handleOpenHistory() {
    setIsHistoryOpen(true);
    loadSessionsList();
  }

  function resetToForm(nextTitle = "", nextRawInput = "") {
    if (
      dirty &&
      !window.confirm(
        "Kaydedilmemiş değişiklikleriniz var. Yeni analiz ekranına geçmek istiyor musunuz?"
      )
    ) {
      return;
    }
    setSavedSession(null);
    setDraftSession(null);
    setAnalyzeError(null);
    setBanner(null);
    setFormTitle(nextTitle);
    setFormRawInput(nextRawInput);
    window.sessionStorage.removeItem(ACTIVE_SESSION_STORAGE_KEY);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleRequirementsChange(nextRequirements) {
    setDraftSession((prev) => {
      if (!prev) return prev;
      const prevRequirements = prev.requirements || [];
      const prevByKey = new Map(
        prevRequirements.map((req) => [req._clientKey, req.code])
      );
      const nextKeys = new Set(nextRequirements.map((req) => req._clientKey));
      const remainingCodes = new Set(
        nextRequirements.map((req) => req.code).filter(Boolean)
      );

      const renamedCodes = new Map();
      for (const req of nextRequirements) {
        const oldCode = prevByKey.get(req._clientKey);
        if (
          oldCode &&
          req.code.trim() &&
          oldCode !== req.code &&
          !remainingCodes.has(oldCode)
        ) {
          renamedCodes.set(oldCode, req.code);
        }
      }

      const deletedCodes = new Set();
      for (const req of prevRequirements) {
        if (!nextKeys.has(req._clientKey) && req.code && !remainingCodes.has(req.code)) {
          deletedCodes.add(req.code);
        }
      }

      const nextStories = (prev.user_stories || []).map((story) => {
        const rel = story.related_requirement_code;
        if (!rel) return story;
        if (renamedCodes.has(rel)) {
          return { ...story, related_requirement_code: renamedCodes.get(rel) };
        }
        if (deletedCodes.has(rel)) {
          return { ...story, related_requirement_code: "" };
        }
        return story;
      });

      return {
        ...prev,
        requirements: nextRequirements,
        user_stories: nextStories,
      };
    });
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Header
        health={health}
        hasActiveSession={Boolean(draftSession)}
        sessionCount={sessions.length}
        onNewAnalysis={() => resetToForm("", "")}
        onOpenHistory={handleOpenHistory}
        onRecheckHealth={refreshHealthAndSessions}
      />

      <main className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 sm:py-8">
        {banner && (
          <div
            role="status"
            className={`flex items-center justify-between gap-3 rounded-xl border px-4 py-3 text-sm ${
              banner.type === "error"
                ? "border-rose-200 bg-rose-50 text-rose-800"
                : banner.type === "info"
                  ? "border-sky-200 bg-sky-50 text-sky-900"
                  : "border-emerald-200 bg-emerald-50 text-emerald-800"
            }`}
          >
            <div className="flex items-center gap-2.5">
              {banner.type === "error" ? (
                <AlertCircle className="h-4 w-4 shrink-0" />
              ) : (
                <CheckCircle2 className="h-4 w-4 shrink-0" />
              )}
              <span className="font-medium">{banner.message}</span>
            </div>
            <button
              type="button"
              aria-label="Bildirimi Kapat"
              onClick={() => setBanner(null)}
              className="cursor-pointer rounded-md p-1 opacity-70 transition hover:bg-black/5 hover:opacity-100"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {isRestoring ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center text-sm text-slate-500 shadow-sm">
            Aktif analiz oturumu yükleniyor...
          </div>
        ) : !draftSession ? (
          <>
            <RequirementForm
              title={formTitle}
              rawInput={formRawInput}
              useDemo={useDemoMode}
              backendDemoMode={health.demoMode}
              onTitleChange={setFormTitle}
              onRawInputChange={(value) => {
                setFormRawInput(value);
                if (analyzeError) setAnalyzeError(null);
              }}
              onUseDemoChange={setUseDemoMode}
              onSelectScenario={(scenario) => {
                setFormTitle(scenario.title);
                setFormRawInput(scenario.rawInput);
                setAnalyzeError(null);
              }}
              onClear={() => {
                setFormTitle("");
                setFormRawInput("");
                setAnalyzeError(null);
              }}
              onSubmit={() => handleAnalyze(false)}
              isAnalyzing={isAnalyzing}
              error={analyzeError}
              onRetry={() => handleAnalyze(false)}
              onRetryWithDemo={() => handleAnalyze(true)}
            />

            <RecentSessionsCard
              sessions={sessions}
              loadingSessionId={loadingSessionId}
              onSelectSession={handleSelectSession}
              onOpenHistory={handleOpenHistory}
            />
          </>
        ) : (
          <div className="space-y-6">
            <ExportToolbar
              session={draftSession}
              isDirty={dirty}
              isSaving={isSaving}
              exportingFormat={exportingFormat}
              onSave={handleSave}
              onRevert={handleRevert}
              onExport={handleExport}
            />

            <MetricsSummary session={draftSession} />

            <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
              <div className="flex flex-wrap gap-1 border-b border-slate-200 px-4 pt-3 sm:px-6">
                {TABS.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  const countBadge =
                    tab.id === "requirements"
                      ? draftSession.requirements.length
                      : tab.id === "stories"
                        ? draftSession.user_stories.length
                        : null;

                  return (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => setActiveTab(tab.id)}
                      className={`inline-flex cursor-pointer items-center gap-2 border-b-2 px-3 py-3 text-xs font-semibold transition sm:text-sm ${
                        isActive
                          ? "border-indigo-600 text-indigo-700"
                          : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-800"
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      <span>{tab.label}</span>
                      {countBadge !== null && (
                        <span
                          className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${
                            isActive
                              ? "bg-indigo-100 text-indigo-700"
                              : "bg-slate-100 text-slate-600"
                          }`}
                        >
                          {countBadge}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>

              <div className="p-4 sm:p-6">
                {activeTab === "requirements" && (
                  <RequirementsTab
                    requirements={draftSession.requirements}
                    onChange={handleRequirementsChange}
                  />
                )}

                {activeTab === "stories" && (
                  <UserStoriesTab
                    userStories={draftSession.user_stories}
                    requirements={draftSession.requirements}
                    onChange={(nextStories) =>
                      setDraftSession((prev) => ({
                        ...prev,
                        user_stories: nextStories,
                      }))
                    }
                  />
                )}

                {activeTab === "overview" && (
                  <OverviewTab
                    session={draftSession}
                    onTitleChange={(nextTitle) =>
                      setDraftSession((prev) => ({
                        ...prev,
                        title: nextTitle,
                      }))
                    }
                    onSummaryChange={(nextSummary) =>
                      setDraftSession((prev) => ({
                        ...prev,
                        summary: nextSummary,
                      }))
                    }
                    onReuseRawInput={(title, rawInput) =>
                      resetToForm(title, rawInput)
                    }
                  />
                )}
              </div>
            </section>
          </div>
        )}
      </main>

      <SessionHistoryDrawer
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        sessions={sessions}
        activeSessionId={draftSession?.id || null}
        isLoadingList={isLoadingSessions}
        loadingSessionId={loadingSessionId}
        deletingSessionId={deletingSessionId}
        onRefresh={loadSessionsList}
        onSelectSession={handleSelectSession}
        onDeleteSession={handleDeleteSession}
      />
    </div>
  );
}
