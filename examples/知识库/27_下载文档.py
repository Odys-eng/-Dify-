"""下载 Dify 知识库中的文档。

这个脚本会：
1. 调用文档下载接口，获取带签名的下载地址。
2. 请求下载地址，拿到文件内容。
3. 保存到 examples/知识库/downloads 目录。

使用方法：
1. 确认下面的 API_BASE_URL、API_KEY、DATASET_ID、DOCUMENT_ID 正确。
2. 右键运行这个 Python 文件。
"""

from pathlib import Path
from urllib.parse import unquote, urlparse

import requests


# 本地 Docker 启动的 Dify API 地址。如果你的端口不同，改这里。
API_BASE_URL = "http://localhost:12010/v1"

# 知识库 API Key。
API_KEY = "请填写知识库APIKey"

# 目标知识库 ID。
DATASET_ID = "425d72e8-e1b4-4048-aa5d-fd591bd6ac1d"

# 目标文档 ID。这里默认下载 002_Dify知识库API接口整理.md。
DOCUMENT_ID = "0d6bb003-904b-4b92-9bd8-63ea25d7f4a3"

# 下载目录。
DOWNLOAD_DIR = Path(__file__).with_name("downloads")


def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
    }


def get_download_url() -> str:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/{DOCUMENT_ID}/download"

    response = requests.get(url, headers=get_headers(), timeout=60)
    response.raise_for_status()

    result = response.json()
    download_url = result.get("url")
    if not download_url:
        raise RuntimeError("下载接口没有返回 url")

    return download_url


def get_document_name() -> str:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/{DOCUMENT_ID}"

    response = requests.get(url, headers=get_headers(), timeout=30)
    response.raise_for_status()

    return response.json().get("name") or "downloaded-document"


def get_filename_from_response(response: requests.Response, default_filename: str) -> str:
    content_disposition = response.headers.get("Content-Disposition", "")
    if "filename=" in content_disposition:
        filename = content_disposition.split("filename=", 1)[1].strip('"')
        return unquote(filename)

    parsed_url = urlparse(response.url)
    filename = Path(parsed_url.path).name
    if filename and filename != "file-preview":
        return filename
    return default_filename


def download_file(download_url: str, filename: str) -> Path:
    response = requests.get(download_url, timeout=120)
    response.raise_for_status()

    DOWNLOAD_DIR.mkdir(exist_ok=True)
    save_filename = get_filename_from_response(response, filename)
    file_path = DOWNLOAD_DIR / save_filename
    file_path.write_bytes(response.content)

    return file_path


def main() -> None:
    print("开始演示下载 Dify 知识库文档...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")
    print(f"文档 ID：{DOCUMENT_ID}")

    download_url = get_download_url()
    document_name = get_document_name()
    print("\n已获取下载地址。")

    file_path = download_file(download_url, document_name)
    print("\n文档下载成功：")
    print(f"保存路径：{file_path}")
    print(f"文件大小：{file_path.stat().st_size} 字节")

    print("\n说明：下载文档接口先返回下载地址，再通过下载地址获取原始文件内容。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
