import logging
import httpx
from bs4 import BeautifulSoup
import yfinance as yf
import db

logger = logging.getLogger(__name__)

_FALLBACK: dict[str, list[str]] = {
    "LQ45": [
        "AALI","ADRO","AKRA","AMMN","AMRT","ANTM","ARTO","ASII","BBCA","BBNI",
        "BBRI","BBTN","BMRI","BRIS","BRMS","BRPT","BUKA","CPIN","EMTK","ENRG",
        "ESSA","EXCL","GOTO","HRUM","ICBP","INCO","INDF","INKP","INTP","ITMG",
        "JPFA","KLBF","MAPI","MBMA","MDKA","MEDC","MIKA","MNCN","PGAS","PTBA",
        "SMGR","TBIG","TLKM","TOWR","UNTR","UNVR",
    ],
    "IDX30": [
        "AALI","ADRO","AMMN","AMRT","ASII","BBCA","BBNI","BBRI","BMRI","BRIS",
        "BRPT","BUKA","EXCL","GOTO","ICBP","INCO","INDF","ITMG","KLBF","MAPI",
        "MDKA","MEDC","MIKA","PGAS","PTBA","SMGR","TLKM","TOWR","UNTR","UNVR",
    ],
}


def get_fallback_tickers() -> dict[str, list[str]]:
    return _FALLBACK


def _scrape_idx_members() -> dict[str, list[str]]:
    """
    Attempt to scrape current LQ45 and IDX30 constituents from IDX website.
    Raises ValueError if parsing is not reliable — caller falls back to hardcoded list.
    """
    url = "https://www.idx.co.id/en/market-data/stocks-data/index-constituent/"
    headers = {"User-Agent": "Mozilla/5.0"}
    with httpx.Client(timeout=15) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    result: dict[str, list[str]] = {}
    # Try to find index-specific sections by heading text
    for index_name in ["LQ45", "IDX30"]:
        section_tickers: list[str] = []
        # Look for a heading or label containing the index name
        heading = soup.find(string=lambda t: t and index_name in t)
        if heading:
            # Walk forward from the heading to find the associated table
            parent = heading.find_parent()
            table = None
            for _ in range(10):  # walk up to 10 ancestors
                if parent is None:
                    break
                table = parent.find_next("table")
                if table:
                    break
                parent = parent.find_parent()
            if table:
                for td in table.find_all("td"):
                    text = td.get_text(strip=True)
                    if 4 <= len(text) <= 6 and text.isupper() and text.isalpha():
                        section_tickers.append(text)
        if section_tickers:
            result[index_name] = list(dict.fromkeys(section_tickers))

    if len(result) < 2:
        raise ValueError(
            f"Could not reliably scrape both LQ45 and IDX30 constituents "
            f"(got {list(result.keys())}). Falling back to hardcoded list."
        )
    return result


def get_all_tickers(use_scrape: bool = True) -> list[str]:
    """Return deduplicated list of all tickers across LQ45 and IDX30."""
    members = _FALLBACK
    if use_scrape:
        try:
            members = _scrape_idx_members()
        except Exception as e:
            logger.warning("IDX scrape failed, using fallback: %s", e)
    seen: set[str] = set()
    result: list[str] = []
    for tickers in members.values():
        for t in tickers:
            if t not in seen:
                seen.add(t)
                result.append(t)
    return result


def seed_stocks_table(conn, use_scrape: bool = True) -> None:
    """Populate stocks and stock_indices tables from IDX data."""
    members = _FALLBACK
    if use_scrape:
        try:
            members = _scrape_idx_members()
        except Exception as e:
            logger.warning("IDX scrape failed during seed, using fallback: %s", e)

    all_tickers: set[str] = set()
    for tickers in members.values():
        all_tickers.update(tickers)

    for ticker in all_tickers:
        name, sector = ticker, "Unknown"
        try:
            info = yf.Ticker(f"{ticker}.JK").info
            name = info.get("longName") or info.get("shortName") or ticker
            sector = info.get("sector") or "Unknown"
        except Exception:
            pass
        db.upsert_stock(conn, ticker=ticker, name=name, sector=sector)
        indices = [idx for idx, tlist in members.items() if ticker in tlist]
        db.set_stock_indices(conn, ticker, indices)

    logger.info("Seeded %d stocks", len(all_tickers))
