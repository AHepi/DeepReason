"""Shared immutable building blocks for append-only canonical records."""

from pydantic import BaseModel, ConfigDict


class FrozenRecord(BaseModel):
    """A record whose fields cannot be reassigned after validation."""

    model_config = ConfigDict(frozen=True)


class FrozenDict(dict):
    """JSON-serializable mapping that rejects every mutating operation."""

    @staticmethod
    def _immutable(*_args, **_kwargs):
        raise TypeError("ontology mappings are immutable")

    __setitem__ = _immutable
    __delitem__ = _immutable
    __ior__ = _immutable
    clear = _immutable
    pop = _immutable
    popitem = _immutable
    setdefault = _immutable
    update = _immutable

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self


class FrozenList(list):
    """List-compatible JSON sequence with mutation disabled."""

    @staticmethod
    def _immutable(*_args, **_kwargs):
        raise TypeError("ontology sequences are immutable")

    __setitem__ = _immutable
    __delitem__ = _immutable
    __iadd__ = _immutable
    __imul__ = _immutable
    append = _immutable
    clear = _immutable
    extend = _immutable
    insert = _immutable
    pop = _immutable
    remove = _immutable
    reverse = _immutable
    sort = _immutable

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self
