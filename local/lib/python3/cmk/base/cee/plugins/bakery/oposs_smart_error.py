#!/usr/bin/env python3
"""
CheckMK Bakery Plugin for SMART Error Monitoring
Automatically distributes the agent plugin to monitored hosts
Compatible with CheckMK 2.3
"""

import json
from pathlib import Path
from typing import Any, Dict

from cmk.base.plugins.bakery.bakery_api.v1 import (
    register,
    Plugin,
    PluginConfig,
    OS,
)


def get_oposs_smart_error_files(conf: Dict[str, Any]):
    """Files function for OPOSS SMART error bakery plugin"""
    if conf is None or not conf.get("enabled", True):
        return
    
    # Get configuration values
    interval = int(conf.get("interval", 0))
    timeout = conf.get("timeout", 30)

    # Generate config file in JSON format
    config_content = json.dumps({"timeout": int(timeout)})
    yield PluginConfig(
        base_os=OS.LINUX,
        target=Path("oposs_smart_error.json"),
        lines=config_content.splitlines(),
    )

    # Generate plugin using source reference
    # This will automatically find the agent plugin in local/share/check_mk/agents/plugins/
    yield Plugin(
        base_os=OS.LINUX,
        source=Path('oposs_smart_error'),
        target=Path('oposs_smart_error'),
        interval=interval,
    )


# Register the bakery plugin using the official API
register.bakery_plugin(
    name="oposs_smart_error",
    files_function=get_oposs_smart_error_files,
)