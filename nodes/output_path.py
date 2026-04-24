class INDGOutputPath:
    """
    Combine base_path / client / product / filename into one path string.
    Replaces the chain of PrimitiveStringMultiline + concat nodes used for
    MetaSaver filename_prefix inputs.  Empty segments are skipped.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "client":   ("STRING", {"default": ""}),
                "product":  ("STRING", {"default": ""}),
                "filename": ("STRING", {"default": "Shot001"}),
            },
            "optional": {
                "base_path": ("STRING", {"default": "ComfyUI"}),
            },
        }

    RETURN_TYPES  = ("STRING",)
    RETURN_NAMES  = ("path",)
    FUNCTION      = "build"
    CATEGORY      = "INDG/utils"
    DESCRIPTION   = (
        "Join base_path / client / product / filename into a single path string. "
        "Empty segments are skipped."
    )

    def build(self, client: str, product: str, filename: str, base_path: str = "ComfyUI") -> tuple:
        parts = [p.strip() for p in [base_path, client, product, filename] if p and p.strip()]
        return ("/".join(parts),)


NODE_CLASS_MAPPINGS        = {"INDGOutputPath": INDGOutputPath}
NODE_DISPLAY_NAME_MAPPINGS = {"INDGOutputPath": "INDG Output Path"}
