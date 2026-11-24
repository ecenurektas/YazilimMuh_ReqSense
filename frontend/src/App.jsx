import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Download,
  FileText,
  Sparkles,
} from "lucide-react";

const WORKFLOW_STEPS = [
  {
    title: "1. Doğal Dil Girdisi",
    description:
      "Mülakat notları, proje fikri veya müşteri talebini serbest metin olarak girin.",
    icon: FileText,
  },
  {
    title: "2. Yapay Zekâ Analizi",
    description:
      "Gemini Structured Output ile FR/NFR, belirsizlik uyarıları, MoSCoW ve User Story üretin.",
    icon: Sparkles,
  },
  {
    title: "3. Düzenleme & Dışa Aktarma",
    description:
      "Üretilen maddeleri satır içi düzenleyin ve Markdown, CSV veya JSON olarak indirin.",
    icon: Download,
  },
];

export default function App() {
  const [health, setHealth] = useState({ status: "checking", demoMode: false });

  useEffect(() => {
    let active = true;

    async function checkBackend() {
      try {
        const res = await fetch("/api/health");
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const data = await res.json();
        if (active) {
          setHealth({
            status: data.status === "ok" ? "online" : "offline",
            demoMode: Boolean(data.demo_mode),
            version: data.version || "0.1.0",
          });
        }
      } catch {
        if (active) {
          setHealth({ status: "offline", demoMode: false });
        }
      }
    }

    checkBackend();
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-sm">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-slate-900">
                ReqSense
              </h1>
              <p className="text-xs text-slate-500">
                Yapay Zekâ Destekli Yazılım Gereksinim Analizi Sistemi
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {health.status === "checking" && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                <Activity className="h-3.5 w-3.5 animate-pulse" />
                API kontrol ediliyor...
              </span>
            )}
            {health.status === "online" && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Backend Bağlı {health.demoMode ? "(Demo Modu)" : ""}
              </span>
            )}
            {health.status === "offline" && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-800 ring-1 ring-amber-200">
                <AlertTriangle className="h-3.5 w-3.5" />
                Backend Çevrimdışı (Port 8000)
              </span>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-10">
        <section className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <div className="max-w-2xl">
            <span className="inline-flex items-center rounded-md bg-indigo-50 px-2.5 py-1 text-xs font-semibold text-indigo-700">
              Aşama 1 İskeleti Hazır
            </span>
            <h2 className="mt-3 text-2xl font-bold tracking-tight text-slate-900">
              Doğal Dil Girdisinden Yapılandırılmış Gereksinimlere
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">
              ReqSense ön yüz iskeleti kuruldu. Sonraki geliştirme adımlarında
              gereksinim giriş formu, sekmeli analiz sonuç tablosu, satır içi
              düzenleme ve Markdown/CSV/JSON dışa aktarma modülleri bu ekrana
              eklenecektir.
            </p>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {WORKFLOW_STEPS.map((step) => {
              const Icon = step.icon;
              return (
                <div
                  key={step.title}
                  className="rounded-xl border border-slate-200 bg-slate-50/70 p-5"
                >
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white text-indigo-600 shadow-xs ring-1 ring-slate-200">
                    <Icon className="h-4 w-4" />
                  </div>
                  <h3 className="mt-4 text-sm font-semibold text-slate-900">
                    {step.title}
                  </h3>
                  <p className="mt-1.5 text-xs leading-relaxed text-slate-600">
                    {step.description}
                  </p>
                </div>
              );
            })}
          </div>
        </section>
      </main>
    </div>
  );
}
