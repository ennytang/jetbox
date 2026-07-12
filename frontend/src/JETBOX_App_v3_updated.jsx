import { useState, useEffect, useCallback, useRef } from "react";

const API = "/api";

// â”€â”€â”€ MUSICAL KEYS â”€â”€â”€
const KEYS = ["Cm","C#m","Dm","D#m","Em","Fm","F#m","Gm","G#m","Am","A#m","Bm",
              "C","C#","D","D#","E","F","F#","G","G#","A","A#","B"];

// â”€â”€â”€ TIER CONFIG â”€â”€â”€
const TIER_LABELS = {
  legends:          { label: "Legends",   icon: "ğŸ‘‘" },
  major:            { label: "Major",     icon: "â­" },
  rising:           { label: "Rising",    icon: "ğŸ”¥" },
  producers:        { label: "Producers", icon: "ğŸ¹" },
  new_wave:         { label: "New Wave",  icon: "ğŸŒŠ" },
  melodic_trap:     { label: "Melodic",   icon: "ğŸ’œ" },
  uk_international: { label: "UK/Intl",   icon: "ğŸŒ" },
  classic:          { label: "Classic",   icon: "ğŸ†" },
  niche_targets:    { label: "Niche ⚡",  icon: "ğŸ¯" },
};

// â”€â”€â”€ ARTIST SELECTOR â”€â”€â”€
function ArtistSelector({ label, value, onSelect, allTiers }) {
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const allArtists = Object.entries(allTiers).flatMap(([tier, artists]) =>
    artists.map((a) => ({ name: a, tier }))
  );
  const filtered = search
    ? allArtists.filter((a) => a.name.toLowerCase().includes(search.toLowerCase()))
    : allArtists;

  return (
    <div ref={ref} className="relative">
      <label className="block text-xs uppercase tracking-widest mb-1.5 font-mono" style={{ color: "#4a4a5a" }}>{label}</label>
      <button onClick={() => setOpen(!open)}
        className="w-full text-left px-4 py-3 rounded-xl border transition-all cursor-pointer"
        style={{
          background: value ? "rgba(0,255,136,0.06)" : "rgba(255,255,255,0.03)",
          borderColor: value ? "rgba(0,255,136,0.3)" : "rgba(255,255,255,0.08)",
          color: value ? "#00ff88" : "#6b6b80",
        }}>
        {value || "Select artist..."}
      </button>
      {open && (
        <div className="absolute z-50 mt-2 w-full max-h-80 overflow-hidden rounded-xl border shadow-2xl"
          style={{ background: "#111118", borderColor: "rgba(255,255,255,0.1)" }}>
          <div className="p-2 sticky top-0" style={{ background: "#111118" }}>
            <input type="text" placeholder="Search artists..." value={search}
              onChange={(e) => setSearch(e.target.value)} autoFocus
              className="w-full px-3 py-2 rounded-lg text-sm border-none outline-none"
              style={{ background: "rgba(255,255,255,0.06)", color: "#e8e8ef" }}
            />
          </div>
          <div className="overflow-y-auto max-h-64 px-1 pb-1">
            {Object.entries(TIER_LABELS).map(([tierKey, tierInfo]) => {
              const tierArtists = filtered.filter((a) => a.tier === tierKey);
              if (!tierArtists.length) return null;
              return (
                <div key={tierKey}>
                  <div className="px-3 py-1.5 text-xs font-mono uppercase tracking-wider" style={{ color: "#3a3a4a" }}>
                    {tierInfo.icon} {tierInfo.label}
                  </div>
                  {tierArtists.map((a) => (
                    <button key={a.name}
                      onClick={() => { onSelect(a.name); setOpen(false); setSearch(""); }}
                      className="w-full text-left px-3 py-2 text-sm rounded-lg transition-all hover:bg-white/5 cursor-pointer"
                      style={{ color: a.name === value ? "#00ff88" : "#c8c8d4" }}>
                      {a.name}
                    </button>
                  ))}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// â”€â”€â”€ ARTWORK BROWSER â”€â”€â”€
function ArtworkBrowser({ artworks, selectedVibe, onVibeChange, selectedArt, onSelectArt }) {
  const vibes = Object.keys(artworks);
  const currentImages = artworks[selectedVibe]?.images || [];
  return (
    <div>
      <div className="flex gap-2 mb-3">
        {vibes.map((v) => (
          <button key={v} onClick={() => onVibeChange(v)}
            className="px-3 py-1.5 rounded-lg text-xs font-mono uppercase tracking-wider transition-all cursor-pointer"
            style={{
              background: selectedVibe === v ? "rgba(0,255,136,0.15)" : "rgba(255,255,255,0.04)",
              color: selectedVibe === v ? "#00ff88" : "#6b6b80",
              border: `1px solid ${selectedVibe === v ? "rgba(0,255,136,0.3)" : "rgba(255,255,255,0.06)"}`,
            }}>
            {v}
          </button>
        ))}
      </div>
      <div className="grid grid-cols-4 gap-2" style={{ maxHeight: "200px", overflowY: "auto" }}>
        {currentImages.map((img) => (
          <button key={img.filename} onClick={() => onSelectArt(img)}
            className="relative rounded-lg overflow-hidden aspect-square cursor-pointer transition-all"
            style={{ border: selectedArt?.filename === img.filename ? "2px solid #00ff88" : "2px solid transparent" }}>
            <img src={`${API}/artworks/image/${selectedVibe}/${img.filename}`} alt={img.filename}
              className="w-full h-full object-cover" loading="lazy" />
            {selectedArt?.filename === img.filename && (
              <div className="absolute inset-0 flex items-center justify-center" style={{ background: "rgba(0,0,0,0.5)" }}>
                <span className="text-2xl">âœ“</span>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

// â”€â”€â”€ PLAYLIST SELECTOR â”€â”€â”€
function PlaylistSelector({ selectedPlaylistId, onSelect }) {
  const [playlists, setPlaylists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API}/youtube/playlists`)
      .then((r) => r.json())
      .then((data) => {
        if (data.success) setPlaylists(data.playlists || []);
        else setError(data.error || "Could not load playlists");
      })
      .catch(() => setError("Network error â€” is backend running?"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="py-3 text-xs font-mono text-center" style={{ color: "#3a3a4a" }}>
      â³ Loading playlists...
    </div>
  );

  if (error) return (
    <div className="py-2 px-3 text-xs font-mono rounded-lg"
      style={{ color: "#ff6644", background: "rgba(255,68,0,0.06)", border: "1px solid rgba(255,68,0,0.15)" }}>
      âš ï¸ {error}
    </div>
  );

  return (
    <div>
      <label className="block text-xs uppercase tracking-widest mb-2 font-mono" style={{ color: "#4a4a5a" }}>
        ğŸ“‹ Playlist
      </label>
      <div className="flex flex-col gap-1.5" style={{ maxHeight: "180px", overflowY: "auto" }}>
        <button onClick={() => onSelect(null)}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all cursor-pointer text-left"
          style={{
            background: selectedPlaylistId === null ? "rgba(107,107,128,0.12)" : "rgba(255,255,255,0.03)",
            border: `1px solid ${selectedPlaylistId === null ? "rgba(107,107,128,0.35)" : "rgba(255,255,255,0.06)"}`,
            color: selectedPlaylistId === null ? "#e8e8ef" : "#6b6b80",
          }}>
          <span>ğŸš«</span>
          <span>No playlist</span>
        </button>
        {playlists.map((pl) => (
          <button key={pl.id} onClick={() => onSelect(pl.id)}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all cursor-pointer text-left"
            style={{
              background: selectedPlaylistId === pl.id ? "rgba(0,255,136,0.08)" : "rgba(255,255,255,0.03)",
              border: `1px solid ${selectedPlaylistId === pl.id ? "rgba(0,255,136,0.3)" : "rgba(255,255,255,0.06)"}`,
              color: selectedPlaylistId === pl.id ? "#00ff88" : "#c8c8d4",
            }}>
            {pl.thumbnail && (
              <img src={pl.thumbnail} alt="" className="rounded flex-shrink-0"
                style={{ width: 32, height: 24, objectFit: "cover" }} />
            )}
            <div className="min-w-0 flex-1">
              <div className="truncate font-medium">{pl.title}</div>
              <div className="text-xs" style={{ color: selectedPlaylistId === pl.id ? "rgba(0,255,136,0.55)" : "#3a3a4a" }}>
                {pl.item_count} videos · {pl.privacy}
              </div>
            </div>
            {selectedPlaylistId === pl.id && <span className="flex-shrink-0 text-xs">âœ“</span>}
          </button>
        ))}
      </div>
    </div>
  );
}

// â”€â”€â”€ PUBLISH PANEL â”€â”€â”€
function PublishPanel({ preview, beat, artist1, artist2, beatName, bpm, musicalKey, drop, outro, vibe, onProcessed, onReset }) {
  const [tab, setTab] = useState("now");

  // Publish Now
  const [privacyNow, setPrivacyNow] = useState("public");
  const [playlistId, setPlaylistId] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);

  // Schedule
  const [scheduleDate, setScheduleDate] = useState(() => {
    const d = new Date(); d.setDate(d.getDate() + 1);
    return d.toISOString().split("T")[0];
  });
  const [scheduleHour, setScheduleHour] = useState(22);
  const [privacySchedule, setPrivacySchedule] = useState("public");
  const [playlistIdSchedule, setPlaylistIdSchedule] = useState(null);
  const [scheduling, setScheduling] = useState(false);
  const [scheduleStatus, setScheduleStatus] = useState(null);
  const [scheduleResult, setScheduleResult] = useState(null);

  const PRIVACY_OPTIONS = [
    { value: "public",   label: "Public",   icon: "ğŸŒ", desc: "Everyone" },
    { value: "unlisted", label: "Unlisted", icon: "ğŸ”-", desc: "Link only" },
    { value: "private",  label: "Private",  icon: "ğŸ”’", desc: "Only you" },
  ];

  const buildSeo = async () => {
    const res = await fetch(`${API}/seo/generate`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        artist1, artist2, beat_name: beatName, bpm, key: musicalKey,
        drop, outro, vibe: vibe.toLowerCase(),
        duration_seconds: preview.render?.duration,
      }),
    });
    return res.json();
  };

  const addToPlaylist = async (videoId, plId) => {
    if (!videoId || !plId) return;
    await fetch(`${API}/youtube/playlists/add`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ video_id: videoId, playlist_id: plId }),
    });
  };

  const handlePublishNow = async () => {
    setUploading(true); setUploadStatus("uploading"); setUploadResult(null);
    try {
      const seo = await buildSeo();
      const res = await fetch(`${API}/upload/youtube`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          beat_id: beat.id,
          mp4_path: preview.mp4_path,
          thumbnail_path: preview.thumbnail_path,
          title: seo.title, description: seo.description, tags: seo.tags,
          category_id: "10", privacy_status: privacyNow,
        }),
      });
      const result = await res.json();
      if (result.success) {
        await addToPlaylist(result.video_id, playlistId);
        setUploadStatus("done"); setUploadResult(result);
        if (onProcessed) onProcessed(beat.id);
      } else {
        setUploadStatus("failed"); setUploadResult(result);
      }
    } catch (e) {
      setUploadStatus("failed"); setUploadResult({ error: e.message });
    }
    setUploading(false);
  };

  const handleSchedule = async () => {
    setScheduling(true); setScheduleStatus("uploading"); setScheduleResult(null);
    try {
      const seo = await buildSeo();
      const res = await fetch(`${API}/schedule/youtube`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          beat_id: beat.id,
          mp4_path: preview.mp4_path,
          thumbnail_path: preview.thumbnail_path,
          title: seo.title, description: seo.description, tags: seo.tags,
          category_id: "10", privacy_status: privacySchedule,
          schedule_date: scheduleDate, schedule_hour: scheduleHour,
        }),
      });
      const result = await res.json();
      if (result.success) {
        await addToPlaylist(result.video_id, playlistIdSchedule);
        setScheduleStatus("done"); setScheduleResult(result);
        if (onProcessed) onProcessed(beat.id);
      } else {
        setScheduleStatus("failed"); setScheduleResult(result);
      }
    } catch (e) {
      setScheduleStatus("failed"); setScheduleResult({ error: e.message });
    }
    setScheduling(false);
  };

  const isDone = uploadStatus === "done" || scheduleStatus === "done";

  if (isDone) {
    const res = uploadResult || scheduleResult;
    const isScheduled = scheduleStatus === "done";
    return (
      <div className="rounded-2xl p-6 text-center"
        style={{ background: isScheduled ? "rgba(255,215,0,0.04)" : "rgba(0,255,136,0.04)",
                 border: `1px solid ${isScheduled ? "rgba(255,215,0,0.2)" : "rgba(0,255,136,0.2)"}` }}>
        <div className="text-4xl mb-3">{isScheduled ? "ğŸ-“" : "ğŸ‰"}</div>
        <h3 className="font-bold text-lg mb-1" style={{ color: isScheduled ? "#ffd700" : "#00ff88" }}>
          {isScheduled ? "Scheduled!" : "Published!"}
        </h3>
        {res?.video_url && (
          <a href={res.video_url} target="_blank" rel="noopener noreferrer"
            className="text-xs font-mono underline block mt-1" style={{ color: "#6b6b80" }}>
            {res.video_url}
          </a>
        )}
        {res?.scheduled_at && (
          <p className="text-xs font-mono mt-2" style={{ color: "#4a4a5a" }}>
            Goes live: {new Date(res.scheduled_at).toLocaleString()}
          </p>
        )}
      </div>
    );
  }

  const PrivacyPicker = ({ value, onChange, accentColor }) => (
    <div className="grid grid-cols-3 gap-2">
      {PRIVACY_OPTIONS.map((opt) => {
        const active = value === opt.value;
        return (
          <button key={opt.value} onClick={() => onChange(opt.value)}
            className="py-3 px-2 rounded-xl text-center transition-all cursor-pointer"
            style={{
              background: active ? `rgba(${accentColor},0.08)` : "rgba(255,255,255,0.03)",
              border: `1px solid ${active ? `rgba(${accentColor},0.35)` : "rgba(255,255,255,0.07)"}`,
            }}>
            <div className="text-lg mb-1">{opt.icon}</div>
            <div className="text-xs font-semibold"
              style={{ color: active ? `rgb(${accentColor})` : "#c8c8d4" }}>{opt.label}</div>
            <div className="text-xs mt-0.5" style={{ color: "#3a3a4a" }}>{opt.desc}</div>
          </button>
        );
      })}
    </div>
  );

  return (
    <div className="rounded-2xl border overflow-hidden" style={{ borderColor: "rgba(255,255,255,0.08)" }}>
      {/* Tabs */}
      <div className="flex" style={{ background: "#0d0d14", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        {[
          { key: "now",      label: "⚡ Publish Now" },
          { key: "schedule", label: "ğŸ-“ Schedule" },
        ].map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className="flex-1 py-3.5 text-sm font-semibold transition-all cursor-pointer"
            style={{
              color: tab === t.key ? "#e8e8ef" : "#4a4a5a",
              borderBottom: tab === t.key
                ? `2px solid ${t.key === "now" ? "#00ff88" : "#ffd700"}`
                : "2px solid transparent",
              background: tab === t.key ? "rgba(255,255,255,0.02)" : "transparent",
            }}>
            {t.label}
          </button>
        ))}
      </div>

      <div className="p-5 space-y-5">

        {/* â”€â”€ PUBLISH NOW â”€â”€ */}
        {tab === "now" && (
          <>
            <div>
              <label className="block text-xs uppercase tracking-widest mb-2 font-mono" style={{ color: "#4a4a5a" }}>
                ğŸ‘ Visibility
              </label>
              <PrivacyPicker value={privacyNow} onChange={setPrivacyNow} accentColor="0,255,136" />
            </div>

            <PlaylistSelector selectedPlaylistId={playlistId} onSelect={setPlaylistId} />

            {uploadStatus === "failed" && (
              <div className="text-xs font-mono px-3 py-2 rounded-lg"
                style={{ background: "rgba(255,68,68,0.08)", color: "#ff4444", border: "1px solid rgba(255,68,68,0.2)" }}>
                âŒ {uploadResult?.error || "Upload failed"}
              </div>
            )}

            <div className="flex gap-3">
              <button onClick={onReset}
                className="px-4 py-3 rounded-xl text-sm transition-all cursor-pointer"
                style={{ background: "rgba(255,255,255,0.04)", color: "#6b6b80", border: "1px solid rgba(255,255,255,0.08)" }}>
                â†© Edit
              </button>
              <button onClick={handlePublishNow} disabled={uploading}
                className="flex-1 py-3 rounded-xl font-bold text-sm transition-all cursor-pointer disabled:opacity-40"
                style={{
                  background: "linear-gradient(135deg, rgba(0,255,136,0.18), rgba(0,180,80,0.1))",
                  color: "#00ff88", border: "1px solid rgba(0,255,136,0.35)",
                }}>
                {uploading ? "â³ Uploading..." : "ğŸš€ Publish Now"}
              </button>
            </div>
          </>
        )}

        {/* â”€â”€ SCHEDULE â”€â”€ */}
        {tab === "schedule" && (
          <>
            <div>
              <label className="block text-xs uppercase tracking-widest mb-2 font-mono" style={{ color: "#4a4a5a" }}>
                ğŸ“… Date & Time (TRT / UTC+3)
              </label>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs mb-1" style={{ color: "#4a4a5a" }}>Date</label>
                  <input type="date" value={scheduleDate}
                    min={new Date().toISOString().split("T")[0]}
                    onChange={(e) => setScheduleDate(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none"
                    style={{ background: "rgba(255,255,255,0.04)", borderColor: "rgba(255,255,255,0.1)", color: "#e8e8ef" }}
                  />
                </div>
                <div>
                  <label className="block text-xs mb-1" style={{ color: "#4a4a5a" }}>Hour (TRT)</label>
                  <select value={scheduleHour} onChange={(e) => setScheduleHour(parseInt(e.target.value))}
                    className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none"
                    style={{ background: "rgba(255,255,255,0.04)", borderColor: "rgba(255,255,255,0.1)", color: "#e8e8ef" }}>
                    {Array.from({ length: 24 }, (_, i) => (
                      <option key={i} value={i}>{String(i).padStart(2, "0")}:00</option>
                    ))}
                  </select>
                </div>
              </div>
              <p className="text-xs mt-1.5 font-mono" style={{ color: "#3a3a4a" }}>
                UTC: {String(((scheduleHour - 3) + 24) % 24).padStart(2, "0")}:00 â€” video uploads now, unlocks at scheduled time
              </p>
            </div>

            <div>
              <label className="block text-xs uppercase tracking-widest mb-2 font-mono" style={{ color: "#4a4a5a" }}>
                ğŸ‘ Visibility at publish time
              </label>
              <PrivacyPicker value={privacySchedule} onChange={setPrivacySchedule} accentColor="255,215,0" />
            </div>

            <PlaylistSelector selectedPlaylistId={playlistIdSchedule} onSelect={setPlaylistIdSchedule} />

            {scheduleStatus === "failed" && (
              <div className="text-xs font-mono px-3 py-2 rounded-lg"
                style={{ background: "rgba(255,68,68,0.08)", color: "#ff4444", border: "1px solid rgba(255,68,68,0.2)" }}>
                âŒ {scheduleResult?.error || "Schedule failed"}
              </div>
            )}

            <div className="flex gap-3">
              <button onClick={onReset}
                className="px-4 py-3 rounded-xl text-sm transition-all cursor-pointer"
                style={{ background: "rgba(255,255,255,0.04)", color: "#6b6b80", border: "1px solid rgba(255,255,255,0.08)" }}>
                â†© Edit
              </button>
              <button onClick={handleSchedule} disabled={scheduling}
                className="flex-1 py-3 rounded-xl font-bold text-sm transition-all cursor-pointer disabled:opacity-40"
                style={{
                  background: "linear-gradient(135deg, rgba(255,215,0,0.15), rgba(255,165,0,0.08))",
                  color: "#ffd700", border: "1px solid rgba(255,215,0,0.35)",
                }}>
                {scheduling ? "â³ Scheduling..." : "ğŸ-“ Schedule Upload"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// â”€â”€â”€ BEAT CARD â”€â”€â”€
function BeatCard({ beat, allTiers, artworks, onProcessed }) {
  const [artist1, setArtist1] = useState("");
  const [artist2, setArtist2] = useState("");
  const [beatName, setBeatName] = useState("");
  const [bpm, setBpm] = useState(140);
  const [musicalKey, setMusicalKey] = useState("Fm");
  const [drop, setDrop] = useState("0:25");
  const [outro, setOutro] = useState("2:30");
  const [vibe, setVibe] = useState(Object.keys(artworks)[0] || "RAGE");
  const [selectedArt, setSelectedArt] = useState(null);
  const [showMore, setShowMore] = useState(false);
  const [status, setStatus] = useState(beat.status);
  const [preview, setPreview] = useState(null);
  const [rendering, setRendering] = useState(false);

  const liveTitle = artist1 && artist2 && beatName
    ? `[FREE] ${artist1} x ${artist2} Type Beat - "${beatName}"`
    : `[FREE] _____ x _____ Type Beat - "_____"`;

  const isReady = artist1 && artist2 && beatName && selectedArt;

  const handleRender = async () => {
    if (!isReady) return;
    setRendering(true); setStatus("rendering");
    try {
      const res = await fetch(`${API}/render/mp4`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          beat_id: beat.id,
          artwork_path: `${vibe}/${selectedArt.filename}`,
          preset: vibe.toLowerCase(),
          beat_name: beatName,
          artist1, artist2, bpm, key: musicalKey, drop,
        }),
      });
      const data = await res.json();
      if (data.error) { alert(`Render failed: ${data.error}`); setStatus("render_failed"); }
      else { setPreview(data); setStatus("rendered"); }
    } catch (e) { alert(`Error: ${e.message}`); setStatus("error"); }
    setRendering(false);
  };

  const handleReset = () => { setPreview(null); setStatus("pending"); };

  const statusColors = {
    pending: "#6b6b80", configuring: "#3b82f6", rendering: "#ffd700",
    rendered: "#00ff88", uploading: "#ff69b4", done: "#00ff88",
    render_failed: "#ff4444", upload_failed: "#ff4444", error: "#ff4444",
  };

  return (
    <div className="rounded-2xl border p-6 mb-6"
      style={{ background: "#111118", borderColor: "rgba(255,255,255,0.08)" }}>

      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <span className="text-2xl">ğŸµ</span>
          <div>
            <h3 className="font-bold text-lg" style={{ color: "#e8e8ef" }}>{beat.filename}</h3>
            <p className="text-xs font-mono" style={{ color: "#3a3a4a" }}>
              {beat.size_mb} MB · {beat.extension} · {new Date(beat.detected_at).toLocaleString()}
            </p>
          </div>
        </div>
        <span className="text-xs font-mono px-3 py-1 rounded-full uppercase tracking-wider"
          style={{ background: `${statusColors[status]}15`, color: statusColors[status] }}>
          {status}
        </span>
      </div>

      {/* Live Title */}
      <div className="rounded-xl p-4 mb-5 font-mono text-sm text-center"
        style={{
          background: isReady ? "rgba(0,255,136,0.06)" : "rgba(255,255,255,0.03)",
          border: `1px dashed ${isReady ? "rgba(0,255,136,0.3)" : "rgba(255,255,255,0.08)"}`,
          color: isReady ? "#00ff88" : "#3a3a4a",
        }}>
        {liveTitle}
      </div>

      {/* Artists */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <ArtistSelector label="Artist 1" value={artist1} onSelect={setArtist1} allTiers={allTiers} />
        <ArtistSelector label="Artist 2" value={artist2} onSelect={setArtist2} allTiers={allTiers} />
      </div>

      {/* Beat Name */}
      <div className="mb-5">
        <label className="block text-xs uppercase tracking-widest mb-1.5 font-mono" style={{ color: "#4a4a5a" }}>Beat Name</label>
        <input type="text" value={beatName} onChange={(e) => setBeatName(e.target.value)}
          placeholder="e.g. Night Vision"
          className="w-full px-4 py-3 rounded-xl border text-sm outline-none transition-all"
          style={{
            background: "rgba(255,255,255,0.03)",
            borderColor: beatName ? "rgba(0,255,136,0.2)" : "rgba(255,255,255,0.08)",
            color: "#e8e8ef",
          }}
        />
      </div>

      {/* Artwork */}
      <div className="mb-5">
        <label className="block text-xs uppercase tracking-widest mb-2 font-mono" style={{ color: "#4a4a5a" }}>Artwork</label>
        <ArtworkBrowser artworks={artworks} selectedVibe={vibe} onVibeChange={setVibe}
          selectedArt={selectedArt} onSelectArt={setSelectedArt} />
      </div>

      {/* More Settings */}
      <button onClick={() => setShowMore(!showMore)}
        className="w-full text-left px-4 py-2.5 rounded-xl mb-4 text-sm transition-all flex items-center justify-between cursor-pointer"
        style={{ background: "rgba(255,255,255,0.03)", color: "#6b6b80" }}>
        <span>âš™ï¸ BPM · Key · Timestamps</span>
        <span style={{ transform: showMore ? "rotate(180deg)" : "rotate(0)", transition: "transform 0.2s" }}>â–¼</span>
      </button>

      {showMore && (
        <div className="mb-5 p-4 rounded-xl"
          style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)" }}>
          {/* BPM & Key */}
          <div className="grid grid-cols-2 gap-4 mb-5">
            <div>
              <label className="block text-xs uppercase tracking-widest mb-1.5 font-mono" style={{ color: "#4a4a5a" }}>BPM</label>
              <input type="number" value={bpm} onChange={(e) => setBpm(parseInt(e.target.value) || 140)}
                min={60} max={220}
                className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none"
                style={{ background: "rgba(255,255,255,0.04)", borderColor: "rgba(255,255,255,0.08)", color: "#e8e8ef" }}
              />
            </div>
            <div>
              <label className="block text-xs uppercase tracking-widest mb-1.5 font-mono" style={{ color: "#4a4a5a" }}>Key</label>
              <select value={musicalKey} onChange={(e) => setMusicalKey(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none"
                style={{ background: "rgba(255,255,255,0.04)", borderColor: "rgba(255,255,255,0.08)", color: "#e8e8ef" }}>
                {KEYS.map((k) => <option key={k} value={k}>{k}</option>)}
              </select>
            </div>
          </div>

          {/* YouTube Chapters */}
          <div>
            <label className="block text-xs uppercase tracking-widest mb-2 font-mono" style={{ color: "#4a4a5a" }}>
              â± YouTube Chapters
            </label>
            <div className="rounded-xl overflow-hidden" style={{ border: "1px solid rgba(255,255,255,0.07)" }}>
              {/* Intro â€” fixed */}
              <div className="flex items-center gap-3 px-4 py-3"
                style={{ background: "rgba(255,255,255,0.02)", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                <span className="font-mono text-sm w-12 text-right flex-shrink-0" style={{ color: "#ffd700" }}>0:00</span>
                <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: "#ffd700" }}></span>
                <span className="text-sm flex-1" style={{ color: "#6b6b80" }}>Intro</span>
                <span className="text-xs font-mono" style={{ color: "#2a2a3a" }}>locked</span>
              </div>
              {/* Drop â€” editable */}
              <div className="flex items-center gap-3 px-4 py-2.5"
                style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                <input type="text" value={drop} onChange={(e) => setDrop(e.target.value)}
                  placeholder="0:25"
                  className="font-mono text-sm w-16 rounded-lg px-2 py-1 border-none outline-none text-right flex-shrink-0"
                  style={{ background: "rgba(0,255,136,0.1)", color: "#00ff88" }}
                />
                <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: "#00ff88" }}></span>
                <span className="text-sm flex-1" style={{ color: "#c8c8d4" }}>Drop</span>
              </div>
              {/* Outro â€” editable */}
              <div className="flex items-center gap-3 px-4 py-2.5">
                <input type="text" value={outro} onChange={(e) => setOutro(e.target.value)}
                  placeholder="2:30"
                  className="font-mono text-sm w-16 rounded-lg px-2 py-1 border-none outline-none text-right flex-shrink-0"
                  style={{ background: "rgba(0,255,136,0.1)", color: "#00ff88" }}
                />
                <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: "#00ff88" }}></span>
                <span className="text-sm flex-1" style={{ color: "#c8c8d4" }}>Outro</span>
              </div>
            </div>
            <p className="text-xs mt-2 font-mono" style={{ color: "#2a2a3a" }}>
              YouTube needs 3+ timestamps starting at 0:00 to show chapters
            </p>
          </div>
        </div>
      )}

      {/* Render result */}
      {preview && !rendering && (
        <div className="rounded-xl p-4 mb-5"
          style={{ background: "rgba(0,255,136,0.04)", border: "1px solid rgba(0,255,136,0.15)" }}>
          <h4 className="text-sm font-semibold mb-1.5" style={{ color: "#00ff88" }}>âœ… Render Complete</h4>
          <div className="text-xs font-mono space-y-0.5" style={{ color: "#6b6b80" }}>
            <p>{preview.render?.file_size_mb} MB · {preview.render?.encoding?.resolution} · {preview.render?.encoding?.audio_bitrate}</p>
            <p>Duration: {Math.round(preview.render?.duration || 0)}s</p>
          </div>
        </div>
      )}

      {/* Render Button OR Publish Panel */}
      {!preview ? (
        <button onClick={handleRender} disabled={!isReady || rendering}
          className="w-full py-3.5 rounded-xl font-semibold text-sm transition-all cursor-pointer disabled:cursor-not-allowed disabled:opacity-30"
          style={{
            background: isReady ? "rgba(0,255,136,0.15)" : "rgba(255,255,255,0.04)",
            color: isReady ? "#00ff88" : "#3a3a4a",
            border: `1px solid ${isReady ? "rgba(0,255,136,0.3)" : "rgba(255,255,255,0.06)"}`,
          }}>
          {rendering ? "â³ Rendering..." : "ğŸ‘ï¸ Preview & Render"}
        </button>
      ) : (
        <PublishPanel
          preview={preview} beat={beat}
          artist1={artist1} artist2={artist2} beatName={beatName}
          bpm={bpm} musicalKey={musicalKey}
          drop={drop} outro={outro} vibe={vibe}
          onProcessed={onProcessed} onReset={handleReset}
        />
      )}
    </div>
  );
}

// â”€â”€â”€ MAIN APP â”€â”€â”€
export default function JETBOXDashboard() {
  const [beats, setBeats] = useState([]);
  const [allTiers, setAllTiers] = useState({});
  const [artworks, setArtworks] = useState({});
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);

  useEffect(() => {
    async function loadInitial() {
      try {
        const [tiersRes, artRes, healthRes] = await Promise.all([
          fetch(`${API}/artists/tiers`).then((r) => r.json()),
          fetch(`${API}/artworks`).then((r) => r.json()),
          fetch(`${API}/health`).then((r) => r.json()),
        ]);
        setAllTiers(tiersRes || {});
        setArtworks(artRes || {});
        setHealth(healthRes);
      } catch (e) { console.error("Failed to fetch:", e); }
      setLoading(false);
    }
    loadInitial();
  }, []);

  const handleScan = async () => {
    setScanning(true);
    try {
      await fetch(`${API}/beats/scan`, { method: "POST" });
      const [beatsRes, artRes] = await Promise.all([
        fetch(`${API}/beats/pending`).then((r) => r.json()),
        fetch(`${API}/artworks`).then((r) => r.json()),
      ]);
      setBeats(beatsRes.beats || []);
      setArtworks(artRes || {});
    } catch (e) { console.error("Scan failed:", e); }
    setScanning(false);
  };

  const handleProcessed = async () => {
    const res = await fetch(`${API}/beats/pending`).then((r) => r.json());
    setBeats(res.beats || []);
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "#0a0a0f", color: "#6b6b80" }}>
      <div className="text-center">
        <div className="text-4xl mb-4">ğŸµ</div>
        <p className="font-mono text-sm">Loading JETBOX...</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen" style={{ background: "#0a0a0f", color: "#e8e8ef" }}>
      <div className="border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
        <div className="max-w-4xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-black tracking-tight">
              JETBOX <span style={{ color: "#00ff88" }}>v3</span>
            </h1>
            <span className="text-xs font-mono px-2.5 py-1 rounded-full"
              style={{ background: "rgba(0,255,136,0.08)", color: "#00ff88" }}>ENNYTANG</span>
          </div>
          <div className="flex items-center gap-4">
            {health && (
              <span className="text-xs font-mono" style={{ color: health.ffmpeg?.available ? "#00ff88" : "#ff4444" }}>
                FFmpeg: {health.ffmpeg?.available ? "âœ“" : "âœ-"}
              </span>
            )}
            <button onClick={handleScan} disabled={scanning}
              className="px-4 py-2 rounded-lg text-xs font-mono transition-all cursor-pointer disabled:opacity-50"
              style={{ background: "rgba(0,255,136,0.1)", color: "#00ff88", border: "1px solid rgba(0,255,136,0.2)" }}>
              {scanning ? "â³ Scanning..." : "ğŸ”„ Scan BEATS/"}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex items-center gap-6 mb-8 text-xs font-mono" style={{ color: "#3a3a4a" }}>
          <span>ğŸ“‚ Pending: <span style={{ color: "#ffd700" }}>{beats.length}</span></span>
          <span>ğŸ¤ Artists: <span style={{ color: "#6b6b80" }}>{Object.values(allTiers).flat().length}</span></span>
          <span>ğŸ¨ Artworks: <span style={{ color: "#6b6b80" }}>{Object.values(artworks).reduce((s, v) => s + (v.count || 0), 0)}</span></span>
          <span>ğŸ‘ï¸ Watcher: <span style={{ color: health?.watcher_running ? "#00ff88" : "#ff4444" }}>{health?.watcher_running ? "ON" : "OFF"}</span></span>
        </div>

        {beats.length === 0 ? (
          <div className="rounded-2xl border p-12 text-center"
            style={{ background: "#111118", borderColor: "rgba(255,255,255,0.06)" }}>
            <div className="text-5xl mb-4">ğŸ“‚</div>
            <h2 className="text-lg font-semibold mb-2" style={{ color: "#6b6b80" }}>No beats waiting</h2>
            <p className="text-sm mb-6" style={{ color: "#3a3a4a" }}>
              Drop a WAV or MP3 into the BEATS/ folder, then click Scan.
            </p>
            <button onClick={handleScan} disabled={scanning}
              className="px-6 py-3 rounded-xl text-sm font-semibold transition-all cursor-pointer disabled:opacity-50"
              style={{ background: "rgba(0,255,136,0.1)", color: "#00ff88", border: "1px solid rgba(0,255,136,0.2)" }}>
              {scanning ? "â³ Scanning..." : "ğŸ”„ Scan for Beats"}
            </button>
          </div>
        ) : (
          beats.map((beat) => (
            <BeatCard key={beat.id} beat={beat} allTiers={allTiers}
              artworks={artworks} onProcessed={handleProcessed} />
          ))
        )}
      </div>
    </div>
  );
}

