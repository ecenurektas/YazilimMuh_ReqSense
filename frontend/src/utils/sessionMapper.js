let keySequence = 0;

export function createClientKey(prefix = "item") {
  keySequence += 1;
  return `${prefix}-${Date.now()}-${keySequence}`;
}

function cleanOptional(value) {
  if (value === null || value === undefined) return null;
  const trimmed = String(value).trim();
  return trimmed ? trimmed : null;
}

export function hydrateSessionForEditor(apiSession) {
  if (!apiSession) return null;

  return {
    ...apiSession,
    summary: apiSession.summary ?? "",
    requirements: (apiSession.requirements || []).map((req) => ({
      ...req,
      category: req.category ?? "",
      ambiguity_warning: req.ambiguity_warning ?? "",
      _clientKey: createClientKey("req"),
    })),
    user_stories: (apiSession.user_stories || []).map((story) => ({
      ...story,
      related_requirement_code: story.related_requirement_code ?? "",
      acceptance_criteria: (story.acceptance_criteria || []).map((ac) => ({
        ...ac,
        _clientKey: createClientKey("ac"),
      })),
      _clientKey: createClientKey("us"),
    })),
  };
}

export function serializeSessionForUpdate(editorSession) {
  if (!editorSession) return null;

  return {
    title: (editorSession.title || "").trim(),
    summary: cleanOptional(editorSession.summary),
    requirements: (editorSession.requirements || []).map((req) => ({
      ...(req.id ? { id: req.id } : {}),
      code: (req.code || "").trim(),
      req_type: req.req_type,
      category: cleanOptional(req.category),
      title: (req.title || "").trim(),
      description: (req.description || "").trim(),
      moscow_priority: req.moscow_priority,
      ambiguity_warning: cleanOptional(req.ambiguity_warning),
    })),
    user_stories: (editorSession.user_stories || []).map((story) => ({
      ...(story.id ? { id: story.id } : {}),
      code: (story.code || "").trim(),
      related_requirement_code: cleanOptional(story.related_requirement_code),
      role: (story.role || "").trim(),
      goal: (story.goal || "").trim(),
      benefit: (story.benefit || "").trim(),
      acceptance_criteria: (story.acceptance_criteria || []).map((ac) => ({
        ...(ac.id ? { id: ac.id } : {}),
        code: (ac.code || "").trim(),
        given_clause: (ac.given_clause || "").trim(),
        when_clause: (ac.when_clause || "").trim(),
        then_clause: (ac.then_clause || "").trim(),
      })),
    })),
  };
}

export function isSessionDirty(savedSession, draftSession) {
  if (!savedSession || !draftSession) return false;
  return (
    JSON.stringify(serializeSessionForUpdate(savedSession)) !==
    JSON.stringify(serializeSessionForUpdate(draftSession))
  );
}

export function validateSessionDraft(editorSession) {
  if (!editorSession) {
    return { valid: false, tab: "overview", message: "Aktif oturum bulunamadı." };
  }

  const title = (editorSession.title || "").trim();
  if (!title) {
    return {
      valid: false,
      tab: "overview",
      message: "Proje başlığı boş bırakılamaz.",
    };
  }
  if (title.length > 255) {
    return {
      valid: false,
      tab: "overview",
      message: "Proje başlığı en fazla 255 karakter olabilir.",
    };
  }

  for (let idx = 0; idx < (editorSession.requirements || []).length; idx += 1) {
    const req = editorSession.requirements[idx];
    const rowLabel = req.code?.trim() || `#${idx + 1}`;
    if (!req.code?.trim() || !req.title?.trim() || !req.description?.trim()) {
      return {
        valid: false,
        tab: "requirements",
        message: `Gereksinim (${rowLabel}) için kod, başlık ve açıklama alanları zorunludur.`,
      };
    }
  }

  for (let sIdx = 0; sIdx < (editorSession.user_stories || []).length; sIdx += 1) {
    const story = editorSession.user_stories[sIdx];
    const storyLabel = story.code?.trim() || `#${sIdx + 1}`;
    if (
      !story.code?.trim() ||
      !story.role?.trim() ||
      !story.goal?.trim() ||
      !story.benefit?.trim()
    ) {
      return {
        valid: false,
        tab: "stories",
        message: `Kullanıcı hikâyesi (${storyLabel}) için kod, rol, hedef ve fayda alanları zorunludur.`,
      };
    }

    for (let aIdx = 0; aIdx < (story.acceptance_criteria || []).length; aIdx += 1) {
      const ac = story.acceptance_criteria[aIdx];
      const acLabel = ac.code?.trim() || `#${aIdx + 1}`;
      if (
        !ac.code?.trim() ||
        !ac.given_clause?.trim() ||
        !ac.when_clause?.trim() ||
        !ac.then_clause?.trim()
      ) {
        return {
          valid: false,
          tab: "stories",
          message: `${storyLabel} içindeki ${acLabel} kabul kriteri için kod ve Given/When/Then alanları zorunludur.`,
        };
      }
    }
  }

  return { valid: true };
}

function nextNumericSuffix(codes, prefix) {
  const regex = new RegExp(`^${prefix}-(\\d+)$`, "i");
  let maxNum = 0;
  for (const code of codes) {
    const match = regex.exec((code || "").trim());
    if (match) {
      maxNum = Math.max(maxNum, Number.parseInt(match[1], 10));
    }
  }
  return maxNum + 1;
}

export function nextRequirementCode(requirements, reqType) {
  const prefix = reqType === "non_functional" ? "NFR" : "FR";
  const nextNum = nextNumericSuffix(
    (requirements || []).map((r) => r.code),
    prefix
  );
  return `${prefix}-${String(nextNum).padStart(2, "0")}`;
}

export function nextStoryCode(userStories) {
  const nextNum = nextNumericSuffix(
    (userStories || []).map((s) => s.code),
    "US"
  );
  return `US-${String(nextNum).padStart(2, "0")}`;
}

export function nextCriterionCode(storyCode, criteria) {
  const usMatch = /^US-(\d+)$/i.exec((storyCode || "").trim());
  const storyPart = usMatch ? usMatch[1].padStart(2, "0") : "01";
  const prefix = `AC-${storyPart}`;
  const regex = new RegExp(`^AC-${storyPart}\\.(\\d+)$`, "i");
  let maxNum = 0;
  for (const ac of criteria || []) {
    const match = regex.exec((ac.code || "").trim());
    if (match) {
      maxNum = Math.max(maxNum, Number.parseInt(match[1], 10));
    }
  }
  return `${prefix}.${maxNum + 1}`;
}
