from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Project:
    name: str
    root_path: str
    allowed_extensions: list[str] = field(default_factory=list)
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "root_path": self.root_path,
            "allowed_extensions": self.allowed_extensions,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Project:
        return cls(
            name=d["name"],
            root_path=d["root_path"],
            allowed_extensions=d.get("allowed_extensions", []),
            created_at=d.get("created_at", 0.0),
        )


@dataclass
class Node:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str = ""
    filename: str = ""
    last_modified: float = 0.0
    description: str = ""
    preview_path: str = ""
    created_at: float = 0.0
    node_type: str = "file"

    @property
    def full_path(self) -> str:
        return self.file_path

    @property
    def ext(self) -> str:
        return os.path.splitext(self.filename)[1].lower()

    @property
    def file_exists(self) -> bool:
        return os.path.isfile(self.file_path)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "file_path": self.file_path,
            "filename": self.filename,
            "last_modified": self.last_modified,
            "description": self.description,
            "preview_path": self.preview_path,
            "created_at": self.created_at,
            "node_type": self.node_type,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Node:
        return cls(
            id=d["id"],
            file_path=os.path.normpath(d.get("file_path", "")),
            filename=d.get("filename", ""),
            last_modified=d.get("last_modified", 0.0),
            description=d.get("description", ""),
            preview_path=d.get("preview_path", ""),
            created_at=d.get("created_at", 0.0),
            node_type=d.get("node_type", "file"),
        )

    @classmethod
    def from_file(cls, file_path: str) -> Node:
        fp = os.path.normpath(file_path)
        stat = os.stat(fp)
        return cls(
            file_path=fp,
            filename=os.path.basename(fp),
            last_modified=stat.st_mtime,
            created_at=stat.st_ctime,
        )


@dataclass
class Edge:
    source_id: str
    target_id: str

    def to_dict(self) -> dict:
        return {"source_id": self.source_id, "target_id": self.target_id}

    @classmethod
    def from_dict(cls, d: dict) -> Edge:
        return cls(source_id=d["source_id"], target_id=d["target_id"])
