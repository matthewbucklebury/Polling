"""Metric catalogue: one place that names every metric, how to format it, which
direction is 'good', where it comes from, and its caveats. Drives the league
table pickers, map legend, and the in-app data dictionary."""

CAVEAT_EOT = (
    "Since ~2013 a growing share of decisions (now ~40% nationally) is made under a "
    "performance agreement — a planning performance agreement, extension of time or "
    "EIA extension. For those, 'in time' means 'within the agreed (extended) time', "
    "which flatters headline speed. Compare the headline and statutory-basis measures."
)
CAVEAT_COVID = "2020Q2–2021Q4 volumes and speed are distorted by COVID-19 disruption."
CAVEAT_REORG = (
    "Where districts merged (2009–2023 reorganisations) predecessor counts are summed "
    "into the successor authority, so series are continuous but pre-merger values "
    "describe a different set of councils. Pre-2009 legacy authorities that cannot be "
    "mapped are excluded from rankings."
)
CAVEAT_SMALL_N = (
    "Quarterly denominators can be tiny (especially major residential and appeals). "
    "Use the rolling-annual (4Q) window and respect minimum-volume thresholds."
)

MHCLG = "MHCLG planning application statistics, PS1/PS2 open data (district matters)"
PINS = "Planning Inspectorate appeals casework database (case level)"
LT122 = "MHCLG Live Table 122 (net additional dwellings)"
HDT = "MHCLG Housing Delivery Test measurement"

METRICS = {
    # --- approval ---
    "approval_rate_all": {"label": "Approval rate (all applications)", "unit": "%", "higher_is": "good",
                          "category": "Approval", "source": MHCLG,
                          "description": "Applications granted as a share of all decisions.",
                          "caveats": [CAVEAT_REORG, CAVEAT_SMALL_N]},
    "approval_rate_major": {"label": "Approval rate (major)", "unit": "%", "higher_is": "good",
                            "category": "Approval", "source": MHCLG,
                            "description": "Major developments granted as a share of major decisions.",
                            "caveats": [CAVEAT_SMALL_N]},
    "approval_rate_major_res": {"label": "Approval rate (major residential)", "unit": "%", "higher_is": "good",
                                "category": "Approval", "source": MHCLG,
                                "description": "Major dwelling schemes (10+ homes) granted as a share of decisions. The headline housing-friction measure.",
                                "caveats": [CAVEAT_SMALL_N, CAVEAT_REORG]},
    "approval_rate_minor": {"label": "Approval rate (minor)", "unit": "%", "higher_is": "good",
                            "category": "Approval", "source": MHCLG,
                            "description": "Minor developments granted as a share of minor decisions.", "caveats": []},
    "approval_rate_minor_res": {"label": "Approval rate (minor residential)", "unit": "%", "higher_is": "good",
                                "category": "Approval", "source": MHCLG,
                                "description": "Minor dwelling schemes (1–9 homes) granted as a share of decisions.", "caveats": []},
    "approval_rate_householder": {"label": "Approval rate (householder)", "unit": "%", "higher_is": "good",
                                  "category": "Approval", "source": MHCLG,
                                  "description": "Householder applications (extensions etc.) granted as a share of decisions.", "caveats": []},
    # --- speed ---
    "pct_intime_headline_major": {"label": "Major decisions in time (headline)", "unit": "%", "higher_is": "good",
                                  "category": "Speed", "source": MHCLG,
                                  "description": "Major decisions within 13 weeks OR within an agreed extended period. This is the government's headline performance measure.",
                                  "caveats": [CAVEAT_EOT, CAVEAT_COVID]},
    "pct_intime_statutory_major": {"label": "Major decisions within statutory 13 weeks", "unit": "%", "higher_is": "good",
                                   "category": "Speed", "source": MHCLG,
                                   "description": "Of major decisions made without a performance agreement, the share within the statutory 13 weeks.",
                                   "caveats": [CAVEAT_EOT, CAVEAT_COVID]},
    "pct_intime_headline_minor": {"label": "Minor decisions in time (headline)", "unit": "%", "higher_is": "good",
                                  "category": "Speed", "source": MHCLG,
                                  "description": "Minor decisions within 8 weeks or an agreed extended period.", "caveats": [CAVEAT_EOT]},
    "pct_intime_statutory_minor": {"label": "Minor decisions within statutory 8 weeks", "unit": "%", "higher_is": "good",
                                   "category": "Speed", "source": MHCLG,
                                   "description": "Of minor decisions made without a performance agreement, the share within the statutory 8 weeks.",
                                   "caveats": [CAVEAT_EOT]},
    "pct_intime_headline_all": {"label": "All decisions in time (headline)", "unit": "%", "higher_is": "good",
                                "category": "Speed", "source": MHCLG,
                                "description": "All decisions within their statutory or agreed period.", "caveats": [CAVEAT_EOT]},
    "pct_intime_statutory_all": {"label": "All decisions within statutory time", "unit": "%", "higher_is": "good",
                                 "category": "Speed", "source": MHCLG,
                                 "description": "Decisions without an agreement made within statutory time.", "caveats": [CAVEAT_EOT]},
    "eot_share_all": {"label": "Decisions under extension agreements", "unit": "%", "higher_is": "bad",
                      "category": "Speed", "source": MHCLG,
                      "description": "Share of all decisions made under a performance agreement / extension of time. The national rise of this share is one of the biggest changes in the system.",
                      "caveats": [CAVEAT_EOT]},
    "eot_share_major": {"label": "Major decisions under extension agreements", "unit": "%", "higher_is": "bad",
                        "category": "Speed", "source": MHCLG,
                        "description": "Share of major decisions made under an agreement.", "caveats": [CAVEAT_EOT]},
    "eot_gap_major": {"label": "EOT flattering gap (major)", "unit": "pp", "higher_is": "bad",
                      "category": "Speed", "source": MHCLG,
                      "description": "Headline in-time share minus statutory-basis share for major decisions — how much extension agreements flatter the headline.",
                      "caveats": [CAVEAT_EOT]},
    "eot_gap_minor": {"label": "EOT flattering gap (minor)", "unit": "pp", "higher_is": "bad",
                      "category": "Speed", "source": MHCLG, "description": "As above, for minor decisions.", "caveats": [CAVEAT_EOT]},
    # --- volume ---
    "received_all": {"label": "Applications received", "unit": "count", "higher_is": "neutral",
                     "category": "Volume", "source": MHCLG,
                     "description": "Planning applications received in the period.", "caveats": [CAVEAT_COVID]},
    "decisions_all": {"label": "Applications decided", "unit": "count", "higher_is": "neutral",
                      "category": "Volume", "source": MHCLG,
                      "description": "Planning applications decided in the period.", "caveats": [CAVEAT_COVID]},
    "decisions_major_res": {"label": "Major residential decisions", "unit": "count", "higher_is": "neutral",
                            "category": "Volume", "source": MHCLG,
                            "description": "Major dwelling decisions in the period.", "caveats": [CAVEAT_SMALL_N]},
    "decisions_vs_5yr": {"label": "Decision volume vs own 5-year average", "unit": "index", "higher_is": "neutral",
                         "category": "Volume", "source": MHCLG,
                         "description": "Rolling-annual decisions as a percentage of the authority's own previous five-year average (100 = on trend).",
                         "caveats": [CAVEAT_COVID, CAVEAT_REORG]},
    # --- appeals ---
    "overturn_rate": {"label": "Appeals overturn rate", "unit": "%", "higher_is": "bad",
                      "category": "Appeals", "source": PINS,
                      "description": "Planning/householder/commercial appeals allowed as a share of appeals decided. A high rate suggests the authority refuses schemes inspectors consider acceptable.",
                      "caveats": [CAVEAT_SMALL_N, "Appeal decisions lag the original refusal by several quarters."]},
    "refusal_overturn_rate": {"label": "Refusals overturned at appeal", "unit": "%", "higher_is": "bad",
                              "category": "Appeals", "source": PINS,
                              "description": "Of appeals against refusals, the share allowed.", "caveats": [CAVEAT_SMALL_N]},
    "appeal_rate_refusals": {"label": "Appeal rate on refusals", "unit": "%", "higher_is": "neutral",
                             "category": "Appeals", "source": PINS,
                             "description": "Appeals (against refusal) decided in the period as a share of refusals in the period. Timing mismatch makes this indicative only.",
                             "caveats": ["Numerator (appeals decided) and denominator (refusals) are from different cohorts of applications; treat as an indicative rate.", CAVEAT_SMALL_N]},
    "appeals_decided": {"label": "Appeals decided", "unit": "count", "higher_is": "neutral",
                        "category": "Appeals", "source": PINS,
                        "description": "Planning, householder and commercial appeals receiving a substantive decision.", "caveats": []},
    "overturn_rate_major_res": {"label": "Major residential overturn rate", "unit": "%", "higher_is": "bad",
                                "category": "Appeals", "source": PINS,
                                "description": "Major dwellings appeals allowed as a share decided.", "caveats": [CAVEAT_SMALL_N]},
    # --- friction ---
    "friction_score": {"label": "Friction score", "unit": "score", "higher_is": "bad",
                       "category": "Friction", "source": "Composite (see settings.yml)",
                       "description": "Weighted mean of percentile ranks: low major-residential approval (0.40), slow statutory-basis major decisions (0.30), high appeal overturn rate (0.30). 0 = least friction, 100 = most. Weights are configurable in config/settings.yml and the components are always shown alongside.",
                       "caveats": ["A percentile rank is relative: the median authority scores 50 by construction.", CAVEAT_SMALL_N]},
    "friction_approval_rate_major_res": {"label": "Friction component: major residential approval", "unit": "score",
                                         "higher_is": "bad", "category": "Friction", "source": "Composite",
                                         "description": "Inverse percentile of major residential approval rate.", "caveats": []},
    "friction_pct_intime_statutory_major": {"label": "Friction component: statutory-basis speed", "unit": "score",
                                            "higher_is": "bad", "category": "Friction", "source": "Composite",
                                            "description": "Inverse percentile of major decisions within statutory 13 weeks.", "caveats": []},
    "friction_overturn_rate": {"label": "Friction component: appeal overturns", "unit": "score",
                               "higher_is": "bad", "category": "Friction", "source": "Composite",
                               "description": "Percentile of appeals overturn rate.", "caveats": []},
}

ANNUAL_METRICS = {
    "net_additions": {"label": "Net additional dwellings", "unit": "count", "higher_is": "good",
                      "category": "Delivery", "source": LT122,
                      "description": "Absolute annual change in dwelling stock: new build + conversions + change of use − demolitions. Financial years.",
                      "caveats": ["2004–2007 figures for some authorities were imputed; 2024-25 is provisional.", CAVEAT_REORG]},
    "hdt_measure": {"label": "Housing Delivery Test score", "unit": "%", "higher_is": "good",
                    "category": "Delivery", "source": HDT,
                    "description": "Homes delivered over three years as a percentage of homes required. Below 95% triggers an action plan, below 85% a buffer, below 75% the presumption in favour of sustainable development.",
                    "caveats": ["The 2023 measurement is the latest published; the HDT was paused pending the revised NPPF."]},
    "hdt_required": {"label": "HDT homes required (3yr)", "unit": "count", "higher_is": "neutral",
                     "category": "Delivery", "source": HDT, "description": "Three-year total homes required.", "caveats": []},
    "hdt_delivered": {"label": "HDT homes delivered (3yr)", "unit": "count", "higher_is": "neutral",
                      "category": "Delivery", "source": HDT, "description": "Three-year total homes delivered.", "caveats": []},
}

# Metrics offered on the map / league tables (order = UI order).
RANKABLE = [
    "friction_score", "approval_rate_all", "approval_rate_major_res", "approval_rate_minor_res",
    "approval_rate_householder", "pct_intime_headline_major", "pct_intime_statutory_major",
    "pct_intime_headline_minor", "pct_intime_statutory_minor", "eot_share_all", "eot_gap_major",
    "overturn_rate", "refusal_overturn_rate", "appeal_rate_refusals", "appeals_decided",
    "decisions_all", "received_all", "decisions_vs_5yr", "decisions_major_res",
]
# Denominator guarding each rankable metric (metric -> (denominator metric, settings key)).
MIN_DENOMINATORS = {
    "approval_rate_all": ("decisions_all", "min_decisions_4q"),
    "approval_rate_major_res": ("decisions_major_res", "min_major_4q"),
    "approval_rate_minor_res": ("decisions_minor_res", "min_decisions_4q"),
    "approval_rate_householder": ("decisions_householder", "min_decisions_4q"),
    "pct_intime_headline_major": ("decisions_major", "min_major_4q"),
    "pct_intime_statutory_major": ("decisions_major", "min_major_4q"),
    "pct_intime_headline_minor": ("decisions_minor", "min_decisions_4q"),
    "pct_intime_statutory_minor": ("decisions_minor", "min_decisions_4q"),
    "overturn_rate": ("appeals_decided", "min_appeals_4q"),
    "refusal_overturn_rate": ("appeals_decided", "min_appeals_4q"),
    "appeal_rate_refusals": ("appeals_decided", "min_appeals_4q"),
    "overturn_rate_major_res": ("appeals_decided_major_res", "min_appeals_4q"),
}
