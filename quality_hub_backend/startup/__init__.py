"""Application startup and shutdown hooks."""

from .lifespan import application_lifespan

__all__ = ["application_lifespan"]
