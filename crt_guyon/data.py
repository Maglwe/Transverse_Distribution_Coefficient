# data.py
from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass
class BridgeGeometry:
    bridge_type: str  # "PSI-BA" ou "VIPP"
    number_of_spans: int
    span: float
    deck_width: float
    number_of_girders: int
    girder_spacing: float

    # Largeur roulable et trottoirs
    rollable_width: float
    left_sidewalk: float
    right_sidewalk: float

    # Nombre de dispositifs de retenue intervenant dans Lch
    number_of_retaining_devices: int = 0

    # Décalage éventuel de la chaussée par rapport à l'axe du tablier
    road_center_offset: float = 0.0

    @property
    def half_width(self) -> float:
        return self.deck_width / 2.0

    @property
    def chargeable_width(self) -> float:
        return (
            self.rollable_width
            - 0.50 * self.number_of_retaining_devices
        )

    @property
    def lane_count(self) -> int:
        return max(1, int(self.chargeable_width // 3.0))

    @property
    def lane_width(self) -> float:
        return self.chargeable_width / self.lane_count

    @property
    def road_left(self) -> float:
        return (
            self.road_center_offset
            - self.chargeable_width / 2.0
        )

    @property
    def road_right(self) -> float:
        return (
            self.road_center_offset
            + self.chargeable_width / 2.0
        )

    def girder_positions(self) -> np.ndarray:
        """Positions y des poutres, origine au centre du tablier."""
        total_girder_span = (
            self.girder_spacing
            * (self.number_of_girders - 1)
        )

        overhang = (
            self.deck_width - total_girder_span
        ) / 2.0

        first = -self.half_width + overhang

        return np.array([
            first + i * self.girder_spacing
            for i in range(self.number_of_girders)
        ], dtype=float)

    def validate(self, hp: float = 0.0) -> tuple[list[str], list[str]]:
        """Validation géométrique et contrôles des recommandations S.E.T.R.A."""
        errors = []
        warnings = []

        if self.bridge_type not in ("PSI-BA", "VIPP"):
            errors.append("Le type de pont doit être 'PSI-BA' ou 'VIPP'.")

        if self.number_of_spans < 1:
            errors.append("Le nombre de travées doit être >= 1.")

        if self.span <= 0:
            errors.append("La portée L doit être > 0.")
        else:
            # Recommandations de portée S.E.T.R.A.
            if self.bridge_type == "PSI-BA":
                if self.number_of_spans == 1 and (self.span < 10.0 or self.span > 35.0):
                    errors.append(
                        f"Pour 1 travée (PSI-BA), la portée conseillée est comprise entre 10 m et 35 m (SETRA, 1979). Portée saisie : {self.span} m."
                    )
                elif self.number_of_spans >= 2 and (self.span < 10.0 or self.span > 20.0):
                    errors.append(
                        f"Pour {self.number_of_spans} travées (PSI-BA), la portée conseillée est comprise entre 10 m et 20 m (SETRA, 1979). Portée saisie : {self.span} m."
                    )
            elif self.bridge_type == "VIPP":
                if self.span < 25.0 or self.span > 50.0:
                    warnings.append(
                        f"Portée VIPP L = {self.span:.2f} m sort de la gamme standard/économique du S.E.T.R.A. (25 m à 50 m)."
                    )

        # Contrôle de l'élancement pour les PSI-BA (h / L)
        if self.bridge_type == "PSI-BA" and hp > 0:
            slenderness = hp / self.span
            if slenderness < (1.0 / 20.0) or slenderness > (1.0 / 15.0):
                warnings.append(
                    f"Élancement PSI-BA h/L = 1/{self.span/hp:.1f} sort de la plage conseillée par le S.E.T.R.A. (de 1/15 pour une travée indépendante à 1/20 dans le cas de travées continues)."
                )

        # Contrôle de l'élancement pour les VIPP (h / L)
        if self.bridge_type == "VIPP" and hp > 0:
            slenderness = hp / self.span
            if slenderness < (1.0 / 22.0) or slenderness > (1.0 / 17.0):
                warnings.append(
                    f"Élancement VIPP h/L = 1/{self.span/hp:.1f} sort de la plage conseillée par le S.E.T.R.A. (1/22 à 1/17, optimum 1/17)."
                )

        if self.deck_width <= 0:
            errors.append("La largeur totale du tablier doit être > 0.")

        if self.number_of_girders < 2:
            errors.append("Il faut au moins 2 poutres.")

        if self.girder_spacing <= 0:
            errors.append("L'espacement des poutres doit être > 0.")

        total_girder_span = self.girder_spacing * (self.number_of_girders - 1)
        if total_girder_span > self.deck_width + 1e-12:
            errors.append(
                "Les poutres ne peuvent pas tenir dans la largeur du tablier."
            )
        else:
            # Contrôle de l'encorbellement (porte-à-faux) <= spacing / 2 (ou b0 / 2)
            cantilever = (self.deck_width - total_girder_span) / 2.0
            max_allowed_cantilever = self.girder_spacing / 2.0
            if cantilever > max_allowed_cantilever + 1e-12:
                errors.append(
                    f"L'encorbellement (porte-à-faux) de {cantilever:.3f} m est supérieur à la moitié de l'entraxe ({max_allowed_cantilever:.3f} m)."
                )

        if self.rollable_width <= 0:
            errors.append("La largeur roulable doit être > 0.")

        if self.rollable_width > self.deck_width + 1e-12:
            errors.append(
                "La largeur roulable ne peut pas dépasser la largeur du tablier."
            )

        if self.left_sidewalk < 0 or self.right_sidewalk < 0:
            errors.append("Les largeurs de trottoirs doivent être >= 0.")

        if (
            abs(
                self.left_sidewalk
                + self.rollable_width
                + self.right_sidewalk
                - self.deck_width
            ) > 1e-8
        ):
            errors.append(
                "Il faut vérifier : largeur gauche + largeur roulable + largeur droite = largeur tablier."
            )

        if not 0 <= self.number_of_retaining_devices <= 2:
            errors.append(
                "Le nombre de dispositifs de retenue pris en compte doit être 0, 1 ou 2."
            )

        if self.chargeable_width <= 0:
            errors.append("La largeur chargeable doit être > 0.")

        return errors, warnings


@dataclass
class GirderSection:
    b0: float
    ba: float
    hd: float
    hp: float
    is_type_choice: int = 2
    bta: float = 0.0
    hta: float = 0.0

    def validate(self) -> list[str]:
        errors = []

        if self.b0 <= 0:
            errors.append("b0 doit être > 0.")
        if self.ba <= 0:
            errors.append("ba doit être > 0.")
        if self.ba > self.b0:
            errors.append("ba ne peut pas être supérieur à b0.")
        if self.hd <= 0:
            errors.append("hd doit être > 0.")
        if self.hp <= 0:
            errors.append("hp doit être > 0.")
        if self.hp <= self.hd:
            errors.append("hp doit être > hd.")

        if self.is_type_choice != 2:
            if self.bta <= 0:
                errors.append("bta (largeur du talon) doit être > 0 pour le type avec talon.")
            if self.hta <= 0:
                errors.append("hta (épaisseur du talon) doit être > 0 pour le type avec talon.")
            if self.ba > self.bta:
                errors.append("ba (largeur d'âme) ne peut pas dépasser bta (largeur du talon).")
            if self.hd + self.hta >= self.hp:
                errors.append(
                    "La somme des épaisseurs (hd + hta) doit être inférieure à la hauteur totale hp."
                )

        return errors