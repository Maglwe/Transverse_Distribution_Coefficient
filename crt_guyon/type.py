# type.py
from __future__ import annotations
from crt_guyon.parameters import BridgeParameters


class BridgeTypeClassifier:
    """Détermination de la classe du pont selon la réglementation."""

    def __init__(self, params: BridgeParameters):
        self.params = params

    def bridge_class(self) -> int:
        """Retourne la classe du pont (1, 2 ou 3) selon la largeur roulable Lr."""
        Lr = self.params.g.rollable_width

        if Lr >= 7.0:
            return 1
        if Lr > 5.50:
            return 2
        return 3