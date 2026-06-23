# 📚 天云 RAG — 企业级智能文档问答系统

基于 **LangGraph + FastAPI + BGE-M3 + Milvus** 的多 Agent 协作 RAG 问答系统。支持 PDF/文档导入、知识库构建、多路召回检索和智能问答。

---

## 🎯 功能概览

| 功能 | 说明 |
|------|------|
| 📄 文档导入 | 上传 PDF/MD，自动解析为结构化知识 |
| 🖼️ 图片理解 | VL 模型自动生成图片描述并入库 |
| 🏷️ 品名识别 | LLM 自动识别文档所属产品名称 |
| 🔍 多路召回 | 稠密向量 + 稀疏向量 + HyDE + 网络搜索四路并行 |
| ⚖️ RRF 融合 | 加权 Reciprocal Rank Fusion 多路结果融合 |
| 🎯 Rerank 重排 | BGE-Reranker 跨编码器精排 + 动态 Top-K |
| 💬 智能问答 | 基于检索结果 + 对话历史的 LLM 回答生成 |
| 🌐 网络增强 | MCP 工具实时搜索互联网信息辅助回答 |

---

## 🏗️ 技术架构

```
用户 → FastAPI Web 服务 → LangGraph 导入/查询工作流

导入流水线:
  PDF/MD 上传 → MinerU 解析 → VL 图片理解 → 文档切片
    → 品名识别 → BGE-M3 向量化 → Milvus 入库

查询流水线:
  用户提问 → 品名确认 + 查询改写
    ├─→ 稠密/稀疏向量检索 (Milvus)
    ├─→ HyDE 假设文档检索
    └─→ MCP 网络搜索
         ↓
    RRF 融合 → BGE Reranker → LLM 回答 → SSE 流式输出
```

### 技术栈

- **后端**: Python / FastAPI / LangGraph / LangChain
- **LLM**: Qwen / DeepSeek（OpenAI 兼容接口）
- **向量模型**: BGE-M3（稠密 + 稀疏混合向量）
- **重排序**: BGE-Reranker-Large（跨编码器）
- **向量库**: Milvus（混合检索：Dense + Sparse）
- **存储**: MongoDB（会话历史）/ MinIO（文档图片）
- **文档解析**: MinerU（PDF 转 Markdown）

---

### 🔒 会话持久化与容错

系统采用 **MongoDB** 持久化聊天历史，支持完整的多轮对话上下文管理：

| 层级 | 存储 | 场景 |
|------|------|------|
| 会话历史 | MongoDB | 聊天记录持久化，支持按 session 查询 |
| 向量数据 | Milvus | 文档切片向量 + 品名向量混合存储 |
| 对象存储 | MinIO | 文档图片上传与访问 |
| 任务状态 | 内存 | 导入任务进度实时追踪（SSE 推送） |

配合 **SSE 流式输出**、**滑动窗口速率限制**、**Milvus 字符串安全转义**，确保在高并发和异常输入下稳定运行。

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -e .
# 或使用 uv
uv sync
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入 API 密钥和连接信息：

```env
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=你的阿里云DashScope密钥
MILVUS_URL=localhost:19530
MINIO_ENDPOINT=localhost:9000
MONGO_URL=mongodb://localhost:27017
```

### 3. 启动依赖服务 (Docker)

```bash
# Milvus 向量数据库
docker run -d --name milvus -p 19530:19530 milvusdb/milvus:latest

# MongoDB 会话存储
docker run -d --name mongo -p 27017:27017 mongo:7

# MinIO 对象存储
docker run -d --name minio -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ":9001"
```

### 4. 下载模型 (可选)

```bash
# BGE-M3 向量模型
python app/tool/download_bgem3.py

# BGE-Reranker 重排序模型
python app/tool/download_reranker.py
```

### 5. 启动服务

**导入服务**（端口 8000）：

```bash
uvicorn app.import_process.api.import_server:app --host 0.0.0.0 --port 8000
```

**问答服务**（端口 8001）：

```bash
uvicorn app.query_process.api.query_server:app --host 0.0.0.0 --port 8001
```

### 6. 访问

- 打开 `http://localhost:8000/import` 上传文档
- 打开 `http://localhost:8001/chat.html` 开始问答

---

## 📁 项目结构

```
├── app/
│   ├── clients/                # 外部服务客户端
│   │   ├── milvus_utils.py     # Milvus 混合检索
│   │   ├── minio_utils.py      # MinIO 对象存储
│   │   ├── mongo_history_utils.py  # MongoDB 会话历史
│   │   └── neo4j_utils.py      # Neo4j 图库（预留）
│   ├── conf/                   # 配置类（.env 映射）
│   ├── core/                   # 日志、提示词加载
│   ├── import_process/         # 导入流水线
│   │   ├── agent/              # LangGraph 节点
│   │   │   ├── nodes/
│   │   │   │   ├── node_entry.py           # 入口：文件校验
│   │   │   │   ├── node_pdf_to_md.py       # MinerU PDF 解析
│   │   │   │   ├── node_md_img.py          # VL 图片理解
│   │   │   │   ├── node_document_split.py  # 语义切片
│   │   │   │   ├── node_item_name_recognition.py  # 品名识别
│   │   │   │   ├── node_bge_embedding.py   # 向量化
│   │   │   │   └── node_import_milvus.py   # 入库
│   │   │   ├── main_graph.py   # 工作流编排
│   │   │   └── state.py        # 状态定义
│   │   ├── api/                # FastAPI 服务
│   │   └── page/               # 上传页面
│   ├── query_process/          # 查询流水线
│   │   ├── agent/
│   │   │   ├── nodes/
│   │   │   │   ├── node_item_name_confirm.py      # 品名确认
│   │   │   │   ├── node_search_embedding.py       # 向量检索
│   │   │   │   ├── node_search_embedding_hyde.py  # HyDE 检索
│   │   │   │   ├── node_web_search_mcp.py         # 网络搜索
│   │   │   │   ├── node_rrf.py                    # RRF 融合
│   │   │   │   ├── node_rerank.py                 # Rerank 重排
│   │   │   │   └── node_answer_output.py          # 答案生成
│   │   │   ├── main_graph.py
│   │   │   └── state.py
│   │   ├── api/                # FastAPI 服务
│   │   ├── page/               # 聊天 & 监控页面
│   │   └── sse/                # SSE 流式示例
│   ├── lm/                     # 大模型工具
│   │   ├── lm_utils.py         # LLM 客户端
│   │   ├── embedding_utils.py  # BGE-M3 向量化
│   │   └── reranker_utils.py   # BGE Reranker
│   ├── test/                   # 集成测试
│   ├── tool/                   # 模型下载脚本
│   └── utils/                  # 工具函数
├── docs/                       # 项目分析文档
├── evals/                      # RAG 评估数据集
├── prompts/                    # LLM 提示词模板
├── rag_eval/                   # Ragas 评估子项目
├── pyproject.toml              # 项目配置
└── .env                        # 环境变量（不提交）
```

---

## 🔧 主要依赖

| 组件 | 用途 |
|------|------|
| langchain + langgraph | 多 Agent 工作流编排 |
| pymilvus | 向量数据库 Milvus 客户端 |
| pymilvus-model | BGE-M3 模型集成 |
| flagembedding | BGE-Reranker 跨编码器重排序 |
| fastapi + uvicorn | Web 服务框架 |
| langchain-openai | LLM 调用（OpenAI 兼容接口） |
| magic-pdf (MinerU) | PDF 转 Markdown 解析 |
| minio | 对象存储客户端 |
| pymongo | MongoDB 会话历史存储 |
| modelscope | ModelScope 模型下载 |
| ragas | RAG 评估框架 |
| openai-agents | MCP 网络搜索工具 |
| loguru | 日志管理 |

---

## ⚠️ 注意事项

- 首次运行需要配置 `.env` 中的 API 密钥和服务连接信息
- MinerU PDF 解析需要启动独立的 MinerU API 服务
- BGE 模型支持本地路径或 HuggingFace/ModelScope 自动下载
- 导入 Milvus 的数据量较大时建议分批处理
- 项目依赖 PyTorch，建议根据 CUDA 版本安装对应 torch 版本
