"""Settings for the critical raw materials analysis.

Everything that is a choice (which products, which countries, which years)
lives here, so that it can be checked and changed in one place.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "eurostat_raw.csv"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"

# Eurostat Comext dataset DS-045409, SDMX-CSV export.
EXPECTED_COLUMNS = [
    "DATAFLOW", "LAST UPDATE", "freq", "reporter", "partner", "product",
    "flow", "indicators", "TIME_PERIOD", "OBS_VALUE",
]
REPORTER = "EU27_2020"   # EU as a whole, current 27 members, applied to all years
FLOW_IMPORTS = "1"        # Comext flow code 1 = imports
FREQ_ANNUAL = "A"

# HS 6-digit codes, grouped into materials. A code missing from the data file
# is simply skipped (the report lists which codes were found).
MATERIALS = {
    "Lithium": {
        "283691": "Lithium carbonates",
        "282520": "Lithium oxide and hydroxide",
    },
    "Rare earths": {
        "280530": "Rare-earth metals, scandium and yttrium",
        "284610": "Cerium compounds",
        "284690": "Other rare-earth compounds",
    },
    "Cobalt": {
        "810520": "Cobalt mattes, unwrought cobalt, powders",
        "282200": "Cobalt oxides and hydroxides",
    },
    "Natural graphite": {
        "250410": "Natural graphite in powder or flakes",
        "250490": "Natural graphite, other forms",
    },
    "Permanent magnets": {
        "850511": "Permanent magnets of metal",
    },
}
# Upstream materials vs. a downstream product, reported separately.
DOWNSTREAM = {"Permanent magnets"}

# EU-27 member states (post-Brexit). Imports from these partners are intra-EU
# and are excluded: the question is dependence on suppliers outside the EU.
EU27 = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
    "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
    "SI", "ES", "SE",
}
# Eurostat's own totals, used only to check the country-level data.
AGG_EXTRA = "EXT_EU27_2020"
AGG_INTRA = "INT_EU27_2020"
# Comext codes for partners that cannot be attributed to a country.
UNATTRIBUTED_EXTRA = {"QW", "QZ"}   # extra-EU: not specified / confidential
UNATTRIBUTED_INTRA = {"QV", "QY"}   # intra-EU: not specified / confidential

FOCUS = {"CN": "China", "AU": "Australia"}

COUNTRY_NAMES = {
    "AR": "Argentina", "AU": "Australia", "BO": "Bolivia", "BR": "Brazil",
    "CA": "Canada", "CD": "DR Congo", "CG": "Congo", "CH": "Switzerland",
    "CL": "Chile", "CN": "China", "GB": "United Kingdom", "HK": "Hong Kong",
    "IN": "India", "JP": "Japan", "KR": "South Korea", "KZ": "Kazakhstan",
    "MG": "Madagascar", "MM": "Myanmar", "MY": "Malaysia", "MZ": "Mozambique",
    "NO": "Norway", "RU": "Russia", "TR": "Turkey", "TW": "Taiwan",
    "US": "United States", "VN": "Vietnam", "ZA": "South Africa",
    "ZM": "Zambia", "ZW": "Zimbabwe", "PH": "Philippines", "TH": "Thailand",
    "ID": "Indonesia", "MA": "Morocco", "UA": "Ukraine", "SG": "Singapore",
    "AE": "United Arab Emirates", "MX": "Mexico", "PE": "Peru",
    "BY": "Belarus", "LA": "Laos", "TZ": "Tanzania", "UZ": "Uzbekistan",
}

# Years: the baseline for the scenario is an average over the last
# BASELINE_YEARS complete years, to smooth single-year swings.
BASELINE_YEARS = 3

# Scenario: share of China's imports that is redirected to Australia.
SCENARIO_SHIFTS = [0.0, 0.10, 0.25, 0.50]

# Reference line for the HHI (0-10,000 scale): the 2023 US Merger Guidelines
# call a market "highly concentrated" above 1,800. Borrowed here only as a
# familiar benchmark, not as a policy threshold for trade.
HHI_HIGH = 1800

# Flag a material-year if more than this share of extra-EU imports is
# confidential or not attributed to a country.
UNATTRIBUTED_WARN = 0.05
