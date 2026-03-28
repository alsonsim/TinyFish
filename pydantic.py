"""Minimal local subset of Pydantic used by this project."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Any, get_args, get_origin, Literal


@dataclass
class FieldInfo:
    default: Any = ...
    default_factory: Any = None
    description: str | None = None
    ge: float | None = None
    le: float | None = None
    annotation: Any = Any


def Field(
    default: Any = ...,
    *,
    default_factory: Any = None,
    description: str | None = None,
    ge: float | None = None,
    le: float | None = None,
) -> FieldInfo:
    return FieldInfo(
        default=default,
        default_factory=default_factory,
        description=description,
        ge=ge,
        le=le,
    )


class BaseModel:
    """Lightweight drop-in replacement for the fields used in this repo."""

    model_fields: dict[str, FieldInfo] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        inherited: dict[str, FieldInfo] = {}
        for base in reversed(cls.__mro__[1:]):
            inherited.update(getattr(base, "model_fields", {}))

        annotations: dict[str, Any] = {}
        for base in reversed(cls.__mro__[:-1]):
            annotations.update(getattr(base, "__annotations__", {}))

        model_fields: dict[str, FieldInfo] = dict(inherited)
        for name, annotation in annotations.items():
            if name == "model_fields" or name.startswith("_"):
                continue
            default = getattr(cls, name, ...)
            if isinstance(default, FieldInfo):
                field_info = FieldInfo(
                    default=default.default,
                    default_factory=default.default_factory,
                    description=default.description,
                    ge=default.ge,
                    le=default.le,
                    annotation=annotation,
                )
            else:
                field_info = FieldInfo(default=default, annotation=annotation)
            model_fields[name] = field_info
        cls.model_fields = model_fields

    def __init__(self, **data: Any) -> None:
        for name, field_info in self.model_fields.items():
            if name in data:
                value = data[name]
            elif field_info.default_factory is not None:
                value = field_info.default_factory()
            elif field_info.default is not ...:
                value = deepcopy(field_info.default)
            else:
                raise TypeError(f"Missing required field: {name}")

            self._validate_literal(name, field_info.annotation, value)
            self._validate_range(name, field_info, value)
            setattr(self, name, value)

    def model_dump(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for name in self.model_fields:
            value = getattr(self, name)
            if isinstance(value, BaseModel):
                payload[name] = value.model_dump()
            elif isinstance(value, list):
                payload[name] = [
                    item.model_dump() if isinstance(item, BaseModel) else item
                    for item in value
                ]
            elif isinstance(value, datetime):
                payload[name] = value.isoformat()
            else:
                payload[name] = value
        return payload

    def model_dump_json(self, indent: int | None = None) -> str:
        return json.dumps(self.model_dump(), indent=indent, default=str)

    def _validate_literal(self, name: str, annotation: Any, value: Any) -> None:
        if get_origin(annotation) is Literal:
            allowed = get_args(annotation)
            if value not in allowed:
                raise ValueError(f"{name} must be one of {allowed}, got {value!r}")

    def _validate_range(self, name: str, field_info: FieldInfo, value: Any) -> None:
        if not isinstance(value, (int, float)):
            return
        if field_info.ge is not None and value < field_info.ge:
            raise ValueError(f"{name} must be >= {field_info.ge}")
        if field_info.le is not None and value > field_info.le:
            raise ValueError(f"{name} must be <= {field_info.le}")
