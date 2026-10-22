"""Configuration module for SentinelMCP using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Global configuration settings for SentinelMCP."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General Environment
    environment: str = Field(default="development", description="Runtime environment")
    log_level: str = Field(default="INFO", description="Logging level")

    # LLM Settings (Free Tier / Fallback)
    llm_provider: str = Field(default="groq", description="LLM provider: groq, gemini, or fallback")
    gemini_api_key: str = Field(default="", description="Google Gemini API Key (free tier)")
    groq_api_key: str = Field(default="", description="Groq API Key (free tier)")
    llm_model: str = Field(default="qwen/qwen3.8-27b", description="Model name (e.g. qwen/qwen3.8-27b for Groq, gemini-2.5-flash-lite for Gemini)")

    # Kubernetes Cluster
    k8s_in_cluster: bool = Field(default=False, description="Whether running inside K3s/K8s pod")
    k8s_namespace: str = Field(default="default", description="Target Kubernetes namespace")
    k8s_context: str = Field(default="", description="Kubeconfig context name if running externally")

    # Jaeger APM & Observability
    telemetry_api_url: str = Field(default="http://localhost:16686", description="Jaeger / OpenTelemetry APM endpoint")
    telemetry_api_key: str = Field(default="", description="Telemetry API token if authentication is enabled")

    # Safety Guardrails
    sentinel_dry_run: bool = Field(default=True, description="Enforce dry-run mode for remediations")
    max_restarts_per_hour: int = Field(default=3, description="Maximum deployment restarts allowed per hour")
    max_replicas_limit: int = Field(default=10, description="Upper bound for replica scaling")
    min_replicas_limit: int = Field(default=1, description="Lower bound for replica scaling")
    remediation_cooldown_seconds: int = Field(default=120, description="Minimum seconds between actions on same target")

    # MCP Server
    mcp_server_name: str = Field(default="sentinel-mcp-sre", description="Name of the MCP server")
    mcp_server_host: str = Field(default="0.0.0.0", description="Host address for MCP server HTTP/SSE")
    mcp_server_port: int = Field(default=8000, description="Port for MCP server HTTP/SSE")


settings = Settings()
