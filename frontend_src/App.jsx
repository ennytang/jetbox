import { useState, useEffect, useCallback, useRef } from "react";

const API = "/api";

// â”€â”€â”€ MUSICAL KEYS â”€â”€â”€
const KEYS = ["Cm","C#m","Dm","D#m","Em","Fm","F#m","Gm","G#m","Am","A#m","Bm",
              "C","C#","D","D#","E","F","F#","G","G#","A","A#","B"];

// â”€â”€â”€ TIER CONFIG â”€â”€â”€
const TIER_LABELS = {
  legends: { label: "Legends", icon: "ğŸ‘‘" },
  major: { label: "Major", icon: "â­" },
  rising: { label: "Rising", icon: "ğŸ”¥" },
  producers: { label: "Producers", icon: "ğŸ¹" },
  new_wave: { label: "New Wave", icon: "ğŸŒŠ" },
  melodic_trap: { label: "Melodic", icon: "ğŸ’œ" },
  uk_international: { label: "UK/Intl", icon: "ğŸŒ" },
  classic: { label: "Classic", icon: "ğŸ†" },
  niche_targets: { label: "Niche âš¡", icon: "ğŸ¯" },
};

// â”€â”€â”€ ARTIST SELECTOR COMPONENT â”€â”€â”€
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
      <label className="block text-xs uppercase tracking-widest text-gray-500 mb-1.5 font-mono">{label}</label>
      <button
        onClick={() => setOpen(!open)}
        className="w-full text-left px-4 py-3 rounded-xl border transition-all cursor-pointer"
        style={{
          background: value ? "rgba(0,255,136,0.06)" : "rgba(255,255,255,0.03)",
          borderColor: value ? "rgba(0,255,136,0.3)" : "rgba(255,255,255,0.08)",
          color: value ? "#00ff88" : "#6b6b80",
        }}
      >
        {value || "Select artist..."}
      </button>

      {open && (
        <div className="absolute z-50 mt-2 w-full max-h-80 overflow-hidden rounded-xl border shadow-2xl"
          style={{ background: "#111118", borderColor: "rgba(255,255,255,0.1)" }}>
          <div className="p-2 sticky top-0" style={{ background: "#111118" }}>
            <input
              type="text"
              placeholder="Search artists..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              autoFocus
              className="w-full px-3 py-2 rounded-lg text-sm border-none outline-none"
              style={{ background: "rgba(255,255,255,0.06)", color: "#e8e8ef" }}
            />
          </div>
          <div className="overflow-y-auto max-h-64 px-1 pb-1">
            {Object.entries(TIER_LABELS).map(([tierKey, tierInfo]) => {
              const tierArtists = filtered.filter((a) => a.tier === tierKey);
              if (tierArtists.length === 0) return null;
              return (
                <div key={tierKey}>
                  <div className="px-3 py-1.5 text-xs font-mono uppercase tracking-wider"
                    style={{ color: "#3a3a4a" }}>
                    {tierInfo.icon} {tierInfo.label}
                  </div>
                  {tierArtists.map((a) => (
                    <button
                      key={a.name}
                      onClick={() => { onSelect(a.name); setOpen(false); setSearch(""); }}
                      className="w-full text-left px-3 py-2 text-sm rounded-lg transition-all hover:bg-white/5 cursor-pointer"
                      style={{ color: a.name === value ? "#00ff88" : "#c8c8d4" }}
                    >
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

// â”€â”€â”€ ARTWORK BROWSER COMPONENT â”€â”€â”€
function ArtworkBrowser({ artworks, selectedVibe, onVibeChange, selectedArt, onSelectArt }) {
  const vibes = Object.keys(artworks);
  if (vibes.length === 0) {
    return (
      <div className="rounded-xl border p-6 text-center"
        style={{ background: "#111118", borderColor: "rgba(255,255,255,0.08)" }}>
        <p className="text-gray-500 text-sm">No artworks found. Add images to ARTWORKS/RAGE/ or ARTWORKS/MELODIC/</p>
      </div>
    );
  }

  const currentImages = artworks[selectedVibe]?.images || [];

  return (
    <div>
      {/* Vibe Tabs */}
      <div className="flex gap-2 mb-4">
        {vibes.map((v) => (
          <button
            key={v}
            onClick={() => onVibeChange(v)}
            className="px-4 py-2 rounded-lg text-sm font-semibold transition-all cursor-pointer"
            style={{
              background: selectedVibe === v
                ? (v === "RAGE" ? "rgba(57,255,20,0.15)" : "rgba(255,105,180,0.15)")
                : "rgba(255,255,255,0.04)",
              color: selectedVibe === v
                ? (v === "RAGE" ? "#39ff14" : "#ff69b4")
                : "#6b6b80",
              border: `1px solid ${selectedVibe === v
                ? (v === "RAGE" ? "rgba(57,255,20,0.3)" : "rgba(255,105,180,0.3)")
                : "rgba(255,255,255,0.06)"}`,
            }}
          >
            {v === "RAGE" ? "ğŸŸ¢ RAGE" : "ğŸ©· MELODIC"} ({artworks[v]?.count || 0})
          </button>
        ))}
      </div>

      {/* Image Grid */}
      <div className="grid grid-cols-3 gap-3">
        {currentImages.map((img) => (
          <button
            key={img.filename}
            onClick={() => onSelectArt(img)}
            className="relative rounded-xl overflow-hidden border-2 transition-all aspect-video cursor-pointer"
            style={{
              borderColor: selectedArt?.filename === img.filename
                ? (selectedVibe === "RAGE" ? "#39ff14" : "#ff69b4")
                : "rgba(255,255,255,0.06)",
              boxShadow: selectedArt?.filename === img.filename
                ? `0 0 20px ${selectedVibe === "RAGE" ? "rgba(57,255,20,0.2)" : "rgba(255,105,180,0.2)"}`
                : "none",
            }}
          >
            <img
              src={`${API}/artworks/image/${selectedVibe}/${img.filename}`}
              alt={img.filename}
              className="w-full h-full object-cover"
              loading="lazy"
            />
            {selectedArt?.filename === img.filename && (
              <div className="absolute inset-0 flex items-center justify-center"
                style={{ background: "rgba(0,0,0,0.5)" }}>
                <span className="text-2xl">âœ“</span>
              </div>
            )}
            <div className="absolute bottom-0 left-0 right-0 px-2 py-1 text-xs truncate"
              style={{ background: "rgba(0,0,0,0.7)", color: "#999" }}>
              {img.filename}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

// â”€â”€â”€ CROP TOOL COMPONENT â”€â”€â”€
function CropTool({ imageUrl, cropBox, onChange }) {
  const containerRef = useRef(null);
  const [dragging, setDragging] = useState(null); // "move" | "resize" | null
  const [dragStart, setDragStart] = useState({ mx: 0, my: 0, ox: 0, oy: 0, os: 0 });

  const handlePointerDown = (e, mode) => {
    e.preventDefault();
    e.stopPropagation();
    const rect = containerRef.current.getBoundingClientRect();
    setDragging(mode);
    setDragStart({
      mx: e.clientX,
      my: e.clientY,
      ox: cropBox.x,
      oy: cropBox.y,
      os: cropBox.size,
      cw: rect.width,
      ch: rect.height,
    });
  };

  useEffect(() => {
    if (!dragging) return;
    const handleMove = (e) => {
      const dx = (e.clientX - dragStart.mx) / dragStart.cw;
      const dy = (e.clientY - dragStart.my) / dragStart.ch;

      if (dragging === "move") {
        const newX = Math.max(0, Math.min(1 - cropBox.size, dragStart.ox + dx));
        const newY = Math.max(0, Math.min(1 - cropBox.size, dragStart.oy + dy));
        onChange({ ...cropBox, x: newX, y: newY });
      } else if (dragging === "resize") {
        const delta = Math.max(dx, dy);
        const newSize = Math.max(0.15, Math.min(1, dragStart.os + delta));
        const newX = Math.max(0, Math.min(1 - newSize, cropBox.x));
        const newY = Math.max(0, Math.min(1 - newSize, cropBox.y));
        onChange({ x: newX, y: newY, size: newSize });
      }
    };
    const handleUp = () => setDragging(null);
    window.addEventListener("pointermove", handleMove);
    window.addEventListener("pointerup", handleUp);
    return () => {
      window.removeEventListener("pointermove", handleMove);
      window.removeEventListener("pointerup", handleUp);
    };
  }, [dragging, dragStart, cropBox, onChange]);

  return (
    <div ref={containerRef} className="relative rounded-xl overflow-hidden select-none"
      style={{ background: "#000", aspectRatio: "auto", maxHeight: "400px" }}>
      {/* Full image (dimmed outside crop) */}
      <img src={imageUrl} alt="artwork" className="w-full h-auto block" style={{ opacity: 0.35 }} draggable={false} />

      {/* Bright crop area */}
      <div style={{
        position: "absolute",
        left: `${cropBox.x * 100}%`,
        top: `${cropBox.y * 100}%`,
        width: `${cropBox.size * 100}%`,
        height: `${cropBox.size * 100}%`,
        overflow: "hidden",
        border: "2px solid #39ff14",
        boxShadow: "0 0 0 9999px rgba(0,0,0,0.6)",
        cursor: "grab",
      }}
        onPointerDown={(e) => handlePointerDown(e, "move")}
      >
        <img src={imageUrl} alt="crop" draggable={false} style={{
          position: "absolute",
          left: `-${(cropBox.x / cropBox.size) * 100}%`,
          top: `-${(cropBox.y / cropBox.size) * 100}%`,
          width: `${(1 / cropBox.size) * 100}%`,
          height: "auto",
          pointerEvents: "none",
        }} />
      </div>

      {/* Resize handle (bottom-right corner) */}
      <div style={{
        position: "absolute",
        left: `calc(${(cropBox.x + cropBox.size) * 100}% - 14px)`,
        top: `calc(${(cropBox.y + cropBox.size) * 100}% - 14px)`,
        width: "20px",
        height: "20px",
        background: "#39ff14",
        borderRadius: "4px",
        cursor: "nwse-resize",
        zIndex: 10,
        boxShadow: "0 0 8px rgba(57,255,20,0.5)",
      }}
        onPointerDown={(e) => handlePointerDown(e, "resize")}
      />

      {/* 1:1 label */}
      <div style={{
        position: "absolute",
        top: "8px",
        right: "8px",
        background: "rgba(0,0,0,0.7)",
        color: "#39ff14",
        fontSize: "11px",
        fontFamily: "monospace",
        padding: "3px 8px",
        borderRadius: "6px",
      }}>
        1:1 CROP
      </div>

      {/* Preview strip â€” shows how it'll look on YouTube */}
      <div style={{
        position: "absolute",
        bottom: "8px",
        left: "50%",
        transform: "translateX(-50%)",
        width: "200px",
        height: "30px",
        background: "#000",
        borderRadius: "4px",
        border: "1px solid rgba(57,255,20,0.3)",
        display: "flex",
        overflow: "hidden",
      }}>
        <div style={{ flex: "420", background: "#000" }} />
        <div style={{
          flex: "1080",
          backgroundImage: `url(${imageUrl})`,
          backgroundSize: `${(1 / cropBox.size) * 100}%`,
          backgroundPosition: `${-cropBox.x / cropBox.size * 100}% ${-cropBox.y / cropBox.size * 100}%`,
        }} />
        <div style={{ flex: "420", background: "#000" }} />
      </div>
    </div>
  );
}

// â”€â”€â”€ BEAT CARD COMPONENT â”€â”€â”€
function BeatCard({ beat, allTiers, artworks, onProcessed, onRefresh }) {
  const [artist1, setArtist1] = useState("");
  const [artist2, setArtist2] = useState("");
  const [beatName, setBeatName] = useState("");
  const [bpm, setBpm] = useState(140);
  const [musicalKey, setMusicalKey] = useState("Fm");
  const [drop, setDrop] = useState("0:25");
  const [vibe, setVibe] = useState(Object.keys(artworks)[0] || "RAGE");
  const [selectedArt, setSelectedArt] = useState(null);
  const [showMore, setShowMore] = useState(false);
  const [status, setStatus] = useState(beat.status);
  const [preview, setPreview] = useState(null);
  const [rendering, setRendering] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [privacy, setPrivacy] = useState("unlisted");
  const [cropBox, setCropBox] = useState({ x: 0.1, y: 0.1, size: 0.8 });
  const [showCrop, setShowCrop] = useState(false);

  // Live title preview
  const liveTitle = artist1 && artist2 && beatName
    ? `[FREE] ${artist1} x ${artist2} Type Beat - "${beatName}"`
    : `[FREE] _____ x _____ Type Beat - "_____"`;

  const isReady = artist1 && artist2 && beatName && selectedArt;

  const handleRender = async () => {
    if (!isReady) return;
    setRendering(true);
    setStatus("rendering");

    try {
      const res = await fetch(`${API}/render/mp4`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          beat_id: beat.id,
          artwork_path: `${vibe}/${selectedArt.filename}`,
          preset: vibe.toLowerCase(),
          beat_name: beatName,
          artist1, artist2,
          crop: { x: cropBox.x, y: cropBox.y, size: cropBox.size },
        }),
      });
      const data = await res.json();

      if (data.error) {
        alert(`Render failed: ${data.error}`);
        setStatus("render_failed");
      } else {
        setPreview(data);
        setStatus("rendered");
      }
    } catch (e) {
      alert(`Error: ${e.message}`);
      setStatus("error");
    }
    setRendering(false);
  };

  const handleUpload = async () => {
    if (!preview) return;
    setUploading(true);
    setStatus("uploading");

    try {
      // Generate SEO
      const seoRes = await fetch(`${API}/seo/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ artist1, artist2, beat_name: beatName, bpm, key: musicalKey, drop, vibe: vibe.toLowerCase() }),
      });
      const seo = await seoRes.json();

      // Trigger upload
      const uploadRes = await fetch(`${API}/upload/youtube`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          beat_id: beat.id,
          mp4_path: preview.mp4_path,
          thumbnail_path: preview.thumbnail_path,
          title: seo.title,
          description: seo.description,
          tags: seo.tags,
          category_id: "10",
          privacy_status: privacy,
        }),
      });
      const result = await uploadRes.json();

      if (result.success) {
        setStatus("done");
        if (onProcessed) onProcessed(beat.id);
      } else {
        alert(`Upload failed: ${result.error}`);
        setStatus("upload_failed");
      }
    } catch (e) {
      alert(`Upload error: ${e.message}`);
      setStatus("upload_failed");
    }
    setUploading(false);
  };

  // Reset to re-edit
  const handleReset = () => {
    setPreview(null);
    setStatus("pending");
  };

  const statusColors = {
    pending: "#6b6b80", configuring: "#3b82f6", rendering: "#ffd700",
    rendered: "#00ff88", uploading: "#ff69b4", done: "#00ff88",
    render_failed: "#ff4444", upload_failed: "#ff4444", error: "#ff4444",
  };

  return (
    <div className="rounded-2xl border p-6 mb-6 transition-all"
      style={{ background: "#111118", borderColor: "rgba(255,255,255,0.08)" }}>

      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <span className="text-2xl">ğŸµ</span>
          <div>
            <h3 className="font-bold text-lg" style={{ color: "#e8e8ef" }}>{beat.filename}</h3>
            <p className="text-xs font-mono" style={{ color: "#3a3a4a" }}>
              {beat.size_mb} MB Â· {beat.extension} Â· {new Date(beat.detected_at).toLocaleString()}
            </p>
          </div>
        </div>
        <span className="text-xs font-mono px-3 py-1 rounded-full uppercase tracking-wider"
          style={{ background: `${statusColors[status]}15`, color: statusColors[status] }}>
          {status}
        </span>
      </div>

      {/* Live Title Preview */}
      <div className="rounded-xl p-4 mb-5 font-mono text-sm text-center"
        style={{
          background: isReady ? "rgba(0,255,136,0.06)" : "rgba(255,255,255,0.03)",
          border: `1px dashed ${isReady ? "rgba(0,255,136,0.3)" : "rgba(255,255,255,0.08)"}`,
          color: isReady ? "#00ff88" : "#3a3a4a",
        }}>
        {liveTitle}
      </div>

      {/* Artist Selectors */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <ArtistSelector label="Artist 1" value={artist1} onSelect={setArtist1} allTiers={allTiers} />
        <ArtistSelector label="Artist 2" value={artist2} onSelect={setArtist2} allTiers={allTiers} />
      </div>

      {/* Beat Name */}
      <div className="mb-5">
        <label className="block text-xs uppercase tracking-widest text-gray-500 mb-1.5 font-mono">Beat Name</label>
        <input
          type="text"
          value={beatName}
          onChange={(e) => setBeatName(e.target.value)}
          placeholder='e.g. Night Vision'
          className="w-full px-4 py-3 rounded-xl border text-sm outline-none transition-all"
          style={{
            background: "rgba(255,255,255,0.03)",
            borderColor: beatName ? "rgba(0,255,136,0.2)" : "rgba(255,255,255,0.08)",
            color: "#e8e8ef",
          }}
        />
      </div>

      {/* Artwork Browser */}
      <div className="mb-5">
        <label className="block text-xs uppercase tracking-widest text-gray-500 mb-2 font-mono">Artwork</label>
        <ArtworkBrowser
          artworks={artworks}
          selectedVibe={vibe}
          onVibeChange={setVibe}
          selectedArt={selectedArt}
          onSelectArt={(art) => { setSelectedArt(art); setShowCrop(true); setCropBox({ x: 0.1, y: 0.1, size: 0.8 }); }}
        />
      </div>

      {/* 1:1 Crop Tool */}
      {selectedArt && showCrop && (
        <div className="mb-5">
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs uppercase tracking-widest text-gray-500 font-mono">Crop & Position (1:1)</label>
            <button
              onClick={() => setCropBox({ x: 0, y: 0, size: 1.0 })}
              className="text-xs font-mono px-3 py-1 rounded-lg cursor-pointer"
              style={{ background: "rgba(255,255,255,0.05)", color: "#6b6b80" }}
            >
              Reset
            </button>
          </div>
          <CropTool
            imageUrl={`${API}/artworks/image/${vibe}/${selectedArt.filename}`}
            cropBox={cropBox}
            onChange={setCropBox}
          />
          <div className="flex items-center gap-4 mt-2 text-xs font-mono" style={{ color: "#3a3a4a" }}>
            <span>X: {(cropBox.x * 100).toFixed(0)}%</span>
            <span>Y: {(cropBox.y * 100).toFixed(0)}%</span>
            <span>Size: {(cropBox.size * 100).toFixed(0)}%</span>
            <span style={{ color: "#39ff14" }}>â†’ 1080Ã-1080 â†’ 1920Ã-1080 (black bars)</span>
          </div>
        </div>
      )}

      {/* More Settings (Collapsible) */}
      <button
        onClick={() => setShowMore(!showMore)}
        className="w-full text-left px-4 py-2.5 rounded-xl mb-4 text-sm transition-all flex items-center justify-between cursor-pointer"
        style={{ background: "rgba(255,255,255,0.03)", color: "#6b6b80" }}
      >
        <span>âš™ï¸ Additional Settings (BPM, Key, Drop...)</span>
        <span style={{ transform: showMore ? "rotate(180deg)" : "rotate(0)", transition: "transform 0.2s" }}>â–¼</span>
      </button>

      {showMore && (
        <div className="grid grid-cols-3 gap-4 mb-5 p-4 rounded-xl"
          style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)" }}>
          <div>
            <label className="block text-xs uppercase tracking-widest text-gray-500 mb-1.5 font-mono">BPM</label>
            <input
              type="number" value={bpm} onChange={(e) => setBpm(parseInt(e.target.value) || 140)}
              min={60} max={220}
              className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none"
              style={{ background: "rgba(255,255,255,0.04)", borderColor: "rgba(255,255,255,0.08)", color: "#e8e8ef" }}
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-widest text-gray-500 mb-1.5 font-mono">Key</label>
            <select
              value={musicalKey} onChange={(e) => setMusicalKey(e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none"
              style={{ background: "rgba(255,255,255,0.04)", borderColor: "rgba(255,255,255,0.08)", color: "#e8e8ef" }}
            >
              {KEYS.map((k) => <option key={k} value={k}>{k}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs uppercase tracking-widest text-gray-500 mb-1.5 font-mono">Drop</label>
            <input
              type="text" value={drop} onChange={(e) => setDrop(e.target.value)}
              placeholder="0:25" pattern="[0-9]:[0-5][0-9]"
              className="w-full px-3 py-2.5 rounded-lg text-sm border outline-none"
              style={{ background: "rgba(255,255,255,0.04)", borderColor: "rgba(255,255,255,0.08)", color: "#e8e8ef" }}
            />
          </div>
        </div>
      )}

      {/* Rendered Preview */}
      {preview && (
        <div className="rounded-xl p-4 mb-5"
          style={{ background: "rgba(0,255,136,0.04)", border: "1px solid rgba(0,255,136,0.15)" }}>
          <h4 className="text-sm font-semibold mb-2" style={{ color: "#00ff88" }}>âœ… Render Complete</h4>
          <div className="text-xs font-mono space-y-1" style={{ color: "#6b6b80" }}>
            <p>MP4: {preview.render?.file_size_mb} MB Â· {preview.render?.encoding?.resolution} Â· {preview.render?.encoding?.audio_bitrate}</p>
            <p>Duration: {Math.round(preview.render?.duration || 0)}s</p>
          </div>
        </div>
      )}

      {/* Privacy Selector â€” Alien Themed */}
      {preview && (
        <div className="rounded-xl mb-5 overflow-hidden"
          style={{
            background: "linear-gradient(135deg, rgba(10,10,25,0.95), rgba(15,5,30,0.95))",
            border: "1px solid rgba(120,80,255,0.2)",
            boxShadow: "0 0 30px rgba(120,80,255,0.05), inset 0 0 60px rgba(120,80,255,0.03)",
          }}>
          {/* Header */}
          <div className="px-5 py-3 flex items-center gap-2"
            style={{ borderBottom: "1px solid rgba(120,80,255,0.1)" }}>
            <span style={{ fontSize: "14px", filter: "hue-rotate(220deg)" }}>ğŸ‘¾</span>
            <span className="text-xs font-mono uppercase tracking-widest" style={{ color: "rgba(120,80,255,0.7)" }}>
              Transmission Mode
            </span>
            <div className="flex-1" />
            <div className="flex gap-1">
              {[0,1,2].map(i => (
                <div key={i} className="w-1 h-1 rounded-full"
                  style={{
                    background: privacy === "public" ? "#00ff88" : "#7850ff",
                    animation: `pulse 1.5s ease-in-out ${i * 0.3}s infinite`,
                    opacity: 0.6,
                  }} />
              ))}
            </div>
          </div>

          {/* Options */}
          <div className="p-4 flex gap-3">
            {/* Public */}
            <button
              onClick={() => setPrivacy("public")}
              className="flex-1 p-4 rounded-xl transition-all cursor-pointer text-left"
              style={{
                background: privacy === "public"
                  ? "linear-gradient(135deg, rgba(0,255,136,0.12), rgba(0,200,100,0.06))"
                  : "rgba(255,255,255,0.02)",
                border: `1px solid ${privacy === "public" ? "rgba(0,255,136,0.35)" : "rgba(255,255,255,0.05)"}`,
                boxShadow: privacy === "public" ? "0 0 20px rgba(0,255,136,0.08)" : "none",
              }}
            >
              <div className="flex items-center gap-2 mb-2">
                <span style={{ fontSize: "18px" }}>ğŸ›¸</span>
                <span className="text-sm font-bold" style={{ color: privacy === "public" ? "#00ff88" : "#4a4a5a" }}>
                  PUBLIC
                </span>
              </div>
              <p className="text-xs" style={{ color: privacy === "public" ? "rgba(0,255,136,0.6)" : "#2a2a3a" }}>
                Full broadcast â€” visible to all earthlings. Algorithm engagement active.
              </p>
              {privacy === "public" && (
                <div className="mt-3 flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full" style={{ background: "#00ff88", boxShadow: "0 0 6px #00ff88" }} />
                  <span className="text-xs font-mono" style={{ color: "#00ff88" }}>SIGNAL: LIVE</span>
                </div>
              )}
            </button>

            {/* Unlisted */}
            <button
              onClick={() => setPrivacy("unlisted")}
              className="flex-1 p-4 rounded-xl transition-all cursor-pointer text-left"
              style={{
                background: privacy === "unlisted"
                  ? "linear-gradient(135deg, rgba(120,80,255,0.12), rgba(80,50,200,0.06))"
                  : "rgba(255,255,255,0.02)",
                border: `1px solid ${privacy === "unlisted" ? "rgba(120,80,255,0.35)" : "rgba(255,255,255,0.05)"}`,
                boxShadow: privacy === "unlisted" ? "0 0 20px rgba(120,80,255,0.08)" : "none",
              }}
            >
              <div className="flex items-center gap-2 mb-2">
                <span style={{ fontSize: "18px" }}>ğŸŒ‘</span>
                <span className="text-sm font-bold" style={{ color: privacy === "unlisted" ? "#7850ff" : "#4a4a5a" }}>
                  UNLISTED
                </span>
              </div>
              <p className="text-xs" style={{ color: privacy === "unlisted" ? "rgba(120,80,255,0.6)" : "#2a2a3a" }}>
                Stealth mode â€” only those with the link can access. Invisible to search.
              </p>
              {privacy === "unlisted" && (
                <div className="mt-3 flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full" style={{ background: "#7850ff", boxShadow: "0 0 6px #7850ff" }} />
                  <span className="text-xs font-mono" style={{ color: "#7850ff" }}>SIGNAL: CLOAKED</span>
                </div>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3">
        {!preview ? (
          <button
            onClick={handleRender}
            disabled={!isReady || rendering}
            className="flex-1 py-3.5 rounded-xl font-semibold text-sm transition-all cursor-pointer disabled:cursor-not-allowed disabled:opacity-30"
            style={{
              background: isReady ? "rgba(0,255,136,0.15)" : "rgba(255,255,255,0.04)",
              color: isReady ? "#00ff88" : "#3a3a4a",
              border: `1px solid ${isReady ? "rgba(0,255,136,0.3)" : "rgba(255,255,255,0.06)"}`,
            }}
          >
            {rendering ? "â³ Rendering..." : "ğŸ‘ï¸ Preview & Render"}
          </button>
        ) : (
          <>
            <button
              onClick={handleReset}
              className="px-5 py-3.5 rounded-xl text-sm transition-all cursor-pointer"
              style={{
                background: "rgba(255,255,255,0.04)",
                color: "#6b6b80",
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              â†© Edit
            </button>
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="flex-1 py-3.5 rounded-xl font-bold text-sm transition-all cursor-pointer disabled:cursor-not-allowed"
              style={{
                background: privacy === "public"
                  ? "linear-gradient(135deg, rgba(0,255,136,0.2), rgba(0,200,100,0.1))"
                  : "linear-gradient(135deg, rgba(120,80,255,0.2), rgba(80,50,200,0.1))",
                color: privacy === "public" ? "#00ff88" : "#7850ff",
                border: `1px solid ${privacy === "public" ? "rgba(0,255,136,0.3)" : "rgba(120,80,255,0.3)"}`,
              }}
            >
              {uploading ? "â³ Uploading..." : privacy === "public" ? "ğŸ›¸ Onayla & YayÄ±nla (Public)" : "ğŸŒ‘ Onayla & YÃ¼kle (Unlisted)"}
            </button>
          </>
        )}
      </div>
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

  // Load only artists, artworks, health on mount â€” NOT beats
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
      } catch (e) {
        console.error("Failed to fetch initial data:", e);
      }
      setLoading(false);
    }
    loadInitial();
  }, []);

  // Scan beats â€” ONLY when button is clicked
  const handleScan = async () => {
    setScanning(true);
    try {
      await fetch(`${API}/beats/scan`, { method: "POST" });
      const res = await fetch(`${API}/beats/pending`).then((r) => r.json());
      setBeats(res.beats || []);
      // Also refresh artworks in case new ones were added
      const artRes = await fetch(`${API}/artworks`).then((r) => r.json());
      setArtworks(artRes || {});
    } catch (e) {
      console.error("Scan failed:", e);
    }
    setScanning(false);
  };

  // Refresh after a beat is processed
  const handleProcessed = async () => {
    const res = await fetch(`${API}/beats/pending`).then((r) => r.json());
    setBeats(res.beats || []);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center"
        style={{ background: "#0a0a0f", color: "#6b6b80" }}>
        <div className="text-center">
          <div className="text-4xl mb-4">ğŸµ</div>
          <p className="font-mono text-sm">Loading JETBOX...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: "#0a0a0f", color: "#e8e8ef" }}>
      {/* Header */}
      <div className="border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
        <div className="max-w-4xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-black tracking-tight">
              JETBOX <span style={{ color: "#00ff88" }}>v3</span>
            </h1>
            <span className="text-xs font-mono px-2.5 py-1 rounded-full"
              style={{ background: "rgba(0,255,136,0.08)", color: "#00ff88" }}>
              ENNYTANG
            </span>
          </div>
          <div className="flex items-center gap-4">
            {health && (
              <span className="text-xs font-mono" style={{ color: health.ffmpeg?.available ? "#00ff88" : "#ff4444" }}>
                FFmpeg: {health.ffmpeg?.available ? "âœ“" : "âœ-"}
              </span>
            )}
            <button
              onClick={handleScan}
              disabled={scanning}
              className="px-4 py-2 rounded-lg text-xs font-mono transition-all cursor-pointer disabled:opacity-50"
              style={{ background: "rgba(0,255,136,0.1)", color: "#00ff88", border: "1px solid rgba(0,255,136,0.2)" }}
            >
              {scanning ? "â³ Scanning..." : "ğŸ”„ Scan BEATS/"}
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Status Bar */}
        <div className="flex items-center gap-6 mb-8 text-xs font-mono" style={{ color: "#3a3a4a" }}>
          <span>ğŸ“‚ Pending: <span style={{ color: "#ffd700" }}>{beats.length}</span></span>
          <span>ğŸ¤ Artists: <span style={{ color: "#6b6b80" }}>{Object.values(allTiers).flat().length}</span></span>
          <span>ğŸ¨ Artworks: <span style={{ color: "#6b6b80" }}>{Object.values(artworks).reduce((s, v) => s + (v.count || 0), 0)}</span></span>
          <span>ğŸ‘ï¸ Watcher: <span style={{ color: health?.watcher_running ? "#00ff88" : "#ff4444" }}>{health?.watcher_running ? "ON" : "OFF"}</span></span>
        </div>

        {/* Beat Cards */}
        {beats.length === 0 ? (
          <div className="rounded-2xl border p-12 text-center"
            style={{ background: "#111118", borderColor: "rgba(255,255,255,0.06)" }}>
            <div className="text-5xl mb-4">ğŸ“‚</div>
            <h2 className="text-lg font-semibold mb-2" style={{ color: "#6b6b80" }}>No beats waiting</h2>
            <p className="text-sm mb-6" style={{ color: "#3a3a4a" }}>
              Drop a WAV file into the BEATS/ folder, then click "Scan BEATS/" to load them.
            </p>
            <button
              onClick={handleScan}
              disabled={scanning}
              className="px-6 py-3 rounded-xl text-sm font-semibold transition-all cursor-pointer disabled:opacity-50"
              style={{ background: "rgba(0,255,136,0.1)", color: "#00ff88", border: "1px solid rgba(0,255,136,0.2)" }}
            >
              {scanning ? "â³ Scanning..." : "ğŸ”„ Scan for Beats"}
            </button>
          </div>
        ) : (
          beats.map((beat) => (
            <BeatCard
              key={beat.id}
              beat={beat}
              allTiers={allTiers}
              artworks={artworks}
              onProcessed={handleProcessed}
            />
          ))
        )}
      </div>
    </div>
  );
}

