# 掌柜智库项目思维导图

下面的思维导图使用 Mermaid 编写，支持 Mermaid 的 Markdown 预览器可直接渲染。

```mermaid
mindmap
  root((zgzk 项目))
    项目定位
      知识库导入
      RAG 问答
      设备手册场景
    技术栈
      Python 3.12
      FastAPI
      LangGraph
      LangChain OpenAI
      Milvus
      MongoDB
      MinIO
      MinerU
      MCP Web Search
    顶层目录
      app
      doc
      output
      logs
      prompts
      .env
      pyproject.toml
    app
      clients
        milvus_utils
        mongo_history_utils
        minio_utils
        neo4j_utils
      conf
        lm_config
        embedding_config
        milvus_config
        minio_config
        mineru_config
        bailian_mcp_config
      core
        logger
        load_prompt
      lm
        lm_utils
        embedding_utils
        reranker_utils
      utils
        task_utils
        sse_utils
        path_util
        rate_limit_utils
      import_process
        api
          import_server
        agent
          state
          main_graph
          node_entry
          node_pdf_to_md
          node_md_img
          node_document_split
          node_item_name_recognition
          node_bge_embedding
          node_import_milvus
        page
          import.html
      query_process
        api
          query_server
        agent
          state
          main_graph
          node_item_name_confirm
          node_search_embedding
          node_search_embedding_hyde
          node_web_search_mcp
          node_rrf
          node_rerank
          node_answer_output
        page
          chat.html
        sse
          sse_step_1
          sse_step_2
    导入链路
      upload 接口
      保存到 output
      BackgroundTasks
      LangGraph 导入图
      node_entry
      PDF 路径
        node_pdf_to_md
      MD 路径
        node_md_img
      通用后续
        node_document_split
        node_item_name_recognition
        node_bge_embedding
        node_import_milvus
    查询链路
      query 接口
      同步返回
      流式返回
        SSE
      node_item_name_confirm
      多路召回
        embedding 搜索
        HyDE 搜索
        web search
      结果融合
        RRF
        Rerank
      最终输出
        LLM 生成
        图片提取
        写入历史
    数据存储
      Milvus
        item_name_collection
        chunks_collection
      MongoDB
        chat_message
      MinIO
        图片对象
      output
        markdown
        images
        chunks.json
        zip
    Prompt 体系
      answer_out
      hyde_prompt
      image_summary
      item_name_recognition
      rewritten_query_and_itemnames
    运行特征
      任务状态基于内存
      节点状态中文映射
      Prompt 与代码解耦
      图片转文本增强检索
      本地样本和产物保存在仓库内
    主要改进点
      补全 README
      明确启动方式
      增强测试覆盖
      把任务状态持久化
      清理实验性代码
```

## 文本版结构

```text
zgzk 项目
├─ 技术底座
│  ├─ FastAPI
│  ├─ LangGraph
│  ├─ Milvus
│  ├─ MongoDB
│  ├─ MinIO
│  └─ OpenAI 兼容模型服务
├─ 导入流程
│  ├─ 上传文件
│  ├─ PDF 转 Markdown
│  ├─ 图片理解
│  ├─ 文档切块
│  ├─ 主体识别
│  ├─ 向量生成
│  └─ Milvus 入库
├─ 查询流程
│  ├─ 问题改写与主体确认
│  ├─ 本地混合检索
│  ├─ HyDE 检索
│  ├─ 联网搜索
│  ├─ RRF 融合
│  ├─ Rerank 精排
│  └─ 大模型答案输出
├─ 存储体系
│  ├─ Milvus: chunk 与 item_name
│  ├─ MongoDB: 历史对话
│  ├─ MinIO: 图片
│  └─ output: 中间产物
└─ 工程支撑
   ├─ conf: 配置映射
   ├─ core: 日志与 Prompt 加载
   ├─ utils: SSE、任务、路径等工具
   └─ prompts: 提示词模板
```
