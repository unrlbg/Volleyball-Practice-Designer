(() => {
  "use strict";
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const SVG = "http://www.w3.org/2000/svg";
  const deep = value => JSON.parse(JSON.stringify(value));
  const uid = () => crypto.randomUUID();
  const clamp = (v, min, max) => Math.min(max, Math.max(min, v));
  const el = (name, attrs = {}, html = "") => {
    const n = document.createElementNS(SVG, name);
    Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, v));
    if (html) n.innerHTML = html;
    return n;
  };

  const roles = {
    "Generic Player": ["Standing", "Ready", "Moving", "Jumping"],
    Setter: ["Ready", "Front Set", "Back Set", "Jump Set", "One-Hand Set", "Setter Dump", "Defensive Position", "Transition"],
    Libero: ["Reception", "Defensive Ready", "Dig", "Dive", "Overhead Defense", "Emergency Set", "Cover", "Transition"],
    Middle: ["Ready", "Quick Attack Ready", "First-Tempo Approach", "Takeoff", "Front Quick Attack", "Behind Setter Quick", "One-Foot Slide Approach", "Slide Attack Contact", "Gap Attack", "Push Attack", "Landing", "Transition After Attack", "Block Ready", "Single Block", "Moving Block", "Transition"],
    Outside: ["Ready", "Reception", "Attack Start", "Approach Step 1", "Approach Step 2", "Takeoff", "Jump Attack", "High Contact", "Line Attack", "Cross-Court Attack", "Tip", "Roll Shot", "Back-Row Attack", "Landing", "Transition After Attack", "Block", "Defense", "Cover", "Transition"],
    Opposite: ["Attack Start", "Approach Step 1", "Approach Step 2", "Takeoff", "Jump Attack", "High Contact", "Line Attack", "Cross-Court Attack", "Tip", "Roll Shot", "Back-Row Attack", "Landing", "Transition After Attack"],
    Coach: ["Holding Ball", "Tossing Ball", "Giving Instructions", "Observing", "Standing", "Serving", "Attacking"]
  };
  const equipment = ["Single Ball", "Ball Group", "Ball Pile", "Ball Cart - Blue", "Ball Cart - Black", "Compact Ball Cart", "Folding Ball Cart", "Cone", "Flat Marker", "Target Mat", "Target Hoop", "Floor Target", "Wall Target", "Blocking Board", "Blocking Pad", "Blocking Dummy", "Training Box", "Bench", "Chair", "Agility Ladder", "Hurdle", "Scoreboard"];
  const drawingTools = ["Straight arrow", "Curved arrow", "Dashed arrow", "Double-ended arrow", "Free movement path", "Ball trajectory", "Set trajectory", "Attack trajectory", "Serve trajectory"];
  const shapeTools = ["Rectangle", "Circle", "Responsibility area", "Target circle", "Text label"];
  const teamColors = { A: "#176b62", B: "#ef7d4d", Neutral: "#596563" };
  const roleKeys = { "Generic Player": "generic", Setter: "setter", Libero: "libero", Middle: "middle", Outside: "outside", Opposite: "opposite", Coach: "coach" };
  const heroRoles = ["Setter", "Outside", "Opposite", "Middle", "Libero", "Coach"];
  const heroDefaults = { Setter: "Ready", Outside: "Reception", Opposite: "Attack Start", Middle: "Block", Libero: "Reception", Coach: "Holding Ball" };
  const fallbackCharacterViews = ["Front", "3/4 Front Left", "3/4 Front Right", "Left Side", "Right Side", "3/4 Back Left", "3/4 Back Right", "Back", "45\u00b0 Back"];
  const ASSET_LIBRARY_PAGE_SIZE = 96;
  const assetAliases = { Ball: "single_ball", "Ball group": "ball_group", "Ball pile": "ball_pile", "Ball cart": "ball_cart_blue" };
  const structuredNoteSections = [
    ["coachingPoints", "Coaching Points", true],
    ["commonMistakes", "Common Mistakes", true],
    ["progressions", "Progressions", true],
    ["regressions", "Regressions", true],
    ["variations", "Variations", true]
  ];
  let assetManifest = [];
  let assetLibraryManifest = [];
  let assetDiagnostics = {};
  let clientSkippedAssets = [];
  let assetIndex = new Map();
  let manifestDefaultPlayerStyle = "professional";
  let professionalPoseGroups = {};
  let professionalCharacterViews = fallbackCharacterViews;
  let defaultCharacterView = "Front";
  let paletteCategory = "Players";
  let paletteQuery = "";
  let paletteLiberoOnly = false;
  let selectedFigureAssetIds = new Set();
  const COURT_RATIO = 2;
  const WORKSPACE = { width: 2600, height: 1800 };
  const courtStyles = {
    competition: { surface: "#dca06f", free: "#57776e", line: "#fffdf7" },
    blue: { surface: "#6eadd1", free: "#315c72", line: "#ffffff" },
    light: { surface: "#e9c99b", free: "#8fa9a0", line: "#ffffff" }
  };

  const defaultCourt = (index = 0, overrides = {}) => {
    const width = overrides.width || 780;
    return {
      id: overrides.id || uid(), type: "court", name: overrides.name || `Court ${index + 1}`,
      x: overrides.x ?? 600 + index * 840, y: overrides.y ?? 390,
      width, height: width / COURT_RATIO, rotation: window.VPDInteraction.normalizeAngle(overrides.rotation ?? 0),
      locked: !!overrides.locked, style: overrides.style || "competition", kind: overrides.kind || "court",
      rotateContentsWithCourt: overrides.rotateContentsWithCourt ?? false,
      keepPlayersUpright: overrides.keepPlayersUpright ?? true,
      settings: {
        showAttackLines: overrides.settings?.showAttackLines ?? overrides.attackLines ?? true,
        showZoneLabels: overrides.settings?.showZoneLabels ?? overrides.zones ?? true,
        showNet: overrides.settings?.showNet ?? overrides.net ?? true,
        showGrid: overrides.settings?.showGrid ?? overrides.grid ?? false,
        showAntennas: overrides.settings?.showAntennas ?? overrides.antennas ?? true
      }
    };
  };
  const emptyFrame = (name = "Frame 1") => {
    const court = defaultCourt();
    return { id: uid(), name, objects: [], courts: [court], court: legacyCourtSettings(court) };
  };
  const defaultNoteItem = (text = "", order = 0) => ({ id: uid(), text, completed: false, order });
  const defaultDrillNotes = () => ({
    description: "", coachingPoints: [], commonMistakes: [], progressions: [], regressions: [],
    variations: [], equipmentNotes: "", generalComments: "", postTrainingObservations: "", formatVersion: 1
  });
  const defaultPracticeNotes = () => ({
    mainObjective: "", technicalObjective: "", tacticalObjective: "", physicalObjective: "", intensity: "",
    importantNotes: "", generalComments: "", postPracticeReview: "", formatVersion: 1
  });
  const defaultObjectNote = () => ({ text: "", showIndicator: true, showInExport: false });
  function normalizeNoteItem(value, order) {
    if (typeof value === "string") return value.trim() ? defaultNoteItem(value.trim(), order) : null;
    if (!value || typeof value !== "object" || !String(value.text || "").trim()) return null;
    return { id: value.id || uid(), text: String(value.text).trim(), completed: !!value.completed, order: Number.isFinite(+value.order) ? +value.order : order };
  }
  function normalizeDrillNotes(raw = {}, legacy = {}) {
    const notes = defaultDrillNotes(), source = raw && typeof raw === "object" ? raw : {};
    ["description", "equipmentNotes", "generalComments", "postTrainingObservations"].forEach(key => notes[key] = typeof source[key] === "string" ? source[key] : "");
    if (!notes.generalComments && typeof legacy.notes === "string") notes.generalComments = legacy.notes;
    if (!notes.equipmentNotes && typeof legacy.equipment === "string") notes.equipmentNotes = legacy.equipment;
    const legacyLists = { coachingPoints: legacy.coaching, commonMistakes: legacy.mistakes };
    structuredNoteSections.forEach(([key]) => {
      let values = Array.isArray(source[key]) ? source[key] : [];
      if (!values.length && typeof legacyLists[key] === "string") values = legacyLists[key].split(/\r?\n/).filter(Boolean);
      notes[key] = values.map(normalizeNoteItem).filter(Boolean).sort((a, b) => a.order - b.order).map((item, index) => ({ ...item, order: index }));
    });
    return notes;
  }
  function normalizePracticeNotes(raw = {}, legacy = {}) {
    const notes = defaultPracticeNotes(), source = raw && typeof raw === "object" ? raw : {};
    Object.keys(notes).forEach(key => { if (key !== "formatVersion") notes[key] = typeof source[key] === "string" ? source[key] : ""; });
    if (!notes.mainObjective && typeof legacy.main_objective === "string") notes.mainObjective = legacy.main_objective;
    if (!notes.generalComments && typeof legacy.notes === "string") notes.generalComments = legacy.notes;
    return notes;
  }
  function normalizeObjectNote(raw = {}) {
    const source = raw && typeof raw === "object" ? raw : {};
    return { text: typeof source.text === "string" ? source.text : "", showIndicator: source.showIndicator !== false, showInExport: !!source.showInExport };
  }
  let state = {
    id: null, metadata: { name: "Untitled drill", objective: "", tags: [] }, created_at: null,
    notes: defaultDrillNotes(),
    frames: [emptyFrame()], frameIndex: 0, selected: [], clipboard: [], team: "A",
    zoom: 1, panX: 0, panY: 0, history: [], future: [], drawing: null,
    exportMode: "all", printMode: "all"
  };
  let currentPractice = { id: null, items: [], practiceNotes: defaultPracticeNotes() };
  let cachedDrills = [];
  let interaction = null;
  const svg = $("#court-svg"), viewport = $("#viewport"), courtLayer = $("#court-layer"), objectsLayer = $("#objects-layer"), selectionLayer = $("#selection-layer");
  const frame = () => state.frames[state.frameIndex];
  function legacyCourtSettings(court) {
    const s = court.settings;
    return { attackLines: s.showAttackLines, zones: s.showZoneLabels, grid: s.showGrid, antennas: s.showAntennas, net: s.showNet };
  }
  function migrateFrame(item) {
    const f = item || {};
    if (!Array.isArray(f.courts) || !f.courts.length) f.courts = [defaultCourt(0, f.court || {})];
    else f.courts = f.courts.map((court, index) => defaultCourt(index, court));
    const valid = new Set(f.courts.map(c => c.id));
    f.objects = (f.objects || []).map(migrateVisualObject).map(o => {
      const assignedCourtId = valid.has(o.assignedCourtId || o.courtId) ? (o.assignedCourtId || o.courtId) : f.courts[0].id;
      return { ...o, courtId: assignedCourtId, assignedCourtId };
    });
    f.court = legacyCourtSettings(f.courts[0]);
    return f;
  }
  function selectedCourt() { return frame().courts.find(c => state.selected.includes(c.id)); }
  function courtById(id) { return frame().courts.find(c => c.id === id); }
  function assignedCourtContents(court) {
    return frame().objects.filter(object => object.courtId === court.id);
  }
  function captureCourtContents(court) {
    return assignedCourtContents(court).map(object => ({
      id: object.id, x: object.x, y: object.y, rotation: object.rotation || 0
    }));
  }
  function rotateCourtTo(court, requestedRotation, options = {}) {
    if (!court) return;
    const baselineRotation = options.baselineRotation ?? court.rotation ?? 0;
    const contentState = options.contentState ?? captureCourtContents(court);
    const targetRotation = window.VPDInteraction.normalizeAngle(requestedRotation);
    const delta = window.VPDInteraction.shortestAngleDelta(baselineRotation, targetRotation);
    court.rotation = targetRotation;
    court.height = court.width / COURT_RATIO;
    if (!court.rotateContentsWithCourt || !delta) return;
    contentState.forEach(original => {
      const object = objectById(original.id);
      if (!object) return;
      const point = window.VPDInteraction.rotatePoint(original, court, delta);
      object.x = point.x;
      object.y = point.y;
      if (!(["player", "character"].includes(object.type) && court.keepPlayersUpright)) {
        object.rotation = window.VPDInteraction.normalizeAngle(original.rotation + delta);
      } else {
        object.rotation = original.rotation;
      }
    });
  }
  function rotateSelectedCourtBy(delta) {
    const court = selectedCourt();
    if (!court || court.locked) return;
    snapshot();
    rotateCourtTo(court, (court.rotation || 0) + delta);
    renderAll();
  }

  const assetKey = value => (value || "").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");
  const isCharacter = object => ["player", "character"].includes(object?.type);
  const normalizeVisualStyle = () => "professional";
  function normalizeCharacterView(value) {
    const normalized = assetKey(value);
    const aliases = {
      front: "Front", back: "Back", left: "Left Side", left_side: "Left Side",
      right: "Right Side", right_side: "Right Side", "3_4_front": "Front",
      three_quarter_front: "Front", "34_front": "Front",
      "3_4_front_left": "3/4 Front Left", three_quarter_front_left: "3/4 Front Left", "34_front_left": "3/4 Front Left",
      "3_4_front_right": "3/4 Front Right", three_quarter_front_right: "3/4 Front Right", "34_front_right": "3/4 Front Right",
      "3_4_back": "Back", three_quarter_back: "Back", "34_back": "Back",
      "3_4_back_left": "3/4 Back Left", three_quarter_back_left: "3/4 Back Left", "34_back_left": "3/4 Back Left",
      "3_4_back_right": "3/4 Back Right", three_quarter_back_right: "3/4 Back Right", "34_back_right": "3/4 Back Right",
      "45_back": "45\u00b0 Back", "45_degree_back": "45\u00b0 Back", "45_back_view": "45\u00b0 Back"
    };
    return aliases[normalized] || defaultCharacterView;
  }
  function validAssetPath(path) {
    return typeof path === "string" && path.startsWith("/static/") && !path.includes("..") && !/^https?:\/\//i.test(path);
  }
  function skipClientAsset(id, reason, asset = null) {
    const entry = { id: id || "unknown", reason };
    clientSkippedAssets.push(entry);
    console.warn(`Skipping Asset Library entry: ${entry.id} - ${reason}`, asset || "");
  }
  function validatedManifestAssets(assets) {
    const ids = new Set();
    clientSkippedAssets = [];
    return assets.filter(asset => {
      const id = asset?.id || "unknown";
      if (!asset || typeof asset !== "object") {
        skipClientAsset(id, "entry is not an object", asset);
        return false;
      }
      if (ids.has(id)) {
        skipClientAsset(id, "duplicate asset ID", asset);
        return false;
      }
      ids.add(id);
      if (!validAssetPath(asset.asset) || !validAssetPath(asset.thumbnail)) {
        skipClientAsset(id, "invalid asset or thumbnail path", asset);
        return false;
      }
      return true;
    });
  }
  function isDefaultCharacterViewValue(value) {
    const key = assetKey(value || defaultCharacterView);
    return key === assetKey(defaultCharacterView) || ["front", "3_4_front", "three_quarter_front", "34_front"].includes(key);
  }
  function playerAssetsFor(team, role, pose) {
    const roleKey = roleKeys[role] || assetKey(role) || "generic";
    const assetTeam = roleKey === "coach" ? "Neutral" : (team === "B" ? "B" : "A");
    const poseKey = assetKey(pose).replace("attack_starting_position", "attack_start");
    return assetManifest.filter(a =>
      a.category === "player" && a.role === roleKey && a.team === assetTeam
      && a.visualStyle === "professional" && assetKey(a.pose) === poseKey
    );
  }
  function characterViewAssets(team, role, pose) {
    const assets = playerAssetsFor(team, role, pose);
    return professionalCharacterViews.map(view => assets.find(asset => normalizeCharacterView(asset.view || asset.characterView) === view)).filter(Boolean);
  }
  function availableCharacterViews(team, role, pose) {
    return characterViewAssets(team, role, pose).map(asset => normalizeCharacterView(asset.view || asset.characterView));
  }
  function playerAsset(team, role, pose, characterView = defaultCharacterView) {
    const roleKey = roleKeys[role] || assetKey(role) || "generic";
    const assetTeam = roleKey === "coach" ? "Neutral" : (team === "B" ? "B" : "A");
    const poseKey = assetKey(pose).replace("attack_starting_position", "attack_start");
    const view = normalizeCharacterView(characterView);
    const exact = (candidateTeam = assetTeam) => assetManifest.find(a =>
      a.category === "player" && a.role === roleKey && a.team === candidateTeam
      && a.visualStyle === "professional" && assetKey(a.pose) === poseKey
      && normalizeCharacterView(a.view || a.characterView) === view
    );
    if (exact()) return exact();
    if (view !== defaultCharacterView) return null;
    return exact()
      || assetManifest.find(a => a.category === "player" && a.role === roleKey
        && a.team === "A" && a.visualStyle === "professional" && assetKey(a.pose) === poseKey
        && isDefaultCharacterViewValue(a.view || a.characterView))
      || assetManifest.find(a => a.category === "player" && a.role === roleKey
        && a.team === assetTeam && a.visualStyle === "professional"
        && assetKey(a.pose) === assetKey(heroDefaults[role] || "Ready")
        && isDefaultCharacterViewValue(a.view || a.characterView))
      || assetManifest.find(a => a.category === "player" && a.role === roleKey
        && a.visualStyle === "professional" && isDefaultCharacterViewValue(a.view || a.characterView))
      || assetIndex.get("safe_fallback");
  }
  function equipmentAsset(label) {
    const id = assetAliases[label] || assetKey(label);
    return assetIndex.get(id) || assetIndex.get("safe_fallback");
  }
  function resolveAsset(o) {
    const indexed = o.assetId && assetIndex.get(o.assetId);
    if (isCharacter(o)) {
      if (indexed?.visualStyle === "professional" && normalizeCharacterView(indexed.view || indexed.characterView) === normalizeCharacterView(o.characterView)) return indexed;
      return playerAsset(o.team, o.role || o.label, o.pose, o.characterView) || indexed || playerAsset(o.team, o.role || o.label, o.pose);
    }
    if (indexed) return indexed;
    if (o.type === "equipment") return equipmentAsset(o.label);
    return assetIndex.get("safe_fallback");
  }
  function migrateVisualObject(o) {
    if (!o.note || typeof o.note !== "object") o.note = normalizeObjectNote(o.note);
    else o.note = normalizeObjectNote(o.note);
    if (o.type === "sticky-note") {
      o.label ||= "Sticky Note";
      o.text ||= "";
      o.width ||= 210;
      o.height ||= 120;
      o.backgroundColor ||= "#fff8bf";
      o.textSize ||= 16;
      o.opacity ??= 1;
      o.zIndex ??= o.layer ?? 1;
      return o;
    }
    if (!["player", "character", "equipment"].includes(o.type)) return o;
    const asset = resolveAsset(o);
    o.assetId = asset.id;
    o.width ||= asset.defaultWidth;
    o.height ||= asset.defaultHeight;
    o.anchor ||= asset.anchor;
    if (isCharacter(o)) {
      o.role ||= o.label || "Generic Player";
      o.pose ||= roles[o.role]?.[0] || "Standing";
      o.facing ||= o.mirrorX || o.mirror ? "Left" : "Right";
      o.visualStyle = "professional";
      o.characterView = normalizeCharacterView(o.characterView || asset.view || asset.characterView);
      o.assetId = asset.id;
      o.characterId = asset.characterId;
      delete o.isProfessionalFallback;
      o.width ||= asset.defaultWidth;
      o.height ||= asset.defaultHeight;
      o.anchor ||= asset.anchor;
      o.mirrorX ??= !!o.mirror;
      o.flipY ??= false;
      o.showShadow ??= o.visualStyle === "professional";
      o.zIndex ??= o.layer ?? 1;
      o.assignedCourtId ||= o.courtId || null;
    }
    return o;
  }
  async function loadAssetManifest() {
    const response = await fetch("/api/assets");
    if (!response.ok) throw new Error("Asset manifest could not be loaded");
    const payload = await response.json();
    assetManifest = validatedManifestAssets(payload.assets || []);
    assetLibraryManifest = validatedManifestAssets(payload.libraryAssets || payload.assets || []);
    assetDiagnostics = payload.diagnostics || {};
    console.info("Asset Library diagnostics", assetDiagnostics);
    (assetDiagnostics.skippedAssets || []).forEach(item => console.warn(`Skipped asset: ${item.id} (${item.kind}) - ${item.reason}`));
    clientSkippedAssets.forEach(item => console.warn(`Client-skipped asset: ${item.id} - ${item.reason}`));
    const catalog = payload.professionalPoseCatalog || {};
    professionalPoseGroups = payload.professionalPoseGroups || {};
    professionalCharacterViews = payload.professionalCharacterViews || fallbackCharacterViews;
    defaultCharacterView = normalizeCharacterView(payload.defaultCharacterView || "Front");
    Object.entries(catalog).forEach(([role, poses]) => {
      const teams = role === "coach" ? ["Neutral"] : ["A", "B"];
      teams.forEach(team => poses.forEach(pose => {
        const matches = assetManifest.filter(asset =>
          asset.category === "player" && asset.visualStyle === "professional"
          && asset.role === role && asset.team === team
          && assetKey(asset.pose) === assetKey(pose)
          && isDefaultCharacterViewValue(asset.view || asset.characterView)
        );
        const anyViewMatches = assetManifest.filter(asset =>
          asset.category === "player" && asset.visualStyle === "professional"
          && asset.role === role && asset.team === team
          && assetKey(asset.pose) === assetKey(pose)
        );
        const teamAFallbackMatches = assetManifest.filter(asset =>
          team === "B"
          && asset.category === "player" && asset.visualStyle === "professional"
          && asset.role === role && asset.team === "A"
          && assetKey(asset.pose) === assetKey(pose)
        );
        if (matches.length > 1 || (!matches.length && !anyViewMatches.length && !teamAFallbackMatches.length)) {
          console.warn(`Invalid Professional manifest entry: ${team} ${role}/${pose}; found ${matches.length}`);
        }
      }));
    });
    manifestDefaultPlayerStyle = normalizeVisualStyle(payload.defaultPlayerVisualStyle || "professional");
    assetIndex = new Map(assetManifest.map(asset => [asset.id, asset]));
    const preload = () => assetManifest.filter(a => a.category === "experimental_player").forEach(asset => { const image = new Image(); image.decoding = "async"; image.src = asset.asset; });
    if ("requestIdleCallback" in window) requestIdleCallback(preload); else setTimeout(preload, 200);
  }

  function toast(message) {
    const node = $("#toast"); node.textContent = message; node.classList.add("show");
    clearTimeout(toast.timer); toast.timer = setTimeout(() => node.classList.remove("show"), 2200);
  }
  function snapshot() {
    state.history.push(JSON.stringify({ frames: state.frames, frameIndex: state.frameIndex, metadata: state.metadata }));
    if (state.history.length > 60) state.history.shift();
    state.future = [];
  }
  function restore(serialized) {
    const v = JSON.parse(serialized);
    Object.assign(state, v, { selected: [] }); renderAll();
  }
  function undo() {
    if (!state.history.length) return;
    state.future.push(JSON.stringify({ frames: state.frames, frameIndex: state.frameIndex, metadata: state.metadata }));
    restore(state.history.pop());
  }
  function redo() {
    if (!state.future.length) return;
    state.history.push(JSON.stringify({ frames: state.frames, frameIndex: state.frameIndex, metadata: state.metadata }));
    restore(state.future.pop());
  }

  function buildPalette() {
    const item = value => `<button class="palette-item" data-type="${value.type}" data-label="${value.label}" data-role="${value.role || ""}">${paletteThumb(value)}<small>${value.label}</small></button>`;
    const playerSections = heroRoles.map(role =>
      `<section class="palette-section player-role-section" data-category="Players" data-role-section="${role}"><button class="palette-title">${role}<span>−</span></button><div class="palette-items">${item({ type: "character", label: role, role })}</div></section>`
    ).join("");
    const sections = [
      ["Balls", equipment.slice(0, 3).map(label => ({ type: "equipment", label }))],
      ["Equipment", equipment.slice(3).map(label => ({ type: "equipment", label }))],
      ["Shapes", [...drawingTools.map(label => ({ type: "drawing", label })), ...shapeTools.filter(label => label !== "Text label").map(label => ({ type: "shape", label }))]],
      ["Text", [{ type: "text", label: "Text label" }, { type: "sticky-note", label: "Sticky Note" }]]
    ].map(([title, items]) => `<section class="palette-section" data-category="${title}"><button class="palette-title">${title}<span>−</span></button><div class="palette-items">${items.map(item).join("")}</div></section>`).join("");
    $("#palette").innerHTML = `
      <div class="palette-tools">
        <input id="palette-search" type="search" placeholder="Search assets…" aria-label="Search editor assets">
        <div class="palette-tabs">${["Players", "Balls", "Equipment", "Shapes", "Text"].map((name, index) => `<button class="${index ? "" : "active"}" data-palette-tab="${name}">${name}</button>`).join("")}</div>
      </div>
      <div class="team-toggle"><button class="active" data-team="A">Team A</button><button data-team="B">Team B</button><button data-libero-filter="true">Libero</button></div>
      ${playerSections}${sections}
      <button type="button" class="more-assets" id="more-assets">＋ More Assets</button>`;
    $$(".team-toggle button").forEach(b => b.onclick = () => {
      paletteLiberoOnly = b.dataset.liberoFilter === "true";
      if (b.dataset.team) state.team = b.dataset.team;
      $$(".team-toggle button").forEach(x => x.classList.toggle("active", x === b));
      updatePalettePlayerThumbs();
      renderPaletteVisibility();
    });
    $$("[data-palette-tab]").forEach(button => button.onclick = () => {
      paletteCategory = button.dataset.paletteTab;
      $$("[data-palette-tab]").forEach(item => item.classList.toggle("active", item === button));
      renderPaletteVisibility();
    });
    $("#palette-search").oninput = e => { paletteQuery = e.target.value.trim().toLowerCase(); renderPaletteVisibility(); };
    $("#more-assets").onclick = () => showView("assets");
    $$(".palette-title").forEach(b => b.onclick = () => {
      const list = b.nextElementSibling; list.classList.toggle("hidden"); b.lastElementChild.textContent = list.classList.contains("hidden") ? "+" : "−";
    });
    $$(".palette-item").forEach(b => b.onclick = () => {
      if (b.dataset.type === "drawing") {
        state.drawing = { tool: b.dataset.label }; svg.classList.add("drawing-cursor"); toast(`Drag on the court to draw: ${b.dataset.label}`); return;
      }
      if (b.dataset.type === "text") {
        addObject({ type: "text", label: "Text label", text: "Instruction", x: 600, y: 390, color: "#14211f" });
        return;
      }
      if (b.dataset.type === "sticky-note") {
        addObject({ type: "sticky-note", label: "Sticky Note", text: "Setter starts here", width: 220, height: 120, backgroundColor: "#fff4a6", color: "#14211f" });
        return;
      }
      const role = b.dataset.role || "";
      const pose = role ? heroDefaults[role] : "";
      const asset = b.dataset.type === "character" ? playerAsset(state.team, role, pose, defaultCharacterView) : equipmentAsset(b.dataset.label);
      addObject({
        type: b.dataset.type, label: b.dataset.label, role, pose,
        characterView: asset.characterView || defaultCharacterView,
        characterId: asset.characterId || (role === "Coach" ? "coach_01" : "female_athlete_01"),
        visualStyle: "professional", assetId: asset.id,
        width: asset.defaultWidth, height: asset.defaultHeight,
        anchor: asset.anchor, facing: "Right",
        mirrorX: false, flipY: false, showShadow: asset.visualStyle === "professional"
      });
    });
    updatePalettePlayerThumbs();
    renderPaletteVisibility();
  }

  function renderPaletteVisibility() {
    $$(".palette-section").forEach(section => {
      const categoryMatch = section.dataset.category === paletteCategory;
      const liberoMatch = !paletteLiberoOnly || section.dataset.roleSection === "Libero";
      const visible = $$(".palette-item", section).filter(button => !paletteQuery || `${button.dataset.label} ${button.dataset.role}`.toLowerCase().includes(paletteQuery));
      $$(".palette-item", section).forEach(button => button.classList.toggle("hidden", !visible.includes(button)));
      section.classList.toggle("hidden", !categoryMatch || !liberoMatch || !visible.length);
    });
    $(".team-toggle").classList.toggle("hidden", paletteCategory !== "Players");
  }

  function paletteThumb(item) {
    if (item.type === "character") {
      const asset = playerAsset(state.team, item.role, heroDefaults[item.role]);
      return `<img class="palette-thumb" src="${asset.thumbnail}" data-asset-id="${asset.id}" alt="" loading="lazy">`;
    }
    if (item.type === "equipment") {
      const asset = equipmentAsset(item.label);
      return `<img class="palette-thumb" src="${asset.asset}" alt="" loading="lazy">`;
    }
    const kind = item.type === "drawing" ? "arrow" : item.type === "text" ? "text" : "shape";
    return `<svg class="palette-vector" viewBox="0 0 48 38" aria-hidden="true"><path class="${kind}" d="${kind === "arrow" ? "M6 31Q24 6 41 12M34 6L42 12L34 18" : kind === "text" ? "M8 29V9H40V29M16 24L22 14L28 24M18 20H26" : "M9 8H39V30H9Z"}"/></svg>`;
  }
  function updatePalettePlayerThumbs() {
    $$('.palette-item[data-type="character"]').forEach(button => {
      const asset = playerAsset(state.team, button.dataset.role, heroDefaults[button.dataset.role]);
      const image = $("img", button);
      if (image) {
        image.src = asset.thumbnail;
        image.dataset.assetId = asset.id;
      }
    });
  }

  function defaultObject(data) {
    const targetCourt = courtById(data.assignedCourtId || data.courtId) || selectedCourt() || frame().courts[0];
    const assignedCourtId = data.assignedCourtId || data.courtId || targetCourt?.id || null;
    return {
      id: uid(), type: data.type, label: data.label, courtId: assignedCourtId, assignedCourtId,
      x: data.x ?? (targetCourt?.x || 600) + (Math.random() - .5) * 100,
      y: data.y ?? (targetCourt?.y || 390) + (Math.random() - .5) * 70,
      width: data.type === "text" ? 180 : (data.width || 70), height: data.type === "text" ? 36 : (data.height || 90),
      rotation: 0, scale: 1, opacity: 1, color: data.color || teamColors[state.team], team: state.team,
      role: data.role || "", pose: data.pose || "", mirror: false, mirrorX: false, flipY: false,
      aspectLocked: true, showShadow: isCharacter(data), zIndex: frame().objects.length + 1,
      locked: false, text: data.text || "", note: normalizeObjectNote(data.note), ...data
    };
  }
  function addObject(data) {
    snapshot(); const obj = defaultObject(data); frame().objects.push(obj); state.selected = [obj.id]; renderAll();
  }
  function addAssetLibraryObject(asset) {
    if (!asset) return toast("Asset is not available");
    const isPlayer = asset.category === "player" && asset.visualStyle === "professional";
    const data = isPlayer ? {
      type: "character",
      label: asset.role || asset.pose || "Player",
      role: asset.role || "",
      pose: asset.pose || "",
      team: asset.team || state.team,
      characterView: normalizeCharacterView(asset.view || asset.characterView),
      characterId: asset.characterId,
      visualStyle: "professional",
      assetId: asset.id,
      width: asset.defaultWidth,
      height: asset.defaultHeight,
      anchor: asset.anchor,
      facing: "Right",
      mirrorX: false,
      flipY: false,
      showShadow: asset.showShadow !== false,
    } : {
      type: asset.category === "equipment" ? "equipment" : asset.category,
      label: asset.variant || asset.pose || asset.id,
      assetId: asset.id,
      width: asset.defaultWidth,
      height: asset.defaultHeight,
      anchor: asset.anchor,
    };
    addObject(data);
    showView("editor");
    toast(`Added ${asset.pose || asset.variant || asset.id}`);
  }
  function objectById(id) { return frame().objects.find(o => o.id === id) || courtById(id); }

  function addCourt(overrides = {}) {
    snapshot();
    const index = frame().courts.length;
    const court = defaultCourt(index, { x: 600 + (index % 3) * 840, y: 390 + Math.floor(index / 3) * 540, ...overrides });
    frame().courts.push(court);
    state.selected = [court.id];
    syncCourtChecks();
    renderAll();
    return court;
  }
  function duplicateCourt(withContents = false) {
    const source = selectedCourt();
    if (!source) return toast("Select a court first");
    snapshot();
    const copy = deep(source);
    copy.id = uid(); copy.name = `${source.name} Copy`; copy.x += 70; copy.y += 70; copy.locked = false;
    frame().courts.push(copy);
    if (withContents) {
      const contents = frame().objects.filter(o => o.courtId === source.id).map(original => ({
        ...deep(original), id: uid(), courtId: copy.id, assignedCourtId: copy.id,
        x: original.x + copy.x - source.x, y: original.y + copy.y - source.y
      }));
      frame().objects.push(...contents);
    }
    state.selected = [copy.id];
    syncCourtChecks(); renderAll();
    toast(withContents ? "Court and contents duplicated" : "Court duplicated");
  }
  function deleteCourt() {
    const court = selectedCourt();
    if (!court) return toast("Select a court first");
    if (frame().courts.length === 1) return toast("A frame needs at least one court");
    snapshot();
    frame().courts = frame().courts.filter(c => c.id !== court.id);
    frame().objects.forEach(o => { if (o.courtId === court.id) o.courtId = null; });
    state.selected = []; syncCourtChecks(); renderAll();
  }
  function arrangeCourts(kind) {
    snapshot();
    const layouts = {
      single: [[600, 390, 780]],
      horizontal2: [[520, 390, 720], [1320, 390, 720]],
      vertical2: [[700, 320, 640], [700, 760, 640]],
      horizontal3: [[430, 390, 600], [1100, 390, 600], [1770, 390, 600]],
      twoPlusOne: [[500, 330, 650], [1220, 330, 650], [860, 790, 650]],
      stations: [[600, 390, 780], [1320, 390, 390], [1320, 760, 520]]
    };
    const positions = layouts[kind] || layouts.single;
    while (frame().courts.length < positions.length) frame().courts.push(defaultCourt(frame().courts.length));
    if (frame().courts.length > positions.length) {
      const removed = new Set(frame().courts.slice(positions.length).map(c => c.id));
      frame().objects.forEach(o => { if (removed.has(o.courtId)) o.courtId = frame().courts[0].id; });
      frame().courts = frame().courts.slice(0, positions.length);
    }
    frame().courts.forEach((court, index) => {
      const old = { x: court.x, y: court.y };
      [court.x, court.y, court.width] = positions[index];
      court.height = court.width / COURT_RATIO;
      if (kind === "stations" && index === 2) {
        court.name = "Equipment Zone"; court.style = "light"; court.kind = "zone";
        Object.keys(court.settings).forEach(key => court.settings[key] = false);
      }
      else court.kind = "court";
      if (!(kind === "stations" && index === 2)) court.name = `Court ${index + 1}`;
      frame().objects.filter(o => o.courtId === court.id).forEach(o => { o.x += court.x - old.x; o.y += court.y - old.y; });
    });
    state.selected = frame().courts.length ? [frame().courts[0].id] : [];
    syncCourtChecks(); renderAll(); fitAll();
  }

  function renderCourt() {
    courtLayer.innerHTML = "";
    frame().courts.forEach(c => {
      const w = c.width, h = c.height, p = Math.max(18, w * .08), colors = courtStyles[c.style] || courtStyles.competition;
      const group = el("g", { "data-id": c.id, "data-court-id": c.id, class: "court-object object-hit", transform: `translate(${c.x} ${c.y}) rotate(${c.rotation})` });
      const freeFill = c.style === "competition" ? "url(#court-free-light)" : colors.free;
      const surfaceFill = c.style === "competition" ? "url(#court-surface-light)" : colors.surface;
      group.append(el("rect", { x: -w / 2 - p, y: -h / 2 - p, width: w + p * 2, height: h + p * 2, rx: Math.max(8, w * .018), fill: freeFill, filter: "url(#shadow)", class: "court-free-zone" }));
      group.append(el("rect", { x: -w / 2, y: -h / 2, width: w, height: h, fill: surfaceFill, class: "court-surface" }));
      group.append(el("path", { d: `M${-w / 2} ${h / 2 - 10}H${w / 2}V${h / 2}H${-w / 2}Z`, fill: "#6f351f", "fill-opacity": ".15", "pointer-events": "none" }));
      if (c.kind === "zone") {
        group.append(el("rect", { x: -w / 2, y: -h / 2, width: w, height: h, fill: "none", stroke: colors.line, "stroke-width": 4, "stroke-dasharray": "18 12" }));
        group.append(el("text", { x: 0, y: 7, "text-anchor": "middle", class: "court-name" }, "FREE EQUIPMENT ZONE"));
        group.append(el("text", { x: -w / 2, y: -h / 2 - p - 10, class: "court-name" }, escapeHtml(c.name)));
        courtLayer.append(group);
        return;
      }
      if (c.settings.showGrid) group.append(el("rect", { x: -w / 2 - p, y: -h / 2 - p, width: w + p * 2, height: h + p * 2, fill: "url(#grid-pattern)" }));
      group.append(el("rect", { x: -w / 2, y: -h / 2, width: w, height: h, fill: "none", stroke: colors.line, "stroke-width": 4, class: "court-line" }));
      if (c.settings.showNet) {
        const netWidth = Math.max(13, w * .018);
        group.append(el("rect", { x: -netWidth / 2, y: -h / 2 - 12, width: netWidth, height: h + 24, fill: "url(#net-mesh)", stroke: "#eef5f1", "stroke-width": 2, class: "net-mesh" }));
        [-h / 2 - 20, h / 2 + 20].forEach(y => {
          group.append(el("rect", { x: -13, y: y - 13, width: 26, height: 26, rx: 7, fill: "#145a82", stroke: "#d9f1ff", "stroke-width": 2, class: "net-post" }));
          group.append(el("circle", { cx: 0, cy: y, r: 5, fill: "#0d334b" }));
        });
        group.append(el("line", { x1: 0, y1: -h / 2 - 14, x2: 0, y2: h / 2 + 14, class: "net" }));
      }
      if (c.settings.showAttackLines) [-w / 6, w / 6].forEach(x => group.append(el("line", { x1: x, y1: -h / 2, x2: x, y2: h / 2, class: "attack-line" })));
      if (c.settings.showAntennas) [-h / 2, h / 2].forEach(y => {
        group.append(el("line", { x1: 0, y1: y - 24, x2: 0, y2: y + 24, stroke: "#fff", "stroke-width": 7, class: "antenna" }));
        group.append(el("line", { x1: 0, y1: y - 24, x2: 0, y2: y + 24, stroke: "#ef4d42", "stroke-width": 4, "stroke-dasharray": "8 7", class: "antenna" }));
      });
      if (c.settings.showZoneLabels) {
        const zones = [[5,-.33,-.28],[6,-.33,0],[1,-.33,.28],[4,-.08,-.28],[3,-.08,0],[2,-.08,.28],[2,.08,-.28],[3,.08,0],[4,.08,.28],[1,.33,-.28],[6,.33,0],[5,.33,.28]];
        zones.forEach(([n, px, py]) => group.append(el("text", { x: w * px, y: h * py + 6, class: "zone-label" }, String(n))));
      }
      group.append(el("text", { x: -w / 2, y: -h / 2 - p - 10, class: "court-name" }, escapeHtml(c.name)));
      if (c.locked) group.setAttribute("data-locked", "true");
      courtLayer.append(group);
    });
  }

  function playerGraphic(o) {
    const pose = (o.pose || "").toLowerCase();
    let arms = `<path d="M-7 1L-28 20M7 1L28 20"/>`, legs = `<path d="M-7 34L-20 64M7 34L20 64"/>`;
    if (pose.includes("set") || pose.includes("block") || pose.includes("overhead")) arms = `<path d="M-7 2L-20-18L-12-36M7 2L20-18L12-36"/>`;
    if (pose.includes("attack") || pose.includes("serve") || pose.includes("toss")) arms = `<path d="M-7 2L-26 18M7 2L22-20L18-38"/>`;
    if (pose.includes("reception") || pose.includes("dig") || pose.includes("defense")) arms = `<path d="M-7 8L-20 28L0 36M7 8L18 28L0 36"/>`;
    if (pose.includes("dive")) { arms = `<path d="M-8 5L-35 12M8 5L35 12"/>`; legs = `<path d="M-6 32L-25 48M6 32L28 38"/>`; }
    const accent = o.team === "B" ? "#163d58" : "#f2c85b";
    return `<g stroke="${o.color}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" fill="none">
      <circle cx="0" cy="-21" r="12" fill="${o.color}" stroke="none"/><path d="M0-7L0 35"/><path d="M-13 12H13" stroke="${accent}" stroke-width="14"/>${arms}${legs}
      </g><text x="0" y="82" text-anchor="middle" font-size="11" font-weight="800" fill="#14211f">${o.role === "Generic Player" ? "PLAYER" : o.role.toUpperCase()}</text>`;
  }
  function equipmentGraphic(o) {
    const label = o.label.toLowerCase();
    if (label.includes("ball")) return `<circle r="23" fill="#f7d15d" stroke="#163d58" stroke-width="3"/><path d="M-20-7Q0 5 20-7M-7-21Q4 0-7 21M9-20Q-4 0 9 20" fill="none" stroke="#163d58" stroke-width="2"/><text y="45" text-anchor="middle" font-size="10" font-weight="800">${o.label.toUpperCase()}</text>`;
    if (label.includes("cone")) return `<path d="M-22 26L0-27L22 26Z" fill="${o.color}" stroke="#fff" stroke-width="3"/><rect x="-30" y="24" width="60" height="9" rx="3" fill="${o.color}"/>`;
    if (label.includes("target") || label.includes("hoop")) return `<circle r="31" fill="none" stroke="${o.color}" stroke-width="8"/><circle r="12" fill="none" stroke="${o.color}" stroke-width="4"/><path d="M-38 0H38M0-38V38" stroke="${o.color}" stroke-width="2"/>`;
    if (label.includes("cart")) return `<rect x="-32" y="-26" width="64" height="46" rx="7" fill="${o.color}" stroke="#fff" stroke-width="3"/><path d="M-24-15h48M-24-3h48" stroke="#fff" stroke-width="3"/><circle cx="-21" cy="28" r="7" fill="#263330"/><circle cx="21" cy="28" r="7" fill="#263330"/>`;
    if (label.includes("ladder")) return `<path d="M-29-42V42M29-42V42${[-32,-16,0,16,32].map(y => `M-29 ${y}H29`).join("")}" stroke="${o.color}" stroke-width="6" fill="none"/>`;
    if (label.includes("bench") || label.includes("chair") || label.includes("box")) return `<rect x="-38" y="-20" width="76" height="40" rx="5" fill="${o.color}"/><path d="M-28 20L-32 39M28 20L32 39" stroke="${o.color}" stroke-width="7"/>`;
    return `<rect x="-30" y="-35" width="60" height="70" rx="6" fill="${o.color}" stroke="#fff" stroke-width="3"/><text y="4" text-anchor="middle" fill="#fff" font-size="10" font-weight="900">${o.label.split(" ").map(x=>x[0]).join("").slice(0,3)}</text>`;
  }
  function textLines(text, maxChars = 24) {
    const words = String(text || "").split(/\s+/).filter(Boolean), lines = [];
    let line = "";
    words.forEach(word => {
      if ((line + " " + word).trim().length > maxChars && line) { lines.push(line); line = word; }
      else line = (line + " " + word).trim();
    });
    if (line) lines.push(line);
    return lines.slice(0, 7);
  }
  function noteIndicatorMarkup(o) {
    return o.note?.text && o.note.showIndicator !== false
      ? `<g class="note-indicator ${o.note.showInExport ? "export-note" : ""}"><circle cx="${Math.max(16, (o.width || 70) / 2)}" cy="${-Math.max(16, (o.height || 70) / 2)}" r="10" fill="#f2c85b" stroke="#14211f" stroke-width="2"/><text x="${Math.max(16, (o.width || 70) / 2)}" y="${-Math.max(16, (o.height || 70) / 2) + 4}" text-anchor="middle" font-size="12" font-weight="900" fill="#14211f">i</text></g>`
      : "";
  }
  function renderObject(o) {
    migrateVisualObject(o);
    const mirrorX = o.mirrorX ?? o.mirror ?? false;
    const flipY = !!o.flipY;
    const g = el("g", {
      "data-id": o.id, class: "object-hit", opacity: o.opacity,
      "data-type": o.type, "data-court-id": o.assignedCourtId || o.courtId || "",
      transform: `translate(${o.x} ${o.y}) rotate(${o.rotation}) scale(${mirrorX ? -o.scale : o.scale} ${flipY ? -o.scale : o.scale})`
    });
    if (isCharacter(o) || o.type === "equipment") {
      const asset = resolveAsset(o);
      const anchor = o.anchor || asset.anchor || { x: .5, y: 1 };
      const shadow = isCharacter(o) && o.showShadow
        ? `<ellipse class="player-shadow" cx="${asset.shadowOffset?.x || 0}" cy="${asset.shadowOffset?.y || 5}" rx="${Math.max(15, o.width * .34)}" ry="${Math.max(5, o.width * .085)}"/>`
        : "";
      g.innerHTML = `${shadow}<rect class="drag-surface" data-drag-surface="raster" x="${-o.width * anchor.x}" y="${-o.height * anchor.y}" width="${o.width}" height="${o.height}"/><image href="${asset.asset}" x="${-o.width * anchor.x}" y="${-o.height * anchor.y}" width="${o.width}" height="${o.height}" preserveAspectRatio="xMidYMid meet" class="visual-asset"/>`;
      g.setAttribute("data-asset-id", asset.id);
    }
    else if (o.type === "text") g.innerHTML = `<rect class="drag-surface" data-drag-surface="text" x="-6" y="-24" width="${o.width}" height="${o.height}"/><rect x="-6" y="-24" width="${o.width}" height="${o.height}" rx="5" fill="white" fill-opacity=".82"/><text x="4" y="0" font-size="18" font-weight="700" fill="${o.color}">${escapeHtml(o.text)}</text>`;
    else if (o.type === "sticky-note") {
      const lines = textLines(o.text, Math.max(12, Math.floor((o.width || 220) / Math.max(7, (o.textSize || 16) * .55))));
      g.innerHTML = `<rect class="drag-surface" data-drag-surface="sticky-note" x="${-o.width / 2}" y="${-o.height / 2}" width="${o.width}" height="${o.height}"/><rect x="${-o.width / 2}" y="${-o.height / 2}" width="${o.width}" height="${o.height}" rx="6" fill="${o.backgroundColor || "#fff4a6"}" stroke="#c7b85e" stroke-width="2"/><path d="M${-o.width / 2 + 10} ${-o.height / 2 + 14}H${o.width / 2 - 10}" stroke="#d9ca70" stroke-width="1"/><text x="${-o.width / 2 + 12}" y="${-o.height / 2 + 34}" font-size="${o.textSize || 16}" font-weight="700" fill="${o.color || "#14211f"}">${lines.map((line, index) => `<tspan x="${-o.width / 2 + 12}" dy="${index ? (o.textSize || 16) + 5 : 0}">${escapeHtml(line)}</tspan>`).join("")}</text>`;
    }
    else if (o.type === "shape") {
      const isCircle = o.label.includes("Circle") || o.label.includes("circle");
      const surface = `<rect class="drag-surface" data-drag-surface="shape" x="${-o.width / 2}" y="${-o.height / 2}" width="${o.width}" height="${o.height}"/>`;
      g.innerHTML = surface + (isCircle ? `<ellipse rx="${o.width / 2}" ry="${o.height / 2}" fill="${o.label.includes("Responsibility") ? o.color : "none"}" fill-opacity=".22" stroke="${o.color}" stroke-width="5"/>`
        : `<rect x="${-o.width / 2}" y="${-o.height / 2}" width="${o.width}" height="${o.height}" fill="${o.color}" fill-opacity=".22" stroke="${o.color}" stroke-width="5"/>`);
    } else if (o.type === "arrow") {
      const dash = o.label.includes("Dashed") ? "12 9" : "none";
      const markerStart = o.label.includes("Double") ? "url(#arrowhead)" : "";
      const d = o.curved ? `M0 0 Q${o.dx / 2} ${-Math.abs(o.dy || 80) - 80} ${o.dx} ${o.dy}` : `M0 0L${o.dx} ${o.dy}`;
      g.innerHTML = `<path data-drag-surface="arrow" d="${d}" fill="none" stroke="transparent" stroke-width="${Math.max(18, (o.thickness || 7) + 12)}" pointer-events="stroke"/><path d="${d}" fill="none" stroke="${o.color}" stroke-width="${o.thickness || 7}" stroke-linecap="round" stroke-dasharray="${dash}" marker-end="url(#arrowhead)" ${markerStart ? `marker-start="${markerStart}"` : ""}/>`;
    }
    g.innerHTML += noteIndicatorMarkup(o);
    if (o.locked) g.setAttribute("data-locked", "true");
    return g;
  }
  function escapeHtml(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

  function renderObjects() {
    objectsLayer.innerHTML = "";
    frame().objects
      .map((object, index) => ({ object, index }))
      .sort((a, b) => (a.object.zIndex ?? a.index) - (b.object.zIndex ?? b.index))
      .forEach(({ object }) => objectsLayer.append(renderObject(object)));
  }
  function transformedPoints(o, points) {
    return points.map(point => window.VPDInteraction.rotatePoint(
      { x: o.x + point.x, y: o.y + point.y },
      o,
      o.rotation || 0
    ));
  }
  function bounds(o) {
    if (o.type === "court") {
      return window.VPDInteraction.boundsFromPoints(
        window.VPDInteraction.rotatedRectCorners(o, o.width, o.height, o.rotation || 0)
      );
    }
    if (o.type === "arrow") {
      return window.VPDInteraction.boundsFromPoints(
        transformedPoints(o, [{ x: 0, y: 0 }, { x: o.dx, y: o.dy }]),
        12
      );
    }
    if (isCharacter(o) || o.type === "equipment") {
      const anchor = o.anchor || resolveAsset(o)?.anchor || { x: .5, y: 1 };
      const mirror = (o.mirrorX ?? o.mirror) ? -1 : 1;
      const left = -o.width * anchor.x * o.scale * mirror;
      const right = o.width * (1 - anchor.x) * o.scale * mirror;
      const vertical = o.flipY ? -1 : 1;
      const top = -o.height * anchor.y * o.scale * vertical;
      const bottom = o.height * (1 - anchor.y) * o.scale * vertical;
      return window.VPDInteraction.boundsFromPoints(transformedPoints(o, [
        { x: left, y: top }, { x: right, y: top },
        { x: right, y: bottom }, { x: left, y: bottom }
      ]));
    }
    const left = o.type === "text" ? -6 * o.scale : -o.width * o.scale / 2;
    const top = o.type === "text" ? -24 * o.scale : -o.height * o.scale / 2;
    const right = o.type === "text" ? (o.width - 6) * o.scale : o.width * o.scale / 2;
    const bottom = o.type === "text" ? (o.height - 24) * o.scale : o.height * o.scale / 2;
    return window.VPDInteraction.boundsFromPoints(transformedPoints(o, [
      { x: left, y: top }, { x: right, y: top },
      { x: right, y: bottom }, { x: left, y: bottom }
    ]));
  }
  function renderSelection(syncProperties = true) {
    selectionLayer.innerHTML = "";
    state.selected.forEach(id => {
      const o = objectById(id); if (!o) return; const b = bounds(o);
      let scalePoint = { x: b.x + b.w, y: b.y + b.h };
      let resizePoints = [
        { x: b.x, y: b.y }, { x: b.x + b.w / 2, y: b.y }, { x: b.x + b.w, y: b.y },
        { x: b.x + b.w, y: b.y + b.h / 2 }, { x: b.x + b.w, y: b.y + b.h },
        { x: b.x + b.w / 2, y: b.y + b.h }, { x: b.x, y: b.y + b.h },
        { x: b.x, y: b.y + b.h / 2 }
      ];
      let rotationPoint = { x: b.x + b.w / 2, y: b.y - 28 };
      let rotationStem = { x: b.x + b.w / 2, y: b.y };
      if (o.type === "court") {
        const corners = window.VPDInteraction.rotatedRectCorners(o, o.width, o.height, o.rotation || 0);
        selectionLayer.append(el("polygon", {
          points: corners.map(point => `${point.x},${point.y}`).join(" "),
          class: "selection-box", "data-select-id": id
        }));
        scalePoint = corners[2];
        resizePoints = [
          corners[0],
          { x: (corners[0].x + corners[1].x) / 2, y: (corners[0].y + corners[1].y) / 2 },
          corners[1],
          { x: (corners[1].x + corners[2].x) / 2, y: (corners[1].y + corners[2].y) / 2 },
          corners[2],
          { x: (corners[2].x + corners[3].x) / 2, y: (corners[2].y + corners[3].y) / 2 },
          corners[3],
          { x: (corners[3].x + corners[0].x) / 2, y: (corners[3].y + corners[0].y) / 2 }
        ];
        const topMiddle = {
          x: (corners[0].x + corners[1].x) / 2,
          y: (corners[0].y + corners[1].y) / 2
        };
        rotationStem = topMiddle;
        rotationPoint = window.VPDInteraction.rotatePoint(
          { x: o.x, y: o.y - o.height / 2 - 28 },
          o,
          o.rotation || 0
        );
      } else {
        selectionLayer.append(el("rect", { x: b.x, y: b.y, width: b.w, height: b.h, class: "selection-box", "data-select-id": id }));
      }
      if (!o.locked && state.selected.length === 1) {
        resizePoints.forEach((point, index) => selectionLayer.append(el("circle", {
          cx: point.x, cy: point.y, r: index % 2 ? 6 : 8,
          class: `selection-handle ${index % 2 ? "midpoint-handle" : "corner-handle"}`,
          "data-handle": "scale", "data-id": id
        })));
        selectionLayer.append(el("line", { x1: rotationStem.x, y1: rotationStem.y, x2: rotationPoint.x, y2: rotationPoint.y, stroke: "#176b62", "stroke-width": 2 }));
        selectionLayer.append(el("circle", { cx: rotationPoint.x, cy: rotationPoint.y, r: 8, class: "rotation-handle", "data-handle": "rotate", "data-id": id }));
      } else if (o.locked && state.selected.length === 1) {
        selectionLayer.append(el("text", { x: b.x + b.w, y: b.y - 10, class: "lock-indicator", "text-anchor": "end" }, "🔒 Locked"));
      }
    });
    if (syncProperties) updateProperties();
  }
  function renderView() {
    viewport.setAttribute("transform", `translate(${state.panX} ${state.panY}) scale(${state.zoom})`);
    $("#zoom-label").textContent = `${Math.round(state.zoom * 100)}%`;
  }
  function frameThumbnail(frameItem) {
    const courts = (frameItem.courts || []).map(court =>
      `<g transform="translate(${court.x} ${court.y}) rotate(${court.rotation || 0})"><rect x="${-court.width / 2 - 35}" y="${-court.height / 2 - 35}" width="${court.width + 70}" height="${court.height + 70}" rx="16" fill="#28645f"/><rect x="${-court.width / 2}" y="${-court.height / 2}" width="${court.width}" height="${court.height}" fill="#e9985d" stroke="#fff" stroke-width="9"/><path d="M0 ${-court.height / 2}V${court.height / 2}M${-court.width / 6} ${-court.height / 2}V${court.height / 2}M${court.width / 6} ${-court.height / 2}V${court.height / 2}" stroke="#fff" stroke-width="7"/></g>`
    ).join("");
    const objects = (frameItem.objects || []).map(object => {
      if (!isCharacter(object) && object.type !== "equipment") return "";
      const asset = resolveAsset(object);
      const anchor = object.anchor || asset.anchor || { x: .5, y: 1 };
      const sx = (object.mirrorX ?? object.mirror) ? -(object.scale || 1) : (object.scale || 1);
      const sy = object.flipY ? -(object.scale || 1) : (object.scale || 1);
      return `<image href="${asset.asset}" x="${-object.width * anchor.x}" y="${-object.height * anchor.y}" width="${object.width}" height="${object.height}" transform="translate(${object.x} ${object.y}) rotate(${object.rotation || 0}) scale(${sx} ${sy})" preserveAspectRatio="xMidYMid meet"/>`;
    }).join("");
    return `<svg class="frame-thumbnail" viewBox="0 0 ${WORKSPACE.width} ${WORKSPACE.height}" aria-hidden="true">${courts}${objects}</svg>`;
  }
  function renderFrames() {
    $("#frames-strip").innerHTML = state.frames.map((f, i) => `<button class="frame-card ${i === state.frameIndex ? "active" : ""}" data-frame="${i}">${frameThumbnail(f)}<small>${i + 1}. ${escapeHtml(f.name)}</small></button>`).join("");
    $("#frame-position").textContent = `Frame ${state.frameIndex + 1} of ${state.frames.length}`;
    $("#frame-name").value = frame().name;
    $$(".frame-card").forEach(b => b.onclick = e => {
      state.frameIndex = +b.dataset.frame; state.selected = []; syncCourtChecks(); renderAll();
    });
  }
  function renderAll() { renderCourt(); renderObjects(); renderSelection(); renderView(); renderFrames(); }

  function updateProperties() {
    const selected = state.selected.map(objectById).filter(Boolean);
    $("#selection-summary").textContent = selected.length ? `${selected.length} object${selected.length > 1 ? "s" : ""} selected` : "Nothing selected";
    $("#properties-empty").classList.toggle("hidden", !!selected.length);
    $("#properties").classList.toggle("hidden", !selected.length);
    if (selected.length !== 1) return;
    const o = selected[0];
    const isCourt = o.type === "court";
    $("#prop-type").value = isCourt ? o.name : o.label;
    $("#prop-team").value = o.team || "A"; $("#prop-rotation").value = Math.round(window.VPDInteraction.normalizeAngle(o.rotation || 0));
    $("#prop-scale").value = isCourt ? 1 : o.scale; $("#prop-opacity").value = o.opacity ?? 1; $("#prop-color").value = o.color || "#176b62";
    $("#prop-x").value = Math.round(o.x); $("#prop-y").value = Math.round(o.y);
    $("#prop-width").value = Math.round(o.width); $("#prop-height").value = Math.round(o.height);
    $("#prop-aspect-lock").checked = o.aspectLocked !== false;
    $("#show-shadow").checked = !!o.showShadow;
    $("#show-shadow-label").classList.toggle("hidden", !isCharacter(o));
    $("#prop-text-label").classList.toggle("hidden", !["text", "sticky-note"].includes(o.type)); $("#prop-text").value = o.text || "";
    $("#sticky-style-options").classList.toggle("hidden", o.type !== "sticky-note");
    $("#prop-bg-color").value = o.backgroundColor || "#fff4a6";
    $("#prop-text-size").value = o.textSize || 16;
    $("#prop-note").value = o.note?.text || "";
    $("#prop-note-indicator").checked = o.note?.showIndicator !== false;
    $("#prop-note-export").checked = !!o.note?.showInExport;
    $("#prop-role").innerHTML = heroRoles.map(x => `<option>${x}</option>`).join(""); $("#prop-role").value = o.role || "Setter";
    fillPoses($("#prop-role").value, o.pose, o.team); $("#lock").textContent = o.locked ? "◉ Unlock" : "⌾ Lock";
    fillCharacterViews(o);
    $("#prop-team").disabled = !isCharacter(o); $("#prop-role").disabled = !isCharacter(o); $("#prop-pose").disabled = !isCharacter(o); $("#prop-character-view").disabled = !isCharacter(o);
    $("#player-options").classList.toggle("hidden", !isCharacter(o));
    $("#character-view-picker").classList.toggle("hidden", !isCharacter(o));
    $("#variant-picker").classList.toggle("hidden", !["player", "equipment", "character"].includes(o.type));
    $("#prop-facing").value = o.facing || (o.mirrorX || o.mirror ? "Left" : "Right");
    $("#object-court-label").classList.toggle("hidden", isCourt);
    $("#prop-court").innerHTML = `<option value="">Unassigned</option>${frame().courts.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join("")}`;
    $("#prop-court").value = o.courtId || "";
    $("#court-object-properties").classList.toggle("hidden", !isCourt);
    $("#prop-court-name").value = isCourt ? o.name : "";
    $("#prop-court-style").value = isCourt ? o.style : "competition";
    $("#prop-court-width").value = isCourt ? Math.round(o.width) : "";
    $("#rotate-court-contents").checked = isCourt ? !!o.rotateContentsWithCourt : false;
    $("#keep-players-upright").checked = isCourt ? o.keepPlayersUpright !== false : true;
    $("#prop-scale").disabled = isCourt;
    $("#prop-opacity").disabled = isCourt;
    $("#prop-color").disabled = isCourt;
    $("#flip-horizontal").classList.toggle("hidden", isCourt);
    $("#flip-vertical").classList.toggle("hidden", isCourt || isCharacter(o));
    $("#reset-size").textContent = isCourt ? "Reset court size" : "Reset size";
    renderVariantPicker(o);
  }
  function availablePlayerAssets(team, role) {
    const roleKey = roleKeys[role] || assetKey(role);
    const assetTeam = roleKey === "coach" ? "Neutral" : (team === "B" ? "B" : "A");
    return assetManifest.filter(asset =>
      asset.category === "player" && asset.role === roleKey
      && asset.team === assetTeam && asset.visualStyle === "professional"
      && isDefaultCharacterViewValue(asset.view || asset.characterView)
    );
  }
  function availablePlayerPoseAssets(team, role) {
    const roleKey = roleKeys[role] || assetKey(role);
    const assetTeam = roleKey === "coach" ? "Neutral" : (team === "B" ? "B" : "A");
    return assetManifest.filter(asset =>
      asset.category === "player" && asset.role === roleKey
      && asset.team === assetTeam && asset.visualStyle === "professional"
    );
  }
  function fillPoses(role, value, team = state.team) {
    const assets = availablePlayerPoseAssets(team, role);
    const poses = assets.length ? [...new Set(assets.map(asset => asset.pose))] : (roles[role] || ["Default"]);
    const groups = professionalPoseGroups[roleKeys[role] || assetKey(role)] || {};
    const grouped = new Set();
    const html = Object.entries(groups).map(([label, groupPoses]) => {
      const visible = groupPoses.filter(pose => poses.includes(pose));
      visible.forEach(pose => grouped.add(pose));
      return visible.length
        ? `<optgroup label="${escapeHtml(label)}">${visible.map(pose => `<option>${escapeHtml(pose)}</option>`).join("")}</optgroup>`
        : "";
    }).join("");
    const remaining = poses.filter(pose => !grouped.has(pose));
    $("#prop-pose").innerHTML = html + remaining.map(pose => `<option>${escapeHtml(pose)}</option>`).join("");
    $("#prop-pose").value = poses.includes(value) ? value : poses[0];
  }
  function fillCharacterViews(o) {
    const assets = isCharacter(o) ? characterViewAssets(o.team, o.role, o.pose) : [];
    const views = assets.map(asset => normalizeCharacterView(asset.view || asset.characterView));
    if (!views.includes(normalizeCharacterView(o.characterView))) o.characterView = views[0] || defaultCharacterView;
    $("#prop-character-view").innerHTML = assets.map(asset => {
      const view = normalizeCharacterView(asset.view || asset.characterView);
      return `<option value="${escapeHtml(view)}">${escapeHtml(view)}</option>`;
    }).join("");
    $("#prop-character-view").value = normalizeCharacterView(o.characterView);
    renderCharacterViewPicker(o, assets);
  }
  function propertyChange(key, value) {
    if (!state.selected.length) return; snapshot();
    state.selected.map(objectById).filter(Boolean).forEach(o => {
      if (key === "rotation" && o.type === "court") rotateCourtTo(o, value);
      else o[key] = key === "rotation" ? window.VPDInteraction.normalizeAngle(value) : value;
      if (key === "team") o.color = teamColors[value];
      if (["team", "role", "pose", "characterView"].includes(key) && isCharacter(o)) {
        o.visualStyle = "professional";
        o.characterView = normalizeCharacterView(o.characterView);
        const views = availableCharacterViews(o.team, o.role, o.pose);
        if (key !== "characterView" && !views.includes(o.characterView)) {
          o.characterView = views[0] || defaultCharacterView;
        }
        const asset = playerAsset(o.team, o.role, o.pose, o.characterView);
        if (!asset) {
          o.characterView = defaultCharacterView;
          return toast(`${value} view is not available for this pose yet`);
        }
        o.assetId = asset.id;
        o.characterId = asset.characterId || o.characterId;
        if (key === "pose" || key === "role") {
          const height = key === "role" ? asset.defaultHeight : (o.height || asset.defaultHeight);
          o.height = height;
          o.width = Math.max(1, height * asset.defaultWidth / asset.defaultHeight);
          o.anchor = deep(asset.anchor);
          o.flipY = false;
        }
        delete o.isProfessionalFallback;
      }
      if (key === "facing") {
        o.mirrorX = value === "Left";
        o.mirror = o.mirrorX;
      }
      if (key === "courtId") o.assignedCourtId = value;
    });
    renderAll();
  }

  function renderVariantPicker(o) {
    const picker = $("#variant-picker");
    let variants = [];
    if (isCharacter(o)) {
      variants = availablePlayerAssets(o.team, o.role);
    } else if (o.type === "equipment" && /cart/i.test(o.label)) {
      variants = assetManifest.filter(a => a.equipmentType === "ball_cart");
    } else if (o.type === "equipment" && /ball/i.test(o.label)) {
      variants = assetManifest.filter(a => a.category === "ball");
    } else if (o.type === "equipment") {
      variants = [resolveAsset(o)];
    }
    picker.innerHTML = variants.map(asset => `<button type="button" class="variant-tile ${asset.id === o.assetId ? "active" : ""}" data-asset-choice="${asset.id}" title="${escapeHtml(asset.pose || asset.variant || asset.id)}"><img src="${asset.thumbnail}" alt="" loading="lazy"><small>${escapeHtml(asset.pose || asset.variant || asset.id)}</small></button>`).join("");
    $$("[data-asset-choice]", picker).forEach(button => button.onclick = () => {
      const asset = assetIndex.get(button.dataset.assetChoice);
      if (!asset) return;
      snapshot();
      const selected = objectById(state.selected[0]);
      selected.assetId = asset.id;
      if (isCharacter(selected)) {
        selected.pose = asset.pose;
        selected.characterView = normalizeCharacterView(asset.view || asset.characterView);
        selected.visualStyle = asset.visualStyle;
        selected.characterId = asset.characterId || selected.characterId;
        selected.width = Math.max(1, selected.height * asset.defaultWidth / asset.defaultHeight);
        selected.anchor = deep(asset.anchor);
        selected.flipY = false;
        selected.isProfessionalFallback = false;
      }
      else selected.label = asset.variant || selected.label;
      renderAll();
    });
  }
  function renderCharacterViewPicker(o, assets = characterViewAssets(o.team, o.role, o.pose)) {
    const picker = $("#character-view-picker");
    if (!isCharacter(o)) {
      picker.innerHTML = "";
      return;
    }
    picker.innerHTML = assets.map(asset => {
      const view = normalizeCharacterView(asset.view || asset.characterView);
      return `<button type="button" class="variant-tile ${view === normalizeCharacterView(o.characterView) ? "active" : ""}" data-character-view="${escapeHtml(view)}" title="${escapeHtml(view)}"><img src="${asset.thumbnail}" alt="" loading="lazy"><small>${escapeHtml(view)}</small></button>`;
    }).join("");
    $$("[data-character-view]", picker).forEach(button => button.onclick = () => propertyChange("characterView", button.dataset.characterView));
  }

  function point(evt) {
    return window.VPDInteraction.clientToWorkspace(svg, viewport, evt.clientX, evt.clientY);
  }
  svg.addEventListener("pointerdown", e => {
    if (e.button !== 0) return;
    const p = point(e);
    if (state.drawing) { snapshot(); interaction = { mode: "draw", start: p, tool: state.drawing.tool }; svg.setPointerCapture(e.pointerId); return; }
    const handle = e.target.closest("[data-handle]");
    if (handle) {
      e.preventDefault(); e.stopPropagation();
      const o = objectById(handle.dataset.id); snapshot(); interaction = {
        mode: handle.dataset.handle, start: p, object: o, scale: o.scale || 1,
        width: o.width, height: o.height, rotation: o.rotation || 0,
        startDistance: Math.max(1, Math.hypot(p.x - o.x, p.y - o.y)),
        startAngle: Math.atan2(p.y - o.y, p.x - o.x) * 180 / Math.PI,
        contentState: o.type === "court" ? captureCourtContents(o) : null
      };
      svg.setPointerCapture(e.pointerId); return;
    }
    const target = e.target.closest(".object-hit");
    if (target) {
      e.preventDefault(); e.stopPropagation();
      const o = objectById(target.dataset.id);
      if (e.shiftKey) state.selected = state.selected.includes(o.id) ? state.selected.filter(x => x !== o.id) : [...state.selected, o.id];
      else if (!state.selected.includes(o.id)) state.selected = [o.id];
      if (o.type === "court") syncCourtChecks();
      renderSelection();
      if (window.VPDInteraction.canMove(o)) {
        snapshot();
        const moveIds = new Set(state.selected);
        state.selected.map(courtById).filter(Boolean).forEach(court => frame().objects.filter(item => item.courtId === court.id).forEach(item => moveIds.add(item.id)));
        interaction = { mode: "move", start: p, originals: [...moveIds].map(id => ({ id, x: objectById(id).x, y: objectById(id).y })).filter(v => !objectById(v.id).locked) };
        svg.setPointerCapture(e.pointerId);
        svg.classList.add("dragging");
      }
    } else { state.selected = []; renderSelection(); interaction = { mode: "pan", startClient: { x: e.clientX, y: e.clientY }, panX: state.panX, panY: state.panY }; svg.setPointerCapture(e.pointerId); }
  });
  svg.addEventListener("pointermove", e => {
    if (!interaction) return; const p = point(e);
    if (interaction.mode === "move") {
      const d = window.VPDInteraction.delta(interaction.start, p);
      interaction.originals.forEach(v => { const o = objectById(v.id); o.x = v.x + d.x; o.y = v.y + d.y; });
    }
    if (interaction.mode === "scale") {
      if (interaction.object.type === "court") {
        const diagonalRatio = Math.hypot(.5, .25);
        interaction.object.width = clamp(Math.hypot(p.x - interaction.object.x, p.y - interaction.object.y) / diagonalRatio, 320, 1400);
        interaction.object.height = interaction.object.width / COURT_RATIO;
      } else {
        const distance = Math.max(1, Math.hypot(p.x - interaction.object.x, p.y - interaction.object.y));
        interaction.object.scale = clamp(interaction.scale * distance / interaction.startDistance, .25, 4);
      }
    }
    if (interaction.mode === "rotate") {
      const currentAngle = Math.atan2(p.y - interaction.object.y, p.x - interaction.object.x) * 180 / Math.PI;
      const target = window.VPDInteraction.snapAngle(interaction.rotation + currentAngle - interaction.startAngle, e.shiftKey);
      if (interaction.object.type === "court") {
        rotateCourtTo(interaction.object, target, {
          baselineRotation: interaction.rotation,
          contentState: interaction.contentState
        });
      } else {
        interaction.object.rotation = target;
      }
    }
    if (interaction.mode === "pan") { state.panX = interaction.panX + e.clientX - interaction.startClient.x; state.panY = interaction.panY + e.clientY - interaction.startClient.y; renderView(); return; }
    if (interaction.mode === "draw") {
      selectionLayer.innerHTML = `<path d="M${interaction.start.x} ${interaction.start.y}L${p.x} ${p.y}" stroke="#f2c85b" stroke-width="6" fill="none" marker-end="url(#arrowhead)"/>`; return;
    }
    renderObjects(); renderSelection();
  });
  function finishPointer(e) {
    if (interaction?.mode === "draw" && e.type === "pointerup") {
      const p = point(e), tool = interaction.tool;
      const obj = defaultObject({ type: "arrow", label: tool, x: interaction.start.x, y: interaction.start.y, dx: p.x - interaction.start.x, dy: p.y - interaction.start.y, curved: tool.includes("Curved") || tool.includes("trajectory"), thickness: tool.includes("Attack") ? 9 : 6, color: tool.includes("Ball") || tool.includes("trajectory") ? "#2668a5" : teamColors[state.team] });
      frame().objects.push(obj); state.selected = [obj.id]; state.drawing = null; svg.classList.remove("drawing-cursor");
    }
    interaction = null;
    svg.classList.remove("dragging");
    if (svg.hasPointerCapture?.(e.pointerId)) svg.releasePointerCapture(e.pointerId);
    renderAll();
  }
  svg.addEventListener("pointerup", finishPointer);
  svg.addEventListener("pointercancel", finishPointer);
  svg.addEventListener("lostpointercapture", () => { interaction = null; svg.classList.remove("dragging"); });
  svg.addEventListener("wheel", e => {
    e.preventDefault(); const old = state.zoom; state.zoom = clamp(state.zoom * (e.deltaY > 0 ? .9 : 1.1), .18, 3);
    const rect = svg.getBoundingClientRect(), x = (e.clientX - rect.left) * WORKSPACE.width / rect.width, y = (e.clientY - rect.top) * WORKSPACE.height / rect.height;
    state.panX = x - (x - state.panX) * state.zoom / old; state.panY = y - (y - state.panY) * state.zoom / old; renderView();
  }, { passive: false });

  function duplicateSelected() {
    if (!state.selected.length) return; snapshot();
    if (selectedCourt()) { state.history.pop(); return duplicateCourt(false); }
    const copies = state.selected.map(objectById).filter(o => o?.type !== "court").map(o => ({ ...deep(o), id: uid(), x: o.x + 24, y: o.y + 24 }));
    frame().objects.push(...copies); state.selected = copies.map(o => o.id); renderAll();
  }
  function deleteSelected() {
    if (!state.selected.length) return;
    if (selectedCourt()) return deleteCourt();
    snapshot(); frame().objects = frame().objects.filter(o => !state.selected.includes(o.id) || o.locked); state.selected = []; renderAll();
  }
  function syncCourtChecks() {
    const court = selectedCourt() || frame().courts[0];
    $("#show-attack").checked = court.settings.showAttackLines; $("#show-zones").checked = court.settings.showZoneLabels;
    $("#show-grid").checked = court.settings.showGrid; $("#show-antennas").checked = court.settings.showAntennas;
    $("#show-net").checked = court.settings.showNet;
  }

  function workspaceBounds(mode = "workspace", court = null) {
    let items = [];
    if (mode === "selected" && court) items = [court, ...frame().objects.filter(o => o.courtId === court.id)];
    else if (mode === "courts") items = [...frame().courts, ...frame().objects.filter(o => o.courtId && courtById(o.courtId))];
    else items = [...frame().courts, ...frame().objects];
    if (!items.length) return { x: 0, y: 0, w: WORKSPACE.width, h: WORKSPACE.height };
    const boxes = items.map(bounds);
    const minX = Math.min(...boxes.map(b => b.x)), minY = Math.min(...boxes.map(b => b.y));
    const maxX = Math.max(...boxes.map(b => b.x + b.w)), maxY = Math.max(...boxes.map(b => b.y + b.h));
    const pad = 70;
    return { x: minX - pad, y: minY - pad, w: maxX - minX + pad * 2, h: maxY - minY + pad * 2 };
  }
  function fitAll() {
    const box = workspaceBounds("workspace");
    state.zoom = clamp(Math.min(WORKSPACE.width / box.w, WORKSPACE.height / box.h) * .86, .18, 2.6);
    state.panX = (WORKSPACE.width / 2) - (box.x + box.w / 2) * state.zoom;
    state.panY = (WORKSPACE.height / 2) - (box.y + box.h / 2) * state.zoom;
    renderView();
  }

  function metadataFromForm() {
    const ids = ["name","objective","secondary","players","duration","repetitions","courts","intensity","skill","tags","equipment","starting","sequence","rotation","scoring","coaching","mistakes","notes"];
    const m = {}; ids.forEach(id => m[id] = $(`#meta-${id}`).value);
    m.tags = m.tags.split(",").map(x => x.trim()).filter(Boolean); return m;
  }
  function fillMetadataForm() {
    const m = state.metadata; Object.entries(m).forEach(([k, v]) => { const n = $(`#meta-${k}`); if (n) n.value = Array.isArray(v) ? v.join(", ") : v; });
  }
  function markNotesDirty() {
    $("#notes-save-status").textContent = "Unsaved changes";
    $("#save-state").textContent = "Unsaved";
    clearTimeout(markNotesDirty.timer);
    markNotesDirty.timer = setTimeout(() => {
      try { localStorage.setItem("vpd-notes-draft", JSON.stringify({ drillId: state.id, notes: state.notes, at: Date.now() })); } catch {}
      $("#notes-save-status").textContent = "Draft saved locally";
    }, 500);
  }
  function renderStructuredNotes() {
    const sectionHtml = (key, title, checklist) => {
      const items = state.notes[key] || [];
      return `<div class="note-items" data-note-list="${key}">${items.map((item, index) => `<div class="note-item" data-note-item="${item.id}"><span class="note-order">${index + 1}</span>${checklist ? `<input type="checkbox" data-note-complete="${key}:${item.id}" ${item.completed ? "checked" : ""} aria-label="Complete item">` : ""}<input value="${escapeHtml(item.text)}" data-note-text="${key}:${item.id}" aria-label="${title} item"><button type="button" data-note-up="${key}:${item.id}" ${index === 0 ? "disabled" : ""}>Up</button><button type="button" data-note-down="${key}:${item.id}" ${index === items.length - 1 ? "disabled" : ""}>Down</button><button type="button" class="danger" data-note-delete="${key}:${item.id}">Delete</button></div>`).join("")}</div><button type="button" class="add-note-item" data-note-add="${key}">Add ${title.slice(0, -1).toLowerCase()}</button>`;
    };
    structuredNoteSections.forEach(([key, title, checklist]) => {
      const target = key === "coachingPoints" ? $("#structured-notes") : $(`#note-section-${key}`);
      if (target) target.innerHTML = sectionHtml(key, title, checklist);
    });
    $$("[data-note-add]").forEach(b => b.onclick = () => { const list = state.notes[b.dataset.noteAdd]; list.push(defaultNoteItem("", list.length)); renderStructuredNotes(); markNotesDirty(); });
    $$("[data-note-text]").forEach(input => input.oninput = () => { const [key, id] = input.dataset.noteText.split(":"); const item = state.notes[key].find(x => x.id === id); if (item) item.text = input.value; markNotesDirty(); });
    $$("[data-note-complete]").forEach(input => input.onchange = () => { const [key, id] = input.dataset.noteComplete.split(":"); const item = state.notes[key].find(x => x.id === id); if (item) item.completed = input.checked; markNotesDirty(); });
    $$("[data-note-delete]").forEach(b => b.onclick = () => { const [key, id] = b.dataset.noteDelete.split(":"); state.notes[key] = state.notes[key].filter(x => x.id !== id).map((x, i) => ({ ...x, order: i })); renderStructuredNotes(); markNotesDirty(); });
    $$("[data-note-up],[data-note-down]").forEach(b => b.onclick = () => { const attr = b.dataset.noteUp ? "noteUp" : "noteDown"; const [key, id] = b.dataset[attr].split(":"); const list = state.notes[key]; const i = list.findIndex(x => x.id === id); const j = attr === "noteUp" ? i - 1 : i + 1; if (i < 0 || j < 0 || j >= list.length) return; [list[i], list[j]] = [list[j], list[i]]; list.forEach((x, index) => x.order = index); renderStructuredNotes(); markNotesDirty(); });
  }
  function renderNotesPanel() {
    state.notes = normalizeDrillNotes(state.notes, state.metadata);
    $("#note-description").value = state.notes.description;
    $("#note-equipmentNotes").value = state.notes.equipmentNotes;
    $("#note-generalComments").value = state.notes.generalComments;
    $("#note-postTrainingObservations").value = state.notes.postTrainingObservations;
    renderStructuredNotes();
  }
  function bindNotesPanel() {
    [["note-description","description"],["note-equipmentNotes","equipmentNotes"],["note-generalComments","generalComments"],["note-postTrainingObservations","postTrainingObservations"]].forEach(([id, key]) => {
      $(`#${id}`).oninput = e => { state.notes[key] = e.target.value; markNotesDirty(); };
    });
  }
  function setNotesCollapsed(collapsed, persist = true) {
    const shell = $(".editor-shell");
    if (!shell) return;
    shell.classList.toggle("notes-collapsed", collapsed);
    $("#coaching-notes-panel")?.setAttribute("aria-expanded", collapsed ? "false" : "true");
    if (persist) localStorage.setItem("vpd-notes-collapsed", collapsed ? "1" : "0");
  }
  function restoreNotesPanelState() {
    setNotesCollapsed(localStorage.getItem("vpd-notes-collapsed") === "1", false);
  }
  function practiceNotesFromForm() {
    const notes = defaultPracticeNotes();
    Object.keys(notes).forEach(key => { const n = $(`#practice-note-${key}`); if (n) notes[key] = n.value; });
    return notes;
  }
  function fillPracticeNotes(notes) {
    const data = normalizePracticeNotes(notes);
    Object.entries(data).forEach(([key, value]) => { const n = $(`#practice-note-${key}`); if (n) n.value = value; });
  }
  function drillPayload(asNew = false) {
    const now = new Date().toISOString();
    frame().court = legacyCourtSettings(frame().courts[0]);
    return { id: asNew || !state.id ? uid() : state.id, schema_version: 4, metadata: state.metadata, notes: normalizeDrillNotes(state.notes, state.metadata), created_at: asNew || !state.created_at ? now : state.created_at, modified_at: now, court: frame().court, frames: state.frames, thumbnail: null };
  }
  async function saveDrill(asNew = false) {
    if (!state.metadata.name?.trim() || state.metadata.name === "Untitled drill") { fillMetadataForm(); $("#drill-dialog").showModal(); toast("Give the drill a name before saving"); return; }
    const payload = drillPayload(asNew), exists = !!state.id && !asNew;
    $("#save-state").textContent = "Saving…";
    const res = await fetch(exists ? `/api/drills/${state.id}` : "/api/drills", { method: exists ? "PUT" : "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    if (!res.ok) { toast("Could not save drill"); $("#save-state").textContent = "Save failed"; return; }
    const saved = await res.json(); state.id = saved.id; state.created_at = saved.created_at; state.notes = normalizeDrillNotes(saved.notes, saved.metadata); $("#save-state").textContent = "Saved"; $("#notes-save-status").textContent = "Saved with drill"; localStorage.removeItem("vpd-notes-draft"); toast("Drill saved"); await refreshData();
  }
  async function loadDrill(id) {
    const res = await fetch(`/api/drills/${id}`); if (!res.ok) return toast("Drill not found");
    const d = await res.json();
    const migratedFrames = (d.frames?.length ? d.frames : [emptyFrame()]).map(migrateFrame);
    state = { ...state, id: d.id, metadata: d.metadata, notes: normalizeDrillNotes(d.notes, d.metadata), created_at: d.created_at, frames: migratedFrames, frameIndex: 0, selected: [], history: [], future: [], zoom: .72, panX: 0, panY: 0 };
    syncCourtChecks(); showView("editor"); renderNotesPanel(); renderAll(); setTimeout(fitAll, 0); toast(`Opened ${d.metadata.name}`);
  }
  function newDrill() {
    if (!confirm("Start a new drill? Unsaved changes will be lost.")) return;
    state = { ...state, id: null, metadata: { name: "Untitled drill", objective: "", tags: [] }, notes: defaultDrillNotes(), created_at: null, frames: [emptyFrame()], frameIndex: 0, selected: [], history: [], future: [] };
    syncCourtChecks(); renderNotesPanel(); renderAll(); setTimeout(fitAll, 0); toast("New drill ready");
  }

  async function refreshData() {
    const [drills, practices] = await Promise.all([fetch("/api/drills").then(r => r.json()), fetch("/api/practices").then(r => r.json())]);
    cachedDrills = drills; renderLibrary(); renderPractices(practices);
    $("#stat-drills").textContent = drills.length; $("#stat-practices").textContent = practices.length;
    $("#stat-frames").textContent = drills.reduce((n, d) => n + (d.frames?.length || 0), 0);
  }
  function renderLibrary() {
    const q = ($("#drill-search")?.value || "").toLowerCase(), filter = $("#drill-filter")?.value || "";
    const list = cachedDrills.filter(d => {
      const notes = normalizeDrillNotes(d.notes, d.metadata);
      const structured = structuredNoteSections.flatMap(([key]) => notes[key].map(item => item.text)).join(" ");
      const hay = `${d.metadata.name} ${d.metadata.objective} ${(d.metadata.tags || []).join(" ")} ${notes.description} ${notes.generalComments} ${structured}`.toLowerCase();
      return hay.includes(q) && (!filter || hay.includes(filter.toLowerCase()));
    });
    $("#drill-grid").innerHTML = list.length ? list.map(d => `<article class="drill-card" data-card="${d.id}"><div class="drill-thumb"><div></div></div><div class="card-eyebrow"><span>${d.metadata.players || "—"} players · ${d.metadata.duration || "—"} min</span><span>${new Date(d.modified_at).toLocaleDateString()}</span></div><h3>${escapeHtml(d.metadata.name)}</h3><p>${escapeHtml(d.metadata.objective || "No objective added")}</p><div class="tag-list">${(d.metadata.tags || []).slice(0,4).map(t=>`<span class="tag">${escapeHtml(t)}</span>`).join("")}</div><div class="card-actions"><button data-open="${d.id}">Open</button><button data-add="${d.id}">Add to practice</button><button data-copy="${d.id}">Duplicate</button><button class="danger" data-delete="${d.id}">Delete</button></div></article>`).join("") : `<div class="empty-library"><h3>No drills found</h3><p>Create a visual drill and save it to begin your library.</p></div>`;
    $$("[data-open]").forEach(b => b.onclick = () => loadDrill(b.dataset.open));
    $$("[data-copy]").forEach(b => b.onclick = async () => { await fetch(`/api/drills/${b.dataset.copy}/duplicate`, { method: "POST" }); refreshData(); toast("Drill duplicated"); });
    $$("[data-delete]").forEach(b => b.onclick = async () => { if (confirm("Delete this drill permanently?")) { await fetch(`/api/drills/${b.dataset.delete}`, { method: "DELETE" }); refreshData(); } });
    $$("[data-add]").forEach(b => b.onclick = () => addToPractice(b.dataset.add));
  }

  function addToPractice(id) {
    const d = cachedDrills.find(x => x.id === id); if (!d) return;
    currentPractice.items.push({ id: uid(), drill_id: id, name: d.metadata.name, duration: +(d.metadata.duration || 10), section: "Technical work" });
    renderPracticeItems(); showView("practices"); toast("Drill added to practice");
  }
  function renderPracticeItems() {
    $("#practice-items").innerHTML = currentPractice.items.length ? currentPractice.items.map((x, i) => `<div class="practice-item" data-item="${i}"><div class="item-order"><button data-move-up="${i}" ${i === 0 ? "disabled" : ""} aria-label="Move drill up">Up</button><button data-move-down="${i}" ${i === currentPractice.items.length - 1 ? "disabled" : ""} aria-label="Move drill down">Down</button></div><div><b>${escapeHtml(x.name)}</b><small>${escapeHtml(x.section)}</small></div><label class="minutes"><span>Minutes</span><input type="number" min="1" value="${x.duration}" data-duration="${i}" aria-label="Minutes"></label><button data-remove-item="${i}" aria-label="Remove drill">Remove</button></div>`).join("") : `<div class="empty-library"><p>No drills yet. Add drills from the library.</p></div>`;
    $$("[data-duration]").forEach(n => n.onchange = () => { currentPractice.items[+n.dataset.duration].duration = +n.value; renderPracticeItems(); });
    $$("[data-remove-item]").forEach(b => b.onclick = () => { currentPractice.items.splice(+b.dataset.removeItem, 1); renderPracticeItems(); });
    $$("[data-move-up]").forEach(b => b.onclick = () => { const i=+b.dataset.moveUp; if(i>0){[currentPractice.items[i-1],currentPractice.items[i]]=[currentPractice.items[i],currentPractice.items[i-1]];renderPracticeItems();} });
    $$("[data-move-down]").forEach(b => b.onclick = () => { const i=+b.dataset.moveDown; if(i<currentPractice.items.length-1){[currentPractice.items[i+1],currentPractice.items[i]]=[currentPractice.items[i],currentPractice.items[i+1]];renderPracticeItems();} });
    $("#practice-total").textContent = `${currentPractice.items.reduce((n, x) => n + +x.duration, 0)} min`;
  }
  async function savePractice() {
    const name = $("#practice-name").value.trim(); if (!name) return toast("Practice name is required");
    const practiceNotes = practiceNotesFromForm();
    const now = new Date().toISOString(), payload = { id: currentPractice.id || uid(), schema_version: 2, name, date: $("#practice-date").value || null, team: $("#practice-team").value, main_objective: $("#practice-objective").value, notes: $("#practice-notes").value, practiceNotes, sections: [{ name: "Practice plan", drills: currentPractice.items }], created_at: currentPractice.created_at || now, modified_at: now };
    const res = await fetch(currentPractice.id ? `/api/practices/${currentPractice.id}` : "/api/practices", { method: currentPractice.id ? "PUT" : "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const saved = await res.json(); currentPractice.id = saved.id; currentPractice.created_at = saved.created_at; currentPractice.practiceNotes = normalizePracticeNotes(saved.practiceNotes, saved); fillPracticeNotes(currentPractice.practiceNotes); toast("Practice saved"); refreshData();
  }
  function renderPractices(practices) {
    const query = ($("#practice-search")?.value || "").toLowerCase();
    const visible = practices.filter(p => {
      const notes = normalizePracticeNotes(p.practiceNotes, p);
      return `${p.name} ${p.main_objective} ${notes.mainObjective} ${notes.technicalObjective} ${notes.tacticalObjective} ${notes.physicalObjective} ${notes.importantNotes} ${notes.generalComments}`.toLowerCase().includes(query);
    });
    $("#practice-grid").innerHTML = visible.length ? visible.map(p => `<article class="practice-card"><div class="card-eyebrow"><span>${p.date || "No date"}</span><span>${p.team || ""}</span></div><h3>${escapeHtml(p.name)}</h3><p>${escapeHtml(p.main_objective || normalizePracticeNotes(p.practiceNotes, p).mainObjective || "No objective")}</p><div class="card-actions"><button data-open-practice="${p.id}">Open</button><button data-copy-practice="${p.id}">Duplicate</button><button class="danger" data-delete-practice="${p.id}">Delete</button></div></article>`).join("") : `<div class="empty-library"><p>No saved practices yet.</p></div>`;
    $$("[data-open-practice]").forEach(b => b.onclick = async () => { const p = await fetch(`/api/practices/${b.dataset.openPractice}`).then(r => r.json()); currentPractice = { id: p.id, created_at: p.created_at, items: p.sections?.[0]?.drills || [], practiceNotes: normalizePracticeNotes(p.practiceNotes, p) }; $("#practice-name").value=p.name; $("#practice-date").value=p.date||""; $("#practice-team").value=p.team; $("#practice-objective").value=p.main_objective; $("#practice-notes").value=p.notes; fillPracticeNotes(currentPractice.practiceNotes); renderPracticeItems(); scrollTo(0,0); });
    $$("[data-copy-practice]").forEach(b => b.onclick = async()=>{await fetch(`/api/practices/${b.dataset.copyPractice}/duplicate`,{method:"POST"});refreshData();toast("Practice duplicated")});
    $$("[data-delete-practice]").forEach(b => b.onclick = async()=>{if(confirm("Delete this practice?")){await fetch(`/api/practices/${b.dataset.deletePractice}`,{method:"DELETE"});refreshData()}});
  }

  async function waitForVisualAssets() {
    const urls = [...new Set(frame().objects.map(resolveAsset).filter(Boolean).map(asset => asset.asset))];
    await Promise.all(urls.map(url => new Promise((resolve, reject) => {
      const image = new Image();
      image.onload = async () => {
        try { if (image.decode) await image.decode(); resolve(); } catch (error) { reject(error); }
      };
      image.onerror = () => reject(new Error(`Could not load export asset: ${url}`));
      image.src = url;
    })));
  }

  async function renderedFrameDataUrl(mode = "all") {
    const court = selectedCourt();
    if (mode === "selected" && !court) throw new Error("Select a court to export");
    await waitForVisualAssets();
    const previousSelection = [...state.selected]; state.selected = []; renderSelection();
    const clone = svg.cloneNode(true), cloneViewport = clone.querySelector("#viewport");
    clone.querySelector("#selection-layer").innerHTML = "";
    clone.querySelectorAll(".note-indicator:not(.export-note)").forEach(node => node.remove());
    let box = { x: 0, y: 0, w: WORKSPACE.width, h: WORKSPACE.height };
    if (mode !== "viewport") {
      cloneViewport.removeAttribute("transform");
      box = workspaceBounds(mode === "selected" ? "selected" : mode === "all" ? "courts" : "workspace", court);
    }
    if (mode === "selected") {
      clone.querySelectorAll("[data-court-id]").forEach(node => { if (node.getAttribute("data-court-id") !== court.id) node.remove(); });
    }
    clone.setAttribute("viewBox", `${box.x} ${box.y} ${box.w} ${box.h}`);
    clone.setAttribute("width", Math.round(box.w)); clone.setAttribute("height", Math.round(box.h));
    $("#save-state").textContent = "Preparing assets…";
    const images = [...clone.querySelectorAll("image.visual-asset")];
    await Promise.all(images.map(async image => {
      const href = image.getAttribute("href");
      if (!href || href.startsWith("data:")) return;
      const response = await fetch(href).then(response => {
        if (!response.ok) throw new Error(`Missing export asset: ${href}`);
        return response;
      });
      if (/\.svg(?:$|\?)/i.test(href)) {
        const source = await response.text();
        image.setAttribute("href", `data:image/svg+xml;charset=utf-8,${encodeURIComponent(source)}`);
      } else {
        const blob = await response.blob();
        const dataUrl = await new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = reject; reader.readAsDataURL(blob); });
        image.setAttribute("href", dataUrl);
      }
    }));
    const data = new XMLSerializer().serializeToString(clone);
    const blob = new Blob([data], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    const img = new Image();
    await new Promise((resolve, reject) => { img.onload = resolve; img.onerror = reject; img.src = url; });
    const canvas = document.createElement("canvas");
    canvas.width = Math.min(2200, Math.max(900, Math.round(box.w * 1.5)));
    canvas.height = Math.round(canvas.width / (box.w / box.h));
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "#dfe4df"; ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    URL.revokeObjectURL(url);
    state.selected = previousSelection; renderSelection();
    return canvas.toDataURL("image/png");
  }

  async function exportPng() {
    const mode = $("#export-mode").value;
    let href = "";
    try {
      $("#save-state").textContent = "Preparing PNG...";
      href = await renderedFrameDataUrl(mode);
    } catch (error) {
      $("#save-state").textContent = "Ready";
      return toast(error.message || "Could not export PNG");
    }
    const a = document.createElement("a");
    a.download = `${(state.metadata.name || "drill").replace(/[^a-z0-9]+/gi, "-").toLowerCase()}-${mode}-frame-${state.frameIndex + 1}.png`;
    a.href = href;
    a.click();
    $("#save-state").textContent = "Ready";
    toast(`PNG exported: ${mode}`);
  }

  async function captureFrameImages(sourceFrames, onlyIndex = null) {
    const original = { frames: state.frames, frameIndex: state.frameIndex, selected: [...state.selected] };
    const targets = onlyIndex === null ? sourceFrames.map((item, index) => [item, index]) : [[sourceFrames[onlyIndex], onlyIndex]];
    const results = [];
    try {
      state.selected = [];
      for (const [item, index] of targets) {
        state.frames = [migrateFrame(deep(item))];
        state.frameIndex = 0;
        renderAll();
        results.push({ id: item.id || "", name: item.name || `Frame ${index + 1}`, image: await renderedFrameDataUrl("all") });
      }
    } finally {
      state.frames = original.frames;
      state.frameIndex = original.frameIndex;
      state.selected = original.selected;
      renderAll();
    }
    return results;
  }

  async function exportPowerPoint() {
    const scope = $("#pptx-export-scope").value;
    $("#save-state").textContent = "Preparing PowerPoint...";
    try {
      let endpoint = "/api/exports/powerpoint/drill";
      let payload;
      if (scope === "practice") {
        const name = $("#practice-name").value.trim() || currentPractice.name || "Practice Plan";
        const sections = [{ name: "Practice plan", drills: currentPractice.items }];
        const practice = { id: currentPractice.id || uid(), name, date: $("#practice-date").value || null, team: $("#practice-team").value, main_objective: $("#practice-objective").value, notes: $("#practice-notes").value, practiceNotes: practiceNotesFromForm(), sections };
        const drills = [];
        for (const item of currentPractice.items) {
          const drill = cachedDrills.find(d => d.id === item.drill_id);
          if (!drill) continue;
          drills.push({ drill, frames: await captureFrameImages(drill.frames || []) });
        }
        if (!drills.length) throw new Error("Add at least one saved drill to the practice first");
        endpoint = "/api/exports/powerpoint/practice";
        payload = { practice, drills };
      } else {
        payload = { drill: drillPayload(false), frames: await captureFrameImages(state.frames, scope === "frame" ? state.frameIndex : null) };
      }
      const response = await fetch(endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "PowerPoint export failed");
      $("#save-state").textContent = "Ready";
      toast(`PowerPoint exported: ${result.path}`);
    } catch (error) {
      $("#save-state").textContent = "Ready";
      toast(error.message || "PowerPoint export failed");
    }
  }

  function noteSectionHtml(title, value, hideEmpty) {
    const empty = Array.isArray(value) ? !value.length : !String(value || "").trim();
    if (empty && hideEmpty) return "";
    if (Array.isArray(value)) return `<section><h3>${title}</h3><ol>${value.map(item => `<li>${escapeHtml(item.text)}</li>`).join("")}</ol></section>`;
    return `<section><h3>${title}</h3><p>${escapeHtml(value || "")}</p></section>`;
  }
  function drillNotesPrintHtml(hideEmpty = true) {
    const notes = normalizeDrillNotes(state.notes, state.metadata);
    return `<article class="print-notes"><h2>Coaching Notes</h2>
      ${noteSectionHtml("Drill Description", notes.description, hideEmpty)}
      ${noteSectionHtml("Coaching Points", notes.coachingPoints, hideEmpty)}
      ${noteSectionHtml("Common Mistakes", notes.commonMistakes, hideEmpty)}
      ${noteSectionHtml("Progressions", notes.progressions, hideEmpty)}
      ${noteSectionHtml("Regressions", notes.regressions, hideEmpty)}
      ${noteSectionHtml("Variations", notes.variations, hideEmpty)}
      ${noteSectionHtml("Equipment Notes", notes.equipmentNotes, hideEmpty)}
      ${noteSectionHtml("General Comments", notes.generalComments, hideEmpty)}
    </article>`;
  }
  function printDrill() {
    const mode = $("#print-mode").value;
    const pages = $("#print-pages"); pages.innerHTML = "";
    const targets = mode === "all" ? [null] : frame().courts;
    targets.forEach(court => {
      const clone = svg.cloneNode(true);
      clone.querySelector("#viewport").removeAttribute("transform");
      const box = court ? workspaceBounds("selected", court) : workspaceBounds("courts");
      if (court) clone.querySelectorAll("[data-court-id]").forEach(node => { if (node.getAttribute("data-court-id") !== court.id) node.remove(); });
      clone.querySelector("#selection-layer").innerHTML = "";
      clone.querySelectorAll(".note-indicator:not(.export-note)").forEach(node => node.remove());
      clone.setAttribute("viewBox", `${box.x} ${box.y} ${box.w} ${box.h}`);
      clone.removeAttribute("width"); clone.removeAttribute("height");
      const page = document.createElement("section"); page.className = "print-page"; page.append(clone); pages.append(page);
    });
    if ($("#print-include-notes").checked) {
      const notesPage = document.createElement("section");
      notesPage.className = "print-page print-notes-page";
      notesPage.innerHTML = drillNotesPrintHtml($("#print-hide-empty").checked);
      pages.append(notesPage);
    }
    document.body.dataset.printMode = mode;
    window.print();
  }

  function renderAssetLibrary() {
    const grid = $("#asset-grid");
    if (!grid) return;
    const query = ($("#asset-search")?.value || "").toLowerCase();
    const category = $("#asset-category")?.value || "";
    const style = $("#asset-style")?.value || "";
    const team = $("#asset-team")?.value || "";
    const role = $("#asset-role")?.value || "";
    const view = $("#asset-view")?.value || "";
    const assets = assetLibraryManifest.filter(asset => {
      if (asset.category === "fallback" || asset.visualStyle === "legacy_vector") return false;
      const assetView = normalizeCharacterView(asset.view || asset.characterView);
      const haystack = `${asset.id} ${asset.role || ""} ${asset.pose || ""} ${assetView} ${asset.variant || ""} ${asset.equipmentType || ""} ${asset.team || ""}`.toLowerCase();
      return haystack.includes(query) && (!category || asset.category === category) && (!style || asset.visualStyle === style) && (!team || asset.team === team) && (!role || asset.role === role) && (!view || assetView === view);
    });
    const visibleAssets = assets;
    $("#asset-summary").textContent = `${visibleAssets.length} shown · ${assets.length} matching assets`;
    renderAssetDiagnostics(visibleAssets.length);
    if (!visibleAssets.length) {
      grid.innerHTML = `<div class="asset-empty-state"><h2>No assets match the current filters.</h2><p>Valid assets are still loaded. Reset the filters or show all released Professional assets.</p><div><button class="btn ghost" data-asset-reset-filters>Reset Filters</button><button class="btn primary" data-asset-show-professional>Show All Professional Assets</button></div></div>`;
      $$("[data-asset-reset-filters]").forEach(button => button.onclick = resetAssetFilters);
      $$("[data-asset-show-professional]").forEach(button => button.onclick = showAllProfessionalAssets);
      return;
    }
    const selectable = asset => asset.category === "player" && asset.visualStyle === "professional";
    grid.innerHTML = visibleAssets.map(asset => `<article class="asset-card ${selectedFigureAssetIds.has(asset.id) ? "selected" : ""}" data-review-asset="${asset.id}"><img src="${asset.thumbnail}" alt="${escapeHtml(asset.pose || asset.variant || asset.id)}" loading="lazy" decoding="async" onerror="this.closest('.asset-card')?.classList.add('asset-card-error');this.removeAttribute('src')"><b>${escapeHtml(asset.pose || asset.variant || asset.id)}</b><small>${escapeHtml([asset.team, asset.role || asset.equipmentType || asset.category].filter(Boolean).join(" · "))}</small>${selectable(asset) ? `<label class="asset-select"><input type="checkbox" data-figure-select="${asset.id}" ${selectedFigureAssetIds.has(asset.id) ? "checked" : ""}> Select</label>` : ""}</article>`).join("");
    $$("[data-review-asset]").forEach(card => {
      const assetId = card.dataset.reviewAsset;
      card.dataset.assetId = assetId;
      const button = document.createElement("button");
      button.type = "button";
      button.className = "asset-place";
      button.dataset.assetPlace = assetId;
      button.textContent = "Add to Court";
      button.onclick = () => addAssetLibraryObject(assetIndex.get(assetId));
      card.insertBefore(button, $(".asset-select", card));
    });
    $$("[data-figure-select]").forEach(input => input.onchange = () => {
      if (input.checked) selectedFigureAssetIds.add(input.dataset.figureSelect);
      else selectedFigureAssetIds.delete(input.dataset.figureSelect);
      input.closest(".asset-card")?.classList.toggle("selected", input.checked);
    });
  }
  function renderAssetDiagnostics(currentFilterResult = 0) {
    const node = $("#asset-diagnostics");
    if (!node) return;
    const skipped = assetDiagnostics.skippedEntries || 0;
    const invalid = assetDiagnostics.invalidEntries || 0;
    const filtered = assetDiagnostics.filteredEntries || 0;
    const missingThumbs = assetDiagnostics.missingThumbnails || 0;
    const missingRuntime = assetDiagnostics.missingRuntimeFiles || 0;
    const loaded = assetDiagnostics.loadedAssets || assetDiagnostics.professionalAssetsLoaded || 0;
    const released = assetDiagnostics.releasedAssets || assetDiagnostics.professionalAssetsReleased || 0;
    const hidden = assetDiagnostics.hiddenAssets || assetDiagnostics.professionalAssetsHidden || 0;
    node.innerHTML = `<details><summary>Developer Diagnostics</summary><p>Loaded assets: ${loaded} · Released assets: ${released} · Hidden assets: ${hidden} · Skipped assets: ${skipped} · Current filter result: ${currentFilterResult}</p><p>Professional assets loaded: ${assetDiagnostics.professionalAssetsLoaded || 0} · Professional assets released: ${assetDiagnostics.professionalAssetsReleased || 0} · Professional assets hidden: ${assetDiagnostics.professionalAssetsHidden || 0} · 45° Back loaded: ${assetDiagnostics.back45AssetsLoaded || 0} · 45° Back released: ${assetDiagnostics.back45AssetsReleased || 0} · 45° Back hidden: ${assetDiagnostics.back45AssetsHidden || 0} · Invalid: ${invalid} · Filtered: ${filtered} · Missing thumbnails: ${missingThumbs} · Missing runtime files: ${missingRuntime}</p><pre>${escapeHtml((assetDiagnostics.skippedAssets || []).slice(0, 80).map(item => `${item.id}: ${item.reason}`).join("\n") || "No skipped assets.")}</pre></details>`;
  }
  function resetAssetFilters() {
    $("#asset-search").value = "";
    $("#asset-category").value = "";
    $("#asset-style").value = "professional";
    $("#asset-team").value = "";
    $("#asset-role").value = "";
    $("#asset-view").value = "";
    renderAssetLibrary();
  }
  function showAllProfessionalAssets() {
    resetAssetFilters();
  }
  function openPlayerFigureExportDialog() {
    $("#player-figure-export-result").classList.add("hidden");
    $("#player-figure-export-path").textContent = "";
    $("#player-figure-export-dialog").showModal();
  }
  function playerFigureExportPayload() {
    const selection = $('input[name="player-figure-selection"]:checked')?.value || "all";
    const format = $('input[name="player-figure-format"]:checked')?.value || "pptx";
    const payload = { format, mode: selection === "all" ? "all" : selection === "selected" ? "selected" : "role" };
    if (payload.mode === "role") payload.role = selection;
    if (payload.mode === "selected") payload.assetIds = [...selectedFigureAssetIds];
    return payload;
  }
  async function exportPlayerFigures() {
    const payload = playerFigureExportPayload();
    if (payload.mode === "selected" && !payload.assetIds.length) return toast("Select one or more professional player figures first");
    $("#save-state").textContent = "Exporting figures...";
    try {
      const response = await fetch("/api/exports/player-figures", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Player figure export failed");
      $("#save-state").textContent = "Ready";
      $("#player-figure-export-result").classList.remove("hidden");
      $("#player-figure-export-path").textContent = result.folder;
      $("#open-player-figure-folder").dataset.folder = result.folder;
      toast(`Player figures exported: ${result.folder}`);
    } catch (error) {
      $("#save-state").textContent = "Ready";
      toast(error.message || "Player figure export failed");
    }
  }
  function showView(name) {
    $$(".view").forEach(v => v.classList.toggle("active", v.id === `view-${name}`));
    $$("#main-nav button").forEach(b => b.classList.toggle("active", b.dataset.view === name));
    if (name === "editor") setTimeout(() => renderAll(), 0);
    if (name === "library" || name === "dashboard" || name === "practices") refreshData();
    if (name === "assets") renderAssetLibrary();
  }

  function bind() {
    $$("[data-view]").forEach(b => b.onclick = () => showView(b.dataset.view));
    $$("[data-right-tab]").forEach(b => b.onclick = () => {
      const tab = b.dataset.rightTab;
      $$("[data-right-tab]").forEach(x => x.classList.toggle("active", x === b));
      $$(".right-tab-panel").forEach(panel => panel.classList.toggle("active", panel.id === `right-tab-${tab}`));
      $("#right-panel-title").textContent = tab === "notes" ? "Coaching Notes" : tab === "info" ? "Drill Info" : "Properties";
    });
    $$("[data-practice-tab]").forEach(b => b.onclick = () => {
      const tab = b.dataset.practiceTab;
      $$("[data-practice-tab]").forEach(x => x.classList.toggle("active", x === b));
      $$(".practice-tab-panel").forEach(panel => panel.classList.toggle("active", panel.id === `practice-tab-${tab}`));
    });
    $("#open-drill-info").onclick = () => { fillMetadataForm(); $("#drill-dialog").showModal(); };
    $("#collapse-notes-panel").onclick = () => setNotesCollapsed(true);
    $("#expand-notes-panel").onclick = () => setNotesCollapsed(false);
    bindNotesPanel();
    $("#new-drill").onclick = newDrill; $("#save-drill").onclick = () => saveDrill(false);
    $("#undo").onclick = undo; $("#redo").onclick = redo; $("#zoom-in").onclick=()=>{state.zoom=clamp(state.zoom+.1,.18,3);renderView()}; $("#zoom-out").onclick=()=>{state.zoom=clamp(state.zoom-.1,.18,3);renderView()};
    $("#fit-view").onclick = fitAll; $("#reset-view").onclick=()=>{state.zoom=1;state.panX=0;state.panY=0;renderView()};
    $("#drill-info-btn").onclick = () => { fillMetadataForm(); $("#drill-dialog").showModal(); };
    $("#apply-meta").onclick = e => { e.preventDefault(); const m=metadataFromForm(); if(!m.name.trim())return toast("Drill name is required");state.metadata=m;$("#drill-dialog").close();toast("Drill details applied") };
    $("#export-png").onclick=exportPng; $("#export-pptx").onclick=exportPowerPoint; $("#print-drill").onclick=printDrill;
    $("#add-court").onclick=()=>addCourt();
    $("#duplicate-court").onclick=()=>duplicateCourt(false);
    $("#duplicate-court-contents").onclick=()=>duplicateCourt(true);
    $("#delete-court").onclick=deleteCourt;
    $("#lock-court").onclick=()=>{const c=selectedCourt();if(!c)return toast("Select a court first");propertyChange("locked",!c.locked)};
    $("#arrange-courts").onclick=()=>arrangeCourts($("#court-template").value);
    $("#duplicate").onclick=duplicateSelected; $("#delete-object").onclick=deleteSelected;
    $("#flip-horizontal").onclick=()=>{const o=objectById(state.selected[0]);if(!o)return;propertyChange("facing",(o.mirrorX??o.mirror)?"Right":"Left")};
    $("#flip-vertical").onclick=()=>{const o=objectById(state.selected[0]);if(!o||isCharacter(o))return;propertyChange("flipY",!o.flipY)};
    $("#show-shadow").onchange=e=>propertyChange("showShadow",e.target.checked);
    $("#reset-size").onclick=()=>{const o=objectById(state.selected[0]);if(!o)return;snapshot();if(o.type==="court"){o.width=780;o.height=390}else{const asset=resolveAsset(o);o.width=asset.defaultWidth;o.height=asset.defaultHeight;o.scale=1}renderAll()};
    $("#lock").onclick=()=>propertyChange("locked",!objectById(state.selected[0])?.locked);
    $("#bring-front").onclick=()=>{snapshot();const courtsMode=!!selectedCourt(),list=courtsMode?frame().courts:frame().objects,selected=list.filter(o=>state.selected.includes(o.id)),result=list.filter(o=>!state.selected.includes(o.id)).concat(selected);if(courtsMode)frame().courts=result;else{const top=Math.max(0,...list.map(o=>o.zIndex||0))+1;selected.forEach((o,index)=>o.zIndex=top+index);frame().objects=result}renderAll()};
    $("#send-back").onclick=()=>{snapshot();const courtsMode=!!selectedCourt(),list=courtsMode?frame().courts:frame().objects,selected=list.filter(o=>state.selected.includes(o.id)),result=selected.concat(list.filter(o=>!state.selected.includes(o.id)));if(courtsMode)frame().courts=result;else{const back=Math.min(0,...list.map(o=>o.zIndex||0))-selected.length;selected.forEach((o,index)=>o.zIndex=back+index);frame().objects=result}renderAll()};
    [["prop-team","team"],["prop-facing","facing"],["prop-character-view","characterView"],["prop-scale","scale"],["prop-opacity","opacity"],["prop-color","color"],["prop-pose","pose"],["prop-bg-color","backgroundColor"],["prop-text-size","textSize"]].forEach(([id,key])=> $(`#${id}`).onchange=e=>propertyChange(key,["scale","opacity","textSize"].includes(key)?+e.target.value:e.target.value));
    $("#prop-rotation").onfocus=()=>snapshot();
    $("#prop-rotation").oninput=e=>{
      const o=objectById(state.selected[0]);if(!o)return;
      if(o.type==="court")rotateCourtTo(o,+e.target.value);
      else o.rotation=window.VPDInteraction.normalizeAngle(+e.target.value);
      renderCourt();renderObjects();renderSelection(false);
    };
    $("#prop-rotation").onchange=()=>renderAll();
    [["prop-x","x"],["prop-y","y"]].forEach(([id,key])=>$(`#${id}`).onchange=e=>propertyChange(key,+e.target.value));
    $("#prop-aspect-lock").onchange=e=>propertyChange("aspectLocked",e.target.checked);
    [["prop-width","width"],["prop-height","height"]].forEach(([id,key])=>$(`#${id}`).onchange=e=>{
      const o=objectById(state.selected[0]);if(!o)return;snapshot();
      const next=clamp(+e.target.value,12,key==="width"?1400:900);
      if(o.type==="court"){o.width=key==="width"?next:next*COURT_RATIO;o.height=o.width/COURT_RATIO}
      else if(o.aspectLocked!==false){const ratio=o.width/Math.max(1,o.height);if(key==="width"){o.width=next;o.height=next/ratio}else{o.height=next;o.width=next*ratio}}
      else o[key]=next;
      renderAll();
    });
    $("#prop-text").onfocus=()=>snapshot();
    $("#prop-text").oninput=e=>{const o=objectById(state.selected[0]);if(["text","sticky-note"].includes(o?.type)){o.text=e.target.value;renderObjects()}};
    $("#prop-text").onblur=e=>{if(!e.target.value.trim()){const o=objectById(state.selected[0]);if(o?.type==="text"){o.text="Instruction";e.target.value=o.text;renderObjects()}}};
    $("#prop-note").onfocus=()=>snapshot();
    $("#prop-note").oninput=e=>{const o=objectById(state.selected[0]);if(!o)return;o.note=normalizeObjectNote(o.note);o.note.text=e.target.value;renderObjects();};
    $("#prop-note-indicator").onchange=e=>{const o=objectById(state.selected[0]);if(!o)return;propertyChange("note", {...normalizeObjectNote(o.note), showIndicator:e.target.checked});};
    $("#prop-note-export").onchange=e=>{const o=objectById(state.selected[0]);if(!o)return;propertyChange("note", {...normalizeObjectNote(o.note), showInExport:e.target.checked});};
    $("#prop-role").onchange=e=>{snapshot();const o=objectById(state.selected[0]);o.role=e.target.value;o.pose=heroDefaults[o.role];o.team=o.role==="Coach"?"Neutral":(o.team==="Neutral"?"A":o.team);o.characterView=normalizeCharacterView(o.characterView);const asset=playerAsset(o.team,o.role,o.pose,o.characterView);o.assetId=asset.id;o.visualStyle="professional";o.characterId=asset.characterId||o.characterId;delete o.isProfessionalFallback;renderAll()};
    $("#prop-court").onchange=e=>propertyChange("courtId",e.target.value||null);
    $("#prop-court-name").onchange=e=>{const c=selectedCourt();if(!c)return;snapshot();c.name=e.target.value.trim()||c.name;renderAll()};
    $("#prop-court-style").onchange=e=>propertyChange("style",e.target.value);
    $("#prop-court-width").onchange=e=>{const c=selectedCourt();if(!c)return;snapshot();c.width=clamp(+e.target.value,320,1400);c.height=c.width/COURT_RATIO;renderAll()};
    $("#rotate-court-left").onclick=()=>rotateSelectedCourtBy(-90);
    $("#rotate-court-right").onclick=()=>rotateSelectedCourtBy(90);
    $("#reset-court-rotation").onclick=()=>{const c=selectedCourt();if(!c||c.locked)return;snapshot();rotateCourtTo(c,0);renderAll()};
    $("#rotate-court-contents").onchange=e=>propertyChange("rotateContentsWithCourt",e.target.checked);
    $("#keep-players-upright").onchange=e=>propertyChange("keepPlayersUpright",e.target.checked);
    [["show-attack","showAttackLines"],["show-zones","showZoneLabels"],["show-grid","showGrid"],["show-antennas","showAntennas"],["show-net","showNet"]].forEach(([id,key])=> $(`#${id}`).onchange=e=>{const c=selectedCourt()||frame().courts[0];snapshot();c.settings[key]=e.target.checked;frame().court=legacyCourtSettings(frame().courts[0]);renderCourt()});
    $("#add-frame").onclick=()=>{snapshot();state.frames.push(emptyFrame(`Frame ${state.frames.length+1}`));state.frameIndex=state.frames.length-1;state.selected=[];syncCourtChecks();renderAll()};
    $("#duplicate-frame").onclick=()=>{snapshot();const c=deep(frame());c.id=uid();c.name+=` Copy`;const courtIds=new Map();c.courts.forEach(court=>{const old=court.id;court.id=uid();courtIds.set(old,court.id)});c.objects.forEach(o=>{o.id=uid();o.courtId=courtIds.get(o.assignedCourtId||o.courtId)||null;o.assignedCourtId=o.courtId});state.frames.splice(state.frameIndex+1,0,c);state.frameIndex++;state.selected=[];syncCourtChecks();renderAll()};
    $("#rename-frame").onclick=()=>{const name=$("#frame-name").value.trim();if(!name)return toast("Frame name cannot be empty");snapshot();frame().name=name;renderFrames()};
    $("#delete-frame").onclick=()=>{if(state.frames.length===1)return toast("A drill needs at least one frame");snapshot();state.frames.splice(state.frameIndex,1);state.frameIndex=Math.min(state.frameIndex,state.frames.length-1);state.selected=[];syncCourtChecks();renderAll()};
    $("#move-frame-left").onclick=()=>{const i=state.frameIndex;if(i===0)return;snapshot();[state.frames[i-1],state.frames[i]]=[state.frames[i],state.frames[i-1]];state.frameIndex--;renderAll()};
    $("#move-frame-right").onclick=()=>{const i=state.frameIndex;if(i===state.frames.length-1)return;snapshot();[state.frames[i+1],state.frames[i]]=[state.frames[i],state.frames[i+1]];state.frameIndex++;renderAll()};
    $("#prev-frame").onclick=()=>{state.frameIndex=Math.max(0,state.frameIndex-1);state.selected=[];syncCourtChecks();renderAll()}; $("#next-frame").onclick=()=>{state.frameIndex=Math.min(state.frames.length-1,state.frameIndex+1);state.selected=[];syncCourtChecks();renderAll()};
    $("#drill-search").oninput=renderLibrary; $("#drill-filter").onchange=renderLibrary; $("#practice-search").oninput=()=>refreshData(); $("#save-practice").onclick=savePractice;
    $("#library-new").onclick=()=>{showView("editor");newDrill()};
    $("#new-practice").onclick=()=>{currentPractice={id:null,items:[],practiceNotes:defaultPracticeNotes()};$("#practice-form").reset();fillPracticeNotes(currentPractice.practiceNotes);renderPracticeItems()};
    $("#asset-search").oninput=renderAssetLibrary; $("#asset-category").onchange=renderAssetLibrary; $("#asset-style").onchange=renderAssetLibrary; $("#asset-team").onchange=renderAssetLibrary; $("#asset-role").onchange=renderAssetLibrary; $("#asset-view").onchange=renderAssetLibrary;
    $("#export-player-figures").onclick=openPlayerFigureExportDialog;
    $("#run-player-figure-export").onclick=e=>{e.preventDefault();exportPlayerFigures()};
    $("#open-player-figure-folder").onclick=e=>{const folder=e.currentTarget.dataset.folder;if(folder)window.open(`file:///${folder.replaceAll("\\\\","/")}`,"_blank")};
    document.addEventListener("keydown", e => {
      if (["INPUT","TEXTAREA","SELECT"].includes(e.target.tagName)) return;
      if (e.altKey && (e.key === "ArrowLeft" || e.key === "ArrowRight") && selectedCourt()) {
        e.preventDefault();
        rotateSelectedCourtBy(e.key === "ArrowLeft" ? -90 : 90);
        return;
      }
      if (e.key==="Escape"){state.selected=[];state.drawing=null;svg.classList.remove("drawing-cursor");renderSelection()}
      if ((e.key==="Delete"||e.key==="Backspace")&&state.selected.length){e.preventDefault();deleteSelected()}
      if (e.ctrlKey&&e.key.toLowerCase()==="d"){e.preventDefault();duplicateSelected()}
      if (e.ctrlKey&&e.key.toLowerCase()==="c") state.clipboard=state.selected.map(objectById).filter(Boolean).map(deep);
      if (e.ctrlKey&&e.key.toLowerCase()==="v"&&state.clipboard.length){snapshot();const copies=state.clipboard.map(o=>({...o,id:uid(),x:o.x+24,y:o.y+24}));frame().courts.push(...copies.filter(o=>o.type==="court"));frame().objects.push(...copies.filter(o=>o.type!=="court"));state.selected=copies.map(o=>o.id);renderAll()}
      if (e.ctrlKey&&e.key.toLowerCase()==="z"){e.preventDefault();undo()} if(e.ctrlKey&&e.key.toLowerCase()==="y"){e.preventDefault();redo()}
      if (["ArrowLeft","ArrowRight","ArrowUp","ArrowDown"].includes(e.key)&&state.selected.length){e.preventDefault();snapshot();const d=e.shiftKey?10:1,moveIds=new Set(state.selected);state.selected.map(courtById).filter(Boolean).forEach(c=>frame().objects.filter(o=>o.courtId===c.id).forEach(o=>moveIds.add(o.id)));[...moveIds].map(objectById).filter(o=>o&&!o.locked).forEach(o=>{if(e.key==="ArrowLeft")o.x-=d;if(e.key==="ArrowRight")o.x+=d;if(e.key==="ArrowUp")o.y-=d;if(e.key==="ArrowDown")o.y+=d});renderAll()}
    });
  }
  async function init() {
    await loadAssetManifest();
    state.frames = state.frames.map(migrateFrame);
    buildPalette(); bind(); restoreNotesPanelState(); syncCourtChecks(); renderNotesPanel(); fillPracticeNotes(currentPractice.practiceNotes); renderAll(); setTimeout(fitAll, 0); renderPracticeItems(); refreshData();
    if ($("#asset-summary")) $("#asset-summary").textContent = "Asset Library loads when opened";
    if ($("#asset-grid")) $("#asset-grid").innerHTML = "";
  }
  init().catch(error => { console.error(error); toast("Visual assets could not be loaded"); });
})();
