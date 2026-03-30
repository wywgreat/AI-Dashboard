# AI Dashboard

一个用于聚合 AI 来源信息的 Dashboard 初始化脚手架，当前包含：

- `backend/`：FastAPI 最小 API 服务。
- `frontend/`：Next.js 首页骨架（刷新按钮、来源筛选、3 个 AA 表格区块、HF Trending 区块）。
- `collectors/`：后续抓取器代码目录。
- `storage/`：后续存储与缓存相关目录。
- `docs/`：文档目录。

## 技术栈与版本

- Backend: `FastAPI 0.115.12` + `Uvicorn 0.34.0` + `Pydantic 2.11.2`
- Frontend: `Next.js 14.2.15` + `React 18.3.1`

## 本地一键启动

### 方式一：Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

启动后：

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Backend Health: http://localhost:8000/health
- Sources API: http://localhost:8000/api/sources

### 方式二：Make

```bash
cp .env.example .env
make dev
```

`make dev` 等价于 `docker compose up --build`。

## 最小 API

- `GET /health`
- `GET /api/sources`
