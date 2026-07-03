# Pipeline status

_Last written 2026-07-03 22:11 UTC by `python -m pipeline.cli`._

## Latest run per source

| Source | Status | Rows | When (UTC) | Detail |
|---|---|---:|---|---|
| authority_meta | ✅ ok | 650 | 2026-07-03T22:06:56+00:00 |  |
| housing_delivery | ✅ ok | 8892 | 2026-07-03T22:09:34+00:00 |  |
| mhclg_applications | ✅ ok | 3430734 | 2026-07-03T22:08:23+00:00 |  |
| pins_appeals | ✅ ok | 94036 | 2026-07-03T22:09:30+00:00 |  |

If a download failed the most likely cause is a moved gov.uk asset URL: open the
landing page listed in `config/sources.yml`, copy the new file URL into the config,
and rerun `make pipeline` (cached raw files make partial reruns cheap).
