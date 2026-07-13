"""Excepciones de dominio compartidas entre capas."""


class DomainError(Exception):
    """Error de regla de negocio o integridad a nivel dominio."""


class NotFoundError(Exception):
    """El recurso solicitado no existe."""


class ConflictError(Exception):
    """Conflicto de estado (p. ej. email ya registrado)."""
