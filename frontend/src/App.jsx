// JETBOX v4 - SIGNAL AUTHORITY
// Complete UI rewrite - FAZA 1
import { useState, useEffect, useCallback, useRef } from "react";
import { createPortal } from "react-dom";

const API = "/api";

// ─── KEYS ───────────────────────────────────────────
const KEYS = ["Cm","C#m","Dm","D#m","Em","Fm","F#m","Gm","G#m","Am","A#m","Bm",
              "C","C#","D","D#","E","F","F#","G","G#","A","A#","B"];

// ─── MOODS ──────────────────────────────────────────
const MOODS = {
  dark_rage:  { label:"DARK RAGE",  text:"Dark, aggressive energy built for heavy flows and punchy delivery." },
  melodic:    { label:"MELODIC",    text:"Melodic and emotional - airy textures with room for hooks and storytelling." },
  aggressive: { label:"AGGRESSIVE", text:"High-energy, aggressive production with hard-hitting 808s and punchy drums." },
  hypnotic:   { label:"HYPNOTIC",   text:"Hypnotic loop-driven atmosphere designed to pull listeners into a trance." },
  cold:       { label:"COLD",       text:"Ice-cold minimalist production with sharp hi-hats and deep sub bass." },
  cinematic:  { label:"CINEMATIC",  text:"Cinematic and atmospheric - built for artists with a larger-than-life presence." },
  drill:      { label:"DRILL",      text:"Drill-influenced with sliding 808s, crisp percussion, and menacing melodies." },
  eerie:      { label:"EERIE",      text:"Eerie, unsettling textures with dissonant melodies and haunting atmosphere." },
  triumphant: { label:"TRIUMPHANT", text:"Triumphant, anthemic energy - built for confident delivery and bold statements." },
};

// ─── TIER LABELS ─────────────────────────────────────
const TIER_LABELS = {
  legends:              { label:"LEGENDS",    icon:"◈" },
  rage_wave:            { label:"RAGE WAVE",  icon:"▲" },
  hyperpop_adjacent:    { label:"HYPERPOP",   icon:"◉" },
  us_active_major:      { label:"US MAJOR",   icon:"●" },
  us_active_rising:     { label:"US RISING",  icon:"○" },
  uk_drill_grime:       { label:"UK/DRILL",   icon:"◆" },
  eu_international:     { label:"EU/INTL",    icon:"◇" },
  tr_rap:               { label:"TR RAP",     icon:"▪" },
  producers_beatmakers: { label:"PRODUCERS",  icon:"⬡" },
  // fallback for old tier names from API
  major:     { label:"MAJOR",    icon:"⭐" },
  rising:    { label:"RISING",   icon:"🔥" },
  producers: { label:"PRODUCERS",icon:"🎹" },
  new_wave:  { label:"NEW WAVE", icon:"🌊" },
  melodic_trap:     { label:"MELODIC",   icon:"💜" },
  uk_international: { label:"UK/INTL",   icon:"🌍" },
  classic:          { label:"CLASSIC",   icon:"🏆" },
  niche_targets:    { label:"NICHE",     icon:"🎯" },
};

// ─── PLATFORM CONFIG ──────────────────────────────────
const PLATFORMS = {
  youtube:    { label:"YOUTUBE",    icon:"▶" },
  soundcloud: { label:"SOUNDCLOUD", icon:"☁" },
  instagram:  { label:"INSTAGRAM",  icon:"◎" },
  beatstars:  { label:"BEATSTARS",  icon:"★" },
};

// ─── TITLE STYLES ─────────────────────────────────────
const TITLE_STYLES = {
  standard:     "[FREE] Artist1 x Artist2 Type Beat - \"Name\"",
  single:       "[FREE] Artist1 Type Beat - \"Name\"",
  mood_tagged:  "[FREE] Artist1 x Artist2 Type Beat - \"Name\" | Mood",
};

// ─── LIVE CLOCK ──────────────────────────────────────
function LiveClock() {
  const [t, setT] = useState(new Date());
  useEffect(() => { const i = setInterval(() => setT(new Date()), 1000); return () => clearInterval(i); }, []);
  const p = (n) => String(n).padStart(2,"0");
  return (
    <span className="f-data" style={{fontSize:10,color:"var(--txt-dim)",letterSpacing:".08em"}}>
      {t.getFullYear()}.{p(t.getMonth()+1)}.{p(t.getDate())} // {p(t.getHours())}:{p(t.getMinutes())}:{p(t.getSeconds())}
    </span>
  );
}

// ─── SECTION DIVIDER ─────────────────────────────────
function SecDiv({ label }) {
  return (
    <div className="sec-div">
      <div className="sec-div-line" />
      {label && <span className="sec-div-lbl">{label}</span>}
      <div className="sec-div-line" />
    </div>
  );
}

// ─── DB METER ────────────────────────────────────────
// SEO Signal Strength meter — score 0-1 mapped to 0-100
// "86" = %86 SEO optimizasyon skoru (başlık+tag+açıklama kalitesi)
function DbMeter({ score = 0 }) {
  const pct    = Math.max(0, Math.min(1, score));
  const bars   = 12;
  const filled = Math.round(pct * bars);
  const db     = Math.round(pct * 100);

  const barColor = (i) => {
    if (i >= filled) return "var(--brd-idle)";
    const ratio = i / bars;
    if (ratio < 0.5) return "#e5ef28";  // yellow-green
    if (ratio < 0.8) return "#9AFF62";  // lime
    return "#39ff14";                   // neon green
  };

  const grade = db >= 76 ? "STRONG" : db >= 51 ? "GOOD" : "WEAK";
  const gradeColor = db >= 76 ? "#39ff14" : db >= 51 ? "#9AFF62" : "#e5ef28";

  return (
    <div title={`SEO Sinyal Gücü: ${db}/100\n${grade} — Başlık, tag ve açıklama kalitesini ölçer\n0-50: Zayıf | 51-75: İyi | 76-100: Güçlü`}
      style={{ display: "flex", alignItems: "center", gap: 8, cursor:"help" }}>
      <div style={{ display: "flex", gap: 2, alignItems: "flex-end", height: 22 }}>
        {Array.from({ length: bars }).map((_, i) => (
          <div key={i} style={{
            width: 5,
            height: 8 + i * 1.1,
            background: barColor(i),
            borderRadius: 1,
            transition: "background .3s",
          }} />
        ))}
      </div>
      <div style={{ fontFamily: "var(--font-data)", fontSize: 14, color: "var(--accent)", lineHeight: 1 }}>
        {db}<span style={{ fontSize: 9, color: "var(--txt-dim)", marginLeft: 2 }}>dB</span>
      </div>
    </div>
  );
}


// ─── BEAT WAVEFORM ───────────────────────────────────
function BeatWave({ active, bpm = 140 }) {
  const heights = [4,8,6,14,10,5,12,7,16,9];
  const dur = Math.max(200, 60000 / Math.max(1, bpm));
  return (
    <div className="beat-waveform" style={{height:18}}>
      {heights.map((h, i) => (
        <div key={i} className="beat-bar" style={{
          height: h,
          transformOrigin: "bottom",
          animationName: active ? "waveform-active" : "waveform-idle",
          animationDuration: active ? `${dur}ms` : "2200ms",
          animationDelay: `${i * 55}ms`,
          animationIterationCount: "infinite",
          animationTimingFunction: "ease-in-out",
        }} />
      ))}
    </div>
  );
}

// ─── STATUS DOT ──────────────────────────────────────
function Dot({ state = "idle" }) {
  return <div className={`s-dot ${state}`} />;
}

// ─── ARTIST DROPDOWN ─────────────────────────────────
// Uses React Portal so overflow:hidden on panels doesn't clip the list
function ArtistDropdown({ label, value, onSelect, allTiers, optional, onClear }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [panelStyle, setPanelStyle] = useState({});
  const triggerRef = useRef(null);
  const panelRef = useRef(null);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const h = (e) => {
      if (
        triggerRef.current && !triggerRef.current.contains(e.target) &&
        panelRef.current  && !panelRef.current.contains(e.target)
      ) setOpen(false);
    };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, [open]);

  const handleOpen = () => {
    if (!open && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      setPanelStyle({
        position: "fixed",
        top:   rect.bottom + 2,
        left:  rect.left,
        width: rect.width,
        zIndex: 9999,
        maxHeight: 260,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        background: "var(--bg-panel)",
        border: "1px solid var(--brd-idle)",
        boxShadow: "0 8px 24px rgba(0,0,0,.55)",
        animation: "slide-down 140ms ease",
      });
    }
    setOpen((v) => !v);
    setQ("");
  };

  const allArtists = Object.entries(allTiers).flatMap(([tier, list]) =>
    (Array.isArray(list) ? list : []).map((a) => ({ name: a, tier }))
  );
  const filtered = q
    ? allArtists.filter((a) => a.name.toLowerCase().includes(q.toLowerCase()))
    : allArtists;

  const tiers = Object.entries(TIER_LABELS);

  const DropdownPanel = (
    <div ref={panelRef} style={panelStyle}>
      <div className="dd-search-wrap">
        <input className="field-input sm" placeholder="SEARCH..."
          value={q} onChange={(e) => setQ(e.target.value)}
          autoFocus style={{height:28}} />
      </div>
      <div className="dd-list" style={{flex:1,overflowY:"auto",padding:"4px"}}>
        {optional && (
          <div className="dd-item skip"
            onClick={() => { onClear && onClear(); setOpen(false); }}>
            - no artist 2 -
          </div>
        )}
        {filtered.length === 0 && (
          <div style={{padding:"12px",textAlign:"center",color:"var(--txt-dim)",fontSize:10,fontFamily:"var(--font-data)"}}>
            NO MATCH
          </div>
        )}
        {tiers.map(([key, info]) => {
          const list = filtered.filter((a) => a.tier === key);
          if (!list.length) return null;
          return (
            <div key={key}>
              <div className="dd-grp-lbl">{info.icon} {info.label}</div>
              {list.map((a) => (
                <div key={a.name}
                  className={`dd-item ${a.name === value ? "sel" : ""}`}
                  onClick={() => { onSelect(a.name); setOpen(false); setQ(""); }}>
                  {a.name}
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );

  return (
    <div className="field">
      <div className="field-hdr">
        <label className="field-label">{label}{optional ? " (OPTIONAL)" : ""}</label>
        {value && optional && (
          <button className="btn-ghost" style={{height:18,fontSize:8,padding:"0 6px"}}
            onClick={() => { onClear && onClear(); }}>CLEAR</button>
        )}
      </div>
      <div className="dd-wrap">
        <button ref={triggerRef}
          className={`dd-trigger ${value ? "has-val" : ""}`}
          onClick={handleOpen}>
          <span className="trunc" style={{flex:1,textAlign:"left"}}>
            {value || (optional ? "- skip -" : "SELECT ARTIST...")}
          </span>
          <span className="dd-arrow">{open ? "▲" : "▼"}</span>
        </button>
        {open && createPortal(DropdownPanel, document.body)}
      </div>
    </div>
  );
}

// ─── COMBO PRESETS ───────────────────────────────────
function ComboPresets({ combos, onLoad, onSave, onDelete, artist1, artist2, vibe }) {
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState("");

  const handleSave = () => {
    if (!artist1 || !name.trim()) return;
    onSave({ name: name.trim(), artist1, artist2: artist2 || null, vibe });
    setName(""); setSaving(false);
  };

  return (
    <div>
      <div className="lbl-xs" style={{marginBottom:6}}>COMBO PRESETS</div>
      <div className="combo-wrap" style={{marginBottom:6}}>
        {combos.map((c) => (
          <div key={c.id} className={`combo-chip`} onClick={() => onLoad(c)}>
            <span className="trunc" style={{maxWidth:80}}>{c.name}</span>
            <button className="combo-del"
              onClick={(e) => { e.stopPropagation(); onDelete(c.id); }}>×</button>
          </div>
        ))}
        <div className="combo-chip combo-chip-new" onClick={() => setSaving(true)}>
          + NEW
        </div>
      </div>
      {saving && (
        <div style={{display:"flex",gap:6,alignItems:"center",marginBottom:8}}>
          <input className="field-input sm" placeholder="COMBO NAME..."
            value={name} onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSave()}
            autoFocus style={{flex:1,height:28}} />
          <button className="btn btn-sec" style={{height:28,fontSize:9,padding:"0 10px"}}
            onClick={handleSave}>SAVE</button>
          <button className="btn btn-ghost" style={{height:28,fontSize:11}}
            onClick={() => setSaving(false)}>×</button>
        </div>
      )}
    </div>
  );
}

// ─── INPUT PANEL ─────────────────────────────────────
function InputPanel({
  beats, selectedBeatId, onSelectBeat, allTiers, combos,
  onLoadCombo, onSaveCombo, onDeleteCombo,
  artist1, setArtist1, artist2, setArtist2,
  beatName, setBeatName, bpm, setBpm, beatKey, setBeatKey,
  vibe, setVibe, mood, setMood,
  onLockTarget, locked, onScanBeats,
}) {
  return (
    <div style={{display:"flex",flexDirection:"column",height:"100%"}}>
      <div className="panel-header">
        <div>
          <div className="panel-title">INPUT</div>
          <div className="panel-sub">SIGNAL INTAKE</div>
        </div>
        <div style={{display:"flex",alignItems:"center",gap:6}}>
          <span className="f-data" style={{fontSize:9,color:"var(--txt-dim)"}}>
            {beats.length} SIG
          </span>
          <button className="btn-icon" style={{width:24,height:24,fontSize:9}}
            onClick={onScanBeats} title="Scan beats folder">⟳</button>
        </div>
      </div>

      <div className="panel-body" style={{display:"flex",flexDirection:"column"}}>

        {/* Beat List */}
        <div className="lbl-xs" style={{marginBottom:6}}>SIGNAL SOURCE</div>
        <div style={{marginBottom:0,flexShrink:0}}>
          {beats.length === 0 ? (
            <div style={{padding:"14px 8px",textAlign:"center",color:"var(--txt-dim)",
              fontSize:10,fontFamily:"var(--font-data)",lineHeight:1.8}}>
              NO SIGNALS DETECTED<br/>
              <span style={{fontSize:8,letterSpacing:".1em"}}>DROP .WAV INTO /BEATS</span>
            </div>
          ) : beats.map((b) => (
            <div key={b.id}
              className={`beat-item ${b.id === selectedBeatId ? "sel" : ""}`}
              onClick={() => onSelectBeat(b.id)}>
              <BeatWave active={b.id === selectedBeatId} bpm={parseInt(bpm)||140} />
              <div style={{flex:1,minWidth:0}}>
                <div className="beat-name">{b.filename}</div>
                <div className="beat-meta">{b.size_mb} MB</div>
              </div>
              <div className="f-data" style={{fontSize:8,color:"var(--txt-dim)",flexShrink:0}}>
                {b.status === "pending" ? "READY" : b.status.toUpperCase()}
              </div>
            </div>
          ))}
        </div>

        <SecDiv label="TARGET LOCK" />

        {/* Combo Presets */}
        <ComboPresets combos={combos} onLoad={onLoadCombo}
          onSave={onSaveCombo} onDelete={onDeleteCombo}
          artist1={artist1} artist2={artist2} vibe={vibe} />

        <div style={{height:10}} />

        {/* Artists */}
        <ArtistDropdown label="ARTIST 1" value={artist1} onSelect={setArtist1} allTiers={allTiers} />
        <div style={{height:6}} />
        <ArtistDropdown label="ARTIST 2" value={artist2} onSelect={setArtist2}
          allTiers={allTiers} optional onClear={() => setArtist2("")} />

        <div style={{height:10}} />

        {/* Beat Name */}
        <div className="field">
          <label className="field-label">BEAT DESIGNATION</label>
          <input className="field-input" value={beatName}
            onChange={(e) => setBeatName(e.target.value)}
            placeholder="ENTER NAME..." />
        </div>
        <div style={{height:6}} />

        {/* BPM + Key */}
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:6}}>
          <div className="field">
            <label className="field-label">BPM</label>
            <input className="field-input" type="number" value={bpm}
              onChange={(e) => setBpm(e.target.value)}
              placeholder="140" style={{fontFamily:"var(--font-data)"}} />
          </div>
          <div className="field">
            <label className="field-label">KEY</label>
            <select className="field-input" value={beatKey}
              onChange={(e) => setBeatKey(e.target.value)}>
              {KEYS.map((k) => <option key={k} value={k}>{k}</option>)}
            </select>
          </div>
        </div>
        <div style={{height:8}} />

        {/* Vibe */}
        <div className="lbl-xs" style={{marginBottom:5}}>VIBE</div>
        <div style={{display:"flex",flexWrap:"wrap",gap:3,marginBottom:10}}>
          {["rage","melodic","trap","drill","hyperpop","rnb"].map((v) => (
            <button key={v} className={`chip ${vibe===v?"active":""}`}
              onClick={() => setVibe(v)}>{v}</button>
          ))}
        </div>

        {/* Mood */}
        <div className="lbl-xs" style={{marginBottom:5}}>MOOD</div>
        <div className="mood-wrap">
          {Object.entries(MOODS).map(([key, m]) => (
            <button key={key} className={`chip ${mood===key?"active":""}`}
              onClick={() => setMood(mood===key ? "" : key)}>
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* Lock Target CTA */}
      <div className="panel-footer">
        <button className="btn btn-cta"
          disabled={!selectedBeatId || !artist1 || !beatName || !bpm}
          onClick={onLockTarget}
          style={{fontSize:11,letterSpacing:".2em"}}>
          {locked ? "TARGET LOCKED ✓" : "LOCK TARGET →"}
        </button>
      </div>
    </div>
  );
}

// ─── ARTWORK BROWSER ─────────────────────────────────
function ArtworkBrowser({ artworks, vibeTab, onVibeTab, selected, onSelect, compact }) {
  const vibes = Object.keys(artworks);
  const rawImgs = artworks[vibeTab]?.images || [];
  const imgs = rawImgs.map((img) => (typeof img === "string" ? img : img.filename));
  // compact=true → 3-col small grid; false → 2-col
  const gridCols = compact ? "repeat(3,1fr)" : "repeat(2,1fr)";

  return (
    <div>
      <div style={{display:"flex",gap:4,marginBottom:8,flexWrap:"wrap"}}>
        {vibes.map((v) => (
          <button key={v} className={`chip ${compact?"":"chip-lg"} ${vibeTab===v?"active":""}`}
            onClick={() => onVibeTab(v)}>{v}</button>
        ))}
      </div>
      {imgs.length === 0 ? (
        <div style={{padding:"16px",textAlign:"center",color:"var(--txt-dim)",fontSize:10,fontFamily:"var(--font-data)"}}>
          NO ARTWORKS IN /ARTWORKS/{vibeTab}
        </div>
      ) : (
        <div style={{display:"grid",gridTemplateColumns:gridCols,gap:compact?5:7}}>
          {imgs.map((filename) => {
            const rel = `${vibeTab}/${filename}`;
            const sel = selected === rel;
            const imgUrl = `${API}/artworks/image/${vibeTab}/${encodeURIComponent(filename)}`;
            return (
              <div key={filename} className={`art-item ${sel?"sel":""}`} onClick={() => onSelect(rel)}>
                <img src={imgUrl} alt={filename} loading="lazy" />
                <div className="art-scan" />
                {sel && <div className="art-sel-badge">SEL</div>}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── LUT TUNER DRAWER ────────────────────────────────
const TUNER_GROUPS = {
  TONE: [
    {key:"exposure",    label:"EXPOSURE",    min:-2,  max:2,   step:.01, def:0},
    {key:"contrast",    label:"CONTRAST",    min:-100,max:100, step:1,   def:0},
    {key:"highlights",  label:"HIGHLIGHTS",  min:-100,max:100, step:1,   def:0},
    {key:"shadows",     label:"SHADOWS",     min:-100,max:100, step:1,   def:0},
    {key:"whites",      label:"WHITES",      min:-100,max:100, step:1,   def:0},
    {key:"blacks",      label:"BLACKS",      min:-100,max:100, step:1,   def:0},
  ],
  CHROMA: [
    {key:"saturation",  label:"SATURATION",  min:-100,max:100, step:1,   def:0},
    {key:"vibrance",    label:"VIBRANCE",    min:-100,max:100, step:1,   def:0},
    {key:"hue_shift",   label:"HUE SHIFT",   min:-180,max:180, step:1,   def:0},
    {key:"temperature", label:"TEMPERATURE", min:-100,max:100, step:1,   def:0},
    {key:"tint",        label:"TINT",        min:-100,max:100, step:1,   def:0},
  ],
  LUMINANCE: [
    {key:"clarity",     label:"CLARITY",     min:-100,max:100, step:1,   def:0},
    {key:"dehaze",      label:"DEHAZE",      min:-100,max:100, step:1,   def:0},
    {key:"gamma",       label:"GAMMA",       min:.1,  max:3,   step:.01, def:1},
  ],
  TEXTURE: [
    {key:"grain",       label:"GRAIN",       min:0,   max:100, step:1,   def:0},
    {key:"blur",        label:"BLUR",        min:0,   max:10,  step:.1,  def:0},
    {key:"sharpen",     label:"SHARPEN",     min:0,   max:100, step:1,   def:0},
    {key:"master",      label:"MASTER BLEND",min:0,   max:1,   step:.01, def:1},
  ],
};

function LutTunerDrawer({ params, onChange, onReset, presetName }) {
  const [group, setGroup] = useState("TONE");

  const handleSlider = (key, val) => {
    onChange({ ...params, [key]: parseFloat(val) });
  };

  return (
    <div style={{padding:16}}>
      <div style={{display:"flex",gap:5,marginBottom:16,alignItems:"center",flexWrap:"wrap"}}>
        {Object.keys(TUNER_GROUPS).map((g) => (
          <button key={g} className={`chip ${group===g?"active":""}`}
            style={{fontSize:11}} onClick={() => setGroup(g)}>{g}</button>
        ))}
        <button className="btn-ghost"
          style={{height:32,fontSize:10,marginLeft:"auto",padding:"0 14px",border:"1px solid var(--brd-idle)"}}
          onClick={onReset}>RESET ALL</button>
      </div>
      <div>
        {(TUNER_GROUPS[group] || []).map((s) => {
          const val = params[s.key] !== undefined ? params[s.key] : s.def;
          const isFloat = ["exposure","gamma","master","blur"].includes(s.key);
          const displayVal = typeof val === "number" ? val.toFixed(isFloat ? 2 : 0) : val;
          return (
            <div key={s.key} className="slider-row">
              <span className="slider-lbl">{s.label}</span>
              <input type="range" className="lut-slider"
                min={s.min} max={s.max} step={s.step} value={val}
                onChange={(e) => handleSlider(s.key, e.target.value)} />
              <span className="slider-val">{displayVal}</span>
            </div>
          );
        })}
      </div>
      {presetName && (
        <div style={{fontSize:10,fontFamily:"var(--font-data)",color:"var(--txt-dim)",
          marginTop:12,letterSpacing:".06em"}}>
          BASE: {presetName.toUpperCase()} - sliders override preset params
        </div>
      )}
    </div>
  );
}

// ─── CROP SELECTOR ───────────────────────────────────
// Drag-based 1:1 square crop overlay on artwork image
function CropSelector({ imgUrl, cropRect, onChange }) {
  const containerRef = useRef(null);
  const dragRef      = useRef(null);
  const [natSize, setNatSize] = useState({ w: 1, h: 1 });

  const { x: cx = 0, y: cy = 0, size: csz = 1 } = cropRect;

  const onImgLoad = (e) => setNatSize({ w: e.target.naturalWidth, h: e.target.naturalHeight });

  const startDrag = (e) => {
    e.preventDefault();
    const rect = containerRef.current.getBoundingClientRect();
    dragRef.current = { mx: e.clientX, my: e.clientY, cx, cy, rw: rect.width, rh: rect.height };

    const onMove = (ev) => {
      const { mx, my, cx: ox, cy: oy, rw, rh } = dragRef.current;
      const { w: nw, h: nh } = natSize;
      const minDim = Math.min(nw, nh);
      // fraction of image per container pixel
      const fx = (ev.clientX - mx) / rw;
      const fy = (ev.clientY - my) / rh;
      const maxX = Math.max(0, 1 - csz * minDim / nw);
      const maxY = Math.max(0, 1 - csz * minDim / nh);
      onChange({
        x: Math.max(0, Math.min(maxX, ox + fx)),
        y: Math.max(0, Math.min(maxY, oy + fy)),
        size: csz,
      });
    };
    const onUp = () => {
      dragRef.current = null;
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
    };
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  };

  // Visual: compute crop box as % of displayed container
  const { w: nw, h: nh } = natSize;
  const minDim   = Math.min(nw, nh);
  const boxW_pct = (csz * minDim / nw) * 100;
  const boxH_pct = (csz * minDim / nh) * 100;
  const boxL_pct = cx * 100;
  const boxT_pct = cy * 100;

  return (
    <div ref={containerRef}
      style={{ position:"relative", cursor:"crosshair", userSelect:"none", lineHeight:0 }}
      onMouseDown={startDrag}>
      <img src={imgUrl} alt="crop" onLoad={onImgLoad}
        style={{ width:"100%", display:"block", pointerEvents:"none" }} />
      {/* Dark overlay — 4 regions around crop box */}
      {[
        // top
        { left:0, top:0, width:"100%", height:`${boxT_pct}%` },
        // bottom
        { left:0, top:`${boxT_pct + boxH_pct}%`, width:"100%", bottom:0, height:`${100 - boxT_pct - boxH_pct}%` },
        // left
        { left:0, top:`${boxT_pct}%`, width:`${boxL_pct}%`, height:`${boxH_pct}%` },
        // right
        { left:`${boxL_pct + boxW_pct}%`, top:`${boxT_pct}%`, right:0, width:`${100 - boxL_pct - boxW_pct}%`, height:`${boxH_pct}%` },
      ].map((s, i) => (
        <div key={i} style={{ position:"absolute", background:"rgba(6,35,29,.72)", pointerEvents:"none", ...s }} />
      ))}
      {/* Crop border */}
      <div style={{
        position:"absolute",
        left:`${boxL_pct}%`, top:`${boxT_pct}%`,
        width:`${boxW_pct}%`, height:`${boxH_pct}%`,
        border:"2px solid var(--accent)",
        boxSizing:"border-box", pointerEvents:"none",
        boxShadow:"0 0 12px rgba(227,239,38,.35)",
      }}>
        {/* Center cross-hair */}
        <div style={{ position:"absolute", inset:0, display:"grid", placeItems:"center" }}>
          <div style={{ width:16, height:16, position:"relative" }}>
            <div style={{ position:"absolute", top:7, left:0, right:0, height:2, background:"rgba(227,239,38,.6)" }} />
            <div style={{ position:"absolute", left:7, top:0, bottom:0, width:2, background:"rgba(227,239,38,.6)" }} />
          </div>
        </div>
        {/* Corner anchors */}
        {[{top:0,left:0},{top:0,right:0},{bottom:0,left:0},{bottom:0,right:0}].map((s,i) => (
          <div key={i} style={{ position:"absolute", width:10, height:10,
            borderColor:"var(--accent)", borderStyle:"solid",
            borderTopWidth:i<2?2:0, borderBottomWidth:i>=2?2:0,
            borderLeftWidth:i%2===0?2:0, borderRightWidth:i%2===1?2:0,
            ...s }} />
        ))}
      </div>
      {/* Instruction */}
      <div style={{ position:"absolute", bottom:6, left:0, right:0,
        textAlign:"center", fontFamily:"var(--font-hud)", fontSize:9,
        color:"rgba(227,239,38,.7)", letterSpacing:".1em", pointerEvents:"none" }}>
        DRAG TO REPOSITION
      </div>
    </div>
  );
}

// ─── QUALITY MODAL ───────────────────────────────────
function QualityModal({ onSelect }) {
  const opts = [
    { id:"2K", label:"2K",  res:"2560 × 1440", desc:"Crisp on 4K/2K displays\nLarger file, best clarity" },
    { id:"HD", label:"HD",  res:"1920 × 1080", desc:"Standard YouTube HD\nFast render, universal" },
  ];
  return (
    <div className="modal-overlay">
      <div className="modal-panel">
        <div className="modal-hdr">
          <span className="modal-ttl">SELECT RENDER QUALITY</span>
        </div>
        <div className="quality-grid">
          {opts.map((o) => (
            <button key={o.id} className="quality-card" onClick={() => onSelect(o.id)}>
              <div className="quality-badge">{o.label}</div>
              <div className="quality-res">{o.res}</div>
              <div className="quality-desc">{o.desc.split("\n").map((l,i) => <div key={i}>{l}</div>)}</div>
            </button>
          ))}
        </div>
        <div style={{padding:"10px 16px 16px",textAlign:"center"}}>
          <span className="f-data" style={{fontSize:10,color:"var(--txt-dim)",letterSpacing:".08em"}}>
            Artwork upscaled with multi-pass LANCZOS + UnsharpMask before render
          </span>
        </div>
      </div>
    </div>
  );
}

// ─── PROCESS PANEL ───────────────────────────────────
function ProcessPanel({
  artworks, artVibeTab, setArtVibeTab, selectedArtwork, setSelectedArtwork,
  lutPresets, selectedPreset, setSelectedPreset,
  lutParams, setLutParams, tunerOpen, setTunerOpen,
  previewUrl, loadingPreview, onPreview,
  cropEnabled, setCropEnabled, cropRect, setCropRect,
  seoData, titleStyle, setTitleStyle,
  drop, setDrop, outro, setOutro,
  onGenerateSeo, generating,
  onRender, rendering, renderResult, renderProgress = 0,
  artist1, artist2, beatName, bpm, beatKey, vibe, mood, locked,
}) {
  // URL for the raw artwork (to display in crop selector)
  const [vibeTab, filename] = selectedArtwork ? selectedArtwork.split("/") : [null, null];
  const rawArtUrl = filename
    ? `${API}/artworks/image/${vibeTab}/${encodeURIComponent(filename)}`
    : null;

  return (
    <div style={{display:"flex",flexDirection:"column",height:"100%"}}>
      {/* Header */}
      <div className="panel-header">
        <div>
          <div className="panel-title">PROCESS</div>
          <div className="panel-sub">SIGNAL PROCESSING · v4.6</div>
        </div>
        {selectedArtwork && (
          <div className="f-data" style={{fontSize:10,color:"var(--txt-dim)"}}>
            {filename?.substring(0,22) || ""}
          </div>
        )}
      </div>

      {/* Body */}
      <div className="panel-body">
        {!locked ? (
          <div className="awaiting-signal">
            <div className="awaiting-signal-icon">◈</div>
            <div className="awaiting-signal-title">AWAITING SIGNAL</div>
            <div className="awaiting-signal-sub">Lock target in INPUT panel</div>
          </div>
        ) : tunerOpen ? (
          <LutTunerDrawer params={lutParams} onChange={setLutParams}
            onReset={() => setLutParams({})} presetName={selectedPreset} />
        ) : (
          <>
            {/* ── 2-COLUMN: Artwork browser LEFT | Preview/Crop RIGHT ── */}
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14,marginBottom:14}}>
              {/* LEFT: Artwork browser */}
              <div>
                <div className="lbl-xs" style={{marginBottom:6}}>VISUAL SPECTRUM</div>
                {Object.keys(artworks).length > 0 && (
                  <ArtworkBrowser compact
                    artworks={artworks} vibeTab={artVibeTab}
                    onVibeTab={setArtVibeTab}
                    selected={selectedArtwork} onSelect={(rel) => {
                      setSelectedArtwork(rel);
                      setCropRect({ x:0, y:0, size:1 }); // reset crop on new artwork
                    }} />
                )}
              </div>

              {/* RIGHT: Preview / Crop toggle */}
              <div>
                {/* Toggle: PREVIEW | CROP 1:1 */}
                <div style={{display:"flex",gap:4,marginBottom:8}}>
                  <button className={`chip ${!cropEnabled?"active":""}`} style={{flex:1}}
                    onClick={() => setCropEnabled(false)}>PREVIEW</button>
                  <button className={`chip ${cropEnabled?"active":""}`} style={{flex:1}}
                    onClick={() => setCropEnabled(true)}>CROP 1:1</button>
                </div>

                {cropEnabled ? (
                  /* ── CROP MODE ── */
                  <div>
                    {rawArtUrl ? (
                      <CropSelector imgUrl={rawArtUrl}
                        cropRect={cropRect} onChange={setCropRect} />
                    ) : (
                      <div className="lut-preview-empty">SELECT ARTWORK FIRST</div>
                    )}
                    <div style={{marginTop:8}}>
                      {/* Size slider */}
                      <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:6}}>
                        <span className="lbl-xs" style={{width:44,flexShrink:0}}>ZOOM</span>
                        <input type="range" className="lut-slider"
                          min={0.2} max={1} step={0.01}
                          value={cropRect.size}
                          onChange={(e) => setCropRect(r => ({...r, size:parseFloat(e.target.value)}))} />
                        <span className="slider-val">{Math.round(cropRect.size*100)}%</span>
                      </div>
                      <button className="btn btn-sec" style={{width:"100%",marginTop:2}}
                        onClick={() => setCropRect({ x:0, y:0, size:1 })}>
                        RESET CROP
                      </button>
                    </div>
                  </div>
                ) : (
                  /* ── PREVIEW MODE ── */
                  <div>
                    <div className="lbl-xs" style={{marginBottom:6}}>FILTER PREVIEW</div>
                    <div className="lut-preview-pane" style={{height:200}}>
                      {previewUrl ? (
                        <img src={previewUrl} alt="LUT preview" />
                      ) : (
                        <div className="lut-preview-empty">
                          SELECT ARTWORK<br/>
                          <span style={{fontSize:8,opacity:.6}}>THEN HIT PREVIEW</span>
                        </div>
                      )}
                      {loadingPreview && (
                        <div className="lut-preview-loading">PROCESSING...</div>
                      )}
                    </div>

                    {/* LUT Preset chips */}
                    <div style={{marginTop:10}}>
                      <div className="lbl-xs" style={{marginBottom:6}}>BASE PRESET</div>
                      <div style={{display:"flex",flexWrap:"wrap",gap:4,marginBottom:8}}>
                        {Object.keys(lutPresets).map((k) => (
                          <button key={k} className={`chip ${selectedPreset===k?"active":""}`}
                            onClick={() => setSelectedPreset(k)}>
                            {k.startsWith("⚡") ? "★ " + k.slice(1) : k.toUpperCase()}
                          </button>
                        ))}
                      </div>
                      <button className="btn btn-sec" style={{width:"100%"}}
                        disabled={!selectedArtwork || loadingPreview}
                        onClick={onPreview}>
                        {loadingPreview ? "PROCESSING..." : "⚡ PREVIEW FILTER"}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <SecDiv label="METADATA" />

            {/* DROP + OUTRO */}
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8,marginBottom:10}}>
              <div className="field">
                <label className="field-label">DROP TIMESTAMP</label>
                <input className="field-input" value={drop}
                  onChange={(e) => setDrop(e.target.value)}
                  placeholder="0:25" style={{fontFamily:"var(--font-data)"}} />
              </div>
              <div className="field">
                <label className="field-label">OUTRO TIMESTAMP</label>
                <input className="field-input" value={outro}
                  onChange={(e) => setOutro(e.target.value)}
                  placeholder="2:30" style={{fontFamily:"var(--font-data)"}} />
              </div>
            </div>

            {/* Title Style */}
            <div className="lbl-xs" style={{marginBottom:6}}>TITLE FORMAT</div>
            <div style={{display:"flex",flexWrap:"wrap",gap:4,marginBottom:12}}>
              {Object.keys(TITLE_STYLES).map((s) => (
                <button key={s} className={`chip ${titleStyle===s?"active":""}`}
                  onClick={() => setTitleStyle(s)}>
                  {s.replace(/_/g," ").toUpperCase()}
                </button>
              ))}
            </div>

            <SecDiv label="SEO ENGINE" />

            <button className="btn btn-cta" style={{marginBottom:10}}
              disabled={!artist1||!beatName||!bpm||generating}
              onClick={onGenerateSeo}>
              {generating ? "GENERATING..." : "GENERATE SEO PACKAGE"}
            </button>


            {seoData && (
              <div style={{marginBottom:12,background:"rgba(7,102,83,.08)",border:"1px solid rgba(7,102,83,.25)",borderRadius:4,padding:"10px 12px"}}>
                {/* Title row */}
                <div style={{display:"flex",alignItems:"flex-start",gap:8,marginBottom:10}}>
                  <div className="title-prev" style={{flex:1,fontSize:11,lineHeight:1.5}}>{seoData.title}</div>
                  <button className="btn-ghost" style={{flexShrink:0,height:24,fontSize:9,padding:"0 8px",border:"1px solid var(--brd-idle)"}}
                    onClick={() => { navigator.clipboard.writeText(seoData.title); }}>COPY</button>
                </div>

                {/* Score + stats row */}
                <div style={{display:"flex",alignItems:"center",gap:12,marginBottom:10}}>
                  <DbMeter score={seoData.seo_score?.overall ?? 0} />
                  <div style={{display:"flex",gap:12}}>
                    <div className="f-data" style={{fontSize:10,color:"var(--txt-dim)"}}>
                      <span style={{color:"var(--accent)"}}>{seoData.tags?.length || 0}</span> TAGS
                    </div>
                    <div className="f-data" style={{fontSize:10,color:"var(--txt-dim)"}}>
                      <span style={{color:"var(--accent)"}}>{seoData.description?.length || 0}</span> CHARS
                    </div>
                    <div className="f-data" style={{fontSize:10,color:"var(--txt-dim)"}}>
                      SCORE: <span style={{color:"var(--accent)"}}>{Math.round((seoData.seo_score?.overall ?? 0)*100)}%</span>
                    </div>
                  </div>
                </div>

                {/* Tags */}
                {seoData.tags?.length > 0 && (
                  <div style={{marginBottom:8}}>
                    <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:4}}>
                      <span className="lbl-xs">TAGS</span>
                      <button className="btn-ghost" style={{height:20,fontSize:8,padding:"0 6px",border:"1px solid var(--brd-idle)"}}
                        onClick={() => { navigator.clipboard.writeText(seoData.tags.join(", ")); }}>COPY ALL</button>
                    </div>
                    <div style={{display:"flex",flexWrap:"wrap",gap:3}}>
                      {seoData.tags.map((t,i) => (
                        <span key={i} style={{
                          fontFamily:"var(--font-data)",fontSize:9,
                          background:"rgba(154,255,98,.08)",border:"1px solid rgba(154,255,98,.2)",
                          borderRadius:2,padding:"2px 5px",color:"var(--txt-dim)",letterSpacing:".04em"
                        }}>{t}</span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Description preview + copy */}
                <div>
          <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:4}}>
                    <span className="lbl-xs">DESCRIPTION</span>
                    <button className="btn-ghost" style={{height:20,fontSize:8,padding:"0 6px",border:"1px solid var(--brd-idle)"}}
                      onClick={() => { navigator.clipboard.writeText(seoData.description || ""); }}>COPY</button>
                  </div>
                  <div style={{
                    fontFamily:"var(--font-data)",fontSize:9,color:"var(--txt-dim)",
                    lineHeight:1.7,maxHeight:80,overflowY:"auto",
                    background:"rgba(0,0,0,.2)",borderRadius:3,padding:"6px 8px",
                    whiteSpace:"pre-wrap",letterSpacing:".03em"
                  }}>{seoData.description}</div>
                </div>
              </div>
            )}


            <SecDiv label="RENDER" />

            <button className="btn btn-cta"
              disabled={!selectedArtwork || !seoData || rendering}
              onClick={onRender}
              style={{background: rendering ? "var(--brd-idle)" : undefined}}>
              {rendering ? `RENDERING... ${renderProgress}%` : "RENDER MP4 ▶"}
            </button>
            {rendering && (
              <div className="render-progress" style={{marginTop:8}}>
                <div className="render-progress-track">
                  <div className="render-progress-fill" style={{width:`${renderProgress}%`}} />
                </div>
                <div className="render-progress-lbl">
                  {renderProgress < 25 ? "PREPARING ARTWORK..." :
                   renderProgress < 55 ? "APPLYING LUT + UPSCALE..." :
                   renderProgress < 85 ? "ENCODING MP4..." : "FINALIZING..."}
                  <span style={{marginLeft:"auto"}}>{renderProgress}%</span>
                </div>
              </div>
            )}
            {renderResult && (
              <div className="ok-banner" style={{marginTop:8}}>
                ✓ {renderResult.file_size_mb} MB - READY TO DEPLOY
              </div>
            )}
          </>
        )}
      </div>

      {/* Footer — Spectral Tuner toggle */}
      <div className="panel-footer">
        <button className={`btn btn-sec ${tunerOpen?"active":""}`}
          style={{width:"100%",borderColor:tunerOpen?"var(--accent)":undefined,
            color:tunerOpen?"var(--accent)":undefined}}
          disabled={!locked}
          onClick={() => setTunerOpen(!tunerOpen)}>
          {tunerOpen ? "← CLOSE SPECTRAL TUNER" : "⚡ OPEN SPECTRAL TUNER"}
        </button>
      </div>
    </div>
  );
}

// ─── CUSTOM CALENDAR ─────────────────────────────────
function CustomCalendar({ value, onChange }) {
  const today = new Date();
  const todayMidnight = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const [view, setView] = useState({ y: today.getFullYear(), m: today.getMonth() });
  const DAYS = ["MO","TU","WE","TH","FR","SA","SU"];
  const MONTHS = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"];

  const firstDay = new Date(view.y, view.m, 1).getDay();
  const offset = (firstDay + 6) % 7; // Mon=0
  const daysInMonth = new Date(view.y, view.m + 1, 0).getDate();

  const cells = [];
  for (let i = 0; i < offset; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);

  const selDate = value ? new Date(value + "T00:00:00") : null;
  const isSelected = (d) => selDate && selDate.getFullYear()===view.y &&
    selDate.getMonth()===view.m && selDate.getDate()===d;
  const isToday = (d) => today.getFullYear()===view.y &&
    today.getMonth()===view.m && today.getDate()===d;
  // Bugun secilebilir olmali: gece yarisiyla karsilastir (saat dahil edilirse bugun "gecmis" sayiliyordu)
  const isPast = (d) => new Date(view.y, view.m, d) < todayMidnight;

  const handleDay = (d) => {
    if (!d || isPast(d)) return;
    const iso = `${view.y}-${String(view.m+1).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
    onChange(iso);
  };

  return (
    <div>
      <div className="cal-hdr">
        <button className="btn-icon" onClick={() => setView(v => {
          const m = v.m === 0 ? 11 : v.m-1;
          return { y: v.m===0 ? v.y-1 : v.y, m };
        })}>{"<"}</button>
        <span className="cal-ttl">{MONTHS[view.m]} {view.y}</span>
        <button className="btn-icon" onClick={() => setView(v => {
          const m = v.m === 11 ? 0 : v.m+1;
          return { y: v.m===11 ? v.y+1 : v.y, m };
        })}>{">"}</button>
      </div>
      <div className="cal-grid">
        {DAYS.map((d) => <div key={d} className="cal-day-name">{d}</div>)}
        {cells.map((d, i) => (
          <div key={i}
            className={`cal-day ${!d?"empty":""} ${d&&isSelected(d)?"sel":""}
              ${d&&isToday(d)&&!isSelected(d)?"today":""} ${d&&isPast(d)?"past":""}`.trim()}
            onClick={() => handleDay(d)}>
            {d || ""}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── PUBLISH MODAL ────────────────────────────────────
// Single modal: Publish Now (instant) or Schedule (future)
function PublishModal({ onClose, onPublishNow, onSchedule,
  date, onDate, hour, onHour, min, onMin,
  privacy, onPrivacy, deploying
}) {
  const today = new Date();
  const todayIso = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,"0")}-${String(today.getDate()).padStart(2,"0")}`;
  const nowHour = today.getHours();

  const trtToUtc = (h, m) => {
    let utcMin = h * 60 + m - 180;
    if (utcMin < 0) utcMin += 1440;
    return `${String(Math.floor(utcMin/60)).padStart(2,"0")}:${String(utcMin%60).padStart(2,"0")}`;
  };

  // If today is selected, only allow hours >= current hour
  const isToday = date === todayIso;
  const minHour = isToday ? nowHour : 0;
  const effectiveHour = isToday && hour < minHour ? minHour : hour;

  const PRIVACY_OPTS = [
    { value: "public",    label: "PUBLIC",     icon: "🌐" },
    { value: "unlisted",  label: "UNLISTED",   icon: "🔗" },
    { value: "private",   label: "PRIVATE",    icon: "🔒" },
  ];

  return (
    <div className="modal-overlay" onClick={(e) => e.target===e.currentTarget && onClose()}>
      <div className="modal-panel" style={{maxWidth:520}}>
        <div className="modal-hdr">
          <span className="modal-ttl">PUBLISH SIGNAL</span>
          <button className="btn-icon" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">

          {/* Privacy selector */}
          <div style={{marginBottom:14}}>
            <div className="lbl-xs" style={{marginBottom:8}}>VISIBILITY</div>
            <div style={{display:"flex",gap:6}}>
              {PRIVACY_OPTS.map(p => (
                <button key={p.value}
                  onClick={() => onPrivacy(p.value)}
                  style={{
                    flex:1, padding:"8px 4px", border:"1px solid",
                    borderColor: privacy===p.value ? "var(--accent)" : "var(--brd-idle)",
                    background: privacy===p.value ? "rgba(154,255,98,.1)" : "transparent",
                    color: privacy===p.value ? "var(--accent)" : "var(--txt-dim)",
                    fontFamily:"var(--font-data)", fontSize:9, letterSpacing:".1em",
                    cursor:"pointer", borderRadius:3, transition:"all .15s",
                  }}>
                  <div style={{fontSize:14,marginBottom:3}}>{p.icon}</div>
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Calendar */}
          <CustomCalendar value={date} onChange={onDate} />

          {/* Time picker */}
          <div className="time-spinner" style={{marginTop:12}}>
            <div className="time-col">
              <button className="time-btn" onClick={() => {
                const next = (effectiveHour+1)%24;
                onHour(isToday && next < minHour ? minHour : next);
              }}>▲</button>
              <div className="time-val">{String(effectiveHour).padStart(2,"0")}</div>
              <button className="time-btn" onClick={() => {
                const prev = (effectiveHour+23)%24;
                onHour(isToday && prev < minHour ? minHour : prev);
              }}>▼</button>
            </div>
            <div className="time-sep">:</div>
            <div className="time-col">
              <button className="time-btn" onClick={() => onMin((min+5)%60)}>▲</button>
              <div className="time-val">{String(min).padStart(2,"0")}</div>
              <button className="time-btn" onClick={() => onMin((min+55)%60)}>▼</button>
            </div>
            <div className="time-tz">TRT (UTC+3)</div>
          </div>
          <div className="time-utc" style={{marginTop:6}}>
            UTC: {date || "---"} {trtToUtc(effectiveHour, min)}
          </div>
        </div>

        <div className="modal-ftr" style={{flexDirection:"column",gap:8}}>
          {/* Primary: schedule */}
          <button className="btn btn-cta" style={{width:"100%"}}
            disabled={!date || deploying}
            onClick={() => onSchedule(effectiveHour)}>
            {deploying ? "TRANSMITTING..." : `📡 SCHEDULE — ${date||"SELECT DATE"} ${String(effectiveHour).padStart(2,"0")}:${String(min).padStart(2,"0")} TRT`}
          </button>
          {/* Secondary: publish now */}
          <button className="btn btn-sec" style={{width:"100%",fontSize:10}}
            disabled={deploying}
            onClick={onPublishNow}>
            {deploying ? "..." : "⚡ PUBLISH NOW (INSTANT)"}
          </button>
          <button className="btn-ghost" style={{width:"100%",fontSize:9,padding:"6px"}}
            onClick={onClose}>CANCEL</button>
        </div>
      </div>
    </div>
  );
}

// ─── PLATFORM SELECTOR ────────────────────────────────
function PlatformSelector({ selected, onToggle }) {
  return (
    <div>
      <div className="lbl-xs" style={{marginBottom:6}}>DEPLOY PLATFORMS</div>
      <div className="platform-grid">
        {Object.entries(PLATFORMS).map(([key, p]) => (
          <div key={key} className={`plat-card ${selected[key]?"active":""}`}
            onClick={() => onToggle(key)}>
            <span className="plat-icon">{p.icon}</span>
            <span className="plat-name">{p.label}</span>
            <div className="plat-check">
              <span className="plat-check-mark">✓</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── ANALYTICS FEED ──────────────────────────────────
function AnalyticsFeed({ channelInfo, loading }) {
  if (loading) return (
    <div style={{padding:"20px 0",textAlign:"center",color:"var(--txt-dim)",fontSize:10,fontFamily:"var(--font-data)"}}>
      FETCHING ANALYTICS...
    </div>
  );
  if (!channelInfo || !channelInfo.success) return (
    <div style={{padding:"16px 0",textAlign:"center",color:"var(--txt-dim)"}}>
      <div className="f-data" style={{fontSize:10}}>CHANNEL NOT CONNECTED</div>
      <div className="f-data" style={{fontSize:8,marginTop:4}}>RUN: python youtube_upload.py --setup</div>
    </div>
  );
  const views = parseInt(channelInfo.video_count||0);
  const subs  = channelInfo.subscriber_count === "hidden" ? "PRIVATE" : channelInfo.subscriber_count;
  return (
    <div>
      <div style={{padding:"10px 0 12px",borderBottom:"1px solid rgba(7,102,83,.3)"}}>
        <div className="f-hud" style={{fontSize:9,color:"var(--txt-dim)",letterSpacing:".15em",marginBottom:4}}>
          CHANNEL
        </div>
        <div style={{fontSize:13,color:"var(--txt-hi)",fontFamily:"var(--font-hud)",letterSpacing:".08em"}}>
          {channelInfo.title}
        </div>
        <div style={{display:"flex",gap:16,marginTop:8}}>
          <div>
            <div className="f-data" style={{fontSize:18,color:"var(--accent)",lineHeight:1}}>
              {subs}
            </div>
            <div className="f-hud" style={{fontSize:8,color:"var(--txt-dim)",letterSpacing:".12em",marginTop:2}}>
              SUBSCRIBERS
            </div>
          </div>
          <div>
            <div className="f-data" style={{fontSize:18,color:"var(--txt-hi)",lineHeight:1}}>
              {channelInfo.video_count}
            </div>
            <div className="f-hud" style={{fontSize:8,color:"var(--txt-dim)",letterSpacing:".12em",marginTop:2}}>
              VIDEOS
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── OUTPUT PANEL ─────────────────────────────────────
function OutputPanel({
  renderResult, seoData,
  channelInfo, analyticsLoading,
  platforms, onTogglePlatform,
  ytPlaylists, selectedPlaylist, setSelectedPlaylist,
  onDeployNow, onSchedule,
  deployStatus, deploying,
  uploadProgress = 0,
  publishModalOpen, setPublishModalOpen,
  scheduleDate, setScheduleDate,
  scheduleHour, setScheduleHour, scheduleMin, setScheduleMin,
  onConfirmSchedule, privacy, setPrivacy,
}) {
  return (
    <div style={{display:"flex",flexDirection:"column",height:"100%"}}>
      <div className="panel-header">
        <div>
          <div className="panel-title">OUTPUT</div>
          <div className="panel-sub">SIGNAL DEPLOYED</div>
        </div>
      </div>

      <div className="panel-body" style={{display:"flex",flexDirection:"column",gap:0}}>

        {/* Analytics */}
        <AnalyticsFeed channelInfo={channelInfo} loading={analyticsLoading} />

        <SecDiv label="DEPLOY CONTROL" />

        {/* Platform Selector */}
        <PlatformSelector selected={platforms} onToggle={onTogglePlatform} />

        <div style={{height:10}} />

        {/* Playlist selector (YouTube) */}
        {platforms.youtube && ytPlaylists.length > 0 && (
          <div className="field" style={{marginBottom:8}}>
            <label className="field-label">YOUTUBE PLAYLIST</label>
            <select className="field-input" value={selectedPlaylist}
              onChange={(e) => setSelectedPlaylist(e.target.value)}>
              <option value="">- No playlist -</option>
              {ytPlaylists.map((pl) => (
                <option key={pl.id} value={pl.id}>{pl.title} ({pl.item_count})</option>
              ))}
            </select>
          </div>
        )}

        {/* Deploy status bars */}
        {Object.keys(deployStatus).length > 0 && (
          <div style={{marginBottom:10}}>
            <div className="lbl-xs" style={{marginBottom:6}}>TRANSMISSION STATUS</div>
            {Object.entries(deployStatus).map(([plat, ds]) => (
              <div key={plat}>
                <div className="deploy-row">
                  <span className="deploy-plat-name">{plat.toUpperCase()}</span>
                  <div className="deploy-track" style={{position:"relative"}}>
                    {ds.status === "uploading" ? (
                      // ── Tahmini ilerleme barı: her 3 saniyede güncellenir ──
                      <div
                        style={{
                          height: "100%",
                          width: `${uploadProgress}%`,
                          background: "linear-gradient(90deg, #076653, #9AFF62)",
                          borderRadius: 2,
                          transition: "width 2.4s ease-out",
                          position: "absolute", left: 0, top: 0,
                        }}
                      />
                    ) : (
                      <div className={`deploy-fill`}
                        style={{
                          width: ds.status==="done" ? "100%" : ds.status==="error" ? "100%" : "0%",
                          background: ds.status==="error" ? "#e05555" : undefined,
                          transition: "width .4s",
                        }}
                      />
                    )}
                  </div>
                  <span
                    className={`deploy-status ${ds.status==="done"?"ok":ds.status==="error"?"err":"wait"}`}
                    style={ds.status==="uploading" ? {color:"#9AFF62",minWidth:48} : {}}
                  >
                    {ds.status==="done" ? "DEPLOYED" : ds.status==="error" ? "ERROR" :
                     ds.status==="uploading" ? `${uploadProgress}%` : ds.status==="unavailable" ? "N/A" : "QUEUED"}
                  </span>
                </div>
                {ds.status === "uploading" && (
                  <div style={{fontFamily:"var(--font-data)",fontSize:8,color:"#555",paddingLeft:6,marginTop:2,letterSpacing:".08em"}}>
                    {uploadProgress < 30 ? "CONNECTING..." : uploadProgress < 60 ? "UPLOADING VIDEO..." : uploadProgress < 85 ? "PROCESSING..." : "FINALIZING..."}
                  </div>
                )}
                {ds.status === "error" && ds.msg && (
                  <div style={{fontFamily:"var(--font-data)",fontSize:9,color:"#e05555",
                    padding:"3px 6px",marginTop:2,lineHeight:1.5,wordBreak:"break-word"}}>
                    ⚠ {ds.msg}
                  </div>
                )}
                {ds.url && (
                  <div style={{fontFamily:"var(--font-data)",fontSize:9,color:"var(--accent)",
                    padding:"3px 6px",marginTop:2}}>
                    <a href={ds.url} target="_blank" rel="noreferrer"
                      style={{color:"var(--accent)",textDecoration:"none"}}>
                      ▶ {ds.url}
                    </a>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {(platforms.soundcloud||platforms.instagram||platforms.beatstars) && (
          <div className="warn-banner" style={{fontSize:9,lineHeight:1.6}}>
            SC / IG / BS modules — FAZA 3 (coming next)
          </div>
        )}
      </div>

      {/* Single PUBLISH button footer */}
      <div className="panel-footer">
        {!renderResult ? (
          <div style={{textAlign:"center",color:"var(--txt-dim)",fontSize:10,fontFamily:"var(--font-data)"}}>
            RENDER TO UNLOCK DEPLOY
          </div>
        ) : (
          <button className="btn btn-cta" style={{width:"100%",fontSize:12,letterSpacing:".18em"}}
            disabled={deploying || !Object.values(platforms).some(Boolean)}
            onClick={() => setPublishModalOpen(true)}>
            {deploying ? "TRANSMITTING..." : "📡 PUBLISH"}
          </button>
        )}
      </div>

      {/* Publish Modal */}
      {publishModalOpen && (
        <PublishModal
          onClose={() => setPublishModalOpen(false)}
          onPublishNow={onDeployNow}
          onSchedule={(effectiveHour) => {
            onSchedule(effectiveHour);
          }}
          date={scheduleDate} onDate={setScheduleDate}
          hour={scheduleHour} onHour={setScheduleHour}
          min={scheduleMin} onMin={setScheduleMin}
          privacy={privacy} onPrivacy={setPrivacy}
          deploying={deploying}
        />
      )}
    </div>
  );
}

// ─── HEADER ──────────────────────────────────────────
const TABS = [
  { id:"beats",  label:"BEATS" },
  { id:"lut",    label:"LUT LAB" },
  { id:"deploy", label:"DEPLOY" },
];

// ─── JB LOGO — PNG (exact brand asset) ──────────────────────────────────────
function JBLogo({ size = 54 }) {
  return (
    <img
      src="/jetbox-logo.png"
      alt="JETBOX"
      style={{
        height: size,
        width: "auto",
        flexShrink: 0,
        objectFit: "contain",
        filter: "drop-shadow(0 0 6px rgba(154,255,98,.35))",
      }}
    />
  );
}

function AppHeader({ activeTab, setActiveTab, ytOk, ffmpegOk }) {
  return (
    <header className="app-header">
      <div className="hdr-top">
        <div className="hdr-logo">
          {/* PNG logo — exact brand asset, no SVG recreation */}
          <JBLogo size={46} />
          <div className="logo-sep" />
          <span className="logo-sub">SIGNAL AUTHORITY</span>
        </div>
        <LiveClock />
      </div>
      <div className="hdr-nav">
        {TABS.map((t) => (
          <button key={t.id}
            className={`nav-tab ${activeTab===t.id?"active":""}`}
            onClick={() => setActiveTab(t.id)}>
            {t.label}
          </button>
        ))}
        <div className="hdr-sys">
          <Dot state={ffmpegOk ? "ok" : "err"} />
          <span>FFMPEG</span>
          <Dot state={ytOk ? "ok" : "err"} />
          <span>YT API</span>
        </div>
      </div>
    </header>
  );
}

// ─── STATUS BAR ──────────────────────────────────────
function StatusBar({ beats, watcher, ffmpegVer, ytOk, lastAction }) {
  return (
    <div className="status-bar">
      <div className="s-item">
        <Dot state="ok" />
        <span>WATCHER: ACTIVE</span>
      </div>
      <div className="s-item">
        <Dot state={ffmpegVer ? "ok" : "err"} />
        <span>FFMPEG: {ffmpegVer ? "OK" : "NOT FOUND"}</span>
      </div>
      <div className="s-item">
        <Dot state={ytOk ? "ok" : "warn"} />
        <span>YT: {ytOk ? "AUTH" : "SETUP REQUIRED"}</span>
      </div>
      <div className="s-item">
        <Dot state="ok" />
        <span className={beats.length > 0 ? "beats-count-nonzero" : ""}>BEATS: {beats.length}</span>
      </div>
      <div className="s-spacer" />
      {lastAction && (
        <div className="s-item" style={{color:"var(--accent)"}}>
          <span>// {lastAction}</span>
        </div>
      )}
      <div className="s-item">
        <span>SYS_ATH_04 // DEC_GRID</span>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════
// MAIN APP
// ═══════════════════════════════════════════════════
function App() {

  // ─── NAVIGATION ───
  const [activeTab, setActiveTab] = useState("beats");

  // ─── BEAT SOURCE ───
  const [beats, setBeats]               = useState([]);
  const [selectedBeatId, setSelectedBeatId] = useState(null);

  // ─── ARTIST DATABASE ───
  const [allTiers, setAllTiers]         = useState({});

  // ─── ARTWORKS ───
  const [artworks, setArtworks]         = useState({});
  const [artVibeTab, setArtVibeTab]     = useState("rage");

  // ─── LUT ───
  const [lutPresets, setLutPresets]     = useState({});
  const [selectedPreset, setSelectedPreset] = useState("");
  const [lutParams, setLutParams]       = useState({});
  const [tunerOpen, setTunerOpen]       = useState(false);
  const [previewUrl, setPreviewUrl]     = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  // ─── METADATA ───
  const [artist1, setArtist1]           = useState("");
  const [artist2, setArtist2]           = useState("");
  const [beatName, setBeatName]         = useState("");
  const [bpm, setBpm]                   = useState("140");
  const [beatKey, setBeatKey]           = useState("Am");
  const [vibe, setVibe]                 = useState("rage");
  const [mood, setMood]                 = useState("");
  const [drop, setDrop]                 = useState("0:25");
  const [outro, setOutro]               = useState("2:30");
  const [titleStyle, setTitleStyle]     = useState("standard");

  // ─── PIPELINE ───
  const [locked, setLocked]             = useState(false);
  const [selectedArtwork, setSelectedArtwork] = useState("");
  const [cropEnabled, setCropEnabled]   = useState(false);
  const [cropRect, setCropRect]         = useState({ x: 0, y: 0, size: 1 });
  const [seoData, setSeoData]           = useState(null);
  const [generating, setGenerating]     = useState(false);
  const [renderResult, setRenderResult] = useState(null);
  const [rendering, setRendering]       = useState(false);
  const [renderProgress, setRenderProgress] = useState(0); // tahmini render %
  const renderTimerRef = useRef(null);

  // ─── YOUTUBE ───
  const [ytStatus, setYtStatus]         = useState(null);
  const [ytPlaylists, setYtPlaylists]   = useState([]);
  const [selectedPlaylist, setSelectedPlaylist] = useState("");
  const [channelInfo, setChannelInfo]   = useState(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);

  // ─── MULTI-PLATFORM ───
  const [platforms, setPlatforms] = useState({
    youtube: true, soundcloud: false, instagram: false, beatstars: false,
  });
  const [deployStatus, setDeployStatus] = useState({});
  const [deploying, setDeploying]       = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0); // 0-100 tahmini %
  const uploadTimerRef = useRef(null);

  // ─── SCHEDULE ───
  const [publishModalOpen, setPublishModalOpen] = useState(false);
  const [scheduleDate, setScheduleDate] = useState("");
  const [scheduleHour, setScheduleHour] = useState(20);
  const [scheduleMin, setScheduleMin]   = useState(0);
  const [privacy, setPrivacy]           = useState("public");


  // ─── SYSTEM ───
  const [combos, setCombos]             = useState([]);
  const [ffmpegVer, setFfmpegVer]       = useState("");
  const [lastAction, setLastAction]     = useState("SYSTEM READY");
  const [qualityModal, setQualityModal] = useState(false);
  const [renderQuality, setRenderQuality] = useState("HD");

  // ─── INIT ─────────────────────────────────────────
  useEffect(() => {
    fetchBeats();
    fetchArtistTiers();
    fetchArtworks();
    fetchLutPresets();
    fetchYtStatus();
    fetchChannelInfo();
    loadCombos();
    checkFfmpeg();
    const poll = setInterval(fetchBeats, 12000);
    return () => clearInterval(poll);
  }, []);

  // ─── LUT LAB AUTO-PREVIEW (debounced 700ms) ───────
  // When tuner sliders change in LUT Lab tab, auto-trigger preview
  const previewDebounceRef = useRef(null);
  const handlePreviewRef   = useRef(null);
  useEffect(() => { handlePreviewRef.current = handlePreview; });

  useEffect(() => {
    if (activeTab !== "lut" || !selectedArtwork) return;
    if (previewDebounceRef.current) clearTimeout(previewDebounceRef.current);
    previewDebounceRef.current = setTimeout(() => {
      handlePreviewRef.current?.();
    }, 700);
    return () => { if (previewDebounceRef.current) clearTimeout(previewDebounceRef.current); };
  }, [lutParams, selectedPreset, activeTab, selectedArtwork]);

  // ─── FETCH: BEATS ──────────────────────────────────
  const fetchBeats = async () => {
    try {
      const r = await fetch(`${API}/beats`);
      const d = await r.json();
      if (d.beats) setBeats(d.beats);
    } catch {}
  };

  // ─── FETCH: ARTIST TIERS ───────────────────────────
  const fetchArtistTiers = async () => {
    try {
      const r = await fetch(`${API}/artists/tiers`);
      const d = await r.json();
      // API returns the tier dict directly (not wrapped in {tiers:{}})
      if (d && typeof d === "object" && !d.error) setAllTiers(d);
    } catch {}
  };

  // ─── FETCH: ARTWORKS ───────────────────────────────
  const fetchArtworks = async () => {
    try {
      const r = await fetch(`${API}/artworks`);
      const d = await r.json();
      // API returns artwork dict directly (not wrapped in {artworks:{}})
      if (d && typeof d === "object" && !d.error) {
        setArtworks(d);
        const first = Object.keys(d)[0];
        if (first) setArtVibeTab(first);
      }
    } catch {}
  };

  // ─── FETCH: LUT PRESETS ────────────────────────────
  const fetchLutPresets = async () => {
    try {
      const r = await fetch(`${API}/lut/presets`);
      const d = await r.json();
      // API returns the preset dict directly (not wrapped in {presets:{}})
      if (d && typeof d === "object" && !d.error && Object.keys(d).length > 0) {
        setLutPresets(d);
        const first = Object.keys(d).find(k => !k.startsWith("⚡")) || Object.keys(d)[0];
        if (first && !selectedPreset) setSelectedPreset(first);
      }
    } catch {}
  };

  // ─── FETCH: YT STATUS + PLAYLISTS ─────────────────
  const fetchYtStatus = async () => {
    try {
      const r = await fetch(`${API}/youtube/status`);
      const d = await r.json();
      setYtStatus(d);
      if (d.authenticated) {
        const pr = await fetch(`${API}/youtube/playlists`);
        const pd = await pr.json();
        if (pd.playlists) setYtPlaylists(pd.playlists);
      }
    } catch {}
  };

  // ─── FETCH: CHANNEL INFO ───────────────────────────
  const fetchChannelInfo = async () => {
    setAnalyticsLoading(true);
    try {
      const r = await fetch(`${API}/youtube/channel`);
      const d = await r.json();
      setChannelInfo(d);
    } catch {}
    finally { setAnalyticsLoading(false); }
  };

  // ─── CHECK FFMPEG ──────────────────────────────────
  const checkFfmpeg = async () => {
    try {
      const r = await fetch(`${API}/ffmpeg/version`);
      const d = await r.json();
      if (d.version) setFfmpegVer(d.version);
    } catch {}
  };

  // ─── COMBO CRUD (localStorage) ────────────────────
  const loadCombos = () => {
    try {
      const s = localStorage.getItem("jetbox_combos");
      if (s) setCombos(JSON.parse(s));
    } catch {}
  };

  const handleSaveCombo = (combo) => {
    const updated = [...combos, { ...combo, id: Date.now().toString() }];
    setCombos(updated);
    localStorage.setItem("jetbox_combos", JSON.stringify(updated));
    setLastAction(`COMBO SAVED: ${combo.name}`);
  };

  const handleLoadCombo = (combo) => {
    setArtist1(combo.artist1 || "");
    setArtist2(combo.artist2 || "");
    if (combo.vibe) setVibe(combo.vibe);
    setLocked(false);
    setLastAction(`COMBO LOADED: ${combo.name}`);
  };

  const handleDeleteCombo = (id) => {
    const updated = combos.filter((c) => c.id !== id);
    setCombos(updated);
    localStorage.setItem("jetbox_combos", JSON.stringify(updated));
  };

  // ─── LOCK TARGET ──────────────────────────────────
  const handleLockTarget = () => {
    const label = `${artist1}${artist2 ? ` x ${artist2}` : ""} - "${beatName}"`;
    setLocked(true);
    setSeoData(null);
    setRenderResult(null);
    setPreviewUrl(null);
    setDeployStatus({});
    setLastAction(`TARGET LOCKED: ${label}`);
  };

  // ─── SCAN BEATS ───────────────────────────────────
  const handleScanBeats = async () => {
    try {
      await fetch(`${API}/beats/scan`, { method: "POST" });
      setTimeout(fetchBeats, 1200);
      setLastAction("SCANNING BEATS FOLDER...");
    } catch {}
  };

  // ─── PREVIEW FILTER ───────────────────────────────
  // Always includes current Spectral Tuner params so sliders affect the preview
  const handlePreview = useCallback(async () => {
    if (!selectedArtwork) return;
    setLoadingPreview(true);
    try {
      const cleanPreset    = selectedPreset.replace(/^⚡/, "");
      const hasLutParams   = Object.keys(lutParams).length > 0;

      const r = await fetch(`${API}/lut/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          artwork_path: selectedArtwork,
          preset:       cleanPreset,
          crop:         cropEnabled ? cropRect : null,
          // Send tuner params — backend uses them over preset when present
          params:       hasLutParams ? lutParams : null,
        }),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        setLastAction(`PREVIEW ERROR: ${err.error || r.status}`);
        return;
      }
      const blob = await r.blob();
      setPreviewUrl((old) => { if (old) URL.revokeObjectURL(old); return URL.createObjectURL(blob); });
      setLastAction("FILTER PREVIEW GENERATED");
    } catch (e) { console.error("preview:", e); }
    finally { setLoadingPreview(false); }
  }, [selectedArtwork, selectedPreset, lutParams, cropEnabled, cropRect]);

  // ─── GENERATE SEO ─────────────────────────────────
  const handleGenerateSeo = async () => {
    setGenerating(true);
    setSeoData(null);
    try {
      const payload = {
        beat_name:  beatName,
        artist1,
        artist2:    artist2 || null,   // optional
        bpm:        parseInt(bpm) || 140,
        key:        beatKey,
        vibe,
        mood:       mood || null,
        drop:       drop,              // backend expects "drop" not "drop_ts"
        outro:      outro,             // backend expects "outro" not "outro_ts"
      };
      const r = await fetch(`${API}/seo/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const d = await r.json();
      if (d.title) {
        setSeoData(d);
        const score = d.seo_score?.overall ?? 0;
        setLastAction(`SEO GENERATED - ${Math.round(score * 100)} dB SIGNAL`);

        // ── YouTube Preview Window ────────────────────────────
        // LUT uygulanmış görseli base64 olarak al, sonra popup aç
        const a1 = artist1 || "ARTIST1";
        const a2 = artist2 || "ARTIST2";
        const searchQ = encodeURIComponent(`${a1} ${a2} type beat`);

        let lutImgSrc = "";
        if (selectedArtwork) {
          try {
            // Mevcut preset + artwork kombinasyonuyla preview endpoint'ini çağır
            const cleanP = selectedPreset.replace(/^⚡/, "");
            const isCustomP = selectedPreset.startsWith("⚡");
            const previewPayload = {
              artwork_path: selectedArtwork,
              preset:       isCustomP ? cleanP : (cleanP || "rage"),
              params:       Object.keys(lutParams).length > 0 ? lutParams : undefined,
              crop:         cropEnabled ? cropRect : undefined,
            };
            const imgRes = await fetch(`${API}/lut/preview`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(previewPayload),
            });
            if (imgRes.ok) {
              const imgBlob = await imgRes.blob();
              // Blob → base64 (popup HTML içine gömülür, memory-safe)
              lutImgSrc = await new Promise((res) => {
                const fr = new FileReader();
                fr.onload = () => res(fr.result);
                fr.readAsDataURL(imgBlob);
              });
            }
          } catch (_) { /* görsel alınamazsa sessizce devam */ }
        }

        const imgBlock = lutImgSrc
          ? `<div class="thumb-wrap"><img src="${lutImgSrc}" alt="LUT preview" class="thumb-img"/><div class="thumb-lbl">LUT PREVIEW — 720x720</div></div>`
          : `<div class="thumb-empty">NO ARTWORK SELECTED</div>`;

        const previewHtml = `<!DOCTYPE html><html lang="en">
<head><meta charset="UTF-8"><title>YT Preview — ${d.title.replace(/"/g,"'")}</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0a0f;color:#e8e8ef;font-family:'Segoe UI',system-ui,sans-serif;padding:18px;overflow-x:hidden}
h1{font-size:12px;color:#9AFF62;letter-spacing:.12em;margin-bottom:14px;text-transform:uppercase;border-bottom:1px solid rgba(154,255,98,.2);padding-bottom:7px}
.thumb-wrap{width:100%;aspect-ratio:1/1;max-width:720px;margin:0 auto 14px;border-radius:6px;overflow:hidden;border:1px solid rgba(154,255,98,.25);position:relative}
.thumb-img{width:100%;height:100%;object-fit:cover;display:block}
.thumb-lbl{position:absolute;bottom:0;left:0;right:0;background:rgba(0,0,0,.65);font-size:9px;color:#9AFF62;letter-spacing:.1em;padding:4px 8px;text-align:center}
.thumb-empty{width:100%;aspect-ratio:1/1;max-width:720px;margin:0 auto 14px;background:rgba(255,255,255,.03);border:1px dashed rgba(255,255,255,.1);border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:10px;color:#333;letter-spacing:.08em}
.title-box{background:rgba(154,255,98,.05);border:1px solid rgba(154,255,98,.2);border-radius:5px;padding:12px 14px;margin-bottom:12px}
.title-text{font-size:13px;font-weight:600;color:#fff;line-height:1.5;margin-bottom:6px}
.channel{font-size:10px;color:#9AFF62;letter-spacing:.08em}
.section{margin-bottom:12px}
.lbl{font-size:9px;color:#444;letter-spacing:.14em;text-transform:uppercase;margin-bottom:5px}
.tags{display:flex;flex-wrap:wrap;gap:3px}
.tag{background:rgba(154,255,98,.07);border:1px solid rgba(154,255,98,.18);border-radius:2px;padding:2px 6px;font-size:9px;color:#999;letter-spacing:.03em}
.desc{background:rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.06);border-radius:3px;padding:8px 10px;font-size:10px;color:#777;line-height:1.7;max-height:120px;overflow-y:auto;white-space:pre-wrap}
.score-row{display:flex;align-items:center;gap:8px;margin-bottom:12px}
.score-bar-wrap{flex:1;height:5px;background:rgba(255,255,255,.07);border-radius:3px;overflow:hidden}
.score-bar{height:100%;background:linear-gradient(90deg,#e5ef28,#9AFF62);border-radius:3px}
.score-val{font-size:12px;color:#9AFF62;font-weight:700;font-family:monospace;min-width:34px;text-align:right}
.links{display:flex;gap:6px;margin-top:14px}
a.yt-btn{flex:1;display:flex;align-items:center;justify-content:center;gap:5px;background:#ff0000;color:#fff;border:none;border-radius:4px;padding:8px 10px;font-size:11px;font-weight:600;text-decoration:none;letter-spacing:.05em}
a.cmp-btn{flex:1;display:flex;align-items:center;justify-content:center;gap:5px;background:rgba(154,255,98,.1);border:1px solid rgba(154,255,98,.3);color:#9AFF62;border-radius:4px;padding:8px 10px;font-size:11px;font-weight:600;text-decoration:none;letter-spacing:.05em}
</style></head>
<body>
<h1>&#9654; YouTube Preview — JETBOX</h1>
${imgBlock}
<div class="title-box">
  <div class="title-text">${d.title.replace(/</g,"&lt;").replace(/>/g,"&gt;")}</div>
  <div class="channel">ENNY TANG</div>
</div>
<div class="score-row">
  <div class="score-bar-wrap"><div class="score-bar" style="width:${Math.round((d.seo_score?.overall??0)*100)}%"></div></div>
  <div class="score-val">${Math.round((d.seo_score?.overall??0)*100)}<span style="font-size:8px;color:#444">%</span></div>
</div>
<div class="section"><div class="lbl">Tags (${(d.tags||[]).length})</div><div class="tags">${(d.tags||[]).map(t=>'<span class="tag">'+t.replace(/</g,"&lt;")+'</span>').join("")}</div></div>
<div class="section"><div class="lbl">Description</div><div class="desc">${(d.description||"").replace(/</g,"&lt;").replace(/>/g,"&gt;")}</div></div>
<div class="links">
  <a class="yt-btn" href="https://studio.youtube.com" target="_blank">&#9654; YouTube Studio</a>
  <a class="cmp-btn" href="https://www.youtube.com/results?search_query=${searchQ}" target="_blank">&#9889; Competition</a>
</div>
</body></html>`;

        const blobHtml = new Blob([previewHtml], { type: "text/html;charset=utf-8" });
        const blobUrl  = URL.createObjectURL(blobHtml);
        // Pencere boyutu: görsel varsa biraz daha uzun
        const pwH = lutImgSrc ? 880 : 660;
        const pw  = window.open(blobUrl, "yt_preview",
          `width=660,height=${pwH},left=${Math.round((screen.width-660)/2)},top=${Math.round((screen.height-pwH)/2)},resizable=yes,scrollbars=yes`);
        if (pw) {
          pw.addEventListener("unload", () => URL.revokeObjectURL(blobUrl), { once: true });
        }
        // ───────────────────────────────────────────────────────
      } else if (d.error) {
        setLastAction(`SEO ERROR: ${d.error}`);
      }
    } catch (e) { console.error("SEO:", e); }
    finally { setGenerating(false); }
  };

  // ─── RENDER MP4 — shows quality modal first ───────
  const handleRenderClick = () => {
    if (!selectedArtwork || !seoData) return;
    setQualityModal(true);  // Show 2K vs HD choice
  };

  // ── RENDER PROGRESS — tahmini ilerleme (upload bariyla ayni mantik) ──
  const startRenderProgress = () => {
    setRenderProgress(2);
    if (renderTimerRef.current) clearInterval(renderTimerRef.current);
    renderTimerRef.current = setInterval(() => {
      setRenderProgress((prev) => {
        if (prev >= 92) return 92; // gercek bitisi bekle
        const remaining = 92 - prev;
        return Math.min(92, prev + Math.max(1, Math.round(remaining * 0.14)));
      });
    }, 1500);
  };
  const stopRenderProgress = (success) => {
    if (renderTimerRef.current) { clearInterval(renderTimerRef.current); renderTimerRef.current = null; }
    setRenderProgress(success ? 100 : 0);
  };

  const handleRender = async (quality = renderQuality) => {
    if (!selectedArtwork || !seoData) return;
    setRenderQuality(quality);
    setRendering(true);
    setRenderResult(null);
    startRenderProgress();
    try {
      const cleanPreset = selectedPreset.replace(/^⚡/, "");
      const isCustom    = selectedPreset.startsWith("⚡");

      const r = await fetch(`${API}/render/mp4`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          beat_id:         selectedBeatId,
          artwork_path:    selectedArtwork,
          preset:          isCustom ? "rage" : cleanPreset,
          lut_preset_name: isCustom ? cleanPreset : null,
          beat_name:       beatName,
          crop:            cropEnabled ? cropRect : null,
          quality:         quality,    // "2K" or "HD"
          title:           seoData.title,
          description:     seoData.description,
          tags:            seoData.tags,
        }),
      });
      const d = await r.json();
      if (d.mp4_path || d.render?.output_path) {
        const mp4 = d.mp4_path || d.render?.output_path;
        setRenderResult({
          output_file: mp4,
          file_size_mb: d.render?.file_size_mb || "?",
          thumbnail_path: d.thumbnail_path,
          ...d,
        });
        setLastAction(`RENDER COMPLETE - ${d.render?.file_size_mb || "?"} MB`);
        stopRenderProgress(true);
      } else if (d.error) {
        setLastAction(`RENDER ERROR: ${d.error}`);
        stopRenderProgress(false);
      }
    } catch (e) { console.error("render:", e); stopRenderProgress(false); }
    finally { setRendering(false); }
  };

  // ─── UPLOAD PROGRESS HELPER ───────────────────────
  // Tahmini ilerleme: 3 saniyede bir artar, max %94'de bekler (gerçek tamamlanmayı bekler)
  const startUploadProgress = () => {
    setUploadProgress(2);
    if (uploadTimerRef.current) clearInterval(uploadTimerRef.current);
    uploadTimerRef.current = setInterval(() => {
      setUploadProgress((prev) => {
        // İlerleme eğrisi: hızlı başlar, yavaşlar, max 94'de durur
        if (prev >= 94) return 94;
        const remaining = 94 - prev;
        const step = Math.max(1, Math.round(remaining * 0.18)); // %18 yaklaşma
        return Math.min(94, prev + step);
      });
    }, 3000);
  };

  const stopUploadProgress = (success) => {
    if (uploadTimerRef.current) { clearInterval(uploadTimerRef.current); uploadTimerRef.current = null; }
    setUploadProgress(success ? 100 : 0);
  };

  // ─── DEPLOY NOW ───────────────────────────────────
  const handleDeployNow = async () => {
    if (!renderResult || !seoData) return;
    setDeploying(true);
    setUploadProgress(0);

    const initial = {};
    Object.entries(platforms).forEach(([k, v]) => {
      if (v) initial[k] = { status: "queued" };
    });
    setDeployStatus(initial);

    // ── YouTube ──
    if (platforms.youtube) {
      setDeployStatus((p) => ({ ...p, youtube: { status: "uploading" } }));
      startUploadProgress();
      try {
        const r = await fetch(`${API}/upload/youtube`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            mp4_path:        renderResult.output_file,
            thumbnail_path:  renderResult.thumbnail_path || null,
            title:           seoData.title,
            description:     seoData.description,
            tags:            seoData.tags,
            category_id:     seoData.category || "10",
            privacy_status:  privacy || "public",
          }),
        });
        const d = await r.json();
        if (d.video_id) {
          const url = `https://youtu.be/${d.video_id}`;
          stopUploadProgress(true);
          if (selectedPlaylist && d.video_id) {
            await fetch(`${API}/youtube/playlists/add`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ video_id: d.video_id, playlist_id: selectedPlaylist }),
            }).catch(() => {});
          }
          setDeployStatus((p) => ({ ...p, youtube: { status: "done", url } }));
          setLastAction(`DEPLOYED: ${url}`);
        } else {
          const errMsg = d.error || "Upload failed";
          stopUploadProgress(false);
          setDeployStatus((p) => ({ ...p, youtube: { status: "error", msg: errMsg } }));
          setLastAction(`DEPLOY ERROR: ${errMsg}`);
        }
      } catch (e) {
        const msg = e?.message || "Network error";
        stopUploadProgress(false);
        setDeployStatus((p) => ({ ...p, youtube: { status: "error", msg } }));
        setLastAction(`DEPLOY ERROR: ${msg}`);
      }
    }

    // ── Faza 3 platforms (infrastructure ready, uploads coming) ──
    const pendingPlatforms = ["soundcloud", "instagram", "beatstars"];
    pendingPlatforms.forEach((plat) => {
      if (platforms[plat]) {
        setDeployStatus((p) => ({ ...p, [plat]: { status: "unavailable" } }));
      }
    });

    setDeploying(false);
  };


  // ─── SCHEDULE ─────────────────────────────────────
  const handleConfirmSchedule = async (effectiveHour) => {
    if (!renderResult || !seoData || !scheduleDate) return;
    setPublishModalOpen(false);  // close modal
    setDeploying(true);
    setUploadProgress(0);
    setDeployStatus({ youtube: { status: "uploading" } });
    startUploadProgress();

    try {
      const r = await fetch(`${API}/schedule/youtube`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mp4_path:        renderResult.output_file,   // ← backend expects mp4_path
          thumbnail_path:  renderResult.thumbnail_path || null,
          title:           seoData.title,
          description:     seoData.description,
          tags:            seoData.tags,
          category_id:     seoData.category || "10",
          schedule_date:   scheduleDate,
          schedule_hour:   effectiveHour ?? scheduleHour,
          schedule_min:    scheduleMin,
        }),
      });
      const d = await r.json();
      if (d.video_id) {
        const url = `https://youtu.be/${d.video_id}`;
        stopUploadProgress(true);
        if (selectedPlaylist && d.video_id) {
          await fetch(`${API}/youtube/playlists/add`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ video_id: d.video_id, playlist_id: selectedPlaylist }),
          }).catch(() => {});
        }
        setDeployStatus({ youtube: { status: "done", url } });
        setLastAction(`SCHEDULED: ${scheduleDate} ${String(effectiveHour ?? scheduleHour).padStart(2,"0")}:${String(scheduleMin).padStart(2,"0")} TRT`);

      } else {
        const errMsg = d.error || "Schedule failed";
        stopUploadProgress(false);
        setDeployStatus({ youtube: { status: "error", msg: errMsg } });
        setLastAction(`SCHEDULE ERROR: ${errMsg}`);
      }
    } catch (e) {
      const msg = e?.message || "Network error";
      stopUploadProgress(false);
      setDeployStatus({ youtube: { status: "error", msg } });
      setLastAction(`SCHEDULE ERROR: ${msg}`);
    }
    setDeploying(false);
  };


  const handleTogglePlatform = (key) => {
    setPlatforms((p) => ({ ...p, [key]: !p[key] }));
  };

  // ─── DERIVED ──────────────────────────────────────
  const ytOk     = !!ytStatus?.authenticated;
  const ffmpegOk = !!ffmpegVer;

  // ─── SHARED PROCESS PANEL PROPS ───────────────────
  const processPanelProps = {
    artworks, artVibeTab, setArtVibeTab,
    selectedArtwork, setSelectedArtwork,
    lutPresets, selectedPreset, setSelectedPreset,
    lutParams, setLutParams,
    tunerOpen, setTunerOpen,
    previewUrl, loadingPreview, onPreview: handlePreview,
    cropEnabled, setCropEnabled, cropRect, setCropRect,
    seoData, titleStyle, setTitleStyle,
    drop, setDrop, outro, setOutro,
    onGenerateSeo: handleGenerateSeo, generating,
    onRender: handleRenderClick,   // ← shows quality modal
    rendering, renderResult, renderProgress,
    artist1, artist2, beatName, bpm, beatKey, vibe, mood, locked,
  };

  // ─── SHARED OUTPUT PANEL PROPS ────────────────────
  const outputPanelProps = {
    renderResult, seoData,
    channelInfo, analyticsLoading,
    platforms, onTogglePlatform: handleTogglePlatform,
    ytPlaylists, selectedPlaylist, setSelectedPlaylist,
    onDeployNow: handleDeployNow,
    onSchedule: handleConfirmSchedule,
    deployStatus, deploying,
    uploadProgress,
    publishModalOpen, setPublishModalOpen,
    scheduleDate, setScheduleDate,
    scheduleHour, setScheduleHour,
    scheduleMin, setScheduleMin,
    onConfirmSchedule: handleConfirmSchedule,
    privacy, setPrivacy,
  };

  return (
    <div className="app-shell">
      <AppHeader activeTab={activeTab} setActiveTab={setActiveTab}
        ytOk={ytOk} ffmpegOk={ffmpegOk} />

      {/* ── BEATS TAB — full 3-panel pipeline ── */}
      {activeTab === "beats" && (
        <div className="panel-grid">
          {/* INPUT */}
          <div className={`panel ${locked ? "p-active" : ""}`}>
            <InputPanel
              beats={beats} selectedBeatId={selectedBeatId}
              onSelectBeat={(id) => { setSelectedBeatId(id); setLocked(false); setSeoData(null); setRenderResult(null); }}
              allTiers={allTiers} combos={combos}
              onLoadCombo={handleLoadCombo} onSaveCombo={handleSaveCombo} onDeleteCombo={handleDeleteCombo}
              artist1={artist1} setArtist1={(v) => { setArtist1(v); setLocked(false); }}
              artist2={artist2} setArtist2={(v) => { setArtist2(v); setLocked(false); }}
              beatName={beatName} setBeatName={(v) => { setBeatName(v); setLocked(false); }}
              bpm={bpm} setBpm={setBpm}
              beatKey={beatKey} setBeatKey={setBeatKey}
              vibe={vibe} setVibe={setVibe}
              mood={mood} setMood={setMood}
              onLockTarget={handleLockTarget} locked={locked}
              onScanBeats={handleScanBeats}
            />
          </div>

          {/* PROCESS */}
          <div className={`panel ${seoData ? "p-active" : ""}`}>
            <ProcessPanel {...processPanelProps} />
          </div>

          {/* OUTPUT */}
          <div className={`panel ${Object.keys(deployStatus).some((k) => deployStatus[k]?.status === "done") ? "p-active" : ""}`}>
            <OutputPanel {...outputPanelProps} />
          </div>
        </div>
      )}

      {/* ── LUT LAB TAB ── */}
      {activeTab === "lut" && (
        <div className="panel-grid">
          {/* LEFT — Artwork selector */}
          <div className="panel">
            <div style={{display:"flex",flexDirection:"column",height:"100%"}}>
              <div className="panel-header">
                <div><div className="panel-title">ARTWORKS</div><div className="panel-sub">SELECT BASE</div></div>
              </div>
              <div className="panel-body">
                <ArtworkBrowser artworks={artworks} vibeTab={artVibeTab}
                  onVibeTab={setArtVibeTab} selected={selectedArtwork} onSelect={(rel) => {
                    setSelectedArtwork(rel);
                    setPreviewUrl(null);  // clear preview on artwork change
                  }} />
              </div>
              <div className="panel-footer" style={{display:"flex",flexDirection:"column",gap:8}}>
                <button className="btn btn-cta"
                  disabled={!selectedArtwork || loadingPreview} onClick={handlePreview}>
                  {loadingPreview ? "PROCESSING..." : "⚡ PREVIEW FILTER"}
                </button>
                {previewUrl && (
                  <button className="btn-download" onClick={() => {
                    const a = document.createElement("a");
                    a.href = previewUrl;
                    a.download = `jetbox_${(selectedPreset||"filter").replace(/⚡/,"")}_${Date.now()}.jpg`;
                    a.click();
                  }}>
                    ↓ DOWNLOAD PROCESSED IMAGE
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* RIGHT — Spectral Tuner (spans 2 cols) */}
          <div className="panel" style={{gridColumn:"2 / 4"}}>
            <div style={{display:"flex",flexDirection:"column",height:"100%"}}>
              <div className="panel-header">
                <div><div className="panel-title">SPECTRAL TUNER</div><div className="panel-sub">LUT LAB</div></div>
                <div style={{display:"flex",gap:5,alignItems:"center",flexWrap:"wrap"}}>
                  {Object.keys(lutPresets).map((k) => (
                    <button key={k} className={`chip ${selectedPreset===k?"active":""}`}
                      onClick={() => setSelectedPreset(k)}>
                      {k.startsWith("⚡") ? "★ " + k.slice(1) : k.toUpperCase()}
                    </button>
                  ))}
                  <button className="btn-ghost" style={{marginLeft:8}}
                    onClick={() => setLutParams({})}>RESET ALL</button>
                </div>
              </div>
              <div className="panel-body" style={{display:"flex",flexDirection:"column"}}>
                {/* Fixed 16:9 preview container — no image overflow */}
                <div className="tuner-preview-container">
                  {previewUrl ? (
                    <img src={previewUrl} alt="LUT preview" />
                  ) : (
                    <div className="tuner-preview-empty">
                      SELECT ARTWORK<br/>
                      <span style={{fontSize:9,opacity:.6,letterSpacing:".12em"}}>
                        THEN HIT PREVIEW FILTER
                      </span>
                    </div>
                  )}
                  {loadingPreview && (
                    <div className="tuner-preview-loading">PROCESSING...</div>
                  )}
                </div>
                {/* Tuner sliders */}
                <div style={{flex:1,overflow:"auto"}}>
                  <LutTunerDrawer params={lutParams} onChange={setLutParams}
                    onReset={() => setLutParams({})} presetName={selectedPreset} />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── DEPLOY TAB ── */}
      {activeTab === "deploy" && (
        <div className="panel-grid">
          {/* Platform channel status */}
          <div className="panel">
            <div style={{display:"flex",flexDirection:"column",height:"100%"}}>
              <div className="panel-header">
                <div><div className="panel-title">CHANNELS</div><div className="panel-sub">PLATFORM STATUS</div></div>
              </div>
              <div className="panel-body">
                <PlatformSelector selected={platforms} onToggle={handleTogglePlatform} />
                <SecDiv label="SYSTEM" />
                <div style={{display:"flex",flexDirection:"column",gap:8}}>
                  <div style={{display:"flex",alignItems:"center",justifyContent:"space-between"}}>
                    <span className="f-data" style={{fontSize:10,color:"var(--txt-dim)"}}>YOUTUBE API</span>
                    <span className="f-data" style={{fontSize:10,color:ytOk?"var(--accent)":"#e05555"}}>
                      {ytOk ? "AUTHENTICATED" : "REQUIRES SETUP"}
                    </span>
                  </div>
                  <div style={{display:"flex",alignItems:"center",justifyContent:"space-between"}}>
                    <span className="f-data" style={{fontSize:10,color:"var(--txt-dim)"}}>FFMPEG</span>
                    <span className="f-data" style={{fontSize:10,color:ffmpegOk?"var(--accent)":"#e05555"}}>
                      {ffmpegVer || "NOT FOUND"}
                    </span>
                  </div>
                  <div style={{display:"flex",alignItems:"center",justifyContent:"space-between"}}>
                    <span className="f-data" style={{fontSize:10,color:"var(--txt-dim)"}}>INSTAGRAM</span>
                    <span className="f-data" style={{fontSize:10,color:"var(--txt-dim)"}}>FAZA 3 — INFRA READY</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          {/* Output panel — spans 2 cols */}
          <div className="panel" style={{gridColumn:"2 / 4"}}>
            <OutputPanel {...outputPanelProps} />
          </div>
        </div>
      )}

      <StatusBar beats={beats} ffmpegVer={ffmpegVer} ytOk={ytOk} lastAction={lastAction} />

      {/* Quality selector modal — appears before render */}
      {qualityModal && (
        <QualityModal onSelect={(q) => {
          setQualityModal(false);
          handleRender(q);
        }} />
      )}
    </div>
  );
}

export default App;
