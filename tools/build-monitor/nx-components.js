const integerFormat = new Intl.NumberFormat('fr-FR');

export function formatBuildProgress(done, total) {
  const parsedDone = Number(done);
  const parsedTotal = Number(total);
  const safeDone = Number.isFinite(parsedDone) ? Math.max(0, Math.floor(parsedDone)) : 0;
  const safeTotal = Number.isFinite(parsedTotal) ? Math.max(0, Math.floor(parsedTotal)) : 0;
  // Floor so an unfinished build never displays 100 %.
  const percent = safeTotal > 0 ? Math.min(100, Math.floor((safeDone / safeTotal) * 100)) : 0;
  return {
    done: safeDone,
    total: safeTotal,
    percent,
    count: `${integerFormat.format(safeDone)} / ${integerFormat.format(safeTotal)}`,
  };
}

// Current-stage fraction (0..1) -> whole percent, or null when blank/invalid/out of range.
export function formatStageProgress(value) {
  if (value === null || value === undefined || String(value).trim() === '') return null;
  const fraction = Number(value);
  if (!Number.isFinite(fraction) || fraction < 0 || fraction > 1) return null;
  // Epsilon guards float noise (0.29 * 100 = 28.999…); floor keeps an unfinished stage below 100 %.
  return fraction === 1 ? 100 : Math.min(99, Math.floor(fraction * 100 + 1e-9));
}

const BASE_CSS = `
  *,*::before,*::after{box-sizing:border-box}
  button{font:inherit}
  @media(prefers-reduced-motion:reduce){
    *,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}
  }
`;
const sheets = new Map();
const HTMLElementBase = globalThis.HTMLElement || class {};

function adoptStyles(shadow, css) {
  let sheet = sheets.get(css);
  if (!sheet) {
    sheet = new CSSStyleSheet();
    sheet.replaceSync(css);
    sheets.set(css, sheet);
  }
  shadow.adoptedStyleSheets = [sheet];
}

class NxElement extends HTMLElementBase {
  constructor(css, delegatesFocus = false) {
    super();
    const shadow = this.attachShadow({ mode: 'open', delegatesFocus });
    adoptStyles(shadow, BASE_CSS + css);
  }
}

function pillText(status, label, value) {
  return status === 'compiling' && value !== null && value.trim() !== ''
    ? `${label}${label ? ' ' : ''}${value} %`
    : label;
}

const PILL_CSS = `
  :host{display:inline-flex;vertical-align:middle;max-width:100%}
  .pill{display:inline-flex;align-items:center;gap:7px;height:35px;padding:6px 10px;border:1px solid #53694166;border-radius:var(--nx-radius-pill);background:#171b0d;color:#f5f7ef;font-family:var(--nx-font);font-size:.9375rem;line-height:20px;white-space:nowrap}
  .dot,.tick,.spinner{flex:none}
  .dot{width:12px;height:12px;border-radius:50%;background:var(--nx-yellow);animation:nx-pill-pulse 2.4s ease-in-out infinite}
  .ready{background:#0b2416;border-color:#3b754d}
  .tick{width:19px;height:19px;border-radius:50%;display:grid;place-items:center;background:#42b947;color:#fff;font-size:.875rem;font-weight:700;line-height:1}
  .compiling{background:#111919;border-color:#3c5650}
  .spinner{width:16px;height:16px;border:2px solid #50665d;border-top-color:#65d853;border-right-color:#65d853;border-radius:50%;animation:nx-pill-spin .9s linear infinite}
  @keyframes nx-pill-spin{to{transform:rotate(1turn)}}
  @keyframes nx-pill-pulse{50%{opacity:.55;transform:scale(.85)}}
`;

class NxPill extends NxElement {
  static observedAttributes = ['status', 'label', 'value'];

  constructor() {
    super(PILL_CSS);
    this.shadowRoot.innerHTML = '<span class="pill"><span class="icon" aria-hidden="true"></span><span class="text"></span></span>';
    this.pill = this.shadowRoot.querySelector('.pill');
    this.icon = this.shadowRoot.querySelector('.icon');
    this.text = this.shadowRoot.querySelector('.text');
  }

  connectedCallback() { this.render(); }
  attributeChangedCallback() { this.render(); }

  render() {
    const requested = this.getAttribute('status') || 'test';
    const status = ['test', 'ready', 'compiling'].includes(requested) ? requested : 'test';
    const label = this.getAttribute('label') || '';
    const value = this.getAttribute('value');
    this.pill.className = `pill ${status}`;
    this.icon.className = `icon ${status === 'ready' ? 'tick' : status === 'compiling' ? 'spinner' : 'dot'}`;
    this.icon.textContent = status === 'ready' ? '✓' : '';
    this.text.textContent = pillText(status, label, value);
  }
}

const TILE_CSS = `
  :host{display:block;min-width:0}
  :host([selected]){z-index:1}
  .tile{position:relative;display:block;width:100%;aspect-ratio:var(--nx-tile-ratio);border:1px solid var(--nx-border);border-radius:var(--nx-radius-tile);overflow:hidden;padding:0;background:var(--nx-surface);color:var(--nx-text);cursor:pointer;text-align:left;transition:border-color .2s,box-shadow .35s var(--nx-ease)}
  img{position:absolute;inset:0;display:block;width:100%;height:100%;object-fit:cover}
  nx-pill{position:absolute;left:4.56%;bottom:5.15%;z-index:1}
  .tile:hover{border-color:var(--nx-border-hover)}
  .tile:focus-visible,.tile[aria-pressed=true]{border-color:var(--nx-focus);outline:2px solid var(--nx-focus);outline-offset:0}
  .tile[aria-pressed=true]{box-shadow:0 18px 40px #0009}
  .tile:active{transform:scale(.98)}
  @media(prefers-reduced-motion:reduce){.tile:active{transform:none}}
`;

class NxTile extends NxElement {
  static observedAttributes = ['src', 'game', 'status', 'label', 'value', 'selected'];

  constructor() {
    super(TILE_CSS, true);
    this.shadowRoot.innerHTML = '<button class="tile" type="button" part="button"><img part="cover" alt="" draggable="false"><nx-pill part="status"></nx-pill></button>';
    this.button = this.shadowRoot.querySelector('button');
    this.image = this.shadowRoot.querySelector('img');
    this.pill = this.shadowRoot.querySelector('nx-pill');
    this.button.addEventListener('click', () => {
      this.selected = true;
      this.dispatchEvent(new CustomEvent('nx-select', {
        bubbles: true,
        composed: true,
        detail: { game: this.getAttribute('game') || '' },
      }));
    });
  }

  connectedCallback() { this.render(); }
  attributeChangedCallback() { this.render(); }

  get selected() { return this.hasAttribute('selected'); }
  set selected(value) { this.toggleAttribute('selected', Boolean(value)); }

  render() {
    const src = this.getAttribute('src');
    const game = this.getAttribute('game') || '';
    const status = this.getAttribute('status') || 'test';
    const label = this.getAttribute('label') || '';
    const value = this.getAttribute('value');
    if (src === null) this.image.removeAttribute('src');
    else this.image.setAttribute('src', src);
    for (const [name, next] of [['status', status], ['label', label]]) this.pill.setAttribute(name, next);
    if (value === null) this.pill.removeAttribute('value');
    else this.pill.setAttribute('value', value);
    const state = pillText(status, label, value);
    this.button.setAttribute('aria-label', [game, state].filter(Boolean).join(' — ') || 'Jeu');
    this.button.setAttribute('aria-pressed', String(this.selected));
  }
}

const ICONS = {
  home: '<path d="m4 14 12-10 12 10-3 2v12h-7v-9h-5v9H7V16Z" fill="currentColor" stroke="none"/>',
  library: '<rect x="5" y="4" width="8" height="9" rx="1.5"/><rect x="19" y="4" width="8" height="9" rx="1.5"/><rect x="5" y="19" width="8" height="9" rx="1.5"/><rect x="19" y="19" width="8" height="9" rx="1.5"/>',
  games: '<path d="M11 7h10c4 0 6 7 7 14 1 6-3 6-7-2H11c-4 8-8 8-7 2 1-7 3-14 7-14Z"/><path d="M11 11v7m-3-3h6"/><circle cx="22" cy="12" r="1"/><circle cx="25" cy="16" r="1"/>',
  friends: '<circle cx="13" cy="10" r="5"/><path d="M4 28v-4c0-5 18-5 18 0v4ZM23 7a5 5 0 0 1 0 10m2 3c4 1 5 3 4 8h-4"/>',
  downloads: '<path d="M16 3v20m-8-8 8 8 8-8M5 29h22"/>',
  settings: '<path d="m13 4 6 0 1 4 4 2 4-1 3 5-3 3 0 4 2 3-3 5-4-1-4 2-1 3h-6l-1-3-4-2-4 1-3-5 3-3v-4l-3-3 3-5 4 1 4-2Z" transform="translate(1 -2) scale(.95)"/><circle cx="16" cy="16" r="5"/>',
  catalog: '<path d="M6 10h20l-2 18H8L6 10Z"/><path d="M11 11V8a5 5 0 0 1 10 0v3"/>',
  builds: '<path d="m16 4 12 7-12 7L4 11l12-7Z"/><path d="m5 16 11 6 11-6M5 21l11 6 11-6"/>',
};

const NAV_CSS = `
  :host{display:inline-block;width:49px;height:49px;color:var(--nx-icon)}
  button{position:relative;display:grid;place-items:center;width:100%;height:100%;padding:0;border:0;border-radius:11px;background:none;color:inherit;cursor:pointer;transition:background .2s,color .2s,transform .2s var(--nx-spring)}
  svg{width:28px;height:28px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
  .label{display:none;pointer-events:none}
  button:hover{background:#ffffff08;color:var(--nx-text)}
  button:active{transform:scale(.94)}
  button:focus-visible{outline:2px solid var(--nx-focus);outline-offset:4px}
  button[aria-pressed=true]{color:var(--nx-green-bright);background:var(--nx-green-deep)}
  :host([data-dock]){width:56px;height:56px}
  :host([data-dock]) button{border-radius:50%}
  :host([data-dock]) .label{position:absolute;top:62px;left:50%;display:block;width:120px;transform:translateX(-50%);color:var(--nx-text-soft);font-family:var(--nx-font);font-size:14px;line-height:18px;text-align:center;white-space:nowrap}
  :host([data-dock]) button[aria-pressed=true] .label{color:var(--nx-green-bright)}
  :host([data-dock]) button[aria-pressed=true]::after{content:"";position:absolute;top:86px;left:50%;width:5px;height:5px;transform:translateX(-50%);border-radius:50%;background:var(--nx-green-bright)}
  @media(max-width:480px){:host([data-dock]) .label{width:84px;font-size:12px}}
  @media(prefers-reduced-motion:reduce){button:active{transform:none}}
`;

class NxNav extends NxElement {
  static observedAttributes = ['icon', 'label', 'active'];

  constructor() {
    super(NAV_CSS, true);
    this.shadowRoot.innerHTML = '<button type="button" part="button"><svg viewBox="0 0 32 32" aria-hidden="true"></svg><span class="label" part="label"></span></button>';
    this.button = this.shadowRoot.querySelector('button');
    this.svg = this.shadowRoot.querySelector('svg');
    this.text = this.shadowRoot.querySelector('.label');
  }

  connectedCallback() { this.render(); }
  attributeChangedCallback() { this.render(); }

  get active() { return this.hasAttribute('active'); }
  set active(value) { this.toggleAttribute('active', Boolean(value)); }

  focus(options) { this.button.focus(options); }

  render() {
    const icon = this.getAttribute('icon') || 'library';
    const label = this.getAttribute('label') || '';
    this.svg.innerHTML = ICONS[icon] || ICONS.library;
    this.text.textContent = label;
    this.button.setAttribute('aria-pressed', String(this.active));
    if (label) {
      this.button.setAttribute('aria-label', label);
      this.button.title = label;
    } else {
      this.button.removeAttribute('aria-label');
      this.button.removeAttribute('title');
    }
  }
}

const DOCK_CSS = `
  :host{display:block;width:max-content;max-width:100%}
  nav{display:grid;grid-template-columns:repeat(4,56px);justify-content:space-evenly;width:540px;max-width:100%;height:116px;padding:12px 0 0;border:1px solid var(--nx-hairline);border-radius:999px;background:#0b1418cc;backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);box-shadow:0 12px 40px #0002}
`;

class NxDock extends NxElement {
  constructor() {
    super(DOCK_CSS);
    this.shadowRoot.innerHTML = '<nav aria-label="Rubriques"><slot></slot></nav>';
    this.shadowRoot.querySelector('slot').addEventListener('slotchange', () => this.syncItems());
    this.addEventListener('click', event => {
      const items = this.items();
      const selected = event.target.closest?.('nx-nav');
      if (!items.includes(selected)) return;
      for (const item of items) item.active = item === selected;
    });
    this.addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) return;
      const items = this.items();
      const current = items.indexOf(event.target);
      if (current < 0) return;
      event.preventDefault();
      const step = event.key === 'ArrowRight' || event.key === 'ArrowDown' ? 1 : -1;
      items[(current + step + items.length) % items.length].focus();
    });
  }

  connectedCallback() { this.syncItems(); }

  items() {
    return Array.from(this.children).filter(child => child.tagName === 'NX-NAV');
  }

  syncItems() {
    for (const item of this.items()) item.setAttribute('data-dock', '');
  }
}

const BUILD_CSS = `
  :host{display:block;width:270px;max-width:100%;font-family:var(--nx-font)}
  .card{position:relative;width:270px;height:274px;max-width:100%;padding:22px 20px 20px;border:1px solid var(--nx-hairline);border-radius:16px;background:var(--nx-surface);color:var(--nx-text)}
  .label{margin:0;color:var(--nx-muted);font-size:13px;line-height:18px}
  .main{display:flex;align-items:center;gap:14px;margin-top:38px}
  .ring{position:relative;width:78px;height:78px;flex:none;border-radius:50%;display:grid;place-items:center}
  .ring::before{content:"";position:absolute;inset:7px;border-radius:50%;background:var(--nx-surface)}
  .percent{position:relative;font-size:15px;font-weight:600}
  .info{min-width:0}
  .name{margin:0 0 8px;font-size:16px;line-height:20px;font-weight:600;overflow-wrap:anywhere}
  .count{margin:0 0 4px;color:var(--nx-green-bright);font-size:15px;line-height:20px;font-variant-numeric:tabular-nums;white-space:nowrap}
  .steps{margin:0;color:var(--nx-muted);font-size:12px;line-height:16px}
  .details{position:absolute;left:20px;right:20px;bottom:20px;width:calc(100% - 40px);height:38px;padding:0 15px;display:inline-flex;align-items:center;justify-content:center;gap:9px;background:var(--nx-raised);color:var(--nx-text);border:1px solid #ffffff08;border-radius:var(--nx-radius-pill);font-size:1rem;cursor:pointer;transition:background .2s,border-color .2s}
  .details:hover{background:#16222a;border-color:#ffffff1a}
  .details:focus-visible{outline:2px solid var(--nx-focus);outline-offset:4px}
`;

class NxBuildCard extends NxElement {
  static observedAttributes = ['name', 'done', 'total', 'progress'];

  constructor() {
    super(BUILD_CSS);
    this.shadowRoot.innerHTML = `
      <aside class="card" aria-labelledby="build-label">
        <p class="label" id="build-label">Construction en cours</p>
        <div class="main">
          <div class="ring" role="progressbar" aria-label="Progression de la compilation" aria-valuemin="0" aria-valuemax="100"><span class="percent"></span></div>
          <div class="info"><h2 class="name"></h2><p class="count"></p><p class="steps">Étapes terminées</p></div>
        </div>
        <button class="details" type="button">Voir les détails</button>
      </aside>`;
    this.ring = this.shadowRoot.querySelector('.ring');
    this.percent = this.shadowRoot.querySelector('.percent');
    this.name = this.shadowRoot.querySelector('.name');
    this.count = this.shadowRoot.querySelector('.count');
    this.steps = this.shadowRoot.querySelector('.steps');
    this.shadowRoot.querySelector('.details').addEventListener('click', () => {
      // `progress` attribute present = real current stage; absent = legacy done/total counter.
      const detail = this.hasAttribute('progress')
        ? { progress: formatStageProgress(this.getAttribute('progress')) }
        : formatBuildProgress(this.getAttribute('done'), this.getAttribute('total'));
      this.dispatchEvent(new CustomEvent('nx-details', {
        bubbles: true,
        composed: true,
        detail: { name: this.getAttribute('name') || '', ...detail },
      }));
    });
  }

  connectedCallback() { this.render(); }
  attributeChangedCallback() { this.render(); }

  render() {
    this.name.textContent = this.getAttribute('name') || '';
    if (this.hasAttribute('progress')) {
      const stage = formatStageProgress(this.getAttribute('progress'));
      const known = stage !== null;
      this.count.hidden = true;
      this.steps.textContent = known ? 'Étape courante' : 'Progression non disponible';
      this.percent.textContent = known ? `${stage} %` : '—';
      this.ring.style.background = known
        ? `conic-gradient(var(--nx-green) 0 ${stage}%, #1f2a2c ${stage}% 100%)`
        : '#1f2a2c';
      if (known) {
        this.ring.setAttribute('aria-valuenow', String(stage));
        this.ring.setAttribute('aria-valuetext', `${stage} %`);
      } else {
        this.ring.removeAttribute('aria-valuenow');
        this.ring.setAttribute('aria-valuetext', 'Progression non disponible');
      }
      return;
    }
    const progress = formatBuildProgress(this.getAttribute('done'), this.getAttribute('total'));
    this.count.hidden = false;
    this.steps.textContent = 'Étapes terminées';
    this.count.textContent = progress.count;
    this.percent.textContent = `${progress.percent} %`;
    this.ring.style.background = `conic-gradient(var(--nx-green) 0 ${progress.percent}%, #1f2a2c ${progress.percent}% 100%)`;
    this.ring.setAttribute('aria-valuenow', String(progress.percent));
    this.ring.setAttribute('aria-valuetext', `${progress.percent} %`);
  }
}

// W3C standard Gamepad mapping: 0 bottom face button, 1 right face button, 12-15 d-pad, axes 0/1 left stick.
// Positional, not by label: on a Nintendo-layout pad (PowerA) the bottom button is printed B.
const PAD_BUTTONS = { 0: 'confirm', 1: 'back', 12: 'up', 13: 'down', 14: 'left', 15: 'right' };

export function padState(pad, dead = 0.5) {
  const held = new Set();
  for (const [index, action] of Object.entries(PAD_BUTTONS)) if (pad?.buttons?.[index]?.pressed) held.add(action);
  const [x = 0, y = 0] = pad?.axes || [];
  if (x <= -dead) held.add('left');
  if (x >= dead) held.add('right');
  if (y <= -dead) held.add('up');
  if (y >= dead) held.add('down');
  return held;
}

// Only new presses count: holding a direction moves once, never a repeated launch.
export function padPresses(before, after) { return [...after].filter(action => !before.has(action)); }

// Polls while a pad is connected and reports each press as a bubbling 'nx-pad' event on document.
// ponytail: no auto-repeat while held, add it when the catalogue grid is driven by pad.
function watchGamepads() {
  if (!globalThis.navigator?.getGamepads) return;
  let held = new Map(), frame = 0;
  const poll = () => {
    const next = new Map();
    for (const pad of navigator.getGamepads()) {
      if (!pad?.connected) continue;
      const state = padState(pad);
      next.set(pad.index, state);
      for (const action of padPresses(held.get(pad.index) || new Set(), state)) {
        document.dispatchEvent(new CustomEvent('nx-pad', { detail: { action } }));
      }
    }
    held = next;
    frame = next.size ? requestAnimationFrame(poll) : 0;
  };
  addEventListener('gamepadconnected', () => { if (!frame) frame = requestAnimationFrame(poll); });
}

if (globalThis.customElements) {
  watchGamepads();
  const elements = {
    'nx-pill': NxPill,
    'nx-tile': NxTile,
    'nx-nav': NxNav,
    'nx-dock': NxDock,
    'nx-build-card': NxBuildCard,
  };
  for (const [name, element] of Object.entries(elements)) {
    if (!customElements.get(name)) customElements.define(name, element);
  }
}
