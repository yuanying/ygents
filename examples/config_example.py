#!/usr/bin/env python3
"""
Configuration Example

このスクリプトはygentsの設定ファイル読み込み機能の例です。
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from ygents.config.loader import ConfigLoader
from ygents.config.models import YgentsConfig


def create_example_config_file():
    """サンプル設定ファイルを作成"""
    config_content = """# Ygents設定ファイル例
# 環境変数も利用可能です

# LiteLLM設定 - 任意のプロバイダーに対応
litellm:
  model: "openai/gpt-3.5-turbo"  # または "anthropic/claude-3-sonnet-20240229"
  api_key: "${OPENAI_API_KEY}"  # 環境変数から読み込み
  temperature: 0.7
  max_tokens: 1000

# MCPサーバー設定（将来の拡張用）
mcpServers: {}
  # 例: 外部MCPサーバー
  # weather:
  #   url: "https://weather-api.example.com/mcp"
  # 例: ローカルMCPサーバー
  # assistant:
  #   command: "python"
  #   args: ["./assistant_server.py"]
"""

    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)

    return config_path


def example_direct_config():
    """コードで直接設定を作成する例"""
    print("=== Direct Configuration Example ===")

    # OpenAI設定例
    openai_config = YgentsConfig(
        litellm={
            "model": "openai/gpt-3.5-turbo",
            "api_key": os.getenv("OPENAI_API_KEY", "your-openai-key"),
            "temperature": 0.7,
        },
        mcp_servers={},
    )

    print("OpenAI設定:")
    print(f"  Model: {openai_config.litellm.get('model')}")
    print(
        f"  API Key: {'設定済み' if openai_config.litellm.get('api_key') else '未設定'}"
    )
    print(f"  Temperature: {openai_config.litellm.get('temperature')}")

    # Claude設定例
    claude_config = YgentsConfig(
        litellm={
            "model": "anthropic/claude-3-sonnet-20240229",
            "api_key": os.getenv("ANTHROPIC_API_KEY", "your-claude-key"),
            "temperature": 0.7,
        },
        mcp_servers={},
    )

    print("\nClaude設定:")
    print(f"  Model: {claude_config.litellm.get('model')}")
    print(
        f"  API Key: {'設定済み' if claude_config.litellm.get('api_key') else '未設定'}"
    )
    print(f"  Temperature: {claude_config.litellm.get('temperature')}")


def example_file_config():
    """設定ファイルから読み込む例"""
    print("\n=== File Configuration Example ===")

    # サンプル設定ファイルを作成
    config_path = create_example_config_file()
    print(f"設定ファイルを作成しました: {config_path}")

    try:
        # 設定ファイルから読み込み
        loader = ConfigLoader()
        config = loader.load_from_file(str(config_path))

        print("設定ファイルから読み込み成功:")
        print(f"  Model: {config.litellm.get('model', '未設定')}")
        print(f"  API Key: {'設定済み' if config.litellm.get('api_key') else '未設定'}")
        print(f"  Temperature: {config.litellm.get('temperature', '未設定')}")
        print(f"  MCP Servers: {len(config.mcp_servers)}個")

    except Exception as e:
        print(f"❌ 設定ファイル読み込みエラー: {e}")

    finally:
        # サンプルファイルを削除
        if config_path.exists():
            config_path.unlink()
            print(f"サンプル設定ファイルを削除しました: {config_path}")


def example_validation():
    """設定バリデーション例"""
    print("\n=== Configuration Validation Example ===")

    # 正常な設定
    try:
        YgentsConfig(
            litellm={
                "model": "openai/gpt-3.5-turbo",
                "api_key": "test-key",
                "temperature": 0.7,
            },
            mcp_servers={},
        )
        print("✅ 正常な設定: バリデーション通過")

    except Exception as e:
        print(f"❌ 正常な設定でエラー: {e}")

    # 空の設定でもOK
    try:
        YgentsConfig()
        print("✅ 空の設定: バリデーション通過（litellmは柔軟）")

    except Exception as e:
        print(f"❌ 空の設定でエラー: {e}")

    # 任意の設定でもOK
    try:
        YgentsConfig(
            litellm={
                "model": "custom/model",
                "custom_parameter": "value",
                "temperature": 0.8,
            },
            mcp_servers={},
        )
        print("✅ カスタム設定: バリデーション通過（litellmは任意のパラメータ対応）")

    except Exception as e:
        print(f"❌ カスタム設定でエラー: {e}")


def main():
    """メイン関数"""
    print("🔧 Ygents Configuration Examples")
    print("=" * 50)

    # 直接設定例
    example_direct_config()

    # ファイル設定例
    example_file_config()

    # バリデーション例
    example_validation()

    print("\n💡 ヒント:")
    print("- 環境変数でAPIキーを設定: export OPENAI_API_KEY='your-key'")
    print('- 設定ファイルで環境変数参照: api_key: "${OPENAI_API_KEY}"')
    print("- litellmは任意のプロバイダーと設定に対応します")
    print("- モデル名の形式: openai/gpt-4, anthropic/claude-3-sonnet-20240229")


if __name__ == "__main__":
    main()
