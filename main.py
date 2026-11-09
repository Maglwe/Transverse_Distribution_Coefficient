# main.py
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import json
import csv
import numpy as np

from crt_guyon.data import BridgeGeometry, GirderSection
from crt_guyon.parameters import BridgeParameters
from crt_guyon.guyon import GuyonEngine
from crt_guyon.type import BridgeTypeClassifier
from crt_guyon.load import LoadRules, LoadCalculator
from crt_guyon.calculator import InfluenceCalculator


# ============================================================
# AIDES À LA SAISIE INTERACTIVE BILINGUES
# ============================================================

def ask_float(prompt: str, *, min_value: float | None = None, strict_positive: bool = False) -> float:
    while True:
        raw = input(f"{prompt}: ").strip()
        try:
            val = float(raw.replace(",", "."))
            if strict_positive and val <= 0:
                print("  Erreur : Cette valeur doit être strictement supérieure à 0 / Must be > 0.")
                continue
            if min_value is not None and val < min_value:
                print(f"  Erreur : Cette valeur doit être supérieure ou égale à {min_value} / Must be >= {min_value}.")
                continue
            return val
        except ValueError:
            print("  Entrée invalide / Invalid entry.")


def ask_int(prompt: str, *, minimum: int | None = None, maximum: int | None = None) -> int:
    while True:
        try:
            value = int(input(f"{prompt}: ").strip())
            if minimum is not None and value < minimum:
                raise ValueError
            if maximum is not None and value > maximum:
                raise ValueError
            return value
        except ValueError:
            print("  Entier invalide ou hors bornes / Invalid integer or out of bounds.")


def interactive_input():
    print("\n" + "=" * 78)
    print("ENTRÉE DES DONNÉES DU PONT (PSI-BA ou VIPP) / BRIDGE DATA INPUT")
    print("=" * 78)
    print(
        "\nLes dimensions sont saisies en mètres / Dimensions are entered in meters.\n"
        "Le tablier est supposé symétrique / Deck is assumed symmetrical.\n"
    )

    print("\n[1] Choix du type de structure et de section / Structure and section type selection:")
    print("    1 = PSI-BA avec talon (Béton Armé) / PSI-BA with bottom flange (Reinforced Concrete)")
    print("    2 = PSI-BA sans talon (Béton Armé) / PSI-BA without bottom flange (Conventional T-beam)")
    print("    3 = VIPP (Viaduc à travées indépendantes à poutres précontraintes) / VIPP (Prestressed Concrete)")

    is_type_choice = ask_int(
        "Sélectionnez le type de pont et de section / Select bridge and section type (1, 2 or 3)",
        minimum=1,
        maximum=3
    )

    if is_type_choice in (1, 2):
        bridge_type = "PSI-BA"
    else:
        bridge_type = "VIPP"

    # Boucle active connectée aux contrôles globaux de data.py
    while True:
        n_spans = ask_int("Nombre de travées / Number of spans", minimum=1)

        # Recommandations et bornes SETRA selon le type de pont
        print("\nRecommandations SETRA pour les portées / SETRA span recommendations:")
        if bridge_type == "PSI-BA":
            min_L = 10.0
            max_L = 35.0 if n_spans == 1 else 20.0
            print(f" -> Pour {n_spans} travée(s) PSI-BA : Portée conseillée entre {min_L} m et {max_L} m.")
        else:
            min_L = 25.0
            max_L = 50.0
            print(f" -> Pour les VIPP : Portée courante entre {min_L} m et {max_L} m.")

        # Saisie de la portée avec contrôle bloquant immédiat
        while True:
            L = ask_float("Portée L (m) / Span L (m)", strict_positive=True)
            if bridge_type == "PSI-BA":
                if L < min_L or L > max_L:
                    print(f"  [x] Erreur bloquante : L = {L} m sort du domaine S.E.T.R.A. ({min_L} m à {max_L} m). Veuillez ressaisir.")
                    continue
            break

        deck_width = ask_float("Largeur totale du tablier (m) / Total deck width (m)", strict_positive=True)
        n_girders = ask_int("Nombre de poutres / Number of girders", minimum=2)
        spacing = ask_float("Entraxe des poutres (m) / Girder spacing (m)", strict_positive=True)
        rollable = ask_float("Largeur roulable (m) / Carriageway width (m)", strict_positive=True)
        left_sidewalk = ask_float("Trottoir gauche (m) / Left sidewalk (m)", min_value=0.0)
        right_sidewalk = ask_float("Trottoir droit (m) / Right sidewalk (m)", min_value=0.0)
        n_retaining = ask_int("Nombre de dispositifs de retenue / Number of retaining devices", minimum=0, maximum=2)
        road_offset = ask_float("Décalage du centre de la chaussée (m) / Road center offset (m)")

        print("\n" + "-" * 50)
        print(f"SECTION DE LA POUTRE PRINCIPALE ({bridge_type}) / MAIN GIRDER SECTION")
        print("-" * 50)

        b0 = spacing
        ba = ask_float("Largeur de l'âme ba (m) / Web width ba (m)", strict_positive=True)
        hd = ask_float("Épaisseur de la table / hourdis hd (m) / Top flange thickness hd (m)", strict_positive=True)
        hp = ask_float("Hauteur totale de la poutre hp (m) / Total beam height hp (m)", strict_positive=True)

        bta, hta = 0.0, 0.0
        if is_type_choice != 2:
            bta = ask_float("Largeur de la semelle inférieure / talon bta (m) / Bottom flange width bta (m)", strict_positive=True)
            hta = ask_float("Épaisseur de la semelle inférieure / talon hta (m) / Bottom flange thickness hta (m)", strict_positive=True)

        geometry = BridgeGeometry(
            bridge_type=bridge_type,
            number_of_spans=n_spans,
            span=L,
            deck_width=deck_width,
            number_of_girders=n_girders,
            girder_spacing=spacing,
            rollable_width=rollable,
            left_sidewalk=left_sidewalk,
            right_sidewalk=right_sidewalk,
            number_of_retaining_devices=n_retaining,
            road_center_offset=road_offset,
        )

        section = GirderSection(
            b0=b0,
            ba=ba,
            hd=hd,
            hp=hp,
            is_type_choice=is_type_choice,
            bta=bta,
            hta=hta,
        )

        # Exécution active des contrôles globaux de data.py
        errors, warnings = geometry.validate(hp=hp)
        errors += section.validate()

        if warnings:
            print("\n[!] AVERTISSEMENTS RÈGLEMENTAIRES (S.E.T.R.A.) / REGULATORY WARNINGS:")
            for w in warnings:
                print(f"  - {w}")

        if errors:
            print("\n[x] ERREURS DE VALIDATION GÉOMÉTRIQUE / RÈGLEMENTAIRE :")
            for err in errors:
                print(f"  - {err}")
            print("\n-> Veuillez recommencer la saisie pour corriger ces erreurs / Please re-enter correct data.\n" + "="*70)
            continue

        break

    return geometry, section


# ============================================================
# SÉLECTION DES POUTRES (CENTRALES ET EXTRÊMITÉS)
# ============================================================

def get_selected_girders(params: BridgeParameters) -> list[int]:
    n = params.g.number_of_girders
    if n % 2 != 0:
        center = n // 2 + 1
        return [1, center, n]
    else:
        c1 = n // 2
        c2 = c1 + 1
        return sorted(list({1, c1, c2, n}))


# ============================================================
# AFFICHAGE DU RAPPORT
# ============================================================

def print_report(params: BridgeParameters, guyon_engine: GuyonEngine, classifier: BridgeTypeClassifier, results: list):
    selected_girders = get_selected_girders(params)

    print("\n" + "=" * 78)
    print("TRANSVERSE LOAD DISTRIBUTION — BRIDGE DATA")
    print("=" * 78)
    print(f"Bridge Type                         = {params.g.bridge_type}")
    print(f"Span L                              = {params.g.span:.3f} m")
    print(f"Total deck width                    = {params.g.deck_width:.3f} m")
    print(f"Number of girders                   = {params.g.number_of_girders}")
    print(f"Girder spacing                      = {params.g.girder_spacing:.3f} m")
    print(f"Carriageway width                   = {params.g.rollable_width:.3f} m")
    print(f"Chargeable width                    = {params.g.chargeable_width:.3f} m")
    print(f"Left sidewalk width                 = {params.g.left_sidewalk:.3f} m")
    print(f"Right sidewalk width                = {params.g.right_sidewalk:.3f} m")
    print(f"Bridge class                        = {classifier.bridge_class()}")
    print(f"Guyon-Massonnet theta               = {params.theta:.4f}")
    print(f"Selected girders                    = {tuple(selected_girders)}")
    print("=" * 78)

    print("\n" + "=" * 78)
    theta_label = "theta > 0.3" if params.theta > 0.3 else "theta <= 0.3"
    print(f"GUYON-MASSONNET METHOD ({theta_label})")
    print("=" * 78)

    print("\nK0, K1 AND K AT SELECTED LOAD ECCENTRICITIES")
    print("-" * 78)
    print(f"{'Girder':>8}{'y (m)':>10}{'e (m)':>10}{'K0':>14}{'K1':>14}{'K':>14}")
    print("-" * 70)

    eccentricities = np.linspace(-params.b, params.b, 9)
    for r in results:
        g_idx = r["girder"]
        if g_idx in selected_girders:
            y = r["y"]
            for e in eccentricities:
                k0, k1 = guyon_engine.K01(y, float(e))
                k_val = guyon_engine.K(y, float(e))
                print(f"{g_idx:>8}{y:>10.3f}{e:>10.3f}{k0:>14.4f}{k1:>14.4f}{k_val:>14.4f}")
            print("-" * 70)

    print("\nTRANSVERSE DISTRIBUTION COEFFICIENTS BY GIRDER")
    print("-" * 78)
    header = (
        f"{'Girder':>8}"
        f"{'y (m)':>12}"
        f"{'AL':>12}"
        f"{'qtr':>12}"
        f"{'Bc':>12}"
        f"{'Mc80':>12}"
        f"{'Mc120':>12}"
    )
    print(header)
    print("-" * len(header))

    for r in results:
        if r["girder"] in selected_girders:
            print(
                f"{r['girder']:>8}"
                f"{r['y']:>12.3f}"
                f"{r['AL']['CRT']:>12.4f}"
                f"{r['qtr']['both']['CRT']:>12.4f}"
                f"{r['Bc']['CRT']:>12.4f}"
                f"{r['Mc80']['CRT']:>12.4f}"
                f"{r['Mc120']['CRT']:>12.4f}"
            )
    print("=" * 78)

    print("\nDETAILED INFORMATION — MOST UNFAVOURABLE LOAD ARRANGEMENTS")
    print("-" * 78)
    for r in results:
        if r["girder"] in selected_girders:
            i = r["girder"]
            y = r["y"]
            al = r["AL"]
            qtr = r["qtr"]["both"]
            bc = r["Bc"]
            mc80 = r["Mc80"]
            mc120 = r["Mc120"]

            mc80_t1 = [round(float(v), 3) for v in mc80['track_1_interval']]
            mc80_t2 = [round(float(v), 3) for v in mc80['track_2_interval']]
            mc120_t1 = [round(float(v), 3) for v in mc120['track_1_interval']]
            mc120_t2 = [round(float(v), 3) for v in mc120['track_2_interval']]

            print(f"\n--- Girder {i} (y = {y:.3f} m) ---")
            print(f"  * AL    : CRT = {al['CRT']:.4f} | a1 = {al['a1']} | L_AL = {al['n_loaded'] * params.g.lane_width:.3f} m | Loaded lanes = {al['n_loaded']}")
            print(f"  * qtr   : CRT = {qtr['CRT']:.4f} | Left sidewalk = True | Right sidewalk = True")
            print(f"  * Bc    : CRT = {bc['CRT']:.4f} | bc = {bc['bc']} | Number of files = {bc['n_files']}")
            print(f"  * Mc80  : CRT = {mc80['CRT']:.4f} | Track 1 = {mc80_t1} | Track 2 = {mc80_t2}")
            print(f"  * Mc120 : CRT = {mc120['CRT']:.4f} | Track 1 = {mc120_t1} | Track 2 = {mc120_t2}")
    print("-" * 78)


# ============================================================
# EXPORTATIONS
# ============================================================

def export_json(params: BridgeParameters, classifier: BridgeTypeClassifier, rules: LoadRules, results: list, path="crt_results.json"):
    def max_case(key):
        return max(results, key=lambda r: r[key]["CRT"])

    summary = {
        "bridge_type": params.g.bridge_type,
        "bridge_class": classifier.bridge_class(),
        "mechanical": {
            "Ip_m4": params.Ip,
            "Kp_m4": params.Kp,
            "rhoP": params.rhoP,
            "rhoE": params.rhoE,
            "gammaP": params.gammaP,
            "gammaE": params.gammaE,
            "alpha": params.alpha,
            "theta": params.theta,
            "lambda": params.lam,
        },
    }
    data = {
        "input": {
            "geometry": asdict(params.g),
            "section": asdict(params.s),
            "rules": asdict(rules),
        },
        "summary": summary,
        "results": results,
    }
    Path(path).write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=float),
        encoding="utf-8"
    )


def export_csv(results: list, path="crt_summary.csv"):
    rows = []
    for r in results:
        rows.append({
            "poutre": r["girder"],
            "y_m": r["y"],
            "CRT_AL": r["AL"]["CRT"],
            "CRT_Bc": r["Bc"]["CRT"],
            "CRT_Mc80": r["Mc80"]["CRT"],
            "CRT_Mc120": r["Mc120"]["CRT"],
        })
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys(), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# FONCTION PRINCIPALE (MAIN)
# ============================================================

def main():
    geometry, section = interactive_input()
    if geometry is None or section is None:
        return

    params = BridgeParameters(geometry, section)
    guyon_engine = GuyonEngine(params)
    classifier = BridgeTypeClassifier(params)
    rules = LoadRules()
    calculator = InfluenceCalculator(params, guyon_engine, rules.influence_points)
    load_calculator = LoadCalculator(params, guyon_engine, calculator, classifier, rules)

    results = []
    for i, y in enumerate(geometry.girder_positions(), start=1):
        al_worst, al_all = load_calculator.calculate_AL(y)
        qtr = load_calculator.calculate_sidewalks(y)
        bc_worst, bc_all = load_calculator.calculate_Bc(y)

        mc80 = load_calculator.calculate_Mc(
            y, rules.mc80_track_width, rules.mc80_track_spacing, "Mc80"
        )
        mc120 = load_calculator.calculate_Mc(
            y, rules.mc120_track_width, rules.mc120_track_spacing, "Mc120"
        )

        results.append({
            "girder": i,
            "y": float(y),
            "AL": al_worst,
            "AL_all": al_all,
            "qtr": qtr,
            "Bc": bc_worst,
            "Bc_all": bc_all,
            "Mc80": mc80,
            "Mc120": mc120,
        })

    print_report(params, guyon_engine, classifier, results)
    export_json(params, classifier, rules, results, "crt_results.json")
    export_csv(results, "crt_summary.csv")

    calculator.plot_influence_lines("plots")
    calculator.plot_load_cases(results, "plots")

    plots_path = Path("plots").resolve()
    print(f"\nAll plots have been saved successfully in: \n{plots_path}")
    print("\nCalcul terminé avec succès / Calculation completed successfully.")


if __name__ == "__main__":
    main()