import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Filter,
  Plus,
  Trash2,
} from "lucide-react";
import {
  MOSCOW_MAP,
  MOSCOW_OPTIONS,
  REQ_TYPE_OPTIONS,
} from "../constants/reqsenseData";
import {
  createClientKey,
  nextRequirementCode,
} from "../utils/sessionMapper";

export default function RequirementsTab({ requirements, onChange }) {
  const [typeFilter, setTypeFilter] = useState("all");
  const [moscowFilter, setMoscowFilter] = useState("all");

  const filteredRequirements = requirements.filter((req) => {
    if (typeFilter === "functional" && req.req_type !== "functional") {
      return false;
    }
    if (typeFilter === "non_functional" && req.req_type !== "non_functional") {
      return false;
    }
    if (
      typeFilter === "ambiguous" &&
      !(req.ambiguity_warning && req.ambiguity_warning.trim())
    ) {
      return false;
    }
    if (moscowFilter !== "all" && req.moscow_priority !== moscowFilter) {
      return false;
    }
    return true;
  });

  function handleUpdateField(clientKey, field, value) {
    onChange(
      requirements.map((item) =>
        item._clientKey === clientKey ? { ...item, [field]: value } : item
      )
    );
  }

  function handleAddRequirement(reqType = "functional") {
    const newItem = {
      code: nextRequirementCode(requirements, reqType),
      req_type: reqType,
      category: reqType === "non_functional" ? "Kalite" : "Genel",
      title: "Yeni Gereksinim",
      description: "Gereksinim açıklamasını buraya girin.",
      moscow_priority: "Should",
      ambiguity_warning: "",
      _clientKey: createClientKey("req"),
    };
    onChange([...requirements, newItem]);
    setTypeFilter("all");
    setMoscowFilter("all");
  }

  function handleDeleteRequirement(clientKey) {
    onChange(requirements.filter((item) => item._clientKey !== clientKey));
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50/70 p-3.5 sm:flex-row sm:items-center">
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-slate-600">
            <Filter className="h-3.5 w-3.5" />
            Filtrele:
          </span>

          {[
            { value: "all", label: `Tümü (${requirements.length})` },
            {
              value: "functional",
              label: `FR (${
                requirements.filter((r) => r.req_type === "functional").length
              })`,
            },
            {
              value: "non_functional",
              label: `NFR (${
                requirements.filter((r) => r.req_type === "non_functional")
                  .length
              })`,
            },
            {
              value: "ambiguous",
              label: `Belirsiz (${
                requirements.filter((r) => Boolean(r.ambiguity_warning?.trim()))
                  .length
              })`,
            },
          ].map((btn) => (
            <button
              key={btn.value}
              type="button"
              onClick={() => setTypeFilter(btn.value)}
              className={`cursor-pointer rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
                typeFilter === btn.value
                  ? "bg-indigo-600 text-white shadow-2xs"
                  : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-100"
              }`}
            >
              {btn.label}
            </button>
          ))}

          <select
            aria-label="MoSCoW Filtresi"
            value={moscowFilter}
            onChange={(e) => setMoscowFilter(e.target.value)}
            className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 focus:border-indigo-500 focus:outline-none"
          >
            <option value="all">Tüm MoSCoW</option>
            {MOSCOW_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <button
          type="button"
          onClick={() =>
            handleAddRequirement(
              typeFilter === "non_functional" ? "non_functional" : "functional"
            )
          }
          className="inline-flex cursor-pointer items-center justify-center gap-1.5 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-slate-800"
        >
          <Plus className="h-3.5 w-3.5" />
          Yeni Gereksinim Ekle
        </button>
      </div>

      {filteredRequirements.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center">
          <p className="text-sm font-medium text-slate-600">
            Seçili filtrelere uyan gereksinim bulunamadı.
          </p>
          <button
            type="button"
            onClick={() => {
              setTypeFilter("all");
              setMoscowFilter("all");
            }}
            className="mt-2 cursor-pointer text-xs font-semibold text-indigo-600 hover:underline"
          >
            Filtreleri Sıfırla
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredRequirements.map((req) => {
            const moscowMeta = MOSCOW_MAP[req.moscow_priority] || MOSCOW_OPTIONS[0];
            const hasWarning = Boolean(
              req.ambiguity_warning && req.ambiguity_warning.trim()
            );

            return (
              <article
                key={req._clientKey}
                className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs transition hover:border-slate-300"
              >
                <div className="flex flex-wrap items-center justify-between gap-2.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <input
                      type="text"
                      aria-label="Gereksinim Kodu"
                      value={req.code}
                      onChange={(e) =>
                        handleUpdateField(req._clientKey, "code", e.target.value)
                      }
                      className="w-24 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-bold text-slate-800 focus:border-indigo-500 focus:bg-white focus:outline-none"
                    />

                    <select
                      aria-label="Gereksinim Türü"
                      value={req.req_type}
                      onChange={(e) =>
                        handleUpdateField(
                          req._clientKey,
                          "req_type",
                          e.target.value
                        )
                      }
                      className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 focus:border-indigo-500 focus:outline-none"
                    >
                      {REQ_TYPE_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>

                    <select
                      aria-label="MoSCoW Önceliği"
                      value={req.moscow_priority}
                      onChange={(e) =>
                        handleUpdateField(
                          req._clientKey,
                          "moscow_priority",
                          e.target.value
                        )
                      }
                      className={`rounded-lg border px-2.5 py-1 text-xs font-semibold focus:outline-none ${moscowMeta.selectClass}`}
                    >
                      {MOSCOW_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>

                    <input
                      type="text"
                      aria-label="Kategori"
                      value={req.category || ""}
                      placeholder="Kategori (ör. Güvenlik)"
                      onChange={(e) =>
                        handleUpdateField(
                          req._clientKey,
                          "category",
                          e.target.value
                        )
                      }
                      className="w-40 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-700 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none"
                    />
                  </div>

                  <button
                    type="button"
                    title="Gereksinimi Sil"
                    onClick={() => handleDeleteRequirement(req._clientKey)}
                    className="inline-flex cursor-pointer items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium text-slate-500 transition hover:bg-rose-50 hover:text-rose-700"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Sil
                  </button>
                </div>

                <div className="mt-3 space-y-2.5">
                  <input
                    type="text"
                    aria-label="Gereksinim Başlığı"
                    value={req.title}
                    placeholder="Gereksinim başlığı"
                    onChange={(e) =>
                      handleUpdateField(req._clientKey, "title", e.target.value)
                    }
                    className="w-full rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-semibold text-slate-900 focus:border-indigo-500 focus:outline-none"
                  />

                  <textarea
                    rows={2}
                    aria-label="Gereksinim Açıklaması"
                    value={req.description}
                    placeholder="Ölçülebilir gereksinim tanımı"
                    onChange={(e) =>
                      handleUpdateField(
                        req._clientKey,
                        "description",
                        e.target.value
                      )
                    }
                    className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm leading-relaxed text-slate-700 focus:border-indigo-500 focus:outline-none"
                  />
                </div>

                <div className="mt-3">
                  {hasWarning ? (
                    <div className="rounded-lg border border-amber-200 bg-amber-50/70 p-3">
                      <div className="flex items-center justify-between gap-2">
                        <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-amber-900">
                          <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />
                          Belirsizlik Uyarısı
                        </span>
                        <button
                          type="button"
                          onClick={() =>
                            handleUpdateField(
                              req._clientKey,
                              "ambiguity_warning",
                              ""
                            )
                          }
                          className="inline-flex cursor-pointer items-center gap-1 rounded-md bg-white px-2 py-0.5 text-[11px] font-semibold text-emerald-700 ring-1 ring-emerald-200 hover:bg-emerald-50"
                        >
                          <CheckCircle2 className="h-3 w-3" />
                          Çözüldü (Kaldır)
                        </button>
                      </div>
                      <textarea
                        rows={2}
                        aria-label="Belirsizlik Uyarısı"
                        value={req.ambiguity_warning || ""}
                        onChange={(e) =>
                          handleUpdateField(
                            req._clientKey,
                            "ambiguity_warning",
                            e.target.value
                          )
                        }
                        className="mt-2 w-full rounded-md border border-amber-200 bg-white px-2.5 py-1.5 text-xs leading-relaxed text-amber-950 focus:border-amber-400 focus:outline-none"
                      />
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() =>
                        handleUpdateField(
                          req._clientKey,
                          "ambiguity_warning",
                          "Ölçülebilir kabul sınırı eklenmelidir."
                        )
                      }
                      className="cursor-pointer text-xs font-medium text-slate-400 hover:text-amber-700"
                    >
                      + Belirsizlik notu ekle
                    </button>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
