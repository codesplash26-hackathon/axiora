"""
Root-level gateway for DiCE setup module.
Exposes all components from ml_core.dice_setup.
"""
from ml_core.dice_setup import (
    SafeModelWrapper,
    CANONICAL_FEATURES,
    load_schema,
    get_actionable_features,
    get_permitted_range,
    init_dice_framework,
    get_dice_data,
    get_dice_model,
    get_genetic_explainer,
    format_query_instance,
)

if __name__ == "__main__":
    print("Testing root dice_setup gateway...")
    d, m, exp = init_dice_framework()
    print("Root dice_setup operational.")
