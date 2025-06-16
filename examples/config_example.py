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

from ygents.config.models import YgentsConfig, LLMConfig, OpenAIConfig, ClaudeConfig
from ygents.config.loader import ConfigLoader


def create_example_config_file():
    """サンプル設定ファイルを作成"""
    config_content = """# Ygents設定ファイル例
# 環境変数も利用可能です

llm:
  provider: "openai"  # "openai" または "claude"
  openai:
    api_key: "${OPENAI_API_KEY}"  # 環境変数から読み込み
    model: "gpt-3.5-turbo"
  claude:
    api_key: "${ANTHROPIC_API_KEY}"  # 環境変数から読み込み
    model: "claude-3-sonnet-20240229"

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
        llm=LLMConfig(
            provider="openai",
            openai=OpenAIConfig(
                api_key=os.getenv("OPENAI_API_KEY", "your-openai-key"),
                model="gpt-3.5-turbo"
            )
        ),
        mcp_servers={}
    )
    
    print("OpenAI設定:")
    print(f"  Provider: {openai_config.llm.provider}")
    print(f"  Model: {openai_config.llm.openai.model}")
    print(f"  API Key: {'設定済み' if openai_config.llm.openai.api_key else '未設定'}")
    
    # Claude設定例
    claude_config = YgentsConfig(
        llm=LLMConfig(
            provider="claude",
            claude=ClaudeConfig(
                api_key=os.getenv("ANTHROPIC_API_KEY", "your-claude-key"),
                model="claude-3-sonnet-20240229"
            )
        ),
        mcp_servers={}
    )
    
    print("\nClaude設定:")
    print(f"  Provider: {claude_config.llm.provider}")
    print(f"  Model: {claude_config.llm.claude.model}")
    print(f"  API Key: {'設定済み' if claude_config.llm.claude.api_key else '未設定'}")


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
        print(f"  Provider: {config.llm.provider}")
        
        if config.llm.provider == "openai" and config.llm.openai:
            print(f"  OpenAI Model: {config.llm.openai.model}")
            print(f"  OpenAI API Key: {'設定済み' if config.llm.openai.api_key else '未設定'}")
        
        if config.llm.provider == "claude" and config.llm.claude:
            print(f"  Claude Model: {config.llm.claude.model}")
            print(f"  Claude API Key: {'設定済み' if config.llm.claude.api_key else '未設定'}")
        
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
        valid_config = YgentsConfig(
            llm=LLMConfig(
                provider="openai",
                openai=OpenAIConfig(
                    api_key="test-key",
                    model="gpt-3.5-turbo"
                )
            ),
            mcp_servers={}
        )
        print("✅ 正常な設定: バリデーション通過")
        
    except Exception as e:
        print(f"❌ 正常な設定でエラー: {e}")
    
    # 不正な設定（プロバイダー設定不一致）
    try:
        invalid_config = YgentsConfig(
            llm=LLMConfig(
                provider="openai",  # openaiを指定
                claude=ClaudeConfig(  # でもclaude設定を提供
                    api_key="test-key",
                    model="claude-3-sonnet-20240229"
                )
                # openai設定がない
            ),
            mcp_servers={}
        )
        print("❌ 不正な設定がバリデーションを通過してしまいました")
        
    except Exception as e:
        print(f"✅ 不正な設定: 期待通りエラー - {e}")


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
    print("- 設定ファイルで環境変数参照: api_key: \"${OPENAI_API_KEY}\"")
    print("- プロバイダーに応じた設定が必要です")


if __name__ == "__main__":
    main()