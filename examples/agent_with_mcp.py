#!/usr/bin/env python3
"""
Agent with MCP Example

このスクリプトはMCPサーバーと連携するAgentの例です。
事前にfastmcpをインストールし、OpenAI APIキーを設定してください。

インストール:
    pip install fastmcp

使用方法:
    export OPENAI_API_KEY="your-openai-api-key"
    python -W ignore examples/agent_with_mcp.py
"""

# !/usr/bin/env python3

# Warningsを最初に抑制
import os
import warnings

os.environ["PYTHONWARNINGS"] = "ignore"
warnings.simplefilter("ignore")
# 全ての警告を抑制
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*")
import logging

# Rich/fastmcpのERRORログも抑制
logging.getLogger("rich").setLevel(logging.CRITICAL)
logging.getLogger("fastmcp").setLevel(logging.CRITICAL)

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from ygents.agent.core import Agent
from ygents.agent.models import (
    ContentChunk,
    ErrorMessage,
    ToolError,
    ToolInput,
    ToolResult,
)
from ygents.config.models import YgentsConfig


def create_inmemory_mcp_config():
    """InMemory MCPサーバー設定を作成"""
    try:
        import fastmcp

        # InMemory MCPサーバーを作成
        server = fastmcp.FastMCP(name="ExampleServer")

        @server.tool()
        def get_weather(city: str) -> str:
            """指定された都市の天気を取得"""
            # 簡単なモック天気データ
            weather_data = {
                "tokyo": "東京: 晴れ、気温25°C",
                "osaka": "大阪: 曇り、気温23°C",
                "kyoto": "京都: 雨、気温20°C",
                "yokohama": "横浜: 晴れ、気温24°C",
            }

            city_lower = city.lower()
            if city_lower in weather_data:
                return weather_data[city_lower]
            else:
                return f"{city}: 天気データが見つかりません"

        @server.tool()
        def calculate(operation: str, a: float, b: float) -> float:
            """基本的な計算を実行"""
            if operation == "add":
                return a + b
            elif operation == "subtract":
                return a - b
            elif operation == "multiply":
                return a * b
            elif operation == "divide":
                if b == 0:
                    raise ValueError("ゼロで割ることはできません")
                return a / b
            else:
                raise ValueError(f"未知の操作: {operation}")

        @server.tool()
        def get_time() -> str:
            """現在時刻を取得"""
            from datetime import datetime

            return datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

        return server

    except ImportError:
        print("❌ fastmcpがインストールされていません")
        print("以下のコマンドでインストールしてください:")
        print("pip install fastmcp")
        return None


async def mcp_agent_example():
    """MCPサーバー連携Agent例"""
    print("=== Agent with MCP Example ===")
    print("MCPサーバーと連携するAgentの例を実行します。\n")

    # InMemory MCPサーバーを作成
    mcp_server = create_inmemory_mcp_config()
    if not mcp_server:
        return

    # 設定を作成（MCPサーバーあり）
    config = YgentsConfig(
        litellm={
            "model": "openai/gpt-4o",
            "api_key": os.getenv("OPENAI_API_KEY", "")
        },
    )

    # APIキーの確認
    if not config.litellm.get("api_key"):
        print("❌ エラー: OPENAI_API_KEYが設定されていません")
        print("以下のコマンドでAPIキーを設定してください:")
        print("export OPENAI_API_KEY='your-openai-api-key'")
        return

    try:
        async with Agent(config) as agent:
            # InMemory MCPサーバーを手動で注入（テスト用）
            import fastmcp

            client = fastmcp.Client(mcp_server)
            async with client:
                agent._mcp_client = client
                agent._mcp_client_connected = True

                print("✅ Agent + MCP初期化完了")

                # 利用可能なツールを表示
                try:
                    tools = await client.list_tools()
                    print(f"📋 利用可能なツール: {[tool.name for tool in tools]}")
                except Exception as e:
                    print(f"⚠️  ツール一覧取得エラー: {e}")

                # 各種質問例
                questions = [
                    "東京の天気を教えて",
                    "10 + 5 を計算して",
                    "現在時刻を教えて",
                    "大阪の天気はどう？",
                ]

                for i, question in enumerate(questions, 1):
                    print(f"\n--- 質問 {i} ---")
                    print(f"💭 質問: {question}")
                    print("📝 応答: ", end="", flush=True)

                    # 自動完了キーワードを追加
                    question_with_completion = (
                        f"{question} 完了したら'完了しました'と言ってください。"
                    )

                    try:
                        async for chunk in agent.run(question_with_completion):
                            if isinstance(chunk, ContentChunk):
                                print(chunk.content, end="", flush=True)
                            elif isinstance(chunk, ToolInput):
                                print(f"\n🔧 ツール実行: {chunk.tool_name}")
                                print(f"   引数: {chunk.arguments}")
                            elif isinstance(chunk, ToolResult):
                                print(f"✅ 結果: {chunk.result}")
                            elif isinstance(chunk, ToolError):
                                print(f"❌ ツールエラー: {chunk.content}")
                            elif isinstance(chunk, ErrorMessage):
                                print(f"\n❌ エラー: {chunk.content}")

                        print("")

                    except Exception as e:
                        print(f"\n❌ 質問処理エラー: {e}")

                print("\n✅ MCP連携テスト完了")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")


async def interactive_mcp_chat():
    """MCPサーバー連携のインタラクティブチャット"""
    print("\n=== Interactive MCP Chat ===")
    print("MCPツールを使用できるインタラクティブチャットです。")
    print("利用可能なツール: get_weather, calculate, get_time")
    print("'quit' または 'exit' で終了します。\n")

    # InMemory MCPサーバーを作成
    mcp_server = create_inmemory_mcp_config()
    if not mcp_server:
        return

    # 設定を作成
    config = YgentsConfig(
        litellm={
            "model": "openai/gpt-4o",
            "api_key": os.getenv("OPENAI_API_KEY", "")
        },
        mcp_servers={"example_server": {}},
    )

    if not config.litellm.get("api_key"):
        print("❌ エラー: OPENAI_API_KEYが設定されていません")
        return

    try:
        async with Agent(config) as agent:
            import fastmcp

            client = fastmcp.Client(mcp_server)
            async with client:
                agent._mcp_client = client
                agent._mcp_client_connected = True

                print("✅ MCP Agent準備完了! ツールを使った質問をしてください。")
                print("例: '東京の天気は？', '10 × 5 は？', '今何時？'\n")

                while True:
                    try:
                        user_input = input("あなた: ")
                        if user_input.lower() in ["quit", "exit", "q"]:
                            break

                        if not user_input.strip():
                            continue

                        # 自動完了キーワードを追加
                        user_input_with_completion = (
                            f"{user_input} 完了したら'完了しました'と言ってください。"
                        )

                        print("Agent: ", end="", flush=True)

                        async for chunk in agent.run(user_input_with_completion):
                            if isinstance(chunk, ContentChunk):
                                print(chunk.content, end="", flush=True)
                            elif isinstance(chunk, ToolInput):
                                print(f"\n🔧 {chunk.tool_name} を実行中...")
                            elif isinstance(chunk, ToolResult):
                                print("✅ 完了")
                            elif isinstance(chunk, ToolError):
                                print(f"\n❌ ツールエラー: {chunk.content}")
                            elif isinstance(chunk, ErrorMessage):
                                print(f"\n❌ エラー: {chunk.content}")

                        print("\n")

                    except KeyboardInterrupt:
                        print("\n\n👋 チャットを終了します。")
                        break
                    except EOFError:
                        print("\n\n👋 チャットを終了します。")
                        break

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")


async def main():
    """メイン関数"""
    print("🤖 Ygents Agent with MCP Example")
    print("=" * 50)

    # MCP連携例
    await mcp_agent_example()

    # インタラクティブMCPチャットの実行確認
    try:
        choice = input("\nインタラクティブMCPチャットを試しますか？ (y/n): ")
        if choice.lower() in ["y", "yes"]:
            await interactive_mcp_chat()
    except KeyboardInterrupt:
        pass

    print("\n👋 ありがとうございました！")


if __name__ == "__main__":
    asyncio.run(main())
