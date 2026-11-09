# parameters.py
from __future__ import annotations
from math import pi, tanh, sqrt
from sectionproperties.pre.library import rectangular_section
from sectionproperties.analysis import Section
from crt_guyon.data import BridgeGeometry, GirderSection


def k_saada(x: float) -> float:
    """Fonction auxiliaire de Saada pour le calcul de la rigidité à la torsion."""
    if x <= 0:
        raise ValueError("L'argument x de k_saada doit être > 0.")
    return 1.0 / 3.0 - (64.0 * tanh(pi * x / 2.0)) / (x * pi**5)


class BridgeParameters:
    """Calcul et encapsulation des paramètres géométriques et mécaniques du pont."""

    def __init__(self, geometry: BridgeGeometry, section: GirderSection):
        self.g = geometry
        self.s = section

        self.b = self.g.deck_width / 2.0
        self.L = self.g.span
        self.b1 = self.g.girder_spacing

        self.Ip = self._calculate_Ip()
        self.Kp = self._calculate_Kp()

        self.rhoP = self.Ip / self.b1
        self.gammaP = self.Kp / (2.0 * self.b1)
        self.rhoE = (self.s.hd ** 3) / 12.0
        self.gammaE = self.rhoE

        self.alpha = (self.gammaE + self.gammaP) / (
            2.0 * sqrt(self.rhoE * self.rhoP)
        )
        self.theta = (self.b / self.L) * ((self.rhoP / self.rhoE) ** 0.25)
        self.lam = (pi * ((self.rhoP / self.rhoE) ** 0.25)) / (
            self.L * sqrt(2.0)
        )

    def _calculate_Ip(self) -> float:
        b0 = self.s.b0
        ba = self.s.ba
        hd = self.s.hd
        hp = self.s.hp
        is_type_choice = getattr(self.s, 'is_type_choice', 2)
        bta = getattr(self.s, 'bta', 0.0)
        hta = getattr(self.s, 'hta', 0.0)
        mesh_size = 0.0005

        table = rectangular_section(
            b=b0,
            d=hd
        ).shift_section(
            x_offset=-b0 / 2,
            y_offset=hp - hd
        )

        if is_type_choice == 2:
            web = rectangular_section(
                b=ba,
                d=hp - hd
            ).shift_section(
                x_offset=-ba / 2,
                y_offset=0
            )
            geometry = table + web
        else:
            web = rectangular_section(
                b=ba,
                d=hp - hd - hta
            ).shift_section(
                x_offset=-ba / 2,
                y_offset=hta
            )
            talon = rectangular_section(
                b=bta,
                d=hta
            ).shift_section(
                x_offset=-bta / 2,
                y_offset=0
            )
            geometry = table + web + talon

        geometry.create_mesh(mesh_sizes=mesh_size)
        sec = Section(geometry=geometry)
        sec.calculate_geometric_properties()

        return float(sec.get_ic()[0])

    def _calculate_Kp(self) -> float:
        b0 = self.s.b0
        ba = self.s.ba
        hd = self.s.hd
        hp = self.s.hp
        is_type_choice = getattr(self.s, 'is_type_choice', 2)

        x_saada2 = 2.0 * (hp - hd) / ba
        gamma1 = (b0 * (hd**3)) / 6.0
        gamma2 = k_saada(x_saada2) * (hp - hd) * (ba**3)

        if is_type_choice != 2:
            bta = self.s.bta
            hta = self.s.hta
            x_saada3 = (bta - ba) / hta
            gamma3 = k_saada(x_saada3) * (bta - ba) * (hta**3)
            return gamma1 + gamma2 + gamma3

        return gamma1 + gamma2