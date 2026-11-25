import {
  AlertCircle,
  Eraser,
  FileText,
  Loader2,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import {
  MAX_TITLE_LENGTH,
  MIN_INPUT_LENGTH,
  SAMPLE_SCENARIOS,
} from "../constants/reqsenseData";

export default function RequirementForm({
  title,
  rawInput,
  useDemo,
  backendDemoMode,
  onTitleChange,
  onRawInputChange,
  onUseDemoChange,
  onSelectScenario,
  onClear,
  onSubmit,
  isAnalyzing,
  error,
  onRetry,
  onRetryWithDemo,
}) {
  const trimmedLength = rawInput.trim().length;
  const isLengthValid = trimmedLength >= MIN_INPUT_LENGTH;
  const effectiveDemo = Boolean(backendDemoMode || useDemo);

  function handleFormSubmit(event) {
    event.preventDefault();
    onSubmit();
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
      <div className="flex flex-col justify-between gap-4 border-b border-slate-100 pb-5 sm:flex-row sm:items-end">
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-md bg-indigo-50 px-2.5 py-1 text-xs font-semibold text-indigo-700">
            <FileText className="h-3.5 w-3.5" />
            Doğal Dil Gereksinim Analizi
          </span>
          <h2 className="mt-2.5 text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">
            Proje Fikrinizi veya Mülakat Notlarını Analiz Edin
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Serbest metin girdinizden otomatik olarak FR/NFR gereksinimleri,
            belirsizlik uyarıları, MoSCoW öncelikleri ve Given-When-Then
            kriterleri üretilir.
          </p>
        </div>
      </div>

      <div className="mt-5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Örnek Senaryolar:
          </span>
          {SAMPLE_SCENARIOS.map((scenario) => (
            <button
              key={scenario.id}
              type="button"
              disabled={isAnalyzing}
              onClick={() => onSelectScenario(scenario)}
              className="cursor-pointer rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {scenario.label}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleFormSubmit} className="mt-5 space-y-5">
        <div>
          <div className="flex items-center justify-between">
            <label
              htmlFor="reqsense-title"
              className="block text-sm font-semibold text-slate-800"
            >
              Proje Başlığı{" "}
              <span className="font-normal text-slate-400">(Opsiyonel)</span>
            </label>
            <span className="text-xs text-slate-400">
              {title.length}/{MAX_TITLE_LENGTH}
            </span>
          </div>
          <input
            id="reqsense-title"
            type="text"
            maxLength={MAX_TITLE_LENGTH}
            value={title}
            disabled={isAnalyzing}
            onChange={(e) => onTitleChange(e.target.value)}
            placeholder="Boş bırakırsanız yapay zekâ metinden otomatik başlık türetir"
            className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:bg-slate-50"
          />
        </div>

        <div>
          <div className="flex items-center justify-between">
            <label
              htmlFor="reqsense-raw-input"
              className="block text-sm font-semibold text-slate-800"
            >
              Gereksinim / Mülakat Metni{" "}
              <span className="text-rose-500">*</span>
            </label>
            <span
              className={`text-xs font-medium ${
                isLengthValid ? "text-emerald-600" : "text-slate-500"
              }`}
            >
              {trimmedLength} / en az {MIN_INPUT_LENGTH} karakter
            </span>
          </div>
          <textarea
            id="reqsense-raw-input"
            rows={7}
            value={rawInput}
            disabled={isAnalyzing}
            onChange={(e) => onRawInputChange(e.target.value)}
            placeholder="Örn: Öğrenciler staj başvurularını çevrimiçi doldurabilmeli, danışmanlar onaylayabilmelidir. Sistem çok hızlı çalışmalı ve arayüz kullanıcı dostu olmalıdır..."
            className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3.5 py-3 text-sm leading-relaxed text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:bg-slate-50"
          />
          {!isLengthValid && rawInput.length > 0 && (
            <p className="mt-1.5 text-xs text-amber-700">
              Analiz başlatmak için en az {MIN_INPUT_LENGTH - trimmedLength}{" "}
              karakter daha girin.
            </p>
          )}
        </div>

        <label className="flex cursor-pointer items-center gap-2.5 rounded-xl border border-slate-200 bg-slate-50/70 px-3.5 py-2.5 text-xs text-slate-700">
          <input
            type="checkbox"
            checked={effectiveDemo}
            disabled={isAnalyzing || backendDemoMode}
            onChange={(e) => onUseDemoChange(e.target.checked)}
            className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
          />
          <span>
            <strong className="font-semibold text-slate-800">
              Çevrimdışı Demo Modunda Analiz Et
            </strong>{" "}
            {backendDemoMode
              ? "(Sunucu genel DEMO_MODE=true ile çalışıyor)"
              : "(API anahtarı veya internet bağlantısı olmadan yerel örnek analiz üretir)"}
          </span>
        </label>

        {error && (
          <div
            role="alert"
            className="flex flex-col justify-between gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 sm:flex-row sm:items-center"
          >
            <div className="flex items-start gap-2.5">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600" />
              <div>
                <p className="font-semibold">Analiz tamamlanamadı</p>
                <p className="mt-0.5 text-xs text-rose-700">{error}</p>
              </div>
            </div>
            <div className="flex shrink-0 flex-wrap items-center gap-2">
              {onRetryWithDemo && !effectiveDemo && (
                <button
                  type="button"
                  onClick={onRetryWithDemo}
                  disabled={isAnalyzing}
                  className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-amber-300 bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-900 transition hover:bg-amber-100"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  Demo Moduyla Çalıştır
                </button>
              )}
              {onRetry && (
                <button
                  type="button"
                  onClick={onRetry}
                  disabled={isAnalyzing}
                  className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-rose-300 bg-white px-3 py-1.5 text-xs font-semibold text-rose-700 transition hover:bg-rose-100"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  Yeniden Dene
                </button>
              )}
            </div>
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
          <button
            type="button"
            disabled={isAnalyzing || (!title && !rawInput)}
            onClick={onClear}
            className="inline-flex cursor-pointer items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Eraser className="h-4 w-4" />
            Temizle
          </button>

          <button
            type="submit"
            disabled={isAnalyzing}
            className="inline-flex cursor-pointer items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 disabled:cursor-not-allowed disabled:bg-indigo-400"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Gereksinimler Analiz Ediliyor...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Analiz Et
              </>
            )}
          </button>
        </div>
      </form>
    </section>
  );
}
