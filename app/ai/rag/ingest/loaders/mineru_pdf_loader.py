"""
基于 MinerU 结构化结果的 PDF 加载器
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys

from app.ai.rag.ingest.base import BaseDocumentLoader
from app.ai.rag.ingest.models import IngestedAsset, IngestedDocument
from app.core.config import settings
from app.utils.logger import app_logger


class MinerUPdfLoader(BaseDocumentLoader):
    """将 MinerU 的结构化输出映射为统一摄取文档"""

    supported_extensions = {".pdf"}

    def __init__(self, asset_root: Path | None = None, parser=None):
        self.asset_root = Path(asset_root) if asset_root is not None else Path("data/knowledge_assets")
        self.parser = parser or self._default_parser

    async def load(self, path: Path) -> list[IngestedDocument]:
        parsed = self.parser(path)
        job_id = parsed.get("job_id", "job")
        content_list = parsed.get("content_list", [])

        assets = self._extract_assets(path, job_id, content_list)
        documents: list[IngestedDocument] = []

        for index, item in enumerate(content_list):
            if item.get("type") not in {"text", "table", "equation"}:
                continue

            content = self._extract_text_content(item)
            if not content:
                continue

            related_assets = self._resolve_related_assets(index, item, content_list, assets)
            documents.append(
                IngestedDocument(
                    source_path=str(path),
                    file_name=path.name,
                    file_type="pdf",
                    content=content,
                    loader_name="mineru",
                    page_start=item.get("page_idx"),
                    page_end=item.get("page_idx"),
                    metadata={
                        "page_idx": item.get("page_idx"),
                        "related_asset_keys": [asset.asset_key for asset in related_assets],
                    },
                    assets=related_assets,
                )
            )

        return documents

    def _extract_assets(self, path: Path, job_id: str, content_list: list[dict]) -> list[IngestedAsset]:
        assets: list[IngestedAsset] = []
        relative_root = Path(path.stem) / job_id
        target_root = self.asset_root / relative_root
        target_root.mkdir(parents=True, exist_ok=True)

        image_index = 0
        for item in content_list:
            if item.get("type") != "image":
                continue

            source_image_path = Path(item["img_path"])
            target_path = target_root / source_image_path.name
            shutil.copy2(source_image_path, target_path)

            caption = self._extract_caption(item)
            assets.append(
                IngestedAsset(
                    asset_key=f"image-{image_index}",
                    asset_type="image",
                    page_idx=item.get("page_idx"),
                    asset_path=str((relative_root / source_image_path.name).as_posix()),
                    caption=caption,
                    metadata={"bbox": item.get("bbox")},
                )
            )
            image_index += 1

        return assets

    def _resolve_related_assets(
        self,
        index: int,
        item: dict,
        content_list: list[dict],
        assets: list[IngestedAsset],
    ) -> list[IngestedAsset]:
        page_idx = item.get("page_idx")
        adjacent_pages: list[int] = []

        for neighbor_index in (index - 1, index + 1):
            if 0 <= neighbor_index < len(content_list):
                neighbor = content_list[neighbor_index]
                if neighbor.get("type") == "image" and neighbor.get("page_idx") == page_idx:
                    adjacent_pages.append(neighbor_index)

        if adjacent_pages:
            same_page_assets = [asset for asset in assets if asset.page_idx == page_idx]
            return same_page_assets

        return [asset for asset in assets if asset.page_idx == page_idx]

    @staticmethod
    def _extract_caption(item: dict) -> str | None:
        raw_caption = item.get("image_caption")
        if isinstance(raw_caption, list):
            parts = [part.get("text", "").strip() for part in raw_caption if isinstance(part, dict)]
            caption = "".join(part for part in parts if part)
            return caption or None
        if isinstance(raw_caption, str):
            return raw_caption.strip() or None
        return None

    @staticmethod
    def _extract_text_content(item: dict) -> str:
        if isinstance(item.get("text"), str):
            return item["text"].strip()
        if isinstance(item.get("latex"), str):
            return item["latex"].strip()
        if isinstance(item.get("html"), str):
            return item["html"].strip()
        return ""

    def _default_parser(self, path: Path) -> dict:
        output_dir = Path("data/mineru_output") / path.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        return self._run_mineru_cli(path, output_dir)

    def _run_mineru_cli(self, path: Path, output_dir: Path) -> dict:
        backend = settings.MINERU_BACKEND.strip()
        server_url = (settings.MINERU_SERVER_URL or "").strip()

        if backend not in {"vlm-http-client", "hybrid-http-client"}:
            raise RuntimeError(f"Unsupported MinerU backend for remote mode: {backend}")
        if not server_url:
            raise RuntimeError("MINERU_SERVER_URL is not configured for remote PDF parsing")

        command = self._resolve_mineru_command() + [
            "-p",
            str(path),
            "-o",
            str(output_dir),
            "-b",
            backend,
            "-u",
            server_url,
        ]

        app_logger.info(f"开始使用 MinerU 远端解析 PDF: {path.name}")
        app_logger.info(f"MinerU backend: {backend}")
        app_logger.info(f"MinerU server: {server_url}")

        subprocess.run(
            command,
            check=True,
        )

        candidates = sorted(output_dir.rglob("*content_list.json"))
        if not candidates:
            raise RuntimeError(f"MinerU output content_list.json not found under: {output_dir}")

        with candidates[0].open("r", encoding="utf-8") as file:
            parsed = json.load(file)

        parsed.setdefault("job_id", output_dir.name)
        return parsed

    @staticmethod
    def _resolve_mineru_command() -> list[str]:
        executable = Path(sys.executable).resolve()
        scripts_dir = executable.parent
        for name in ("mineru.exe", "mineru"):
            candidate = scripts_dir / name
            if candidate.exists():
                return [str(candidate)]
        return ["mineru"]
