# 新增信息源指南

本文说明如何在 AI Dashboard 中新增一个信息源，并接入统一聚合接口。

## 1. 目录位置

- 信息源实现目录：`collectors/sources/`
- 注册中心：`collectors/registry.py`
- 聚合接口：`backend/app/main.py` 的 `GET /api/dashboard/summary`
- 记录 schema：`schemas/normalized_record.schema.json`

## 2. 接口约定

每个来源需要实现统一接口：

```python
class XxxSource:
    name = "source_name"

    def fetch(self) -> list[NormalizedRecord]:
        ...
```

说明：
- `name`：来源唯一标识，用于前端来源管理面板显示。
- `fetch()`：负责拉取并标准化数据，返回 `list[NormalizedRecord]`。
- 发生异常时抛出异常，注册中心会记录状态为 `error` 并附带错误信息。

## 3. 字段规范（NormalizedRecord）

每条记录必须包含以下字段：

- `id: str`：唯一 ID。
- `title: str`：标题或摘要。
- `category: str`：分类（如 `announcement`、`equity`）。
- `timestamp: str`：ISO-8601 时间（`date-time`）。
- `payload: object`：来源原始扩展字段。

以 `schemas/normalized_record.schema.json` 为准。

## 4. 接入步骤

1. 在 `collectors/sources/` 新建来源实现文件（如 `my_source.py`）。
2. 在 `backend/app/main.py` 中 `registry.register(MySource())`。
3. 本地运行 `GET /api/dashboard/summary`，确认该来源出现在 `sources` 与 `snapshot`。
4. 前端“来源管理”面板检查状态、最后同步时间、错误信息显示正确。

## 5. 测试要求

至少执行以下自动化检查：

```bash
make check
```

该命令会执行：
- `ruff check .`（lint）
- `mypy backend collectors`（类型检查）
- `python scripts/validate_schema.py`（schema 校验）

额外建议执行 `pytest -q` 做基础行为验证。若新增来源，请补充对应单元测试并确保 `make check` 全绿。
