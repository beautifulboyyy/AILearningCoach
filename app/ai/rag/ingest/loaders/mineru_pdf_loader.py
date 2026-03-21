"""
基于 MinerU 结构化结果的 PDF 加载器
"""
from pathlib import Path
import shutil
from types import SimpleNamespace

from app.ai.rag.ingest.base import BaseDocumentLoader
from app.ai.rag.ingest.models import IngestedAsset, IngestedDocument
from app.core.config import settings
from app.utils.logger import app_logger


class MinerUPdfLoader(BaseDocumentLoader):
    """将 MinerU 的结构化输出映射为统一摄取文档"""

    supported_extensions = {".pdf"}

    def __init__(self, asset_root: Path | None = None, parser=None, client_factory=None):
        self.asset_root = Path(asset_root) if asset_root is not None else Path("data/knowledge_assets")
        self.parser = parser or self._default_parser
        self.client_factory = client_factory or self._create_client

    async def load(self, path: Path) -> list[IngestedDocument]:
        parsed = self.parser(path)
        job_id = parsed.get("job_id", "job")
        content_list = parsed.get("content_list", [])
        images = parsed.get("images", [])
        images_by_path = {
            str(Path(getattr(image, "path", "")).as_posix()): image
            for image in images
        }
        images_by_path.update(
            {
                getattr(image, "name", ""): image
                for image in images
                if getattr(image, "name", "")
            }
        )

        assets = self._extract_assets(path, job_id, content_list, images_by_path)
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

    def _extract_assets(self, path: Path, job_id: str, content_list: list[dict], images_by_path: dict[str, object]) -> list[IngestedAsset]:
        assets: list[IngestedAsset] = []
        relative_root = Path(path.stem) / job_id
        target_root = self.asset_root / relative_root
        target_root.mkdir(parents=True, exist_ok=True)

        image_index = 0
        for item in content_list:
            if item.get("type") != "image":
                continue

            source_image_path = Path(item["img_path"])
            image_key = str(Path(item["img_path"]).as_posix())
            image = images_by_path.get(image_key) or images_by_path.get(source_image_path.name)
            if image is None:
                continue

            target_path = target_root / source_image_path.name
            target_path.write_bytes(image.data)

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
        return self._extract_with_sdk(path)

    def _extract_with_sdk(self, path: Path) -> dict:
        mode = (settings.MINERU_API_MODE or "precision").strip().lower()
        token = (settings.MINERU_TOKEN or "").strip() or None
        client = self.client_factory(token)

        app_logger.info(f"开始使用 MinerU Open API 解析 PDF: {path.name}")
        app_logger.info(f"MinerU API mode: {mode}")

        if mode == "precision":
            if not token:
                app_logger.warning("未配置 MINERU_TOKEN，MinerU precision 模式不可用，已降级为 flash 模式。")
                mode = "flash"
            else:
                result = client.extract(
                    str(path),
                    language="ch",
                    timeout=settings.MINERU_TIMEOUT,
                    ocr=False,
                    formula=True,
                    table=True,
                )
                return self._normalize_result(path, result, mode)

        if mode == "flash":
            result = client.flash_extract(
                str(path),
                language="ch",
                timeout=settings.MINERU_TIMEOUT,
            )
            return self._normalize_result(path, result, mode)

        raise RuntimeError(f"Unsupported MinerU API mode: {mode}")

    @staticmethod
    def _create_client(token: str | None):
        try:
            from mineru import MinerU
        except ImportError as exc:
            raise ImportError(
                "mineru-open-sdk is required for PDF parsing. Install with: pip install mineru-open-sdk"
            ) from exc
        return MinerU(token=token)

    @staticmethod
    def _normalize_result(path: Path, result: object, mode: str) -> dict:
        state = getattr(result, "state", None)
        if state != "done":
            error = getattr(result, "error", None)
            raise RuntimeError(f"MinerU extraction failed for {path.name}: state={state}, error={error}")

        content_list = getattr(result, "content_list", None) or []
        images = getattr(result, "images", None) or []
        markdown = getattr(result, "markdown", None) or ""

        if not content_list and markdown:
            content_list = [
                {
                    "type": "text",
                    "page_idx": 1,
                    "text": markdown,
                }
            ]

        return {
            "job_id": getattr(result, "task_id", None) or path.stem,
            "content_list": content_list,
            "images": images,
            "mode": mode,
        }
