# 真实设备手册上传指南

> 当前知识库中的 84 个 MD 文件为演示用合成数据。要让平台真正服务维修工人，需要上传真实设备手册。

## 推荐优先获取的手册

| 设备类型 | 品牌/型号 | 官方下载地址 |
|---------|---------|------------|
| CNC 数控系统 | FANUC 0i-MF 维修手册 | https://www.fanuc.co.jp/en/product/cnc/index.html |
| CNC 数控系统 | SINUMERIK 840D sl 编程手册 | https://support.industry.siemens.com |
| 伺服驱动 | 三菱 MR-J4 报警代码 | https://www.mitsubishielectric.com/fa/ |
| 伺服驱动 | 安川 Σ-7 参数手册 | https://www.yaskawa.co.jp |
| 变频器 | 西门子 G120 故障手册 | https://support.industry.siemens.com |
| 变频器 | ABB ACS880 手册 | https://new.abb.com/drives |
| PLC | 西门子 S7-1500 系统手册 | https://support.industry.siemens.com |
| PLC | 三菱 Q 系列编程手册 | https://www.mitsubishielectric.com/fa/ |
| 工业机器人 | ABB IRB 系列维修手册 | https://new.abb.com/products/robotics |
| 工业机器人 | FANUC LR Mate 维修手册 | https://www.fanuc.co.jp |

## 上传步骤

### 方式一：脚本批量上传（推荐）

```bash
# 1. 将 PDF 手册放入新建目录
mkdir -p data/new-manuals
# 把下载的 PDF 放进去...

# 2. 运行同步脚本
cd D:\Windows-OS\code\Summer_study\agent\homework
DIFY_KB_KEY="<你的知识库API密钥 dataset-xxxx>" \
  python src/knowledge/sync_knowledge_base.py \
  --watch-dir data/new-manuals \
  --base-url https://localhost/v1

# 3. 脚本会自动：
#    - 检查哪些文件已在知识库（跳过）
#    - 上传新文件
#    - 等待索引完成
#    - 报告结果
```

### 方式二：Dify 控制台手动上传

1. 打开 `https://localhost/datasets`
2. 点击「制造业设备维修」知识库
3. 点击右上角「添加文件」
4. 上传 PDF（支持最大 50MB，已配置）

## PDF 预处理建议

| 问题 | 处理方法 |
|-----|---------|
| PDF 超过 50MB | 用 `gs -dBATCH -dNOPAUSE -sDEVICE=pdfwrite -dFirstPage=1 -dLastPage=100` 拆分 |
| 扫描版 PDF（无文字层）| 用 OCR 工具处理后再上传，推荐 `ocrmypdf` |
| 日文/韩文手册 | Dify 支持多语言，可直接上传；System Prompt 已配置英文回答英文问题 |
| 加密 PDF | 先解密（`qpdf --decrypt input.pdf output.pdf`）再上传 |

## 知识库分类建议

上传时建议按设备类别命名，方便后续检索：

```
FANUC_0iMF_维修手册.pdf          ← CNC 类
Siemens_840D_操作手册.pdf         ← CNC 类  
MitsubishiMRJ4_伺服报警代码.pdf   ← 伺服类
ABB_IRB6700_维修手册.pdf          ← 机器人类
```

## 上传后验证

```bash
# 检查新文档是否成功索引
docker exec docker-api-1 python3 -c "
import requests
s = requests.Session(); s.trust_env = False
s.headers['Authorization'] = 'Bearer <你的知识库API密钥>'
r = s.get('http://127.0.0.1:5001/v1/datasets/<你的知识库ID>/documents',
          params={'limit': 100}, timeout=30)
docs = r.json()['data']
from collections import Counter
print(Counter(d['indexing_status'] for d in docs))
print(f'Total: {r.json()[\"total\"]}')
"
```

## 持续更新流程

设备有新固件/新报警代码时：

```bash
# 1. 将新手册放入 data/new-manuals/
# 2. 运行同步脚本（自动跳过已存在文档）
DIFY_KB_KEY="<你的知识库API密钥 dataset-xxxx>" \
  python src/knowledge/sync_knowledge_base.py \
  --watch-dir data/new-manuals

# 可选：设置定时任务（每天凌晨2点扫描）
# crontab -e
# 0 2 * * * cd /path/to/homework && DIFY_KB_KEY=xxx python src/knowledge/sync_knowledge_base.py --watch-dir data/new-manuals >> sync.log 2>&1
```
