# 掌柜智库项目分析文档

## 1. 项目定位

`zgzk` 是一个围绕知识库导入与问答检索构建的 RAG 项目，核心目标是把 PDF/Markdown 文档导入知识库，并基于向量检索、多路召回、重排序和大模型生成实现问答服务。

从代码结构来看，项目包含两条核心业务链路：

- 导入链路：文档上传 -> 解析 -> 图片理解 -> 切块 -> 主体识别 -> 向量化 -> Milvus 入库
- 查询链路：问题接收 -> 主体识别/确认 -> 多路召回 -> RRF 融合 -> Rerank 精排 -> 大模型生成答案

整体上，这不是一个单纯的 Web 项目，而是一个由 `FastAPI + LangGraph + Milvus + MongoDB + MinIO + 外部模型服务` 组成的知识库问答系统。

## 2. 技术栈总览

根据 `pyproject.toml`，项目主要技术栈如下：

- Python `>=3.12`
- Web 框架：`FastAPI`、`uvicorn`
- Agent/流程编排：`langgraph`
- LLM 调用：`langchain-openai`、`langchain`
- 向量模型：`pymilvus-model`、`flagembedding`
- 向量数据库：`Milvus`
- 历史对话存储：`MongoDB`
- 对象存储：`MinIO`
- PDF 解析：`MinerU / magic-pdf`
- 联网搜索：`openai-agents` + MCP
- 日志：`loguru`

## 3. 项目总体架构

项目可以分为 6 个层次：

### 3.1 接口层

- `app/import_process/api/import_server.py`
  - 提供文档上传、导入进度查询、导入页面访问
- `app/query_process/api/query_server.py`
  - 提供问答接口、SSE 流式输出、历史记录查询与删除、聊天页面访问

### 3.2 Agent 流程层

- `app/import_process/agent/`
  - 使用 LangGraph 编排导入知识库流程
- `app/query_process/agent/`
  - 使用 LangGraph 编排查询与答案生成流程

### 3.3 模型能力层

- `app/lm/lm_utils.py`
  - OpenAI 兼容 LLM 客户端统一封装
- `app/lm/embedding_utils.py`
  - BGE-M3 混合向量生成
- `app/lm/reranker_utils.py`
  - Cross-Encoder 重排序模型加载

### 3.4 存储与外部服务层

- `app/clients/milvus_utils.py`
  - Milvus 连接、混合检索、chunk 拉取等能力
- `app/clients/mongo_history_utils.py`
  - 会话历史记录读写
- `app/clients/minio_utils.py`
  - 图片对象存储
- `MinerU`
  - PDF 转 Markdown
- `MCP Web Search`
  - 外部联网搜索

### 3.5 通用基础设施层

- `app/core/logger.py`
  - 全局日志初始化
- `app/core/load_prompt.py`
  - Prompt 文件读取
- `app/utils/`
  - 路径、SSE、任务状态、字符串处理、限流等工具

### 3.6 前端页面层

- `app/import_process/page/import.html`
  - 上传导入页面
- `app/query_process/page/chat.html`
  - 问答页面

## 4. 目录结构分析

项目根目录下的重要目录如下：

```text
zgzk/
├─ app/
│  ├─ clients/              # 外部系统客户端封装
│  ├─ conf/                 # .env 配置映射
│  ├─ core/                 # 日志、Prompt 加载
│  ├─ import_process/       # 导入知识库流程
│  ├─ lm/                   # LLM / Embedding / Reranker
│  ├─ query_process/        # 查询问答流程
│  ├─ test/                 # 测试
│  ├─ tool/                 # 模型下载脚本
│  └─ utils/                # 公共工具
├─ doc/                     # 原始知识文档样本（大量 PDF）
├─ output/                  # 导入过程产物与解析结果
├─ logs/                    # 日志输出
├─ prompts/                 # Prompt 模板
├─ .env                     # 运行配置
├─ pyproject.toml           # 依赖与项目定义
├─ uv.lock                  # 锁文件
└─ main.py                  # 占位入口
```

### 4.1 `app/clients`

职责是把外部资源访问从业务流程中抽离出来，当前包括：

- `milvus_utils.py`：Milvus 连接、混合搜索、按 chunk_id 回查
- `minio_utils.py`：MinIO 客户端与桶初始化
- `mongo_history_utils.py`：历史消息写入/查询/删除
- `neo4j_utils.py`：预留图谱能力

### 4.2 `app/conf`

将 `.env` 配置映射为 dataclass，避免业务代码散落 `os.getenv()`。

当前主要配置包括：

- 大模型配置
- Embedding 模型配置
- Milvus 配置
- MinIO 配置
- MinerU 配置
- MCP 搜索配置

### 4.3 `app/import_process`

负责文档导入知识库，包含：

- API 接口
- LangGraph 状态定义
- 多个导入节点
- 前端上传页

### 4.4 `app/query_process`

负责查询、流式返回和答案生成，包含：

- API 接口
- Query Agent 图
- SSE 示例
- 聊天页面

### 4.5 `prompts`

Prompt 被单独抽到文件中，说明项目已经有“提示词与代码解耦”的意识。典型文件包括：

- `answer_out.prompt`
- `hyde_prompt.prompt`
- `image_summary.prompt`
- `item_name_recognition.prompt`
- `rewritten_query_and_itemnames.prompt`

### 4.6 `doc` 与 `output`

- `doc/`：项目输入样本，主要是设备说明书、用户手册 PDF
- `output/`：导入流程的中间产物与最终结果
  - 解析后的 Markdown
  - 图片目录
  - layout / content_list JSON
  - chunks.json
  - 打包 ZIP

这说明项目当前更偏“工程实验 + 业务验证”形态，既保留了原始语料，也保留了流程产物，方便追踪处理效果。

## 5. 导入流程分析

导入服务主入口为 `app/import_process/api/import_server.py`。

### 5.1 接口职责

- `GET /import`
  - 返回上传页面 `import.html`
- `POST /upload`
  - 接收多个文件，保存到 `output/日期/task_id/`
  - 为每个文件生成独立任务 ID
  - 通过 FastAPI `BackgroundTasks` 启动导入图
- `GET /status/{task_id}`
  - 返回全局状态、已完成节点、运行中节点

### 5.2 LangGraph 导入图

导入图定义在 `app/import_process/agent/main_graph.py`，流程如下：

```text
node_entry
  ├─ 如果是 PDF -> node_pdf_to_md
  │                 -> node_md_img
  └─ 如果是 MD  -> node_md_img
                     -> node_document_split
                     -> node_item_name_recognition
                     -> node_bge_embedding
                     -> node_import_milvus
                     -> END
```

### 5.3 各节点职责

#### 1. `node_entry`

- 检查输入文件路径
- 识别是 `pdf` 还是 `md`
- 设置 `state` 中的路径和开关
- 提取 `file_title`

#### 2. `node_pdf_to_md`

- 对 PDF 进行路径校验
- 调用 MinerU 上传并轮询解析结果
- 下载结果 ZIP 到本地
- 解压出 Markdown 与相关目录

这是导入链路里最依赖外部服务的节点。

#### 3. `node_md_img`

- 读取 Markdown 内容
- 扫描 Markdown 中引用的图片
- 提取图片上下文
- 调用视觉模型生成图片摘要
- 上传图片到 MinIO
- 回写 Markdown，把图片变成“图片说明 + 图片地址”的可检索内容

这个节点的价值很高，它把“图像不可检索”问题转化成“图像说明可检索”问题。

#### 4. `node_document_split`

- 基于 Markdown 标题进行语义粗切
- 对超长 chunk 进行二次切分
- 对过短 chunk 做合并
- 最终得到适合检索的 chunk 列表

这是知识库效果的关键节点之一。

#### 5. `node_item_name_recognition`

- 从前几个 chunk 中拼接上下文
- 调用 LLM 识别文档主体名称 `item_name`
- 给所有 chunk 补齐 `item_name`
- 为 `item_name` 生成向量
- 把主体信息写入单独的 Milvus 集合

这个设计说明项目不仅做“内容切片检索”，还做了“文档主体识别 + 主体级约束检索”。

#### 6. `node_bge_embedding`

- 对每个 chunk 生成 BGE-M3 的稠密向量与稀疏向量
- 为后续 Milvus 混合检索准备入库数据

#### 7. `node_import_milvus`

- 检查或创建 Milvus 集合与索引
- 按 `item_name` 删除旧数据，保证幂等
- 批量插入 chunk 数据
- 回填 `chunk_id`

### 5.4 导入流程状态管理

导入和查询共用 `app/utils/task_utils.py` 进行任务状态管理。

特点：

- 使用进程内内存字典保存任务状态
- 可以记录 `running_list`、`done_list`、`status`
- 节点名称会映射成中文返回给前端

优点：

- 实现简单
- 前端轮询易用

局限：

- 单进程有效
- 服务重启后任务状态丢失
- 不适合多实例部署

## 6. 查询流程分析

查询服务主入口为 `app/query_process/api/query_server.py`。

### 6.1 接口职责

- `GET /health`
  - 健康检查
- `GET /chat.html`
  - 返回聊天页面
- `POST /query`
  - 发起同步或异步查询
- `GET /stream/{session_id}`
  - 建立 SSE 长连接
- `GET /history/{session_id}`
  - 查询历史消息
- `DELETE /history/{session_id}`
  - 清空历史消息

### 6.2 同步与流式两种模式

`/query` 支持：

- 非流式
  - 直接执行图并同步返回最终答案
- 流式
  - 先返回 `session_id`
  - 后台异步执行图
  - 前端通过 SSE 接收进度、token 增量和最终结果

### 6.3 Query LangGraph

查询图定义在 `app/query_process/agent/main_graph.py`。

```text
node_item_name_confirm
  ├─ 若已能直接回答 -> node_answer_output -> END
  └─ 否则并行进入：
      - node_search_embedding
      - node_search_embedding_hyde
      - node_web_search_mcp
        -> node_rrf
        -> node_rerank
        -> node_answer_output
        -> END
```

### 6.4 各节点职责

#### 1. `node_item_name_confirm`

- 读取历史记录
- 通过 LLM 完成问题改写与主体识别
- 再用 Milvus 的 `item_name` 集合做相似匹配确认
- 根据分数判断：
  - 已确定主体
  - 可选主体
  - 无法识别主体

如果无法确定主体，节点会提前生成引导性回答，减少无效检索。

#### 2. `node_search_embedding`

- 对重写后的问题生成混合向量
- 按 `item_name` 约束在 chunk 集合中检索
- 返回本地知识库召回结果

#### 3. `node_search_embedding_hyde`

- 先让 LLM 生成假设性答案
- 把“问题 + 假设性答案”再进行向量检索
- 提升召回率

#### 4. `node_web_search_mcp`

- 调用百炼 MCP 搜索工具
- 获取联网结果页面列表
- 用作外部知识补充

#### 5. `node_rrf`

- 对本地向量召回和 HyDE 召回做 Reciprocal Rank Fusion
- 解决多路本地召回结果融合问题

#### 6. `node_rerank`

- 将本地结果和联网结果合并
- 用 Reranker 对问题-文档对重新打分
- 再通过“断崖阈值 + TopK”策略截断结果

这是最终上下文质量控制的关键节点。

#### 7. `node_answer_output`

- 若前面已提前生成答案，直接输出
- 否则加载 Prompt 拼接上下文
- 调用 LLM 生成最终答案
- 在流式模式下通过 SSE 推送增量 token
- 提取相关图片 URL
- 写入 MongoDB 历史记录

## 7. 状态对象设计

### 7.1 导入状态 `ImportGraphState`

主要字段包括：

- 任务标识：`task_id`
- 控制开关：是否走 PDF / MD 路径
- 文件路径：`local_file_path`、`pdf_path`、`md_path`、`local_dir`
- 内容数据：`md_content`、`chunks`、`item_name`
- 入库数据：`embeddings_content`

### 7.2 查询状态 `QueryGraphState`

主要字段包括：

- 会话信息：`session_id`、`original_query`
- 多路召回结果：`embedding_chunks`、`hyde_embedding_chunks`、`web_search_docs`
- 排序结果：`rrf_chunks`、`reranked_docs`
- 生成结果：`prompt`、`answer`
- 辅助信息：`item_names`、`rewritten_query`、`history`、`is_stream`

项目用 `TypedDict` 维护流程状态，优点是结构清晰、对 LangGraph 友好，缺点是状态增长后容易失控，需要靠文档与命名规范维持可读性。

## 8. 数据存储设计

### 8.1 Milvus

项目至少使用两个集合：

- `item_name_collection`
  - 存储文档主体名称向量
  - 用于 query 阶段确认产品/设备主体
- `chunks_collection`
  - 存储 chunk 内容及其 dense/sparse 向量
  - 用于混合检索

设计特点：

- 稠密向量索引：`HNSW + COSINE`
- 稀疏向量索引：`SPARSE_INVERTED_INDEX + IP`
- 检索采用“稠密 + 稀疏”的混合搜索

### 8.2 MongoDB

Mongo 用于存储会话历史：

- `session_id`
- `role`
- `text`
- `rewritten_query`
- `item_names`
- `image_urls`
- `ts`

其作用是：

- 构造多轮对话上下文
- 支持历史查询与删除

### 8.3 MinIO

用于托管图片资源，支撑：

- Markdown 图片公网可访问
- 图文检索结果回显
- LLM 最终答案附图

## 9. Prompt 设计思路

项目中 Prompt 已经单独存放在 `prompts/` 目录，说明设计倾向于“Prompt 工程文件化”。

从文件名可以看出项目的 Prompt 覆盖了：

- 主体识别
- 问题改写
- 图片理解
- HyDE 假设答案生成
- 最终答案生成

这使业务逻辑和提示词能独立演化，是一个比较成熟的工程实践。

## 10. 当前项目的结构特点

### 10.1 优点

- 业务边界清晰，导入与查询分层明确
- LangGraph 的使用使流程可读性较高
- Prompt、配置、外部客户端已做模块化拆分
- 检索链路完整，包含主体识别、HyDE、RRF、Rerank、SSE
- 对图片处理有专门设计，优于纯文本 RAG

### 10.2 目前存在的典型工程特征

- `README.md` 为空，项目知识主要依赖源码阅读
- `main.py` 仍是占位文件，不是实际启动入口
- 任务状态基于内存，不适合多实例和重启恢复
- 一些节点文件中保留了较多测试代码、注释和实验性实现
- 存在少量无关 import、调试语句、示例代码痕迹
- `doc/` 与 `output/` 直接放在仓库内，说明当前偏本地运行与验证环境

### 10.3 架构成熟度判断

项目已经具备：

- 可运行的服务接口
- 可编排的导入/查询流程
- 外部存储与模型服务接入
- 一定程度的前后端闭环

但还处于“工程可用、生产前加强”的阶段，而不是完全标准化的企业级产品形态。

## 11. 建议的项目认知方式

如果后续要继续维护本项目，建议按以下顺序理解源码：

1. 先看 `app/import_process/api/import_server.py`
2. 再看 `app/import_process/agent/main_graph.py`
3. 再看导入节点 `node_*`
4. 然后看 `app/query_process/api/query_server.py`
5. 再看 `app/query_process/agent/main_graph.py`
6. 最后看 `clients/`、`lm/`、`utils/`、`prompts/`

这样可以优先掌握主流程，再补全基础设施实现。

## 12. 后续可补充的文档建议

当前项目最值得继续补充的文档包括：

- 环境变量说明文档
- 本地部署与启动文档
- Milvus/Mongo/MinIO 初始化说明
- 导入流程时序图
- 查询流程时序图
- Prompt 设计说明
- 错误排查手册

## 13. 一句话总结

这是一个围绕“设备/产品手册知识库问答”构建的 RAG 工程，采用 `FastAPI + LangGraph` 组织业务流程，利用 `Milvus + MongoDB + MinIO + 外部模型服务` 搭建了一条从文档导入到问答生成的完整闭环。
