<div align="center">

# Transverse Distribution Coefficient Calculator

### Computational analysis of transverse load distribution in multi-girder concrete bridges

**PSI-BA · VIPP · Guyon–Massonnet**

<br>

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Scientific Computing](https://img.shields.io/badge/Scientific-Computing-245A7A)
![Structural Engineering](https://img.shields.io/badge/Structural-Engineering-6B8E23)
![Status](https://img.shields.io/badge/Status-Under%20Development-orange)

*A Python-based engineering tool for evaluating transverse load distribution coefficients (CRT) in longitudinal-girder bridge decks.*

</div>

---

## Overview

**Transverse Distribution Coefficient Calculator** is a Python project for the computational study of transverse load distribution in multi-girder concrete bridges.

The current application is designed around two bridge families:

- **PSI-BA** — *Passage Supérieur ou Inférieur à poutres sous chaussée en béton armé* (reinforced-concrete girder bridges).
- **VIPP** — *Viaduc à travées indépendantes à poutres précontraintes* (simply supported spans with prestressed-concrete girders).

The calculation workflow uses the **Guyon–Massonnet method** to evaluate transverse distribution coefficients and assess the effect of load eccentricity on selected longitudinal girders. The program also handles bridge geometry, girder-section inputs, loading cases, result reporting and data export.

> **Project scope:** this repository is a computational engineering tool under development. Its outputs must be checked against the applicable design provisions, reference calculations and independently verified examples before being used for professional design.

## Key features

- Interactive input of bridge geometry and girder-section parameters.
- Support for PSI-BA and VIPP bridge configurations.
- Three girder-section input choices:
  1. PSI-BA with a bottom haunch/flange;
  2. PSI-BA without a bottom haunch (conventional T-section);
  3. VIPP prestressed-concrete girder.
- Geometric validation and span/slenderness checks based on the recommendations currently encoded in the project.
- Guyon–Massonnet transverse distribution calculations, including \(K_0\), \(K_1\) and \(K\).
- Evaluation of loading cases currently implemented in the program: \(A_L\), \(q_{tr}\), \(B_c\), \(Mc80\) and \(Mc120\).
- Identification and reporting of governing load arrangements for the evaluated girders.
- Export of calculation data to JSON and summary results to CSV.
- Generation of numerical plots, including influence-line and load-arrangement figures.

## Calculation workflow

The application follows this general sequence:

1. **Bridge definition** — select the bridge family and enter the span, deck width, girder count, girder spacing, carriageway, sidewalks and retaining-device data.
2. **Section definition** — enter the geometric properties of the selected girder section.
3. **Validation** — check the geometric inputs and display warnings or errors.
4. **Mechanical parameters** — construct the bridge parameters required by the calculation engine.
5. **Transverse distribution** — evaluate the Guyon–Massonnet coefficients.
6. **Loading analysis** — evaluate the implemented loading models and determine governing arrangements.
7. **Reporting and export** — display the results and write the JSON, CSV and plot outputs.

## Theoretical background

### Guyon–Massonnet method

The Guyon–Massonnet approach is used in the project to represent the transverse distribution of loads between longitudinal girders. The calculation evaluates the coefficients \(K_0\), \(K_1\) and their combined coefficient \(K\) at girder coordinates and load eccentricities.

The transverse position of a girder is measured relative to the centreline of the deck. The eccentricity of a load is likewise considered in the transverse direction. This makes it possible to study how a load placed at different positions across the deck affects the response attributed to a given girder.

The program reports coefficients for selected girders, including exterior and central girders, rather than requiring the user to inspect every printed value manually.

> The mathematical formulations, engineering assumptions, numerical interpolation procedures, and cross-sectional property calculations implemented in this project should be documented and verified against the relevant technical references. Detailed theoretical derivations and calculation procedures are beyond the scope of this README. Users should consult the original technical publications and applicable bridge-design standards for complete calculation requirements.

## Bridge geometry and section inputs

The interactive interface requests the main geometric data needed by the current implementation.

| Input | Description |
|---|---|
| Bridge family | PSI-BA or VIPP |
| Number of spans | Number of bridge spans |
| Span \(L\) | Span length, in metres |
| Deck width | Total transverse deck width, in metres |
| Number of girders | Number of longitudinal girders |
| Girder spacing | Centre-to-centre distance between adjacent girders |
| Carriageway width | Width assigned to the carriageway |
| Sidewalk widths | Left and right sidewalk widths |
| Retaining devices | Number considered in the chargeable-width calculation |
| Road-centre offset | Transverse offset of the carriageway centre |
| Girder-section dimensions | \(b_0\), \(b_a\), \(h_d\), \(h_p\), and, where applicable, \(b_{ta}\), \(h_{ta}\) |

All geometric dimensions are entered in **metres**.

The current geometry model assumes a symmetrical arrangement of the longitudinal girders within the deck width. The road-centre offset can be used to represent an eccentric carriageway. The geometry validation also checks the relationship between deck width, carriageway width and sidewalk widths.

## Loading cases currently represented

The current calculation workflow includes the following loading-case identifiers:

| Identifier | Description in the program |
|---|---|
| \(A_L\) | Loading case \(A_L\) |
| \(q_tr\) | Sidewalk loading |
| \(B_c\) | \(B_c\) vehicle loading |
| \(Mc80\) | Mc80 military vehicle |
| \(Mc120\) | Mc120 military vehicle |

The program evaluates the transverse distribution associated with these cases and reports the governing result for each evaluated girder. The detailed placement rules, load magnitudes, combinations and regulatory assumptions must be consulted in the implementation and its technical references.

## Results and generated files

After a successful run, the application currently writes the following outputs in the working directory:

| File or directory | Purpose |
|---|---|
| `crt_results.json` | Detailed input data, calculation parameters and results |
| `crt_summary.csv` | Tabular summary of transverse distribution coefficients |
| `plots/` | Figures generated by the plotting routines |

The CSV summary includes the girder identifier, transverse coordinate and the reported CRT values for \(A_L\), \(B_c\), \(Mc80\) and \(Mc120\). The detailed JSON output also retains the input geometry, section data, loading rules and calculation results.

The exact plot contents depend on the plotting routines available in the project version being executed.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Maglwe/Transverse_Distribution_Coefficient.git
cd Transverse_Distribution_Coefficient
```


### 2. Create and activate a virtual environment

**Windows — PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies


```bash
python -m pip install -r requirements.txt
```


## Usage

Run the application from the repository root:

```bash
python main.py
```

The program starts an interactive session. Follow the prompts to:

1. Select the bridge and section configuration.
2. Enter the bridge geometry.
3. Enter the girder-section dimensions.
4. Review any validation warnings or errors.
5. Allow the calculation and export routines to complete.

The program accepts decimal values with either a dot or a comma in the interactive floating-point inputs.

## Project structure

The exact package contents may evolve as development continues. The main application currently imports calculation modules responsible for bridge data, parameters, Guyon–Massonnet calculations, bridge classification, loading rules and influence calculations.

A representative structure is:

```text
Transverse_Distribution_Coefficient/
│
├── crt_guyon/
│   ├── __init__.py
│   ├── data.py
│   ├── parameters.py
│   ├── guyon.py
│   ├── type.py
│   ├── load.py
│   └── calculator.py
├── LICENSE
├── main.py
├── requirements.txt
└── README.md
```


## Validation, assumptions and limitations

The application includes input checks for several geometric conditions, such as positive dimensions, girder spacing, girder fit within the deck, carriageway width and the relationship between deck width and the sidewalk/carriageway widths. It also applies span-range and slenderness checks encoded for PSI-BA and VIPP configurations.

These checks are **not a complete code-compliance verification**. A warning or a successful validation does not certify that a bridge design satisfies every applicable structural, serviceability, fatigue, ultimate-limit-state or detailing requirement.

Before using results in a design context:

- verify the mechanical properties and section idealisations;
- verify the loading models, load positions and combinations against the selected standard;
- compare representative cases with trusted hand calculations, published examples or validated software;
- document the limits of applicability of the Guyon–Massonnet model;
- independently review all engineering assumptions and results.

---

# Section of future development:

The following two standards frameworks are identified as major directions for future development. **They are planned extensions, not a claim that the current version already implements full code-compliant design under either framework.**

<details>
<summary><strong>🇪🇺 EUROCODES — European standards for bridge design</strong></summary>

### Planned development: Eurocode framework

Future work will investigate the integration of the relevant Eurocodes for bridge loading and structural design, including:

- **EN 1990** — *Eurocode: Basis of structural design*.
- **EN 1991-2** — *Eurocode 1: Actions on structures — Part 2: Traffic loads on bridges*.
- **EN 1992-2** — *Eurocode 2: Design of concrete structures — Part 2: Concrete bridges — Design and detailing rules*.

The development will consider the applicable National Annexes, where relevant, and will distinguish the requirements for actions, combinations and concrete bridge design.

**Development objective:** provide a clearly documented Eurocode-oriented loading and verification framework, while preserving traceability between each implemented rule, its source and its calculation procedure.

</details>

<details>
<summary><strong>🇺🇸 AASHTO — American bridge design specifications</strong></summary>

### Planned development: AASHTO LRFD framework

Future work will investigate the **AASHTO LRFD Bridge Design Specifications** (*American Association of State Highway and Transportation Officials — Load and Resistance Factor Design*).

Areas to be studied include:

- bridge design loads and load combinations;
- vehicular live loads and their placement;
- transverse load distribution among longitudinal girders;
- relevant provisions for concrete bridge members;
- the assumptions and applicability limits associated with the selected analysis methods.

**Development objective:** establish a separate AASHTO LRFD-oriented calculation pathway, with its own loading definitions, combinations, assumptions and verification cases.

</details>

### Standards implementation principles

The Eurocode and AASHTO developments will be treated as **distinct regulatory frameworks**. Their load models, combinations, factors and verification requirements will not be mixed. Each implementation will be supported by traceable references, documented assumptions and benchmark examples.

---


## References

The current implementation is based on the French bridge-loading regulations and the Guyon–Massonnet method. The following references document the principal technical foundations used in the project.

### References used in the current implementation

1. **Ministère de l'Équipement, des Transports et du Logement.** (1971). *Fascicule 61 — Conception, calcul et épreuves des ouvrages d'art, Titre II : Programmes de charges et épreuves des ponts-routes*. Cahier des prescriptions communes (CPC).

   *Note: Specify whether the calculations refer to the original 1971 publication or the 1981 re-edition, which incorporates subsequent modifications.*

2. **Guyon, V.** (1949). Work on the calculation of bridge decks and transverse load distribution. *Annales des ponts et chaussées*. 

   Complementary numerical tables and developments by **Massonnet** form part of the practical application of the Guyon–Massonnet method.

3. **Ben Ouézdou, M.** (2018). *Cours d'ouvrages d'art — Tome 2 : Dimensionnement*. Polycopié, Département de Génie Civil, École Nationale d'Ingénieurs de Tunis (ENIT), Université Tunis El Manar. Updated November 2018.

   This course provides complementary technical material on bridge loading regulations, the design of beam bridges, and the application of the Guyon–Massonnet method.



## Contributing

Contributions, technical reviews and benchmark examples are welcome.

When proposing a change to a calculation module, please include, where possible:

1. the engineering assumption or rule being implemented;
2. its technical or regulatory reference;
3. a reproducible input example;
4. the expected result or an independent reference result;
5. tests demonstrating that existing calculations remain consistent.

## Disclaimer

This software is provided for **research, educational and engineering-computation development purposes**. It is not a substitute for applicable design standards, independent engineering review or professional judgement. The author makes no claim that the current implementation is certified or suitable, without further verification, for the design or assessment of a real bridge.

---

<div align="center">

**Transverse Distribution Coefficient Calculator**

*Bridging structural mechanics, numerical computation and bridge engineering.*

</div>
# Transverse_Distribution_Coefficient
