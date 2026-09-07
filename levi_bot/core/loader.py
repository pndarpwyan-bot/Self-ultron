"""Fault-isolated plugin discovery."""
from __future__ import annotations

import importlib
import logging
import os
from dataclasses import dataclass, field

from aiogram import Dispatcher

logger = logging.getLogger(__name__)

PLUGIN_MODULES = [
    "plugins.profile.plugin", "plugins.autoreply.plugin", "plugins.filter.plugin",
    "plugins.reaction.plugin", "plugins.scheduler.plugin", "plugins.forward.plugin",
    "plugins.content.plugin", "plugins.fonts.plugin", "plugins.media.plugin",
    "plugins.groups.plugin", "plugins.ai.plugin", "plugins.tools.plugin",
    "plugins.games.plugin", "plugins.meow.plugin",
]


@dataclass(slots=True)
class PluginReport:
    loaded: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)


def load_plugins(dispatcher: Dispatcher) -> PluginReport:
    report = PluginReport()
    disabled = {name.strip().lower() for name in os.getenv("DISABLED_PLUGINS", "").split(",") if name.strip()}
    for module_name in PLUGIN_MODULES:
        short_name = module_name.split(".")[1]
        if short_name in disabled:
            logger.info("Plugin disabled by configuration: %s", short_name)
            continue
        try:
            module = importlib.import_module(module_name)
            router = getattr(module, "router")
            dispatcher.include_router(router)
            report.loaded.append(module_name)
        except Exception as exc:
            logger.exception("Plugin disabled after load failure: %s", module_name)
            report.failed[module_name] = f"{type(exc).__name__}: {exc}"
    return report
