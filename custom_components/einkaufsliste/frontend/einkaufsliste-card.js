/*
 * Einkaufsliste-Karte für Home Assistant
 * Zeigt eine Bring!-Liste (Integration „einkaufsliste“) als hübsche Kacheln an.
 * https://github.com/domiundergroun/Einkaufsliste
 */
const CARD_VERSION = "1.0.0";

const ACCENTS = {
  bring: ["#ee524f", "#d63d3a"],
  smaragd: ["#1fae7a", "#13895e"],
  ozean: ["#2f80ed", "#1c5fc0"],
  violett: ["#8b5cf6", "#6d3fe0"],
  orange: ["#f2994a", "#e07b22"],
  graphit: ["#4b5563", "#2f3742"],
  theme: ["var(--primary-color)", "var(--primary-color)"],
};

const EMOJI = [
  [["milch", "hafermilch", "sojamilch"], "🥛"], [["käse", "kaese", "parmesan", "mozzarella", "gouda", "feta"], "🧀"],
  [["brötchen", "baguette", "semmel"], "🥖"], [["brot", "toast"], "🍞"], [["butter"], "🧈"], [["eier", "ei"], "🥚"],
  [["äpfel", "apfel"], "🍎"], [["banane"], "🍌"], [["birne"], "🍐"], [["orange", "mandarine"], "🍊"], [["zitrone", "limette"], "🍋"],
  [["trauben", "weintrauben"], "🍇"], [["erdbeer"], "🍓"], [["kirsche"], "🍒"], [["pfirsich", "nektarine"], "🍑"], [["ananas"], "🍍"],
  [["melone"], "🍉"], [["kiwi"], "🥝"], [["heidelbeer", "blaubeer", "beeren"], "🫐"], [["tomate"], "🍅"], [["gurke"], "🥒"],
  [["karotte", "möhre", "moehre"], "🥕"], [["kartoffel"], "🥔"], [["zwiebel"], "🧅"], [["knoblauch"], "🧄"], [["paprika"], "🫑"],
  [["salat", "spinat", "rucola", "kohl"], "🥬"], [["brokkoli"], "🥦"], [["pilze", "champignon"], "🍄"], [["mais"], "🌽"],
  [["avocado"], "🥑"], [["aubergine"], "🍆"], [["chili"], "🌶️"], [["hähnchen", "haehnchen", "huhn", "chicken", "pute"], "🍗"],
  [["hack", "fleisch", "steak", "rind", "schnitzel"], "🥩"], [["wurst", "würstchen", "salami"], "🌭"], [["schinken", "speck", "bacon"], "🥓"],
  [["lachs", "fisch", "thunfisch", "forelle"], "🐟"], [["garnele", "shrimp", "krabbe"], "🦐"], [["nudeln", "pasta", "spaghetti", "penne", "lasagne"], "🍝"],
  [["reis"], "🍚"], [["mehl"], "🌾"], [["zucker"], "🍬"], [["salz"], "🧂"], [["öl", "olivenöl", "oliven"], "🫒"], [["honig"], "🍯"],
  [["kaffee", "espresso", "kaffeebohnen"], "☕"], [["tee"], "🍵"], [["wasser", "sprudel", "mineralwasser"], "💧"], [["saft"], "🧃"],
  [["bier"], "🍺"], [["wein", "rotwein", "weißwein"], "🍷"], [["sekt", "prosecco", "champagner"], "🍾"], [["cola", "limo", "limonade", "fanta"], "🥤"],
  [["joghurt", "quark", "müsli", "muesli", "cornflakes", "haferflocken"], "🥣"], [["sahne", "schmand"], "🥛"], [["eis", "eiscreme"], "🍨"],
  [["schokolade", "schoko"], "🍫"], [["kekse", "cookies", "plätzchen"], "🍪"], [["chips", "popcorn", "snacks"], "🍿"], [["pizza"], "🍕"],
  [["kuchen", "torte"], "🍰"], [["nüsse", "nuesse", "erdnüsse", "mandeln"], "🥜"], [["marmelade", "konfitüre", "nutella"], "🍯"],
  [["klopapier", "toilettenpapier", "küchenrolle", "kuechenrolle", "taschentücher"], "🧻"], [["seife", "handseife"], "🧼"],
  [["shampoo", "duschgel", "spülung", "creme", "deo"], "🧴"], [["zahnpasta", "zahnbürste", "zahncreme"], "🪥"],
  [["waschmittel", "weichspüler"], "🧺"], [["spülmittel", "schwamm", "spülmaschinentabs", "tabs"], "🧽"], [["müllbeutel", "muellbeutel"], "🗑️"],
  [["batterien", "batterie"], "🔋"], [["windeln"], "👶"], [["katzenfutter", "katzenstreu"], "🐱"], [["hundefutter"], "🐶"],
  [["blumen"], "💐"], [["kerzen", "teelichter"], "🕯️"], [["medikamente", "tabletten", "pflaster"], "💊"], [["gewürz", "pfeffer", "paprikapulver"], "🧂"],
];

const failedImages = new Set();

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const slugify = (name) =>
  name
    .toLowerCase()
    .replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue").replace(/ß/g, "ss")
    .replace(/[éèê]/g, "e").replace(/[áàâ]/g, "a")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");

function emojiFor(name) {
  const n = name.toLowerCase().trim();
  const words = n.split(/[\s,\-/]+/);
  for (const [keys, emoji] of EMOJI) {
    for (const k of keys) {
      if (n === k || words.includes(k)) return emoji;
    }
  }
  for (const [keys, emoji] of EMOJI) {
    for (const k of keys) {
      if (k.length >= 4 && n.includes(k)) return emoji;
    }
  }
  return null;
}

function hueFor(name) {
  let h = 0;
  for (const ch of name) h = (h * 31 + ch.charCodeAt(0)) % 360;
  return h;
}

function fallbackIcon(name) {
  const emoji = emojiFor(name);
  if (emoji) return `<span class="emoji">${emoji}</span>`;
  const letter = esc((name.trim()[0] || "?").toUpperCase());
  return `<span class="letter" style="--h:${hueFor(name)}">${letter}</span>`;
}

function iconHtml(name, useImages) {
  const slug = slugify(name);
  if (useImages && slug && !failedImages.has(slug)) {
    return `<img loading="lazy" alt="" data-slug="${slug}" src="https://web.getbring.com/assets/images/items/${slug}.png">`;
  }
  return fallbackIcon(name);
}

const ICONS = {
  cart: `<svg viewBox="0 0 24 24"><path fill="currentColor" d="M17 18a2 2 0 0 1 2 2 2 2 0 0 1-2 2 2 2 0 0 1-2-2c0-1.11.89-2 2-2M1 2h3.27l.94 2H20a1 1 0 0 1 1 1c0 .17-.05.34-.12.5l-3.58 6.47c-.34.61-1 1.03-1.75 1.03H8.1l-.9 1.63-.03.12a.25.25 0 0 0 .25.25H19v2H7a2 2 0 0 1-2-2c0-.35.09-.68.24-.96l1.36-2.45L3 4H1V2m6 16a2 2 0 0 1 2 2 2 2 0 0 1-2 2 2 2 0 0 1-2-2c0-1.11.89-2 2-2Z"/></svg>`,
  refresh: `<svg viewBox="0 0 24 24"><path fill="currentColor" d="M17.65 6.35A7.958 7.958 0 0 0 12 4a8 8 0 0 0-8 8 8 8 0 0 0 8 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0 1 12 18a6 6 0 0 1-6-6 6 6 0 0 1 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35Z"/></svg>`,
  plus: `<svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2Z"/></svg>`,
  check: `<svg viewBox="0 0 24 24"><path fill="currentColor" d="M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17Z"/></svg>`,
  chevron: `<svg viewBox="0 0 24 24"><path fill="currentColor" d="M7.41 8.58 12 13.17l4.59-4.59L18 10l-6 6-6-6 1.41-1.42Z"/></svg>`,
  party: `<svg viewBox="0 0 64 64"><circle cx="32" cy="32" r="30" fill="var(--acc)" opacity=".12"/><path d="M20 33l8 8 16-17" fill="none" stroke="var(--acc)" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
};

const STYLE = `
:host { --acc: ${ACCENTS.bring[0]}; --acc2: ${ACCENTS.bring[1]}; }
ha-card { position: relative; overflow: hidden; border-radius: var(--ha-card-border-radius, 20px); }
.wrap { padding: 18px 18px 16px; }
header { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.badge { width: 44px; height: 44px; border-radius: 14px; display: grid; place-items: center; color: #fff;
  background: linear-gradient(135deg, var(--acc), var(--acc2)); box-shadow: 0 6px 16px -6px var(--acc); flex: none; }
.badge svg { width: 24px; height: 24px; }
.titles { flex: 1; min-width: 0; }
.title { font-size: 1.25rem; font-weight: 700; letter-spacing: -0.01em; color: var(--primary-text-color);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sub { font-size: 0.85rem; color: var(--secondary-text-color); margin-top: 1px; }
.sub b { color: var(--acc); font-weight: 600; }
.icon-btn { border: 0; background: transparent; color: var(--secondary-text-color); width: 38px; height: 38px;
  border-radius: 12px; display: grid; place-items: center; cursor: pointer; transition: background .2s, color .2s; }
.icon-btn:hover { background: var(--secondary-background-color); color: var(--primary-text-color); }
.icon-btn svg { width: 22px; height: 22px; }
.icon-btn.spin svg { animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

form.add { display: flex; gap: 8px; align-items: center; background: var(--secondary-background-color);
  border-radius: 16px; padding: 5px 5px 5px 14px; border: 1.5px solid transparent; transition: border-color .2s, box-shadow .2s; }
form.add:focus-within { border-color: var(--acc); box-shadow: 0 0 0 4px color-mix(in srgb, var(--acc) 15%, transparent); }
form.add input { flex: 1; min-width: 0; border: 0; outline: 0; background: transparent; font: inherit; font-size: 0.98rem;
  color: var(--primary-text-color); padding: 8px 0; }
form.add input::placeholder { color: var(--secondary-text-color); opacity: .8; }
.add-btn { border: 0; width: 38px; height: 38px; border-radius: 12px; color: #fff; cursor: pointer; display: grid; place-items: center;
  background: linear-gradient(135deg, var(--acc), var(--acc2)); transition: transform .15s, opacity .2s; flex: none; }
.add-btn:active { transform: scale(.92); }
.add-btn svg { width: 22px; height: 22px; }
.suggest { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.suggest:empty { display: none; }
.chip { border: 0; cursor: pointer; font: inherit; font-size: .82rem; padding: 5px 11px; border-radius: 999px;
  background: color-mix(in srgb, var(--acc) 12%, transparent); color: var(--acc); font-weight: 600; }
.chip:hover { background: color-mix(in srgb, var(--acc) 20%, transparent); }

.items { margin-top: 14px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(var(--tile, 92px), 1fr)); gap: 10px; }
.tile { position: relative; border: 0; cursor: pointer; font: inherit; color: #fff; text-align: center;
  aspect-ratio: 1 / 1; border-radius: 18px; padding: 8px 6px; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 3px; background: linear-gradient(150deg, var(--acc), var(--acc2));
  box-shadow: 0 6px 14px -8px var(--acc); transition: transform .18s ease, box-shadow .18s ease, opacity .3s;
  -webkit-tap-highlight-color: transparent; user-select: none; -webkit-user-select: none; -webkit-touch-callout: none; }
.tile.new, .row.new { animation: pop .28s ease both; }
.tile:hover { transform: translateY(-2px); box-shadow: 0 10px 20px -10px var(--acc); }
.tile:active { transform: scale(.95); }
@keyframes pop { from { transform: scale(.85); opacity: 0; } to { transform: none; opacity: 1; } }
.ico { width: 46px; height: 46px; display: grid; place-items: center; flex: none; }
.ico img { width: 46px; height: 46px; object-fit: contain; filter: drop-shadow(0 2px 3px rgba(0,0,0,.18)); }
.emoji { font-size: 30px; line-height: 1; filter: drop-shadow(0 2px 3px rgba(0,0,0,.15)); }
.letter { width: 38px; height: 38px; border-radius: 12px; display: grid; place-items: center; font-weight: 700; font-size: 1.1rem;
  background: rgba(255,255,255,.22); color: #fff; }
.name { font-size: .84rem; font-weight: 600; line-height: 1.15; max-width: 100%; overflow: hidden; text-overflow: ellipsis;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; word-break: break-word; }
.spec { font-size: .72rem; opacity: .85; max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tile.done { pointer-events: none; animation: done .45s ease forwards; }
.tile .tick { position: absolute; inset: 0; display: grid; place-items: center; border-radius: inherit;
  background: rgba(0,0,0,.25); opacity: 0; transition: opacity .15s; }
.tile .tick svg { width: 40px; height: 40px; color: #fff; }
.tile.done .tick { opacity: 1; }
@keyframes done { 0% { transform: scale(1); } 40% { transform: scale(1.06); } 100% { transform: scale(.6); opacity: 0; } }

.list { display: flex; flex-direction: column; gap: 6px; }
.row { display: flex; align-items: center; gap: 12px; border: 0; cursor: pointer; font: inherit; text-align: left; width: 100%;
  padding: 8px 12px 8px 8px; border-radius: 14px; background: var(--secondary-background-color); color: var(--primary-text-color);
  transition: transform .15s, opacity .3s; user-select: none; -webkit-user-select: none; -webkit-touch-callout: none; }
.row:active { transform: scale(.98); }
.row .ico { width: 40px; height: 40px; border-radius: 12px; background: linear-gradient(150deg, var(--acc), var(--acc2)); }
.row .ico img { width: 32px; height: 32px; }
.row .emoji { font-size: 22px; }
.row .letter { width: 40px; height: 40px; font-size: 1rem; background: transparent; }
.row .txt { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.row .name { font-size: .95rem; -webkit-line-clamp: 1; }
.row .spec { color: var(--secondary-text-color); opacity: 1; font-size: .8rem; }
.row .circle { width: 24px; height: 24px; border-radius: 50%; border: 2px solid var(--divider-color); flex: none; display: grid;
  place-items: center; color: transparent; transition: all .2s; }
.row .circle svg { width: 16px; height: 16px; }
.row.done { animation: rowdone .45s ease forwards; pointer-events: none; }
.row.done .circle { background: var(--acc); border-color: var(--acc); color: #fff; }
@keyframes rowdone { 60% { opacity: 1; } 100% { opacity: 0; transform: translateX(30px); } }

.empty { text-align: center; padding: 18px 8px 8px; color: var(--secondary-text-color); }
.empty svg { width: 64px; height: 64px; }
.empty .big { font-size: 1.05rem; font-weight: 700; color: var(--primary-text-color); margin-top: 6px; }
.error { margin-top: 12px; padding: 10px 12px; border-radius: 12px; font-size: .85rem;
  background: color-mix(in srgb, var(--error-color, #db4437) 12%, transparent); color: var(--error-color, #db4437); }

.recent-wrap { margin-top: 16px; border-top: 1px solid var(--divider-color); padding-top: 10px; }
.recent-toggle { display: flex; align-items: center; gap: 8px; width: 100%; border: 0; background: transparent; cursor: pointer;
  font: inherit; color: var(--secondary-text-color); font-size: .85rem; font-weight: 600; padding: 4px 2px; letter-spacing: .02em; text-transform: uppercase; }
.recent-toggle .cnt { background: var(--secondary-background-color); border-radius: 999px; padding: 1px 8px; font-size: .75rem; }
.recent-toggle svg { width: 20px; height: 20px; margin-left: auto; transition: transform .25s; }
.recent-wrap.open .recent-toggle svg { transform: rotate(180deg); }
.recent { display: none; margin-top: 10px; }
.recent-wrap.open .recent { display: grid; }
.recent .tile { background: var(--secondary-background-color); color: var(--primary-text-color); box-shadow: none; --tile: 76px; }
.recent .tile .ico { width: 34px; height: 34px; }
.recent .tile .ico img { width: 34px; height: 34px; filter: grayscale(.35); opacity: .85; }
.recent .tile .emoji { font-size: 22px; }
.recent .tile .letter { width: 30px; height: 30px; background: hsl(var(--h) 55% 55% / .9); font-size: .9rem; }
.recent .tile .name { font-size: .76rem; font-weight: 500; }
.recent .tile .spec { display: none; }
.recent.grid { grid-template-columns: repeat(auto-fill, minmax(76px, 1fr)); gap: 8px; }
.recent .tile:hover { box-shadow: inset 0 0 0 2px var(--acc); }
.recent .tile.readd { animation: done .4s ease forwards; }

.sheet { position: absolute; inset: 0; display: flex; align-items: flex-end; justify-content: center; z-index: 5;
  background: rgba(0,0,0,.35); backdrop-filter: blur(3px); -webkit-backdrop-filter: blur(3px); animation: fade .2s ease; }
.sheet[hidden] { display: none; }
@keyframes fade { from { opacity: 0; } }
.panel { width: 100%; background: var(--ha-card-background, var(--card-background-color, #fff)); border-radius: 20px 20px 0 0;
  padding: 18px; box-shadow: 0 -10px 30px rgba(0,0,0,.2); animation: up .25s ease; }
@keyframes up { from { transform: translateY(40px); opacity: 0; } }
.panel h3 { margin: 0 0 12px; font-size: 1.05rem; color: var(--primary-text-color); }
.panel label { display: block; font-size: .78rem; color: var(--secondary-text-color); margin: 8px 0 4px; font-weight: 600; }
.panel input { width: 100%; box-sizing: border-box; border: 1.5px solid var(--divider-color); border-radius: 12px; padding: 10px 12px;
  font: inherit; background: var(--secondary-background-color); color: var(--primary-text-color); outline: 0; }
.panel input:focus { border-color: var(--acc); }
.actions { display: flex; gap: 8px; margin-top: 16px; }
.actions button { border: 0; border-radius: 12px; padding: 10px 14px; font: inherit; font-weight: 600; cursor: pointer; }
.btn-del { background: color-mix(in srgb, var(--error-color, #db4437) 14%, transparent); color: var(--error-color, #db4437); }
.btn-cancel { margin-left: auto; background: var(--secondary-background-color); color: var(--primary-text-color); }
.btn-save { background: linear-gradient(135deg, var(--acc), var(--acc2)); color: #fff; }
`;

class EinkaufslisteCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._items = [];
    this._loaded = false;
    this._pending = new Map(); // uid -> {status, ts}
    this._recentOpen = false;
    this._unsub = null;
    this._seen = new Set();
    this._sig = "";
  }

  static getStubConfig(hass) {
    const ent = Object.keys(hass.states).find(
      (e) => e.startsWith("todo.") && hass.states[e].attributes.einkaufsliste
    );
    return { entity: ent || "", layout: "grid", accent: "bring", show_recent: true, show_icons: true };
  }

  static getConfigForm() {
    return {
      schema: [
        { name: "entity", required: true, selector: { entity: { domain: "todo", integration: "einkaufsliste" } } },
        { name: "title", selector: { text: {} } },
        {
          type: "grid",
          name: "",
          schema: [
            {
              name: "layout",
              selector: { select: { mode: "dropdown", options: [
                { value: "grid", label: "Kacheln" }, { value: "list", label: "Liste" } ] } },
            },
            {
              name: "accent",
              selector: { select: { mode: "dropdown", options: [
                { value: "bring", label: "Bring-Rot" }, { value: "smaragd", label: "Smaragd" },
                { value: "ozean", label: "Ozean" }, { value: "violett", label: "Violett" },
                { value: "orange", label: "Orange" }, { value: "graphit", label: "Graphit" },
                { value: "theme", label: "Theme-Farbe" } ] } },
            },
            {
              name: "sort",
              selector: { select: { mode: "dropdown", options: [
                { value: "bring", label: "Wie in Bring" }, { value: "alpha", label: "Alphabetisch" } ] } },
            },
            { name: "recent_limit", selector: { number: { min: 0, max: 60, mode: "box" } } },
          ],
        },
        { name: "show_recent", selector: { boolean: {} } },
        { name: "show_icons", selector: { boolean: {} } },
      ],
      computeLabel: (s) =>
        ({
          entity: "Einkaufsliste",
          title: "Titel (optional)",
          layout: "Darstellung",
          accent: "Farbe",
          sort: "Sortierung",
          recent_limit: "Anzahl „Zuletzt gekauft“",
          show_recent: "„Zuletzt gekauft“ anzeigen",
          show_icons: "Bring-Bilder verwenden",
        })[s.name],
    };
  }

  setConfig(config) {
    if (!config || !config.entity) throw new Error("Bitte eine Einkaufsliste (todo-Entität) auswählen.");
    const old = this._config;
    this._config = {
      layout: "grid", accent: "bring", sort: "bring", show_recent: true, show_icons: true, recent_limit: 24, ...config,
    };
    if (old && old.entity !== this._config.entity) this._unsubscribe();
    this._build();
    this._subscribe();
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) this._subscribe();
    this._renderHeader();
  }

  connectedCallback() { this._subscribe(); }
  disconnectedCallback() { this._unsubscribe(); }

  getCardSize() { return 3 + Math.ceil(this._open().length / 4); }
  getGridOptions() { return { columns: 12, min_columns: 4, rows: "auto" }; }

  // ------------------------------------------------------------------ data
  async _subscribe() {
    if (!this._hass || !this._config || this._unsub || this._subscribing || !this.isConnected) return;
    this._subscribing = true;
    try {
      this._unsub = await this._hass.connection.subscribeMessage(
        (msg) => {
          this._items = msg.items || [];
          this._loaded = true;
          this._error = null;
          const now = Date.now();
          for (const [uid, p] of this._pending) {
            const it = this._items.find((i) => i.uid === uid);
            if (!it || it.status === p.status || now - p.ts > 8000) this._pending.delete(uid);
          }
          this._renderItems();
        },
        { type: "todo/item/subscribe", entity_id: this._config.entity }
      );
    } catch (e) {
      this._error = e && e.message ? e.message : "Liste konnte nicht geladen werden.";
      this._renderItems();
    }
    this._subscribing = false;
  }

  _unsubscribe() {
    if (this._unsub) {
      try { this._unsub(); } catch (_) {}
      this._unsub = null;
    }
  }

  _status(item) {
    const p = this._pending.get(item.uid);
    return p ? p.status : item.status;
  }

  _sorted(list) {
    if (this._config.sort === "alpha") return [...list].sort((a, b) => a.summary.localeCompare(b.summary, "de"));
    return list;
  }

  _open() { return this._sorted(this._items.filter((i) => this._status(i) === "needs_action")); }
  _recent() { return this._items.filter((i) => this._status(i) === "completed"); }

  async _call(service, data) {
    try {
      await this._hass.callService("todo", service, { entity_id: this._config.entity, ...data });
    } catch (e) {
      this._error = e && e.message ? e.message : "Aktion fehlgeschlagen.";
      this._pending.clear();
      this._renderItems();
    }
  }

  _setStatus(uid, status) {
    this._pending.set(uid, { status, ts: Date.now() });
    this._call("update_item", { item: uid, status });
  }

  _add(text) {
    let name = text.trim();
    if (!name) return;
    let spec = "";
    const idx = name.indexOf(",");
    if (idx > 0) { spec = name.slice(idx + 1).trim(); name = name.slice(0, idx).trim(); }
    const existing = this._items.find((i) => i.summary.toLowerCase() === name.toLowerCase());
    if (existing) {
      this._pending.set(existing.uid, { status: "needs_action", ts: Date.now() });
      const data = { item: existing.uid, status: "needs_action" };
      if (spec) data.description = spec;
      this._call("update_item", data);
      this._renderItems();
      return;
    }
    const data = { item: name };
    if (spec) data.description = spec;
    this._call("add_item", data);
  }

  // ------------------------------------------------------------------ render
  _build() {
    const [a1, a2] = ACCENTS[this._config.accent] || ACCENTS.bring;
    this.shadowRoot.innerHTML = `
      <style>${STYLE}</style>
      <ha-card style="--acc:${a1};--acc2:${a2}">
        <div class="wrap">
          <header>
            <div class="badge">${ICONS.cart}</div>
            <div class="titles"><div class="title"></div><div class="sub"></div></div>
            <button class="icon-btn" id="refresh" title="Aktualisieren">${ICONS.refresh}</button>
          </header>
          <form class="add" autocomplete="off">
            <input id="input" enterkeyhint="done" placeholder="Was brauchst du? (z. B. Milch, 2 Liter)">
            <button class="add-btn" type="submit" title="Hinzufügen">${ICONS.plus}</button>
          </form>
          <div class="suggest"></div>
          <div class="items"></div>
          <div class="recent-wrap ${this._recentOpen ? "open" : ""}" hidden>
            <button class="recent-toggle" type="button">Zuletzt gekauft <span class="cnt"></span>${ICONS.chevron}</button>
            <div class="recent grid"></div>
          </div>
          <div class="err-slot"></div>
        </div>
        <div class="sheet" hidden>
          <div class="panel">
            <h3>Artikel bearbeiten</h3>
            <label>Name</label><input id="ed-name">
            <label>Beschreibung (Menge, Marke …)</label><input id="ed-spec" placeholder="z. B. 2 Liter, Bio">
            <div class="actions">
              <button class="btn-del" type="button">Löschen</button>
              <button class="btn-cancel" type="button">Abbrechen</button>
              <button class="btn-save" type="button">Speichern</button>
            </div>
          </div>
        </div>
      </ha-card>`;
    const $ = (s) => this.shadowRoot.querySelector(s);
    this._els = {
      title: $(".title"), sub: $(".sub"), items: $(".items"), recentWrap: $(".recent-wrap"), recent: $(".recent"),
      cnt: $(".cnt"), input: $("#input"), suggest: $(".suggest"), err: $(".err-slot"), sheet: $(".sheet"),
      edName: $("#ed-name"), edSpec: $("#ed-spec"), refresh: $("#refresh"),
    };

    $("form.add").addEventListener("submit", (ev) => {
      ev.preventDefault();
      this._add(this._els.input.value);
      this._els.input.value = "";
      this._renderSuggest();
    });
    this._els.input.addEventListener("input", () => this._renderSuggest());
    this._els.suggest.addEventListener("click", (ev) => {
      const chip = ev.target.closest(".chip");
      if (!chip) return;
      this._setStatus(chip.dataset.uid, "needs_action");
      this._els.input.value = "";
      this._renderSuggest();
      this._renderItems();
    });
    this._els.refresh.addEventListener("click", async () => {
      this._els.refresh.classList.add("spin");
      try {
        await this._hass.callService("homeassistant", "update_entity", { entity_id: this._config.entity });
      } catch (_) {}
      setTimeout(() => this._els.refresh.classList.remove("spin"), 600);
    });
    $(".recent-toggle").addEventListener("click", () => {
      this._recentOpen = !this._recentOpen;
      this._els.recentWrap.classList.toggle("open", this._recentOpen);
    });

    // Antippen = erledigt / wieder hinzufügen, langes Drücken = bearbeiten
    const onTap = (ev) => {
      const el = ev.target.closest("[data-uid]");
      if (!el) return;
      if (this._longPressed) { this._longPressed = false; return; }
      const uid = el.dataset.uid;
      if (el.closest(".recent")) {
        el.classList.add("readd");
        setTimeout(() => { this._setStatus(uid, "needs_action"); this._renderItems(); }, 300);
      } else {
        el.classList.add("done");
        setTimeout(() => { this._setStatus(uid, "completed"); this._renderItems(); }, 420);
      }
    };
    const startPress = (ev) => {
      const el = ev.target.closest("[data-uid]");
      if (!el) return;
      clearTimeout(this._pressTimer);
      this._pressTimer = setTimeout(() => { this._markLongPress(); this._openEditor(el.dataset.uid); }, 550);
    };
    const endPress = () => clearTimeout(this._pressTimer);
    for (const container of [this._els.items, this._els.recent]) {
      container.addEventListener("click", onTap);
      container.addEventListener("pointerdown", startPress);
      container.addEventListener("pointerup", endPress);
      container.addEventListener("pointerleave", endPress);
      container.addEventListener("pointercancel", endPress);
      container.addEventListener("contextmenu", (ev) => {
        const el = ev.target.closest("[data-uid]");
        if (!el) return;
        ev.preventDefault();
        clearTimeout(this._pressTimer);
        this._markLongPress();
        if (this._els.sheet.hidden) this._openEditor(el.dataset.uid);
      });
      container.addEventListener("error", (ev) => {
        const img = ev.target;
        if (img.tagName !== "IMG") return;
        failedImages.add(img.dataset.slug);
        const name = img.closest("[data-name]")?.dataset.name || "";
        img.outerHTML = fallbackIcon(name);
      }, true);
    }

    // Editor
    const sheet = this._els.sheet;
    sheet.addEventListener("click", (ev) => { if (ev.target === sheet) this._closeEditor(); });
    $(".btn-cancel").addEventListener("click", () => this._closeEditor());
    $(".btn-del").addEventListener("click", () => {
      const uid = this._editUid;
      this._items = this._items.filter((i) => i.uid !== uid);
      this._call("remove_item", { item: [uid] });
      this._closeEditor();
      this._renderItems();
    });
    $(".btn-save").addEventListener("click", () => this._saveEditor());
    for (const inp of [this._els.edName, this._els.edSpec]) {
      inp.addEventListener("keydown", (ev) => { if (ev.key === "Enter") this._saveEditor(); if (ev.key === "Escape") this._closeEditor(); });
    }

    this._sig = "";
    this._seen = new Set();
    this._renderHeader();
    this._renderItems();
  }

  _markLongPress() {
    this._longPressed = true;
    clearTimeout(this._lpReset);
    this._lpReset = setTimeout(() => { this._longPressed = false; }, 900);
  }

  _openEditor(uid) {
    const item = this._items.find((i) => i.uid === uid);
    if (!item) return;
    this._editUid = uid;
    this._els.edName.value = item.summary;
    this._els.edSpec.value = item.description || "";
    this._els.sheet.hidden = false;
    setTimeout(() => this._els.edSpec.focus(), 50);
  }

  _closeEditor() {
    this._els.sheet.hidden = true;
    this._editUid = null;
  }

  _saveEditor() {
    const item = this._items.find((i) => i.uid === this._editUid);
    if (!item) return this._closeEditor();
    const name = this._els.edName.value.trim();
    const spec = this._els.edSpec.value.trim();
    if (!name) return;
    const data = { item: item.uid, description: spec };
    if (name !== item.summary) data.rename = name;
    item.summary = name;
    item.description = spec;
    this._call("update_item", data);
    this._closeEditor();
    this._renderItems();
  }

  _renderHeader() {
    if (!this._els || !this._hass) return;
    const st = this._hass.states[this._config.entity];
    const name = this._config.title || st?.attributes?.list_name || st?.attributes?.friendly_name || "Einkaufsliste";
    if (this._els.title.textContent !== name) this._els.title.textContent = name;
    this._renderSub();
  }

  _renderSub() {
    if (!this._els) return;
    const n = this._open().length;
    this._els.sub.innerHTML = !this._loaded
      ? "Wird geladen …"
      : n === 0 ? "Alles erledigt" : `<b>${n}</b> ${n === 1 ? "Artikel" : "Artikel"} auf der Liste`;
  }

  _tile(item) {
    const icons = this._config.show_icons !== false;
    const spec = item.description ? `<span class="spec">${esc(item.description)}</span>` : "";
    if (this._config.layout === "list" && !this._renderingRecent) {
      return `<button class="row${this._isNew(item)}" data-uid="${esc(item.uid)}" data-name="${esc(item.summary)}">
        <span class="ico">${iconHtml(item.summary, icons)}</span>
        <span class="txt"><span class="name">${esc(item.summary)}</span>${spec}</span>
        <span class="circle">${ICONS.check}</span></button>`;
    }
    return `<button class="tile${this._isNew(item)}" data-uid="${esc(item.uid)}" data-name="${esc(item.summary)}" title="${esc(item.summary)}">
      <span class="ico">${iconHtml(item.summary, icons)}</span>
      <span class="name">${esc(item.summary)}</span>${spec}
      <span class="tick">${ICONS.check}</span></button>`;
  }

  _isNew(item) {
    const key = (this._renderingRecent ? "r:" : "o:") + item.uid;
    if (this._seen.has(key)) return "";
    this._seen.add(key);
    return this._firstPaint ? "" : " new";
  }

  _renderItems() {
    if (!this._els) return;
    this._renderSub();
    const open = this._open();
    const els = this._els;
    const sig = JSON.stringify([
      this._loaded, this._error, open.map((i) => [i.uid, i.summary, i.description]),
      this._recent().map((i) => [i.uid, i.summary]),
    ]);
    if (sig === this._sig) return;
    this._sig = sig;
    this._firstPaint = this._seen.size === 0;

    if (!this._loaded && !this._error) {
      els.items.innerHTML = `<div class="empty">Liste wird geladen …</div>`;
    } else if (open.length === 0) {
      els.items.innerHTML = `<div class="empty">${ICONS.party}<div class="big">Alles eingekauft!</div>
        <div>Füge oben etwas hinzu oder tippe unten auf einen Artikel.</div></div>`;
    } else {
      this._renderingRecent = false;
      const cls = this._config.layout === "list" ? "list" : "grid";
      els.items.innerHTML = `<div class="${cls}">${open.map((i) => this._tile(i)).join("")}</div>`;
    }

    const recent = this._recent().slice(0, Number(this._config.recent_limit ?? 24));
    const showRecent = this._config.show_recent !== false && recent.length > 0;
    els.recentWrap.hidden = !showRecent;
    if (showRecent) {
      this._renderingRecent = true;
      els.cnt.textContent = recent.length;
      els.recent.innerHTML = recent.map((i) => this._tile(i)).join("");
      this._renderingRecent = false;
    }

    els.err.innerHTML = this._error ? `<div class="error">${esc(this._error)}</div>` : "";
    this._renderSuggest();
  }

  _renderSuggest() {
    if (!this._els) return;
    const q = this._els.input.value.split(",")[0].trim().toLowerCase();
    if (!q) { this._els.suggest.innerHTML = ""; return; }
    const hits = this._recent().filter((i) => i.summary.toLowerCase().includes(q)).slice(0, 6);
    this._els.suggest.innerHTML = hits
      .map((i) => `<button class="chip" type="button" data-uid="${esc(i.uid)}">+ ${esc(i.summary)}</button>`)
      .join("");
  }
}

if (!customElements.get("einkaufsliste-card")) {
  customElements.define("einkaufsliste-card", EinkaufslisteCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "einkaufsliste-card",
    name: "Einkaufsliste (Bring!)",
    description: "Deine Bring!-Einkaufsliste als hübsche Kacheln – antippen zum Abhaken.",
    preview: true,
    documentationURL: "https://github.com/domiundergroun/Einkaufsliste",
  });
  console.info(`%c EINKAUFSLISTE-CARD %c v${CARD_VERSION} `,
    "background:#ee524f;color:#fff;font-weight:700;border-radius:4px 0 0 4px;padding:2px 4px",
    "background:#333;color:#fff;border-radius:0 4px 4px 0;padding:2px 4px");
}
