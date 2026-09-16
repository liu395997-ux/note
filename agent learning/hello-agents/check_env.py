r"""
Hello-Agents 环境自检脚本

用法:
    .\.venv\Scripts\python.exe check_env.py

会依次检查:
    1. 依赖包是否装齐
    2. .env 是否读到密钥
    3. wttr.in 天气 API 是否通
    4. Tavily 搜索 API 是否通
    5. LLM API 是否通（没填 key 就跳过）
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Windows 控制台默认是 GBK，中文输出会乱码，这里强制用 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

OK = "[通过]"
FAIL = "[失败]"
SKIP = "[跳过]"


def check_packages() -> bool:
    print("== 1. 依赖包 ==")
    all_ok = True
    for name in ("requests", "openai", "tavily", "dotenv"):
        try:
            __import__(name)
            print(f"  {OK} {name}")
        except ImportError:
            print(f"  {FAIL} {name} 未安装")
            all_ok = False
    return all_ok


def check_keys() -> tuple[str | None, str | None]:
    print("\n== 2. .env 密钥 ==")
    tavily_key = os.environ.get("TAVILY_API_KEY")
    llm_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    model = os.environ.get("MODEL_NAME")

    print(f"  {OK if tavily_key else FAIL} TAVILY_API_KEY"
          + (f"（{tavily_key[:12]}...）" if tavily_key else " 未配置"))
    print(f"  {OK if llm_key else FAIL} OPENAI_API_KEY"
          + ("（已配置）" if llm_key else " 未配置"))
    print(f"  {OK if base_url else FAIL} OPENAI_BASE_URL = {base_url or '未配置'}")
    print(f"  {OK if model else FAIL} MODEL_NAME = {model or '未配置'}")
    return tavily_key, (llm_key if llm_key and base_url and model else None)


def check_weather() -> None:
    print("\n== 3. 天气 API (wttr.in) ==")
    try:
        import requests

        r = requests.get("https://wttr.in/Beijing?format=j1", timeout=20)
        r.raise_for_status()
        cur = r.json()["current_condition"][0]
        desc = cur["weatherDesc"][0]["value"]
        print(f"  {OK} 北京当前 {desc}，气温 {cur['temp_C']} 摄氏度")
    except Exception as e:
        print(f"  {FAIL} {type(e).__name__}: {e}")
        print("       如果是连接超时，检查网络或代理设置")


def check_tavily(tavily_key: str | None) -> None:
    print("\n== 4. Tavily 搜索 API ==")
    if not tavily_key:
        print(f"  {SKIP} 未配置 TAVILY_API_KEY")
        return
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=tavily_key)
        res = client.search(
            query="北京 晴天 值得去的旅游景点",
            search_depth="basic",
            include_answer=True,
            max_results=3,
        )
        answer = (res.get("answer") or "").strip()
        print(f"  {OK} 搜索成功，返回 {len(res.get('results', []))} 条结果")
        if answer:
            print(f"       摘要: {answer[:120]}...")
    except Exception as e:
        print(f"  {FAIL} {type(e).__name__}: {e}")
        print("       常见原因：key 无效、额度用尽、网络不通")


def check_llm(cfg: tuple[str, str, str] | None) -> None:
    print("\n== 5. LLM API ==")
    if not cfg:
        print(f"  {SKIP} 未配置 OPENAI_API_KEY / OPENAI_BASE_URL / MODEL_NAME")
        return
    api_key, base_url, model = cfg
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "只回复两个字：你好"}],
            max_tokens=20,
        )
        print(f"  {OK} 模型 {model} 响应: {resp.choices[0].message.content!r}")
    except Exception as e:
        print(f"  {FAIL} {type(e).__name__}: {e}")
        print("       常见原因：key 无效、模型名写错、余额不足、地址不对")


def main() -> int:
    print("Hello-Agents 环境自检\n" + "=" * 40)
    print(f"Python {sys.version.split()[0]}  ({sys.executable})\n")

    check_packages()
    tavily_key, llm_cfg = check_keys()
    check_weather()
    check_tavily(tavily_key)
    check_llm(llm_cfg)

    print("\n" + "=" * 40)
    print("自检结束。第 1 章需要前四项全部通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
