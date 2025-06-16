#!/usr/bin/env python3
"""
Simple Agent Example

このスクリプトはygentsのAgentクラスを使用した基本的な例です。
OpenAI APIキーを環境変数に設定してからご利用ください。

使用方法:
    export OPENAI_API_KEY="your-openai-api-key"
    python examples/simple_agent.py
"""

import asyncio
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from ygents.agent.core import Agent
from ygents.config.models import LLMConfig, OpenAIConfig, YgentsConfig


async def simple_chat_example():
    """シンプルなチャット例"""
    print("=== Simple Agent Example ===")
    print("Agentとの簡単な対話例を実行します。\n")

    # 設定を作成
    config = YgentsConfig(
        llm=LLMConfig(
            provider="openai",
            openai=OpenAIConfig(
                api_key=os.getenv("OPENAI_API_KEY", ""), model="gpt-4o"
            ),
        ),
        mcp_servers={},  # MCPサーバーなしで実行
    )

    # APIキーの確認
    if not config.llm.openai.api_key:
        print("❌ エラー: OPENAI_API_KEYが設定されていません")
        print("以下のコマンドでAPIキーを設定してください:")
        print("export OPENAI_API_KEY='your-openai-api-key'")
        return

    try:
        async with Agent(config) as agent:
            print("✅ Agent初期化完了")
            print("💭 質問: 'こんにちは！今日の天気について教えて。'")
            print("📝 応答:")

            # Agentに質問（デモのため回数制限付き）
            user_input = "こんにちは！今日の天気について教えて。完了したら'完了しました'と言ってください。"

            loop_count = 0
            max_loops = 3  # デモのための制限

            async for chunk in agent.run(user_input):
                loop_count += 1
                if loop_count > max_loops:
                    print("\n📊 デモのため処理を制限しました")
                    break
                if chunk.get("type") == "content":
                    print(chunk["content"], end="", flush=True)
                elif chunk.get("type") == "error":
                    print(f"\n❌ エラー: {chunk['content']}")
                elif chunk.get("type") == "status":
                    print(f"\n📊 ステータス: {chunk['content']}")

            print("\n\n✅ 対話完了")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")


async def interactive_chat():
    """インタラクティブなチャット例"""
    print("\n=== Interactive Agent Chat ===")
    print("Agentとのインタラクティブな対話を開始します。")
    print("'quit' または 'exit' で終了します。\n")

    # 設定を作成
    config = YgentsConfig(
        llm=LLMConfig(
            provider="openai",
            openai=OpenAIConfig(
                api_key=os.getenv("OPENAI_API_KEY", ""), model="gpt-3.5-turbo"
            ),
        ),
        mcp_servers={},
    )

    if not config.llm.openai.api_key:
        print("❌ エラー: OPENAI_API_KEYが設定されていません")
        return

    try:
        async with Agent(config) as agent:
            print("✅ Agent準備完了! 何でもお聞きください。\n")

            while True:
                # ユーザー入力
                try:
                    user_input = input("あなた: ")
                    if user_input.lower() in ["quit", "exit", "q"]:
                        break

                    if not user_input.strip():
                        continue

                    # 自動完了キーワードを追加
                    user_input_with_completion = (
                        f"{user_input} 回答が完了したら'完了しました'と言ってください。"
                    )

                    print("Agent: ", end="", flush=True)

                    # Agent応答
                    async for chunk in agent.run(user_input_with_completion):
                        if chunk.get("type") == "content":
                            print(chunk["content"], end="", flush=True)
                        elif chunk.get("type") == "error":
                            print(f"\n❌ エラー: {chunk['content']}")
                        elif chunk.get("type") == "status":
                            print(f"\n📊 {chunk['content']}")

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
    print("🤖 Ygents Agent Example")
    print("=" * 50)

    # シンプルなチャット例
    await simple_chat_example()

    # インタラクティブチャットの実行確認
    try:
        choice = input("\nインタラクティブチャットを試しますか？ (y/n): ")
        if choice.lower() in ["y", "yes"]:
            await interactive_chat()
    except (KeyboardInterrupt, EOFError):
        pass

    print("\n👋 ありがとうございました！")


if __name__ == "__main__":
    asyncio.run(main())
