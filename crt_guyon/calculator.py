# calculator.py
from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from crt_guyon.parameters import BridgeParameters
from crt_guyon.guyon import GuyonEngine


def trapz(x: np.ndarray, y: np.ndarray) -> float:
    """Intégration trapézoïdale numérique."""
    return float(np.sum(0.5 * (y[:-1] + y[1:]) * np.diff(x)))


class InfluenceCalculator:
    """Calculateur d'intégrales numériques et générateur de graphiques."""

    def __init__(
        self,
        params: BridgeParameters,
        guyon_engine: GuyonEngine,
        influence_points: int = 2001,
    ):
        self.params = params
        self.guyon = guyon_engine
        self.influence_points = influence_points
        self._line_cache = {}

    def influence_line(self, y: float, points: int | None = None):
        """Génère la ligne d'influence K(e) pour une position de poutre y."""
        pts = points or self.influence_points
        e = np.linspace(-self.params.b, self.params.b, pts)
        K_values = np.array([self.guyon.K(y, float(x)) for x in e])
        return e, K_values

    def _prepared_line(self, y: float):
        """Calcule et met en cache K(e) ainsi que son intégrale cumulative."""
        key = round(float(y), 12)
        if key not in self._line_cache:
            e = np.linspace(
                -self.params.b, self.params.b, self.influence_points
            )
            K_values = np.array([self.guyon.K(y, float(x)) for x in e])

            cumulative = np.zeros_like(e)
            cumulative[1:] = np.cumsum(
                0.5 * (K_values[:-1] + K_values[1:]) * np.diff(e)
            )
            self._line_cache[key] = (e, K_values, cumulative)

        return self._line_cache[key]

    def integrate_K(self, y: float, e1: float, e2: float) -> float:
        """Intégrale de K(e) entre e1 et e2."""
        if e2 <= e1:
            raise ValueError("e2 doit être > e1.")
        if (
            e1 < -self.params.b - 1e-10
            or e2 > self.params.b + 1e-10
        ):
            raise ValueError("L'intervalle d'intégration sort du tablier.")

        e, _, cumulative = self._prepared_line(y)
        c1 = float(np.interp(e1, e, cumulative))
        c2 = float(np.interp(e2, e, cumulative))
        return c2 - c1

    def average_K(self, y: float, e1: float, e2: float) -> float:
        """Valeur moyenne de K(e) sur l'intervalle [e1, e2]."""
        return self.integrate_K(y, e1, e2) / (e2 - e1)

    def plot_influence_lines(self, output_dir: str = "plots"):
        """Génère et sauvegarde les courbes de K(e) pour chaque poutre."""
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        for i, y in enumerate(self.params.g.girder_positions(), start=1):
            e, K_values = self.influence_line(y)
            fig, ax = plt.subplots(figsize=(11, 6))

            ax.plot(e, K_values, linewidth=2, label="K(e)")
            ax.axhline(0, linewidth=0.8)
            ax.axvline(0, linewidth=0.8)
            ax.set_xlabel("e (m)")
            ax.set_ylabel("K(e)")
            ax.set_title(f"Ligne d'influence K(e) - Poutre {i}, y={y:.3f} m")
            ax.grid(True)
            ax.legend()

            fig.tight_layout()
            fig.savefig(output / f"poutre_{i}_K_e.png", dpi=180)
            plt.close(fig)

    def plot_load_cases(self, results: list, output_dir: str = "plots"):
        """Trace les lignes d'influence avec zones chargées (AL, Bc, Mc)."""
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        for r in results:
            i, y = r["girder"], r["y"]
            e, K_values = self.influence_line(y)

            # Trace AL
            fig, ax = plt.subplots(figsize=(11, 6))
            ax.plot(e, K_values, label="K(e)", linewidth=2)
            for e1, e2 in r["AL"]["intervals"]:
                xx = np.linspace(e1, e2, 100)
                yy = np.array([self.guyon.K(y, float(v)) for v in xx])
                ax.fill_between(xx, 0, yy, alpha=0.25)
            ax.set_title(f"AL - Poutre {i}")
            ax.set_xlabel("e (m)")
            ax.set_ylabel("K(e)")
            ax.grid(True)
            ax.legend()
            fig.tight_layout()
            fig.savefig(output / f"poutre_{i}_AL.png", dpi=180)
            plt.close(fig)

            # Trace Bc
            fig, ax = plt.subplots(figsize=(11, 6))
            ax.plot(e, K_values, label="K(e)", linewidth=2)
            for j, x in enumerate(r["Bc"]["wheel_positions"], start=1):
                kval = self.guyon.K(y, x)
                ax.scatter([x], [kval], s=45)
                ax.annotate(
                    f"K{j}",
                    (x, kval),
                    xytext=(5, 5),
                    textcoords="offset points",
                )
            ax.set_title(
                f'Bc - Poutre {i} - {r["Bc"]["n_files"]} file(s)'
            )
            ax.set_xlabel("e (m)")
            ax.set_ylabel("K(e)")
            ax.grid(True)
            ax.legend()
            fig.tight_layout()
            fig.savefig(output / f"poutre_{i}_Bc.png", dpi=180)
            plt.close(fig)

            # Trace Mc80 / Mc120
            for name in ("Mc80", "Mc120"):
                mc = r[name]
                fig, ax = plt.subplots(figsize=(11, 6))
                ax.plot(e, K_values, label="K(e)", linewidth=2)
                for interval in (
                    mc["track_1_interval"],
                    mc["track_2_interval"],
                ):
                    e1, e2 = interval
                    xx = np.linspace(e1, e2, 100)
                    yy = np.array([self.guyon.K(y, float(v)) for v in xx])
                    ax.fill_between(xx, 0, yy, alpha=0.25)
                ax.set_title(f"{name} - Poutre {i}")
                ax.set_xlabel("e (m)")
                ax.set_ylabel("K(e)")
                ax.grid(True)
                ax.legend()
                fig.tight_layout()
                fig.savefig(output / f"poutre_{i}_{name}.png", dpi=180)
                plt.close(fig)