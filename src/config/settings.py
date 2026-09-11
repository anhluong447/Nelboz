from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict
import json

try:
    import yaml
except ImportError:
    yaml = None


@dataclass(frozen=True)
class TargetWindowConfig:
    title_pattern: str = ".*Chrome.*"
    tab_title_pattern: str = ".*Facebook.*"
    dpi_aware: bool = True


@dataclass(frozen=True)
class FlowAConfig:
    max_comments_per_hour: int = 5
    min_interval_seconds: int = 300
    scroll_min_px: int = 300
    scroll_max_px: int = 600


@dataclass(frozen=True)
class FlowBConfig:
    max_replies_per_hour: int = 3
    max_replies_per_thread: int = 2
    min_interval_seconds: int = 400
    indent_level_px: int = 45


@dataclass(frozen=True)
class InputConfig:
    mouse_min_speed: float = 400.0
    mouse_max_speed: float = 1200.0
    bezier_deviation_max: float = 60.0
    overshoot_chance: float = 0.25
    typing_wpm_min: int = 45
    typing_wpm_max: int = 95
    action_delay_min_sec: float = 0.8
    action_delay_max_sec: float = 2.5


@dataclass(frozen=True)
class AppConfig:
    name: str = "FacebookAutoBot"
    log_level: str = "INFO"
    target_window: TargetWindowConfig = field(default_factory=TargetWindowConfig)
    flow_a: FlowAConfig = field(default_factory=FlowAConfig)
    flow_b: FlowBConfig = field(default_factory=FlowBConfig)
    input: InputConfig = field(default_factory=InputConfig)

    @classmethod
    def load_from_yaml(cls, path: Path | str) -> "AppConfig":
        file_path = Path(path)
        if not file_path.exists():
            return cls()

        data: Dict[str, Any] = {}
        with open(file_path, "r", encoding="utf-8") as f:
            if yaml is not None:
                data = yaml.safe_load(f) or {}

        target_win = TargetWindowConfig(**data.get("target_window", {}))
        flow_a = FlowAConfig(**data.get("flow_a", {}))
        flow_b = FlowBConfig(**data.get("flow_b", {}))
        input_cfg = InputConfig(**data.get("input", {}))
        app_data = data.get("app", {})

        return cls(
            name=app_data.get("name", "FacebookAutoBot"),
            log_level=app_data.get("log_level", "INFO"),
            target_window=target_win,
            flow_a=flow_a,
            flow_b=flow_b,
            input=input_cfg,
        )
