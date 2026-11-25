import { AlertTriangle, Layers, ListChecks, ShieldCheck } from "lucide-react";
import { MOSCOW_OPTIONS } from "../constants/reqsenseData";

export default function MetricsSummary({ session }) {
  const requirements = session?.requirements || [];
  const userStories = session?.user_stories || [];

  const frCount = requirements.filter((r) => r.req_type === "functional").length;
  const nfrCount = requirements.filter(
    (r) => r.req_type === "non_functional"
  ).length;
  const ambiguityCount = requirements.filter(
    (r) => Boolean(r.ambiguity_warning && r.ambiguity_warning.trim())
  ).length;
  const criteriaCount = userStories.reduce(
    (acc, story) => acc + (story.acceptance_criteria?.length || 0),
    0
  );

  const moscowCounts = MOSCOW_OPTIONS.map((opt) => ({
    ...opt,
    count: requirements.filter((r) => r.moscow_priority === opt.value).length,
  }));

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Toplam Gereksinim
          </span>
          <Layers className="h-4 w-4 text-indigo-600" />
        </div>
        <p className="mt-2 text-2xl font-bold text-slate-900">
          {requirements.length}
        </p>
        <p className="mt-1 text-xs text-slate-500">
          {frCount} Fonksiyonel (FR) · {nfrCount} NFR
        </p>
      </div>

      <div
        className={`rounded-xl border p-4 shadow-2xs ${
          ambiguityCount > 0
            ? "border-amber-200 bg-amber-50/60"
            : "border-slate-200 bg-white"
        }`}
      >
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-600">
            Belirsizlik Uyarısı
          </span>
          <AlertTriangle
            className={`h-4 w-4 ${
              ambiguityCount > 0 ? "text-amber-600" : "text-emerald-600"
            }`}
          />
        </div>
        <p className="mt-2 text-2xl font-bold text-slate-900">
          {ambiguityCount}
        </p>
        <p className="mt-1 text-xs text-slate-600">
          {ambiguityCount > 0
            ? "Netleştirme önerisi bulunan madde"
            : "Muğlak ifade uyarısı kalmadı"}
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Çevik Çıktılar
          </span>
          <ListChecks className="h-4 w-4 text-indigo-600" />
        </div>
        <p className="mt-2 text-2xl font-bold text-slate-900">
          {userStories.length}{" "}
          <span className="text-sm font-medium text-slate-500">Hikâye</span>
        </p>
        <p className="mt-1 text-xs text-slate-500">
          {criteriaCount} Given-When-Then kabul kriteri
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            MoSCoW Dağılımı
          </span>
          <ShieldCheck className="h-4 w-4 text-indigo-600" />
        </div>
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {moscowCounts.map((item) => (
            <span
              key={item.value}
              className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-semibold ring-1 ${item.badgeClass}`}
            >
              {item.shortLabel}: {item.count}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
