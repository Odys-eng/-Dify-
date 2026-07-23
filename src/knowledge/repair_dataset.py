"""Repair and synchronize the manufacturing Dify dataset without duplicate names."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import requests


TERMINAL_STATUSES = {"completed", "error", "paused"}


class DifyClient:
    def __init__(self, base_url: str, dataset_id: str, api_key: str) -> None:
        self.dataset_url = f"{base_url.rstrip('/')}/datasets/{dataset_id}"
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})
        # 走 Nginx https://localhost/v1 时为自签证书，跳过校验（仅本地部署场景）
        if base_url.lower().startswith("https"):
            self.session.verify = False
            requests.packages.urllib3.disable_warnings(
                requests.packages.urllib3.exceptions.InsecureRequestWarning
            )

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                response = self.session.request(method, url, **kwargs)
                return response
            except requests.RequestException as error:
                last_error = error
                print(f"  API request failed ({attempt}/3): {error}", flush=True)
                time.sleep(attempt * 3)
        raise RuntimeError(f"Dify API unavailable: {last_error}")

    def list_documents(self) -> list[dict]:
        documents: list[dict] = []
        page = 1
        while True:
            response = self.request(
                "GET",
                f"{self.dataset_url}/documents",
                params={"page": page, "limit": 100},
                timeout=60,
            )
            response.raise_for_status()
            payload = response.json()
            documents.extend(payload.get("data", []))
            if not payload.get("has_more"):
                return documents
            page += 1

    def get_document(self, document_id: str) -> dict:
        response = self.request(
            "GET", f"{self.dataset_url}/documents/{document_id}", timeout=60
        )
        response.raise_for_status()
        return response.json()

    def delete_document(self, document_id: str) -> None:
        response = self.request(
            "DELETE", f"{self.dataset_url}/documents/{document_id}", timeout=60
        )
        # A timed-out DELETE may still succeed server-side; a retry then returns 404.
        if response.status_code not in {204, 404}:
            raise RuntimeError(
                f"Delete failed for {document_id}: {response.status_code} {response.text[:300]}"
            )

    def create_document(self, path: Path, upload_name: str) -> str:
        config = {
            "indexing_technique": "high_quality",
            "process_rule": {"mode": "automatic"},
        }
        mime = {
            ".md": "text/markdown",
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }.get(path.suffix.lower(), "application/octet-stream")
        with path.open("rb") as file:
            response = self.request(
                "POST",
                f"{self.dataset_url}/document/create-by-file",
                files={"file": (upload_name, file, mime)},
                data={"data": json.dumps(config, ensure_ascii=False)},
                timeout=300,
            )
        if response.status_code != 200:
            raise RuntimeError(
                f"Upload failed for {upload_name}: {response.status_code} {response.text[:500]}"
            )
        return response.json()["document"]["id"]

    def wait_for_terminal(self, document_ids: list[str], timeout: int) -> dict[str, dict]:
        deadline = time.monotonic() + timeout
        latest: dict[str, dict] = {}
        wanted = set(document_ids)
        while time.monotonic() < deadline:
            try:
                documents = self.list_documents()
            except (RuntimeError, requests.RequestException) as error:
                print(f"  status API unavailable, waiting: {error}", flush=True)
                time.sleep(30)
                continue
            latest = {document["id"]: document for document in documents if document["id"] in wanted}
            if len(latest) != len(wanted):
                print(f"  status: waiting for {len(wanted) - len(latest)} document(s) to appear", flush=True)
                time.sleep(15)
                continue
            counts: dict[str, int] = {}
            for document in latest.values():
                status = document.get("indexing_status", "unknown")
                counts[status] = counts.get(status, 0) + 1
            print(f"  status: {counts}", flush=True)
            if all(
                document.get("indexing_status") in TERMINAL_STATUSES
                for document in latest.values()
            ):
                return latest
            time.sleep(15)
        raise TimeoutError(f"Indexing did not finish within {timeout} seconds")


def sync_batch(
    client: DifyClient,
    entries: list[tuple[Path, str]],
    timeout: int,
    max_retries: int,
) -> None:
    remaining = entries
    for attempt in range(max_retries + 1):
        remote = {document["name"]: document for document in client.list_documents()}
        pending: list[tuple[Path, str, str]] = []

        for path, upload_name in remaining:
            document = remote.get(upload_name)
            if document and document.get("indexing_status") == "completed":
                print(f"  skip completed: {upload_name}", flush=True)
                continue
            if document and document.get("indexing_status") in {"error", "paused"}:
                print(f"  delete failed: {upload_name}", flush=True)
                client.delete_document(document["id"])
                document = None
            if document:
                pending.append((path, upload_name, document["id"]))
            else:
                print(f"  upload: {upload_name}", flush=True)
                pending.append((path, upload_name, client.create_document(path, upload_name)))

        if not pending:
            return

        statuses = client.wait_for_terminal([item[2] for item in pending], timeout)
        failures: list[tuple[Path, str]] = []
        for path, upload_name, document_id in pending:
            document = statuses[document_id]
            if document.get("indexing_status") == "completed":
                print(f"  completed: {upload_name}", flush=True)
            else:
                print(
                    f"  failed: {upload_name}: {document.get('error') or document.get('indexing_status')}",
                    flush=True,
                )
                failures.append((path, upload_name))

        if not failures:
            return
        if attempt == max_retries:
            raise RuntimeError(f"Indexing failed after retries: {[name for _, name in failures]}")
        remaining = failures
        print(f"  retrying {len(remaining)} failed document(s)", flush=True)
        time.sleep(10)


def category_entries(root: Path) -> list[list[tuple[Path, str]]]:
    batches: list[list[tuple[Path, str]]] = []
    for category in sorted(path for path in root.iterdir() if path.is_dir() and path.name[:2].isdigit()):
        if not 1 <= int(category.name[:2]) <= 12:
            continue
        files = sorted(category.glob("*.md"))
        if len(files) != 7:
            raise RuntimeError(f"Expected 7 Markdown files in {category}, found {len(files)}")
        batches.append([(path, f"{category.name}__{path.name}") for path in files])
    if len(batches) != 12:
        raise RuntimeError(f"Expected 12 category directories, found {len(batches)}")
    return batches


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="https://localhost/v1")
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--knowledge-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=7200)
    parser.add_argument("--max-retries", type=int, default=2)
    args = parser.parse_args()

    api_key = os.environ.get("DIFY_KB_KEY")
    if not api_key:
        raise RuntimeError("DIFY_KB_KEY is required")

    client = DifyClient(args.base_url, args.dataset_id, api_key)
    for index, batch in enumerate(category_entries(args.knowledge_root), start=1):
        print(f"category {index:02d}/12", flush=True)
        sync_batch(client, batch, args.timeout, args.max_retries)

    extras = [
        (args.data_root / "CNC故障案例集.md", "CNC故障案例集.md"),
        (
            args.data_root / "pdfs" / "SINUMERIK_840Dsl_828D_通用操作手册.pdf",
            "SINUMERIK_840Dsl_828D_通用操作手册.pdf",
        ),
        (
            args.data_root / "pdfs" / "1MB8014系列三相异步电动机安装与维护手册.pdf",
            "1MB8014系列三相异步电动机安装与维护手册.pdf",
        ),
    ]
    for path, _ in extras:
        if not path.is_file():
            raise FileNotFoundError(path)
    print("supplemental files", flush=True)
    sync_batch(client, extras, args.timeout, args.max_retries)

    documents = client.list_documents()
    status_counts: dict[str, int] = {}
    for document in documents:
        status = document.get("indexing_status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    result = {"total": len(documents), "status_counts": status_counts}
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    if len(documents) != 102 or status_counts != {"completed": 102}:
        raise RuntimeError(f"Final dataset verification failed: {result}")


if __name__ == "__main__":
    main()
