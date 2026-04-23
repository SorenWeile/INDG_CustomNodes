# INDG_CustomNodes

Custom ComfyUI nodes for the INDG Toolset.

## Node reference

| Node | Class name | Category | Short description |
|------|-----------|----------|-------------------|
| INDG Flexible Image Batch | `INDGFlexibleImageBatch` | `INDG/image` | Batch 1–7 images into one tensor; optional slots silently skipped |
| NBP RAM Cleanup | `NBPRAMCleanup` | `INDG/utils` | Aggressively free CPU RAM at the end of a workflow |

---

## Nodes

### INDG Flexible Image Batch (`INDGFlexibleImageBatch`)

**Category:** INDG/image

Accepts 1–7 images and concatenates them into a single batched IMAGE tensor.
Unconnected optional slots are silently skipped — no dummy wiring needed.
Images with mismatched dimensions are automatically resized to match `image_1`.

Designed to replace the dynamic `BatchImagesNode` pattern so that the
RP Interface workflow builder can treat every input as a plain
`node_id → input_key → value` patch, with no special backend logic required.

**Inputs**
- `image_1` (required)
- `image_2` … `image_7` (optional)

**Output**
- `images` — batched IMAGE tensor

---

### NBP RAM Cleanup (`NBPRAMCleanup`)

**Category:** INDG/utils

Chain at the end of any workflow to aggressively free CPU RAM.
Clears PromptExecutor node-output caches, unloads models from VRAM,
runs Python GC, and returns freed pages to the OS via tcmalloc or libc.

Optional `passthrough_image` input lets you connect it inline without
breaking the graph.

---

## Installation

Clone into your ComfyUI `custom_nodes` directory:

```bash
cd /ComfyUI/custom_nodes
git clone https://github.com/SorenWeile/INDG_CustomNodes.git
```

No extra dependencies required beyond what ComfyUI already provides.
`psutil` is optional — install it for RAM usage stats in the NBP RAM Cleanup node.
