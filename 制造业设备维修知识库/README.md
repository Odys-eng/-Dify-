# 制造业设备维修综合知识库

本目录包含 92 个结构化知识条目，覆盖通用维修方法和 12 类制造业设备。内容用于课程答辩、知识检索和维修辅助，不替代制造商手册、企业规程、法定检验或具备资格人员的现场判断。

## 文件说明

- `sources.csv`：已验证来源、可信度、范围和版权说明。
- `knowledge_manifest.csv`：条目路径、设备分类、风险和来源映射。
- `evaluation_questions.csv`：标准评测题、期望要点和安全要求。
- `00_通用安全与维修方法/`：跨设备通用条目。
- `01_...` 至 `12_...`：十二类设备知识条目。

## 使用边界

1. 优先遵守中国现行法律法规、设备制造商手册和本单位规程。
2. 条目中的通用检查顺序不能替代具体型号的拆装、参数和校准步骤。
3. 带电、承压、起重、动火、受限空间和防护区内作业必须由具备资格的人员按许可程序执行。
4. Dify 回答必须展示来源；资料不足或型号不明时应说明限制并升级专业人员。

## 重新生成与校验

```powershell
python scripts/knowledge_base/build_manufacturing_kb.py
python scripts/knowledge_base/build_manufacturing_kb.py --validate-only
```
