"""
INDG Flexible Image Batch

Accepts 1–7 images and concatenates them into a single batched IMAGE tensor.
Optional slots are simply skipped when not connected — no dummy wiring needed.

Designed to replace the dynamic BatchImagesNode pattern used in Image Edit and
Image Prompting workflows, so the RP Interface generic patcher can treat every
input as a plain node_id → input_key → value assignment.
"""

import torch
import comfy.utils


class INDGFlexibleImageBatch:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_1": ("IMAGE",),
            },
            "optional": {
                "image_2": ("IMAGE",),
                "image_3": ("IMAGE",),
                "image_4": ("IMAGE",),
                "image_5": ("IMAGE",),
                "image_6": ("IMAGE",),
                "image_7": ("IMAGE",),
            },
        }

    RETURN_TYPES  = ("IMAGE",)
    RETURN_NAMES  = ("images",)
    FUNCTION      = "batch"
    CATEGORY      = "INDG/image"
    DESCRIPTION   = "Batch 1–7 images into a single IMAGE tensor. Unconnected slots are ignored."

    def batch(
        self,
        image_1,
        image_2=None,
        image_3=None,
        image_4=None,
        image_5=None,
        image_6=None,
        image_7=None,
    ):
        slots = [image_1, image_2, image_3, image_4, image_5, image_6, image_7]
        images = [img for img in slots if img is not None]

        if len(images) == 1:
            return (images[0],)

        # Resize any image that doesn't match image_1's spatial dimensions.
        # ComfyUI images are [B, H, W, C]; common_upscale expects [B, C, H, W].
        h, w = images[0].shape[1], images[0].shape[2]
        normalised = [images[0]]
        for img in images[1:]:
            if img.shape[1] != h or img.shape[2] != w:
                img = comfy.utils.common_upscale(
                    img.movedim(-1, 1), w, h, "bilinear", "center"
                ).movedim(1, -1)
            normalised.append(img)

        return (torch.cat(normalised, dim=0),)


NODE_CLASS_MAPPINGS        = {"INDGFlexibleImageBatch": INDGFlexibleImageBatch}
NODE_DISPLAY_NAME_MAPPINGS = {"INDGFlexibleImageBatch": "INDG Flexible Image Batch"}
