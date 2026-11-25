import { Plus, Trash2 } from "lucide-react";
import {
  createClientKey,
  nextCriterionCode,
  nextStoryCode,
} from "../utils/sessionMapper";

export default function UserStoriesTab({
  userStories,
  requirements,
  onChange,
}) {
  const totalCriteria = userStories.reduce(
    (sum, s) => sum + (s.acceptance_criteria?.length || 0),
    0
  );

  function updateStory(storyKey, updater) {
    onChange(
      userStories.map((story) =>
        story._clientKey === storyKey ? updater(story) : story
      )
    );
  }

  function handleAddStory() {
    const storyCode = nextStoryCode(userStories);
    const defaultReqCode = requirements[0]?.code || "";
    const newStory = {
      code: storyCode,
      related_requirement_code: defaultReqCode,
      role: "Kullanıcı",
      goal: "hedeflenen işlemi tamamlayabilmek",
      benefit: "iş akışımı hızlı ve hatasız yürütebilirim",
      acceptance_criteria: [
        {
          code: nextCriterionCode(storyCode, []),
          given_clause: "Kullanıcı ilgili ekrandadır",
          when_clause: "İşlem tetiklendiğinde",
          then_clause: "Beklenen sonuç görüntülenir",
          _clientKey: createClientKey("ac"),
        },
      ],
      _clientKey: createClientKey("us"),
    };
    onChange([...userStories, newStory]);
  }

  function handleDeleteStory(storyKey) {
    onChange(userStories.filter((story) => story._clientKey !== storyKey));
  }

  function handleAddCriterion(storyKey) {
    updateStory(storyKey, (story) => ({
      ...story,
      acceptance_criteria: [
        ...(story.acceptance_criteria || []),
        {
          code: nextCriterionCode(story.code, story.acceptance_criteria),
          given_clause: "Ön koşul sağlanmıştır",
          when_clause: "Kullanıcı eylemi gerçekleştirdiğinde",
          then_clause: "Sistem beklenen çıktıyı üretir",
          _clientKey: createClientKey("ac"),
        },
      ],
    }));
  }

  function handleUpdateCriterion(storyKey, acKey, field, value) {
    updateStory(storyKey, (story) => ({
      ...story,
      acceptance_criteria: (story.acceptance_criteria || []).map((ac) =>
        ac._clientKey === acKey ? { ...ac, [field]: value } : ac
      ),
    }));
  }

  function handleDeleteCriterion(storyKey, acKey) {
    updateStory(storyKey, (story) => ({
      ...story,
      acceptance_criteria: (story.acceptance_criteria || []).filter(
        (ac) => ac._clientKey !== acKey
      ),
    }));
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50/70 p-3.5">
        <p className="text-xs font-medium text-slate-600">
          Toplam <strong className="text-slate-900">{userStories.length}</strong>{" "}
          kullanıcı hikâyesi ve{" "}
          <strong className="text-slate-900">{totalCriteria}</strong>{" "}
          Given-When-Then kabul kriteri
        </p>

        <button
          type="button"
          onClick={handleAddStory}
          className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-slate-800"
        >
          <Plus className="h-3.5 w-3.5" />
          Yeni Kullanıcı Hikâyesi Ekle
        </button>
      </div>

      {userStories.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center">
          <p className="text-sm text-slate-600">
            Henüz kullanıcı hikâyesi eklenmemiş.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {userStories.map((story) => (
            <article
              key={story._clientKey}
              className="rounded-xl border border-slate-200 bg-white p-5 shadow-2xs"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  <input
                    type="text"
                    aria-label="Hikâye Kodu"
                    value={story.code}
                    onChange={(e) =>
                      updateStory(story._clientKey, (s) => ({
                        ...s,
                        code: e.target.value,
                      }))
                    }
                    className="w-24 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-bold text-slate-800 focus:border-indigo-500 focus:bg-white focus:outline-none"
                  />

                  <select
                    aria-label="İlişkili Gereksinim"
                    value={story.related_requirement_code || ""}
                    onChange={(e) =>
                      updateStory(story._clientKey, (s) => ({
                        ...s,
                        related_requirement_code: e.target.value,
                      }))
                    }
                    className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="">İlişkili gereksinim seçilmedi</option>
                    {story.related_requirement_code &&
                      !requirements.some(
                        (req) => req.code === story.related_requirement_code
                      ) && (
                        <option value={story.related_requirement_code}>
                          {story.related_requirement_code} (Silinmiş/Eşleşmeyen)
                        </option>
                      )}
                    {requirements.map((req) => (
                      <option key={req._clientKey} value={req.code}>
                        {req.code} — {req.title}
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  type="button"
                  onClick={() => handleDeleteStory(story._clientKey)}
                  className="inline-flex cursor-pointer items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium text-slate-500 transition hover:bg-rose-50 hover:text-rose-700"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Hikâyeyi Sil
                </button>
              </div>

              <div className="mt-3 rounded-lg border border-indigo-100 bg-indigo-50/60 px-3.5 py-2.5 text-xs leading-relaxed text-indigo-950">
                <strong>Bir</strong> {story.role || "..."} <strong>olarak</strong>
                , {story.goal || "..."} <strong>istiyorum</strong>;{" "}
                <strong>böylece</strong> {story.benefit || "..."}.
              </div>

              <div className="mt-3 grid gap-3 md:grid-cols-3">
                <div>
                  <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                    Rol
                  </label>
                  <input
                    type="text"
                    value={story.role}
                    onChange={(e) =>
                      updateStory(story._clientKey, (s) => ({
                        ...s,
                        role: e.target.value,
                      }))
                    }
                    className="mt-1 w-full rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs text-slate-800 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                    Hedef
                  </label>
                  <input
                    type="text"
                    value={story.goal}
                    onChange={(e) =>
                      updateStory(story._clientKey, (s) => ({
                        ...s,
                        goal: e.target.value,
                      }))
                    }
                    className="mt-1 w-full rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs text-slate-800 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                    Fayda
                  </label>
                  <input
                    type="text"
                    value={story.benefit}
                    onChange={(e) =>
                      updateStory(story._clientKey, (s) => ({
                        ...s,
                        benefit: e.target.value,
                      }))
                    }
                    className="mt-1 w-full rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs text-slate-800 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="mt-4 border-t border-slate-100 pt-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wide text-slate-600">
                    Kabul Kriterleri (Given - When - Then)
                  </h4>
                  <button
                    type="button"
                    onClick={() => handleAddCriterion(story._clientKey)}
                    className="inline-flex cursor-pointer items-center gap-1 rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700"
                  >
                    <Plus className="h-3 w-3" />
                    Kabul Kriteri Ekle
                  </button>
                </div>

                <div className="mt-2.5 space-y-2.5">
                  {(story.acceptance_criteria || []).map((ac) => (
                    <div
                      key={ac._clientKey}
                      className="rounded-lg border border-slate-200 bg-slate-50/70 p-3"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <input
                          type="text"
                          aria-label="Kabul Kriteri Kodu"
                          value={ac.code}
                          onChange={(e) =>
                            handleUpdateCriterion(
                              story._clientKey,
                              ac._clientKey,
                              "code",
                              e.target.value
                            )
                          }
                          className="w-24 rounded-md border border-slate-200 bg-white px-2 py-1 text-xs font-bold text-slate-800 focus:border-indigo-500 focus:outline-none"
                        />
                        <button
                          type="button"
                          onClick={() =>
                            handleDeleteCriterion(story._clientKey, ac._clientKey)
                          }
                          className="inline-flex cursor-pointer items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium text-slate-500 hover:bg-rose-50 hover:text-rose-700"
                        >
                          <Trash2 className="h-3 w-3" />
                          Sil
                        </button>
                      </div>

                      <div className="mt-2 grid gap-2 md:grid-cols-3">
                        <div>
                          <span className="text-[11px] font-bold text-emerald-700">
                            Given (Ön Koşul)
                          </span>
                          <input
                            type="text"
                            value={ac.given_clause}
                            onChange={(e) =>
                              handleUpdateCriterion(
                                story._clientKey,
                                ac._clientKey,
                                "given_clause",
                                e.target.value
                              )
                            }
                            className="mt-1 w-full rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-800 focus:border-indigo-500 focus:outline-none"
                          />
                        </div>
                        <div>
                          <span className="text-[11px] font-bold text-sky-700">
                            When (Tetikleyici)
                          </span>
                          <input
                            type="text"
                            value={ac.when_clause}
                            onChange={(e) =>
                              handleUpdateCriterion(
                                story._clientKey,
                                ac._clientKey,
                                "when_clause",
                                e.target.value
                              )
                            }
                            className="mt-1 w-full rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-800 focus:border-indigo-500 focus:outline-none"
                          />
                        </div>
                        <div>
                          <span className="text-[11px] font-bold text-indigo-700">
                            Then (Beklenen Sonuç)
                          </span>
                          <input
                            type="text"
                            value={ac.then_clause}
                            onChange={(e) =>
                              handleUpdateCriterion(
                                story._clientKey,
                                ac._clientKey,
                                "then_clause",
                                e.target.value
                              )
                            }
                            className="mt-1 w-full rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-800 focus:border-indigo-500 focus:outline-none"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
