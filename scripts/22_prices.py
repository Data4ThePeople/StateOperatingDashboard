"""Price index for putting dollar amounts from different years on one footing.

R-CPI-U-RS (BLS research series, all items, U.S. city average, annual average, Dec 1977=100). This is the
index the Census Bureau uses to compare household income across years. Writes data/processed/prices.json
with no measures, only extras.price_index {year: annual average}.
"""
import pandas as pd

from common import RAW, cached, write_json

URL = "https://www.bls.gov/cpi/research-series/r-cpi-u-rs-allitems.xlsx"

if __name__ == "__main__":
    path = RAW / "prices" / "r-cpi-u-rs-allitems.xlsx"
    cached(path, URL)
    x = pd.read_excel(path, header=None)
    head = x.index[x[0].astype(str).str.strip() == "YEAR"][0]
    t = x.iloc[head + 1:, [0, 13]].dropna()
    t = t[pd.to_numeric(t[0], errors="coerce").notna() & pd.to_numeric(t[13], errors="coerce").notna()]
    idx = {str(int(y)): float(v) for y, v in zip(t[0], t[13])}
    assert len(idx) == len(t), "duplicate years in R-CPI-U-RS"
    for y in ("2014", "2019", "2024"):
        assert y in idx, f"R-CPI-U-RS has no {y} annual average"
    write_json("prices.json", {"metrics": {}, "counties": {}, "ohio": {},
                               "extras": {"price_index": {"name": "R-CPI-U-RS, annual average", "base_year": "2024", "years": idx}}})
    print({y: round(idx[y], 3) for y in ("2014", "2019", "2024")}, "2014 to 2024 factor", round(idx["2024"] / idx["2014"], 4))
