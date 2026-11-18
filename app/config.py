import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    llm: str = "foundry"  # "foundry" (Claude on Azure AI Foundry) or "fake" (offline, scripted)
    db_path: str = "data/mission_control.db"
    model: str = "claude-sonnet-5-5"  # the Foundry deployment name
    foundry_api_key: str | None = None
    foundry_resource: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            llm=os.environ.get("MC_LLM", cls.llm),
            db_path=os.environ.get("MC_DB_PATH", cls.db_path),
            model=os.environ.get("MC_MODEL", cls.model),
            foundry_api_key=os.environ.get("ANTHROPIC_FOUNDRY_API_KEY"),
            foundry_resource=os.environ.get("ANTHROPIC_FOUNDRY_RESOURCE"),
        )
