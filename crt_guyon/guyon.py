# guyon.py
from __future__ import annotations
from math import cosh, sinh, cos, sin, pi, exp, sqrt
from crt_guyon.parameters import BridgeParameters


class GuyonEngine:
    """Moteur analytique de Guyon-Massonnet (K0, K1 et interpolation K)."""

    def __init__(self, params: BridgeParameters):
        self.params = params

    def K01(self, y: float, e: float) -> tuple[float, float]:
        """Calcul analytique des valeurs fondamentales K0 (alpha=0) et K1 (alpha=1)."""
        if e <= y:
            yc = -y
            ec = -e
        else:
            yc = y
            ec = e

        lam = self.params.lam
        b = self.params.b
        theta = self.params.theta

        # --- CALCUL DE K0 ---
        a_prime = 2.0 * cosh(lam * (yc + b)) * cos(lam * (yc + b))
        A = (
            sinh(2.0 * lam * b) * cos(lam * (b + ec)) * cosh(lam * (b - ec))
            - sin(2.0 * lam * b) * cosh(lam * (b + ec)) * cos(lam * (b - ec))
        )

        b_prime = (
            cosh(lam * (yc + b)) * sin(lam * (yc + b))
            + sinh(lam * (yc + b)) * cos(lam * (yc + b))
        )

        B1 = sinh(2.0 * lam * b) * (
            sin(lam * (b + ec)) * cosh(lam * (b - ec))
            - cos(lam * (b + ec)) * sinh(lam * (b - ec))
        )
        B2 = sin(2.0 * lam * b) * (
            sinh(lam * (b + ec)) * cos(lam * (b - ec))
            - cosh(lam * (b + ec)) * sin(lam * (b - ec))
        )

        den0 = (sinh(2.0 * lam * b) ** 2) - (sin(2.0 * lam * b) ** 2)
        K0 = 2.0 * lam * b * (a_prime * A + b_prime * (B1 + B2)) / den0

        # --- CALCUL DE K1 ---
        sigma = theta * pi
        beta = pi * y / b
        psi = pi * e / b
        chi = pi - abs(beta - psi)

        def Ru(u: float) -> float:
            return cosh(theta * u) * (
                sigma * cosh(sigma) - sinh(sigma)
            ) - theta * u * sinh(sigma) * sinh(theta * u)

        def Qu(u: float) -> float:
            return sinh(theta * u) * (
                2.0 * sinh(sigma) + sigma * cosh(sigma)
            ) - theta * u * sinh(sigma) * cosh(theta * u)

        C = cosh(theta * chi) * (sigma * cosh(sigma) + sinh(sigma))
        D = theta * chi * sinh(sigma) * sinh(theta * chi)
        E_term = (Ru(beta) * Ru(psi)) / (
            3.0 * sinh(sigma) * cosh(sigma) - sigma
        )
        F = (Qu(beta) * Qu(psi)) / (3.0 * sinh(sigma) * cosh(sigma) + sigma)

        K1 = sigma * (C - D + E_term + F) / (2.0 * (sinh(sigma) ** 2))

        return K0, K1

    def K(self, y: float, e: float) -> float:
        """Formule d'interpolation de Sattler pour K en fonction d'alpha et theta."""
        K0, K1 = self.K01(y, e)
        theta = self.params.theta
        alpha = self.params.alpha

        if theta <= 0.1:
            return K0 + (K1 - K0) * (alpha**0.05)

        if theta <= 1.0:
            theta0 = (0.065 - theta) / 0.663
            return K0 + (K1 - K0) * (alpha ** (1.0 - exp(theta0)))

        return K0 + (K1 - K0) * sqrt(alpha)