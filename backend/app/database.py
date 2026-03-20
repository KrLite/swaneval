import json
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings

# 异步数据库引擎 / Async database engine
# 使用 asyncpg 驱动连接 PostgreSQL / Connect to PostgreSQL using asyncpg driver
engine = create_async_engine(settings.DATABASE_URL, echo=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话 / Get database session

    依赖注入函数，用于在API路由中获取数据库会话。
    Dependency injection function to get database session in API routes.

    Yields:
        AsyncSession: 异步数据库会话 / Async database session
    """
    async with AsyncSession(engine) as session:
        yield session


async def init_db():
    """
    Initialize database.

    Skips create_all when Alembic manages the schema (alembic_version table exists).
    For fresh dev without migrations, creates tables from SQLModel metadata.
    """
    from sqlalchemy import inspect

    async with engine.begin() as conn:
        has_alembic = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).has_table("alembic_version")
        )
        if not has_alembic:
            await conn.run_sync(SQLModel.metadata.create_all)


# 预置数据集定义 / Preset dataset definitions
# hf_id: HuggingFace dataset ID used for downloading content on demand
PRESET_DATASETS = [
    {
        "name": "GSM8K",
        "description": "Grade School Math 8K — 8500道小学数学应用题，评估模型的多步数学推理能力",
        "hf_id": "openai/gsm8k",
        "split": "test",
        "format": "jsonl",
        "tags": "math,reasoning,preset",
    },
    {
        "name": "MATH",
        "description": "12500道竞赛级数学题，涵盖代数、几何、数论等7个类别，评估高级数学推理",
        "hf_id": "hendrycks/competition_math",
        "split": "test",
        "format": "jsonl",
        "tags": "math,reasoning,competition,preset",
    },
    {
        "name": "BBH",
        "description": "BIG-Bench Hard — 23项挑战性任务，评估模型的逻辑推理、常识和语言理解能力",
        "hf_id": "lukaemon/bbh",
        "split": "test",
        "format": "jsonl",
        "tags": "reasoning,logic,preset",
    },
    {
        "name": "HumanEval",
        "description": "164道 Python 编程题，评估模型的代码生成能力（Pass@k 指标）",
        "hf_id": "openai/openai_humaneval",
        "split": "test",
        "format": "jsonl",
        "tags": "code,python,preset",
    },
    {
        "name": "MBPP",
        "description": "Mostly Basic Python Problems — 974道 Python 编程题，评估基础代码生成能力",
        "hf_id": "google-research-datasets/mbpp",
        "split": "test",
        "format": "jsonl",
        "tags": "code,python,preset",
    },
    {
        "name": "AlpacaEval",
        "description": "805条指令，评估模型的指令跟随和开放式生成质量，常用于对话模型对比",
        "hf_id": "tatsu-lab/alpaca_eval",
        "split": "eval",
        "format": "jsonl",
        "tags": "instruction,chat,preset",
    },
    {
        "name": "MT-Bench",
        "description": "80组多轮对话题目，涵盖写作、推理、数学等8个类别，评估多轮对话能力",
        "hf_id": "HuggingFaceH4/mt_bench_prompts",
        "split": "train",
        "format": "jsonl",
        "tags": "chat,multi-turn,preset",
    },
    {
        "name": "LongBench",
        "description": "多任务长文本理解基准，涵盖摘要、问答、代码补全等6大类21个子任务",
        "hf_id": "THUDM/LongBench",
        "split": "test",
        "format": "jsonl",
        "tags": "long-context,comprehension,preset",
    },
]



# 预置评测标准定义 / Preset evaluation criteria definitions
PRESET_CRITERIA = [
    {
        "name": "精确匹配 (Exact Match)",
        "type": "preset",
        "config_json": '{"metric": "exact_match"}',
        "description": "输出必须与预期答案完全一致（去除首尾空白后比较）",
    },
    {
        "name": "包含匹配 (Contains)",
        "type": "preset",
        "config_json": '{"metric": "contains"}',
        "description": "输出中必须包含预期答案字符串",
    },
    {
        "name": "数值接近 (Numeric)",
        "type": "preset",
        "config_json": '{"metric": "numeric", "tolerance": 0.01}',
        "description": "从输出中提取数值，在容差范围内与预期值比较",
    },
    {
        "name": "BLEU",
        "type": "preset",
        "config_json": '{"metric": "bleu"}',
        "description": "基于 n-gram 重叠度的翻译/生成质量评估（BLEU-4），适用于翻译和文本生成任务",
    },
    {
        "name": "ROUGE-L",
        "type": "preset",
        "config_json": '{"metric": "rouge_l"}',
        "description": "基于最长公共子序列的摘要质量评估，适用于摘要和长文本生成任务",
    },
    {
        "name": "F1 分数",
        "type": "preset",
        "config_json": '{"metric": "f1"}',
        "description": "Token 级别的 F1 分数（精确率与召回率的调和平均值），适用于问答和信息抽取",
    },
    {
        "name": "余弦相似度 (Cosine Similarity)",
        "type": "preset",
        "config_json": '{"metric": "cosine_similarity"}',
        "description": "基于字符 n-gram 的余弦相似度，衡量文本整体相似程度",
    },
    {
        "name": "Pass@k (k=1)",
        "type": "preset",
        "config_json": '{"metric": "exact_match"}',
        "description": "代码生成 Pass@1 — 单次生成的通过率。配合重复次数 > 1 使用以计算 Pass@k",
    },
    {
        "name": "LLM 评判 (LLM-as-a-Judge)",
        "type": "llm_judge",
        "config_json": json.dumps({
            "system_prompt": "你是一个严格的评估专家。"
            "请根据预期答案与实际输出的匹配程度，给出 0 到 1 之间的评分。只返回一个数字。"
        }),
        "description": "使用大模型作为裁判评估输出质量，需在任务中配置裁判模型",
    },
    {
        "name": "ELO 评分 (ELO Rating)",
        "type": "llm_judge",
        "config_json": json.dumps({
            "system_prompt": "你是一个公正的评委。请比较以下两段回答的质量。"
            "优于预期返回 0.7-1.0，相当返回 0.4-0.6，较差返回 0.0-0.3。只返回一个数字。"
        }),
        "description": "基于 LLM 对比评判的 ELO 竞技评分，适用于开放式生成质量的相对排名",
    },
    {
        "name": "困惑度 (Perplexity)",
        "type": "llm_judge",
        "config_json": json.dumps({
            "system_prompt": "你是一个语言模型专家。请评估以下文本的流畅度和连贯性。"
            "1.0 表示完美流畅，0.0 表示完全不连贯。只返回一个 0-1 的数字。"
        }),
        "description": "通过 LLM 评判近似估计困惑度——评估输出的流畅性和连贯性",
    },
]


