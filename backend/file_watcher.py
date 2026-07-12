"""
JETBOX v3 â€” File Watcher
Monitors BEATS/ folder for new WAV drops.
Notifies Flask backend via internal queue.
"""

import os
import time
import threading
import json
from datetime import datetime
from collections import deque


class BeatWatcher:
    """
    Watches a directory for new audio files.
    Uses polling (cross-platform compatible, no watchdog dependency needed).
    """
    
    VALID_EXTENSIONS = {'.wav', '.mp3', '.flac'}
    
    def __init__(self, beats_dir: str, poll_interval: float = 2.0):
        self.beats_dir = os.path.abspath(beats_dir)
        self.poll_interval = poll_interval
        self._known_files = set()
        self._pending_beats = deque()  # New beats waiting for dashboard processing
        self._processed_beats = []     # Completed beats
        self._running = False
        self._thread = None
        
        # Initialize known files
        self._scan_existing()
    
    def _scan_existing(self):
        """Scan directory for existing files (don't treat as new)."""
        if os.path.exists(self.beats_dir):
            for fname in os.listdir(self.beats_dir):
                ext = os.path.splitext(fname)[1].lower()
                if ext in self.VALID_EXTENSIONS:
                    self._known_files.add(fname)
    
    def _check_for_new(self):
        """Check for new files in BEATS/ directory."""
        if not os.path.exists(self.beats_dir):
            return
        
        current_files = set()
        for fname in os.listdir(self.beats_dir):
            ext = os.path.splitext(fname)[1].lower()
            if ext in self.VALID_EXTENSIONS:
                current_files.add(fname)
        
        new_files = current_files - self._known_files
        
        for fname in sorted(new_files):
            fpath = os.path.join(self.beats_dir, fname)
            
            # Wait briefly for file to finish writing
            try:
                size1 = os.path.getsize(fpath)
                time.sleep(0.5)
                size2 = os.path.getsize(fpath)
                if size1 != size2:
                    continue  # Still writing, check next cycle
            except OSError:
                continue
            
            beat_info = {
                "id": f"beat_{int(time.time() * 1000)}",
                "filename": fname,
                "filepath": fpath,
                "extension": os.path.splitext(fname)[1].lower(),
                "size_mb": round(os.path.getsize(fpath) / (1024 * 1024), 2),
                "detected_at": datetime.now().isoformat(),
                "status": "pending",  # pending → configuring → rendering → uploading → done
            }
            
            self._pending_beats.append(beat_info)
            self._known_files.add(fname)
            
            print(f"[NEW BEAT] {fname} ({beat_info['size_mb']} MB)")
    
    def _poll_loop(self):
        """Background polling loop."""
        while self._running:
            try:
                self._check_for_new()
            except Exception as e:
                print(f"Watcher error: {e}")
            time.sleep(self.poll_interval)
    
    def start(self):
        """Start watching in background thread."""
        if self._running:
            return
        
        os.makedirs(self.beats_dir, exist_ok=True)
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        print(f"[WATCHER] Watching: {self.beats_dir}")
    
    def stop(self):
        """Stop watching."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[WATCHER] Stopped")
    
    def get_pending(self) -> list:
        """Get list of pending beats (not yet processed)."""
        return list(self._pending_beats)
    
    def get_beat_by_id(self, beat_id: str) -> dict:
        """Find a beat by its ID."""
        for beat in self._pending_beats:
            if beat["id"] == beat_id:
                return beat
        for beat in self._processed_beats:
            if beat["id"] == beat_id:
                return beat
        return None
    
    def mark_processed(self, beat_id: str, result: dict = None):
        """Move a beat from pending to processed."""
        for i, beat in enumerate(self._pending_beats):
            if beat["id"] == beat_id:
                beat["status"] = "done"
                beat["processed_at"] = datetime.now().isoformat()
                if result:
                    beat["result"] = result
                self._processed_beats.append(beat)
                del self._pending_beats[i]
                return True
        return False
    
    def update_status(self, beat_id: str, status: str):
        """Update beat status (configuring, rendering, uploading, done)."""
        for beat in self._pending_beats:
            if beat["id"] == beat_id:
                beat["status"] = status
                return True
        return False
    
    def get_all_beats(self) -> dict:
        """Get all beats organized by status."""
        return {
            "pending": list(self._pending_beats),
            "processed": self._processed_beats,
            "watching": self.beats_dir,
            "known_files": len(self._known_files),
            "is_running": self._running
        }
    
    def add_existing_as_pending(self):
        """Add all existing files as pending (for fresh start).

        Also refreshes size_mb for any file already in the pending queue
        whose on-disk size has changed since it was first detected (e.g.
        the file was re-exported/overwritten after the previous scan).
        """
        if not os.path.exists(self.beats_dir):
            return 0

        # --- Refresh size_mb for beats already in pending queue ---
        # This fixes the stale-cache problem: if a file was re-exported with a
        # different size, the in-memory record gets updated on every scan call.
        pending_map = {b["filename"]: b for b in self._pending_beats}
        for fname, beat in pending_map.items():
            fpath = os.path.join(self.beats_dir, fname)
            if os.path.exists(fpath):
                current_size = round(os.path.getsize(fpath) / (1024 * 1024), 2)
                if beat["size_mb"] != current_size:
                    print(f"[WATCHER] Size updated for {fname}: {beat['size_mb']} MB -> {current_size} MB")
                    beat["size_mb"] = current_size

        # Build existing set ONCE before the loop – filenames already in pending or processed
        existing_fnames = {b["filename"] for b in self._pending_beats}
        existing_fnames.update(b["filename"] for b in self._processed_beats)

        count = 0
        for fname in sorted(os.listdir(self.beats_dir)):
            ext = os.path.splitext(fname)[1].lower()
            if ext not in self.VALID_EXTENSIONS:
                continue
            
            fpath = os.path.join(self.beats_dir, fname)
            
            if fname not in existing_fnames:
                beat_info = {
                    "id": f"beat_{int(time.time() * 1000)}_{count}",
                    "filename": fname,
                    "filepath": fpath,
                    "extension": ext,
                    "size_mb": round(os.path.getsize(fpath) / (1024 * 1024), 2),
                    "detected_at": datetime.now().isoformat(),
                    "status": "pending",
                }
                self._pending_beats.append(beat_info)
                self._known_files.add(fname)  # Also mark as known so watcher doesn't re-detect
                existing_fnames.add(fname)  # Prevent duplicates within this loop
                count += 1
                time.sleep(0.002)  # Windows time.time() has ~15ms resolution; ensure unique ms timestamps
        
        return count
