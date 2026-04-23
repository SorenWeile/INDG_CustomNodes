"""
NBP RAM Cleanup — aggressively frees CPU RAM inside the ComfyUI process.

Root causes addressed:
  1. PromptExecutor.caches holds node output references across runs, keeping
     model tensors alive so Python GC can never collect them.
  2. current_loaded_models keeps LoadedModel refs even after VRAM unload.
  3. malloc_trim(0) has no effect when tcmalloc is active via LD_PRELOAD;
     tcmalloc's own ReleaseFreeMemory must be called instead.
  4. Calling unload_all_models() BEFORE clearing refs moves 8+ GB from VRAM
     to RAM right before measurement — making the numbers look worse.
"""

import gc
import ctypes
import torch
import comfy.model_management as mm


# ── helpers ──────────────────────────────────────────────────────────────────

def _get_ram_gb():
    try:
        import psutil
        return psutil.virtual_memory().used / (1024 ** 3)
    except ImportError:
        return None


def _clear_executor_caches():
    """
    Find the live PromptExecutor via Python's object graph and clear its
    node-output caches.  These caches keep strong references to every model
    tensor loaded during the last N workflows, preventing GC from freeing them.
    """
    try:
        import execution
        for obj in gc.get_objects():
            if isinstance(obj, execution.PromptExecutor):
                for cache in obj.caches.all:
                    for attr in ("cache", "data", "_data", "outputs"):
                        store = getattr(cache, attr, None)
                        if isinstance(store, dict):
                            store.clear()
                            break
                print("[NBP RAM Cleanup] PromptExecutor caches cleared")
                return True
    except Exception as e:
        print(f"[NBP RAM Cleanup] executor cache clear failed: {e}")
    return False


def _clear_model_management():
    """
    Unload models from VRAM and drop all Python references in
    current_loaded_models so GC can actually collect the tensors.
    Note: we do NOT call unload_all_models() first because it moves weights
    from VRAM to RAM right before we try to free — spiking measured usage.
    """
    if not hasattr(mm, "current_loaded_models"):
        return
    for lm in list(mm.current_loaded_models):
        try:
            lm.model_unload()
        except Exception:
            pass
    mm.current_loaded_models.clear()
    mm.soft_empty_cache()


def _release_os_memory():
    """
    Return freed heap pages to the OS.
    tcmalloc (LD_PRELOAD) replaces malloc entirely, so libc malloc_trim(0)
    is a no-op.  Call tcmalloc's own ReleaseFreeMemory first.
    """
    for lib in ("libtcmalloc.so.4", "libtcmalloc.so.4.14", "libtcmalloc.so"):
        try:
            tc = ctypes.CDLL(lib)
            tc.MallocExtension_ReleaseFreeMemory()
            print(f"[NBP RAM Cleanup] tcmalloc ReleaseFreeMemory OK ({lib})")
            return
        except Exception:
            pass
    try:
        ctypes.CDLL("libc.so.6").malloc_trim(0)
        print("[NBP RAM Cleanup] libc malloc_trim(0) called (tcmalloc not found)")
    except Exception:
        pass


# ── node ─────────────────────────────────────────────────────────────────────

class NBPRAMCleanup:
    """
    Chain at the end of any workflow to aggressively free CPU RAM.
    Optional passthrough_image lets you connect it without breaking the graph.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {"passthrough_image": ("IMAGE",)},
        }

    RETURN_TYPES  = ("IMAGE",)
    RETURN_NAMES  = ("passthrough_image",)
    FUNCTION      = "cleanup"
    CATEGORY      = "INDG/utils"
    OUTPUT_NODE   = True

    def cleanup(self, passthrough_image=None):
        before = _get_ram_gb()

        _clear_executor_caches()
        _clear_model_management()

        gc.collect()
        gc.collect()

        _release_os_memory()

        after = _get_ram_gb()
        if before is not None and after is not None:
            freed = before - after
            print(f"[NBP RAM Cleanup] {before:.1f} GB → {after:.1f} GB  "
                  f"({'freed' if freed >= 0 else 'delta'}: {abs(freed):.1f} GB)")
        else:
            print("[NBP RAM Cleanup] done  (pip install psutil for usage stats)")

        return (passthrough_image,)


NODE_CLASS_MAPPINGS        = {"NBPRAMCleanup": NBPRAMCleanup}
NODE_DISPLAY_NAME_MAPPINGS = {"NBPRAMCleanup": "NBP RAM Cleanup"}
