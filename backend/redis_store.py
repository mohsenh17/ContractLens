import json
import redis

# Single connection pool shared across the process
_redis = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

JOB_TTL = 60 * 60 * 24  # keep job state for 24 hours


def set_job(job_id: str, data: dict) -> None:
    """Persist job state to Redis."""
    _redis.set(f"job:{job_id}", json.dumps(data), ex=JOB_TTL)


def get_job(job_id: str) -> dict | None:
    """Retrieve job state from Redis. Returns None if not found."""
    raw = _redis.get(f"job:{job_id}")
    if raw is None:
        return None
    return json.loads(raw)