"""Intermediate representation for finite, section-aware model contexts."""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PackSection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    text_ref: str = Field(min_length=1)
    priority: int = Field(ge=1)
    min_tokens: int = Field(ge=0)
    max_tokens: int = Field(gt=0)
    droppable: bool
    compressible: bool
    cache_group: str = Field(min_length=1)
    provenance_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _bounds(self):
        if self.min_tokens > self.max_tokens:
            raise ValueError("min_tokens cannot exceed max_tokens")
        return self


class PackIR(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    profile: str = Field(min_length=1)
    template_role: str = Field(min_length=1)
    target_tokens: int = Field(gt=0)
    sections: tuple[PackSection, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_sections(self):
        ids = [section.id for section in self.sections]
        if len(ids) != len(set(ids)):
            raise ValueError("pack section ids must be unique")
        return self
