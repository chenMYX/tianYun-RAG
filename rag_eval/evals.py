import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from ragas import Dataset, experiment
from ragas.llms import llm_factory
from ragas.metrics import DiscreteMetric

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")

# Add the project root to sys.path so we can import the app module
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.query_process.agent.main_graph import query_app
from app.query_process.agent.state import create_query_default_state

openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)
llm = llm_factory("qwen3.7-max", client=openai_client)


def load_dataset():
    dataset = Dataset(
        name="test_dataset",
        backend="local/csv",
        root_dir="evals",
    )

    data_samples = [
        {
            "question": "HAK 180烫金机的使用环境温度和湿度要求是什么？",
            "grading_notes": "温度保持在10 °C和32 °C之间，湿度保持在20%和80%之间，无冷凝。",
        },
        {
            "question": "HAK 180烫金机的供电要求是什么？",
            "grading_notes": "本设备通过AC 220 V-240 V 50/60 Hz电源供电，请勿将本设备连接到直流电源或逆变器。",
        },
        {
            "question": "清洁HAK 180烫金机内部之前需要做什么？",
            "grading_notes": "先拔掉电源线，拔出电源线时不要拉电线，而是捏住插头往外拔。",
        },
        {
            "question": "使用HAK 180烫金机之后短时间内，设备内部零件有什么特点？需要注意什么？",
            "grading_notes": "使用本设备之后短时间内，本设备的一些内部零件仍然处于极热状态。打开前盖时，请勿触摸以灰色标记的区域，存在烧伤的风险，先等待设备冷却下来，再触摸设备的内部零件。",
        },
        {
            "question": "对于使用起搏器的用户，使用HAK 180烫金机有什么注意事项？",
            "grading_notes": "本设备可能会产生弱磁场，如果您在本设备附近感觉到起搏器工作不正常，请远离本设备，并立即咨询医生。",
        },
        {
            "question": "HAK 180烫金机包装中的塑料袋有什么安全提示？",
            "grading_notes": "塑料袋并不是玩具，为避免窒息的危险，请将这些塑料袋远离婴儿和儿童，并正确弃置这些塑料袋。",
        },
        {
            "question": "搬运HAK 180烫金机的正确方法是什么？",
            "grading_notes": "提起本设备时，请使用双手抓稳本设备的两侧，如果抓住的是进纸托板和出纸盒，它们可能会掉下来，必须通过将双手放在本设备下面来搬运本设备。",
        },
        {
            "question": "清洁HAK 180烫金机时不能使用什么？应该使用什么？",
            "grading_notes": "请勿使用任何易燃物品、任何类型的喷雾剂包含酒精或氨水的有机溶剂/液体来清洁本设备的内部或外部，请改用无绒干抹布。",
        },
        {
            "question": "如果意外在HAK 180烫金机上倒入任何液体，应该怎么做？",
            "grading_notes": "请立即从电源插座拔掉设备的插头，然后联系Brother呼叫中心或您当地的Brother经销商。",
        },
        {
            "question": "使用非Brother正品烫金膜盒可能会有什么后果？",
            "grading_notes": "Brother不建议使用Brother正品烫金膜盒以外的其他品牌烫金膜盒，如果使用与本设备不兼容的耗材导致损坏本设备的任何零件，由此导致的任何维修可能不在保修范围内。",
        },
        {
            "question": "雷暴天气期间能否使用HAK 180烫金机？为什么？",
            "grading_notes": "请勿在雷暴天气期间使用本设备，存在闪电导致触电的潜在风险。",
        },
        {
            "question": "HAK 180烫金机的接地插头有什么使用要求？",
            "grading_notes": "本设备装有接地的插头，此插头只能插入接地的电源插座中，这是一项安全功能，如果您无法将插头插入到插座中，请让电工更换过时的插座，请勿试图破坏接地插头的作用。",
        },
        {
            "question": "长时间不使用HAK 180烫金机时，电源方面需要做什么处理？",
            "grading_notes": "如果您长时间不会使用本设备，请从电源插座中拔掉电源线以确保安全。",
        },
        {
            "question": "HAK 180烫金机出现异常高温、冒烟或产生强烈味道时应该怎么做？",
            "grading_notes": "请立即从电源插座拔掉设备的插头，然后联系Brother呼叫中心或您当地的Brother经销商。",
        },
        {
            "question": "能否自行维修HAK 180烫金机？为什么？",
            "grading_notes": "请勿尝试自行维修本设备，打开或拆下盖子可能使您接触到危险电压点以及带来其他风险，并且可能使您的保修失效，对于所有维修事宜，请联系Brother呼叫中心或您当地的Brother经销商。",
        }
    ]

    for sample in data_samples:
        row = {"question": sample["question"], "grading_notes": sample["grading_notes"]}
        dataset.append(row)

    # make sure to save it
    dataset.save()
    return dataset


my_metric = DiscreteMetric(
    name="correctness",
    prompt="Check if the response contains points mentioned from the grading notes and return 'pass' or 'fail'.\nResponse: {response} Grading Notes: {grading_notes}",
    allowed_values=["pass", "fail"],
)


@experiment()
async def run_experiment(row):
    state = create_query_default_state(
        session_id=str(uuid.uuid4()),
        original_query=row["question"],
        is_stream=False,
    )
    final_state = query_app.invoke(state)
    response = final_state.get("answer", "")

    score = my_metric.score(
        llm=llm,
        response=response,
        grading_notes=row["grading_notes"],
    )

    experiment_view = {
        **row,
        "response": response,
        "score": score.value,
    }
    return experiment_view


async def main():
    dataset = load_dataset()
    print("dataset loaded successfully", dataset)
    experiment_results = await run_experiment.arun(dataset)
    print("Experiment completed successfully!")
    print("Experiment results:", experiment_results)

    # Save experiment results to CSV
    experiment_results.save()
    csv_path = Path(".") / "experiments" / f"{experiment_results.name}.csv"
    print(f"\nExperiment results saved to: {csv_path.resolve()}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
