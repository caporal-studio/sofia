import os
import sys
import asyncio
import types
import importlib

def apply_runtime_fixes():
    # Permite execução paralela com MKL no Windows
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    # Corrige erro 'no running event loop' em ambientes assíncronos
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    # Corrige introspecção problemática do torch.classes
    try:
        if "torch.classes" in sys.modules:
            sys.modules["torch.classes"].__path__ = types.SimpleNamespace(_path=[])
        else:
            importlib.import_module("torch.classes")
            sys.modules["torch.classes"].__path__ = types.SimpleNamespace(_path=[])
    except Exception:
        pass
