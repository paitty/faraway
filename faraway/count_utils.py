from collections.abc import Sequence

from faraway.data_structures import (
    Assets,
    Card,
    Prerequisites,
    Rewards,
    SummedAssets,
)


def validate_prerequisites(prerequisites: Prerequisites, assets: SummedAssets) -> bool:
    return all(getattr(assets, key) >= value for key, value in prerequisites.model_dump().items())


def sum_assets(cards: Sequence[Card]) -> SummedAssets:
    summed_assets = {}
    for key in Assets.model_fields:
        summed_assets[key] = sum(getattr(card.assets, key) for card in cards)
    all_4_colors = min(
        summed_assets["red"],
        summed_assets["green"],
        summed_assets["blue"],
        summed_assets["yellow"],
    )
    return SummedAssets(**summed_assets, all_4_colors=all_4_colors)


def compute_value(rewards: Rewards, assets: SummedAssets) -> int:
    return sum(getattr(assets, key) * reward for key, reward in rewards.model_dump().items())
