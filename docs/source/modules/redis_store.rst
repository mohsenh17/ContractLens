Redis Store Module
==================

`redis_store.py` provides simple job state persistence in Redis.

Functions
---------

- **set_job(job_id, data)** → Save job dict to Redis
- **get_job(job_id)** → Retrieve job dict, returns None if missing