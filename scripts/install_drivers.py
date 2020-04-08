#!/usr/bin/env python3
import importlib
import pkgutil

discovered_plugins = {
    name: importlib.import_module(name)
    for finder, name, ispkg in pkgutil.iter_modules()
    if name.startswith("scos_")
}

for name, module in discovered_plugins.items():
    #discover = importlib.import_module(name + ".discover")
    if hasattr(module, "scripts"):
        scripts = importlib.import_module(name + ".scripts")
        if hasattr(scripts, "install_drivers"):
            scripts.install_drivers()
