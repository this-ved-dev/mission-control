from app.config import Settings


def test_settings_read_from_env(monkeypatch):
    monkeypatch.setenv("MC_LLM", "fake")
    monkeypatch.setenv("MC_DB_PATH", "/tmp/x.db")
    monkeypatch.setenv("MC_MODEL", "my-deployment")
    monkeypatch.setenv("ANTHROPIC_FOUNDRY_API_KEY", "k")
    monkeypatch.setenv("ANTHROPIC_FOUNDRY_RESOURCE", "r")
    assert Settings.from_env() == Settings("fake", "/tmp/x.db", "my-deployment", "k", "r")
