from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI


def application_lifespan(task_queue):
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        task_queue.start()
        try:
            yield
        finally:
            task_queue.shutdown()

    return lifespan
