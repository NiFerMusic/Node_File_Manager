from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from typing import Optional

from core.models import Edge, Node, Project


class ProjectStorage:
    def __init__(self, root_path: str):
        self._root = root_path
        self._vmtree = os.path.join(root_path, ".vmtree")
        self._previews = os.path.join(self._vmtree, "previews")
        self._project_file = os.path.join(self._vmtree, "project.json")
        self._nodes_file = os.path.join(self._vmtree, "nodes.json")
        self._edges_file = os.path.join(self._vmtree, "edges.json")

    # ---- init ----
    def init_project(self, project: Project) -> None:
        os.makedirs(self._vmtree, exist_ok=True)
        os.makedirs(self._previews, exist_ok=True)
        self._write_json(self._project_file, project.to_dict())
        self._write_json(self._nodes_file, [])
        self._write_json(self._edges_file, [])

    # ---- project ----
    def load_project(self) -> Optional[Project]:
        if not os.path.isfile(self._project_file):
            return None
        data = self._read_json(self._project_file)
        return Project.from_dict(data) if data else None

    def save_project(self, project: Project) -> None:
        self._write_json(self._project_file, project.to_dict())

    # ---- nodes ----
    def load_nodes(self) -> list[Node]:
        data = self._read_json(self._nodes_file)
        return [Node.from_dict(d) for d in data] if data else []

    def save_nodes(self, nodes: list[Node]) -> None:
        self._write_json(self._nodes_file, [n.to_dict() for n in nodes])

    def add_node(self, node: Node) -> None:
        nodes = self.load_nodes()
        nodes.append(node)
        self.save_nodes(nodes)

    def update_node(self, updated: Node) -> None:
        nodes = self.load_nodes()
        for i, n in enumerate(nodes):
            if n.id == updated.id:
                nodes[i] = updated
                break
        self.save_nodes(nodes)

    def remove_node(self, node_id: str) -> None:
        nodes = self.load_nodes()
        nodes = [n for n in nodes if n.id != node_id]
        self.save_nodes(nodes)
        edges = self.load_edges()
        edges = [e for e in edges if e.source_id != node_id and e.target_id != node_id]
        self.save_edges(edges)
        preview_dir = os.path.join(self._previews, node_id)
        if os.path.isdir(preview_dir):
            shutil.rmtree(preview_dir)

    def get_node(self, node_id: str) -> Optional[Node]:
        nodes = self.load_nodes()
        for n in nodes:
            if n.id == node_id:
                return n
        return None

    # ---- edges ----
    def load_edges(self) -> list[Edge]:
        data = self._read_json(self._edges_file)
        return [Edge.from_dict(d) for d in data] if data else []

    def save_edges(self, edges: list[Edge]) -> None:
        self._write_json(self._edges_file, [e.to_dict() for e in edges])

    def add_edge(self, edge: Edge) -> None:
        edges = self.load_edges()
        if not any(e.source_id == edge.source_id and e.target_id == edge.target_id for e in edges):
            edges.append(edge)
        self.save_edges(edges)

    def remove_edge(self, edge: Edge) -> None:
        edges = self.load_edges()
        edges = [e for e in edges if not (e.source_id == edge.source_id and e.target_id == edge.target_id)]
        self.save_edges(edges)

    # ---- previews ----
    def import_preview(self, node_id: str, source_path: str) -> str:
        dest_dir = os.path.join(self._previews, node_id)
        os.makedirs(dest_dir, exist_ok=True)
        ext = os.path.splitext(source_path)[1]
        dest_name = f"preview{ext}"
        dest_path = os.path.join(dest_dir, dest_name)
        shutil.copy2(source_path, dest_path)
        return dest_path

    def get_preview_path(self, node_id: str) -> str:
        for ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".mp4", ".mov", ".avi"):
            p = os.path.join(self._previews, node_id, f"preview{ext}")
            if os.path.isfile(p):
                return p
        return ""

    def remove_preview(self, node_id: str) -> None:
        dest_dir = os.path.join(self._previews, node_id)
        if os.path.isdir(dest_dir):
            shutil.rmtree(dest_dir)

    # ---- helpers ----
    def _read_json(self, path: str) -> Optional[list | dict]:
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_json(self, path: str, data: list | dict) -> None:
        dirpath = os.path.dirname(path)
        os.makedirs(dirpath, exist_ok=True)
        tmp = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json", dir=dirpath, delete=False)
        try:
            json.dump(data, tmp, indent=2, ensure_ascii=False)
            tmp.close()
            os.replace(tmp.name, path)
        except Exception:
            os.unlink(tmp.name)
            raise

    @property
    def root_path(self) -> str:
        return self._root
