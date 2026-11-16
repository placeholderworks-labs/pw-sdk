import os
import tomllib
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field

CONFIG_ENV = "PW_CONFIG"


class ClientSection(BaseModel):
    model_config = ConfigDict(extra="allow")
    slug: str = "default"
    name: str = "PlaceholderWorks"
    timezone: str = "Asia/Kolkata"
    country: str = "IN"


class IntakeSpec(BaseModel):
    model_config = ConfigDict(extra="allow")
    adapter: str = "builtin.canonical"
    adapter_config: dict[str, Any] = Field(default_factory=dict)
    journey: str | None = None
    agent: str | None = None
    name: str | None = None
    enabled: bool = True
    contact_hours: tuple[str, str] | None = None


class ClientConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    path: Path | None = None
    client: ClientSection = Field(default_factory=ClientSection)
    branding: dict[str, Any] = Field(default_factory=dict)
    llm: dict[str, Any] = Field(default_factory=dict)
    voice: dict[str, Any] = Field(default_factory=dict)
    whatsapp: dict[str, Any] = Field(default_factory=dict)
    email: dict[str, Any] = Field(default_factory=dict)
    intakes: dict[str, IntakeSpec] = Field(default_factory=dict)
    journeys: dict[str, dict[str, Any]] = Field(default_factory=dict)
    policy: dict[str, Any] = Field(default_factory=dict)
    env: dict[str, Any] = Field(default_factory=dict)

    def get(self, dotted: str, default: Any = None) -> Any:
        node: Any = self.model_dump()
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    @property
    def root(self) -> Path:
        return self.path.parent if self.path else Path.cwd()


def find(path: str | Path | None = None) -> Path | None:
    candidate = path or os.getenv(CONFIG_ENV)
    if candidate:
        resolved = Path(candidate).expanduser().resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"config file not found: {resolved}")
        return resolved
    local = Path.cwd() / "pw.toml"
    return local if local.exists() else None


def load(path: str | Path | None = None, *, dotenv: bool = True) -> ClientConfig:
    found = find(path)
    if found is None:
        if dotenv:
            load_dotenv(Path.cwd() / ".env")
        return ClientConfig()
    if dotenv:
        load_dotenv(found.parent / ".env")
    data = tomllib.loads(found.read_text())
    config = ClientConfig.model_validate({**data, "path": found})
    os.environ.setdefault(CONFIG_ENV, str(found))
    return config


def apply_env(config: ClientConfig, mapping: dict[str, str] | None = None) -> dict[str, str]:
    applied: dict[str, str] = {}
    pairs = {key: value for key, value in config.env.items()}
    for env_key, dotted in (mapping or {}).items():
        value = config.get(dotted)
        if value is not None:
            pairs.setdefault(env_key, value)
    for key, value in pairs.items():
        text = str(value).lower() if isinstance(value, bool) else str(value)
        if key not in os.environ:
            os.environ[key] = text
            applied[key] = text
    return applied


_current: ClientConfig | None = None


def current() -> ClientConfig:
    global _current
    if _current is None:
        _current = load()
    return _current


def use(config: ClientConfig) -> ClientConfig:
    global _current
    _current = config
    return config
