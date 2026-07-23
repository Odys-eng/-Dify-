"""
upload_to_dify.py
将 制造业设备维修知识库/ 和 data/pdfs/ 下的所有文件上传到 Dify 知识库
用法：python src/knowledge/upload_to_dify.py
"""

import os
import json
import time
import requests
from pathlib import Path

# ============================================================
# 配置区：密钥从环境变量读取，不硬编码进源码
# 运行前先设置：  export DIFY_KB_KEY="dataset-xxxx"   (Windows: $env:DIFY_KB_KEY="dataset-xxxx")
# ============================================================
DIFY_BASE_URL = os.environ.get("DIFY_BASE_URL", "http://localhost")
DATASET_API_KEY = os.environ.get("DIFY_KB_KEY", "")
if not DATASET_API_KEY:
    raise SystemExit("请先设置环境变量 DIFY_KB_KEY（你的知识库 API 密钥，形如 dataset-xxxx）")

# 项目根目录（脚本在 src/knowledge/ 下，上两级是根目录）
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 要上传的文件夹
SOURCE_DIRS = [
    PROJECT_ROOT / "制造业设备维修知识库",
    PROJECT_ROOT / "data" / "pdfs",
]

# 支持的文件类型
SUPPORTED_EXTENSIONS = {".md", ".pdf", ".txt", ".docx", ".csv"}

# 上传间隔（秒），避免请求过快
UPLOAD_DELAY = 1.5

# ============================================================


def get_headers():
    return {"Authorization": f"Bearer {DATASET_API_KEY}"}


def get_dataset_id():
    """获取知识库 ID（从 API Key 关联的第一个知识库）"""
    url = f"{DIFY_BASE_URL}/v1/datasets?page=1&limit=20"
    resp = requests.get(url, headers=get_headers(), timeout=15)
    resp.raise_for_status()
    data = resp.json()
    datasets = data.get("data", [])
    if not datasets:
        raise ValueError("未找到知识库，请确认 API Key 正确且已创建知识库")
    # 打印所有知识库供确认
    print("\n找到以下知识库：")
    for ds in datasets:
        print(f"  [{ds['id']}] {ds['name']} — {ds['document_count']} 个文档")
    # 取第一个
    chosen = datasets[0]
    print(f"\n将上传到：「{chosen['name']}」 (id: {chosen['id']})\n")
    return chosen["id"]


def collect_files(source_dirs):
    """收集所有待上传文件"""
    files = []
    for folder in source_dirs:
        if not folder.exists():
            print(f"  ⚠️  文件夹不存在，跳过：{folder}")
            continue
        for path in sorted(folder.rglob("*")):
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(path)
    return files


def upload_file(dataset_id, file_path):
    """上传单个文件"""
    url = f"{DIFY_BASE_URL}/v1/datasets/{dataset_id}/document/create-by-file"

    # 文档处理参数：高质量 + 自动切分
    doc_data = {
        "indexing_technique": "high_quality",
        "process_rule": {"mode": "automatic"},
    }

    # 根据扩展名设置 MIME 类型
    mime_map = {
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".csv": "text/csv",
    }
    mime = mime_map.get(file_path.suffix.lower(), "application/octet-stream")

    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, mime)}
        data = {"data": json.dumps(doc_data, ensure_ascii=False)}
        resp = requests.post(
            url,
            headers=get_headers(),
            files=files,
            data=data,
            timeout=60,
        )

    if resp.status_code in (200, 201):
        doc_id = resp.json().get("document", {}).get("id", "?")
        return True, doc_id
    else:
        return False, resp.text


def main():
    print("=" * 60)
    print("  Dify 知识库批量上传工具")
    print("=" * 60)

    # 1. 获取知识库 ID
    try:
        dataset_id = get_dataset_id()
    except Exception as e:
        print(f"❌ 获取知识库失败：{e}")
        print("   请确认：1) Dify 已启动  2) API Key 正确  3) 知识库已创建")
        return

    # 2. 收集文件
    print("扫描文件夹...")
    all_files = collect_files(SOURCE_DIRS)
    total = len(all_files)
    print(f"共找到 {total} 个文件待上传\n")

    if total == 0:
        print("没有找到任何文件，请检查文件夹路径。")
        return

    # 3. 逐个上传
    success_count = 0
    fail_list = []

    for i, file_path in enumerate(all_files, 1):
        # 显示相对路径更清晰
        try:
            rel = file_path.relative_to(PROJECT_ROOT)
        except ValueError:
            rel = file_path

        print(f"[{i:3d}/{total}] 上传：{rel} ... ", end="", flush=True)

        try:
            ok, result = upload_file(dataset_id, file_path)
            if ok:
                print(f"✓ (doc_id: {result})")
                success_count += 1
            else:
                print(f"✗ 失败：{result[:100]}")
                fail_list.append((str(rel), result[:200]))
        except Exception as e:
            print(f"✗ 异常：{e}")
            fail_list.append((str(rel), str(e)))

        # 上传间隔，避免 worker 过载
        if i < total:
            time.sleep(UPLOAD_DELAY)

    # 4. 汇总
    print("\n" + "=" * 60)
    print(f"  完成：{success_count}/{total} 个文件上传成功")
    if fail_list:
        print(f"  失败：{len(fail_list)} 个文件")
        print("\n失败详情：")
        for fname, reason in fail_list:
            print(f"  - {fname}")
            print(f"    原因：{reason}")
    print("=" * 60)
    print("\n文件已提交，Dify 后台正在进行向量化处理（约需几分钟）")
    print("可在 Dify 控制台「知识库 → 文档」页面查看处理进度")


if __name__ == "__main__":
    main()
