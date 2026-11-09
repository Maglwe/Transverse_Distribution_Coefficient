# load.py
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
import numpy as np

from crt_guyon.parameters import BridgeParameters
from crt_guyon.type import BridgeTypeClassifier


@dataclass
class LoadRules:
    """Configuration et paramètres du règlement de charges (Fascicule 61)."""

    bc_file_width: float = 2.50
    bc_wheel_track_spacing: float = 2.00
    bc_edge_clearance: float = 0.25
    bc_coefficients: dict = None

    mc80_track_width: float = 0.85
    mc80_track_spacing: float = 1.95

    mc120_track_width: float = 1.00
    mc120_track_spacing: float = 2.30

    influence_points: int = 2001
    integration_points: int = 1001
    position_scan_points: int = 1001

    al_a1_two_lanes: float = 1.0
    al_a1_three_lanes: float = 0.90

    def __post_init__(self):
        if self.bc_coefficients is None:
            self.bc_coefficients = {
                1: {1: 1.20, 2: 1.10, 3: 0.95},
                2: {1: 1.20, 2: 1.10},
                3: {1: 1.20, 2: 1.10},
            }


class LoadCalculator:
    """Solveur des systèmes de charges routières et militaires."""

    def __init__(
        self,
        params: BridgeParameters,
        guyon_engine,
        calculator,
        classifier: BridgeTypeClassifier,
        rules: LoadRules | None = None,
    ):
        self.params = params
        self.guyon = guyon_engine
        self.calc = calculator
        self.classifier = classifier
        self.rules = rules or LoadRules()

    def calculate_AL(self, y: float):
        """Recherche du cas AL le plus défavorable."""
        Nv = self.params.g.lane_count
        v = self.params.g.lane_width
        x0 = self.params.g.road_left

        results = []

        for n_loaded in range(1, Nv + 1):
            a1 = (
                self.rules.al_a1_three_lanes
                if n_loaded >= 3
                else self.rules.al_a1_two_lanes
            )

            for combo in combinations(range(Nv), n_loaded):
                intervals = [(x0 + i * v, x0 + (i + 1) * v) for i in combo]
                K_total = sum(
                    self.calc.integrate_K(y, e1, e2) for e1, e2 in intervals
                )
                K_AL = K_total / (n_loaded * v)
                eta = K_AL / self.params.g.number_of_girders
                effect = a1 * K_AL * (n_loaded * v)

                results.append({
                    "n_loaded": n_loaded,
                    "lanes": [i + 1 for i in combo],
                    "a1": a1,
                    "K_AL": K_AL,
                    "CRT": eta,
                    "effect": effect,
                    "intervals": intervals,
                })

        return max(results, key=lambda r: r["effect"]), results

    def calculate_sidewalks(self, y: float):
        """Calcul de l'effet des surcharges sur trottoirs."""
        left_e1 = -self.params.b
        left_e2 = self.params.g.road_left
        right_e1 = self.params.g.road_right
        right_e2 = self.params.b

        KL = (
            self.calc.average_K(y, left_e1, left_e2)
            if self.params.g.left_sidewalk > 0
            else 0.0
        )
        KR = (
            self.calc.average_K(y, right_e1, right_e2)
            if self.params.g.right_sidewalk > 0
            else 0.0
        )
        K_both = KL + KR

        return {
            "left": {"K": KL, "CRT": KL / self.params.g.number_of_girders},
            "right": {"K": KR, "CRT": KR / self.params.g.number_of_girders},
            "both": {
                "K": K_both,
                "CRT": K_both / self.params.g.number_of_girders,
            },
        }

    def _bc_allowed_center_range(self):
        """Plage autorisée pour le centre des files du camion Bc."""
        wheel_half = self.rules.bc_wheel_track_spacing / 2.0
        xmin = (
            self.params.g.road_left
            + self.rules.bc_edge_clearance
            + wheel_half
        )
        xmax = (
            self.params.g.road_right
            - self.rules.bc_edge_clearance
            - wheel_half
        )
        return xmin, xmax

    def calculate_Bc(self, y: float):
        """Balayage transversal du système de camions Bc."""
        Nv = self.params.g.lane_count
        xmin, xmax = self._bc_allowed_center_range()
        results = []

        for n_files in range(1, Nv + 1):
            bc_factor = self.rules.bc_coefficients.get(
                self.classifier.bridge_class(), {}
            ).get(n_files)

            if bc_factor is None:
                continue

            if n_files == 1:
                base_min = xmin
                base_max = xmax
            else:
                base_min = xmin
                base_max = xmax - (n_files - 1) * self.rules.bc_file_width

            base_max = xmax - (n_files - 1) * self.rules.bc_file_width

            if base_max < base_min:
                continue

            shifts = np.linspace(
                base_min, base_max, self.rules.position_scan_points
            )
            best = None

            for first_center in shifts:
                centers = [
                    first_center + i * self.rules.bc_file_width
                    for i in range(n_files)
                ]
                wheel_positions = []
                wheel_half = self.rules.bc_wheel_track_spacing / 2.0

                for c in centers:
                    wheel_positions.extend([c - wheel_half, c + wheel_half])

                K_Bc = 0.5 * sum(self.guyon.K(y, e) for e in wheel_positions)
                CRT = K_Bc / self.params.g.number_of_girders
                effect = bc_factor * K_Bc

                candidate = {
                    "n_files": n_files,
                    "bc": bc_factor,
                    "file_centers": centers,
                    "wheel_positions": wheel_positions,
                    "K_Bc": K_Bc,
                    "CRT": CRT,
                    "effect": effect,
                }

                if best is None or effect > best["effect"]:
                    best = candidate

            if best is not None:
                results.append(best)

        if not results:
            raise ValueError(
                "Aucun cas Bc calculable : vérifier les règles bc."
            )

        return max(results, key=lambda r: r["effect"]), results

    def calculate_Mc(
        self, y: float, track_width: float, track_spacing: float, name: str
    ):
        """Balayage transversal des chenilles militaires (Mc80 ou Mc120)."""
        min_center = (
            self.params.g.road_left + track_spacing + 1.5 * track_width
        )
        max_center = self.params.g.road_right - 0.5 * track_width

        if max_center < min_center:
            raise ValueError(
                f"{name}: les chenilles ne tiennent pas dans la largeur chargeable."
            )

        centers = np.linspace(
            min_center, max_center, self.rules.position_scan_points
        )
        best = None

        for c1 in centers:
            c2 = c1 - (track_spacing + track_width)

            e11, e12 = c1 - track_width / 2.0, c1 + track_width / 2.0
            e21, e22 = c2 - track_width / 2.0, c2 + track_width / 2.0

            K1 = self.calc.average_K(y, e11, e12)
            K2 = self.calc.average_K(y, e21, e22)

            K_Mc = 0.5 * (K1 + K2)
            CRT = K_Mc / self.params.g.number_of_girders

            candidate = {
                "name": name,
                "track_centers": [c1, c2],
                "track_1_interval": [e11, e12],
                "track_2_interval": [e21, e22],
                "K_track_1": K1,
                "K_track_2": K2,
                "K_Mc": K_Mc,
                "CRT": CRT,
            }

            if best is None or CRT > best["CRT"]:
                best = candidate

        return best