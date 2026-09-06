"""
JETBOX — Arka plan iş kuyruğu (render / upload / auth)

Uzun süren işler HTTP request'ini bloklamasın diye thread'de çalışır.
Frontend `/api/jobs/<id>` ile gerçek ilerlemeyi (0-100) ve sonucu okur.
"""

import threading
import time
import traceback
import uuid


class JobManager:
    MAX_KEPT = 200  # bellekte tutulan iş sayısı

    def __init__(self):
        self._jobs = {}
        self._lock = threading.Lock()

    # ── oluşturma ──────────────────────────────────────────
    def create(self, kind: str, fn, *args, **kwargs) -> dict:
        """
        fn(progress, *args, **kwargs) çağrılır.
        progress(percent:int, message:str|None) ile ilerleme bildirilir.
        fn dict döner; {"success": False} veya {"error": ...} → failed.
        """
        job_id = uuid.uuid4().hex[:12]
        job = {
            "id": job_id, "kind": kind, "status": "queued",
            "progress": 0, "message": "", "result": None, "error": None,
            "created_at": time.time(), "updated_at": time.time(),
        }
        with self._lock:
            self._jobs[job_id] = job
            self._trim()

        def progress(pct, message=None):
            fields = {"progress": max(0, min(100, int(pct)))}
            if message is not None:
                fields["message"] = str(message)
            self.update(job_id, **fields)

        def runner():
            self.update(job_id, status="running")
            try:
                res = fn(progress, *args, **kwargs)
                failed = isinstance(res, dict) and (res.get("success") is False or res.get("error"))
                if failed:
                    self.update(job_id, status="failed", result=res,
                                error=str(res.get("error") or "İş başarısız"))
                else:
                    self.update(job_id, status="done", progress=100, result=res)
            except Exception as e:  # noqa
                self.update(job_id, status="failed", error=str(e),
                            result={"traceback": traceback.format_exc()[-1500:]})

        threading.Thread(target=runner, daemon=True, name=f"job-{kind}-{job_id}").start()
        return dict(job)

    # ── güncelleme / okuma ────────────────────────────────
    def update(self, job_id: str, **fields):
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            job.update(fields)
            job["updated_at"] = time.time()
            return dict(job)

    def get(self, job_id: str):
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def list(self, limit: int = 50, kind: str = None) -> list:
        with self._lock:
            items = [dict(j) for j in self._jobs.values() if not kind or j["kind"] == kind]
        items.sort(key=lambda j: j["created_at"], reverse=True)
        return items[:limit]

    def _trim(self):
        if len(self._jobs) <= self.MAX_KEPT:
            return
        finished = [j for j in self._jobs.values() if j["status"] in ("done", "failed")]
        finished.sort(key=lambda j: j["updated_at"])
        for j in finished[: len(self._jobs) - self.MAX_KEPT]:
            self._jobs.pop(j["id"], None)
