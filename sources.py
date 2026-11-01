"""
Λήψη τρεχουσών τιμών από το διαδίκτυο (μόνο βιβλιοθήκες της Python).

Πηγές (ενημερώνονται από τα επίσημα sites των παρόχων):
  Ρεύμα:         https://timesrevmatos.gr/api/plans.json   (ανοιχτά δεδομένα CC-BY-4.0)
  Φυσικό αέριο:  https://timesrevmatos.gr/fysiko-aerio/
  Internet:      https://agorasmart.gr/internet
  Κινητή:        https://agorasmart.gr/mobile
"""
import json
import os
import re
import ssl
import urllib.request

import mini_html

URLS = {
    "electricity": "https://timesrevmatos.gr/api/plans.json",
    "gas": "https://timesrevmatos.gr/fysiko-aerio/",
    "internet": "https://agorasmart.gr/internet",
    "mobile": "https://agorasmart.gr/mobile",
}
SOURCE_NAMES = {
    "electricity": "timesrevmatos.gr", "gas": "timesrevmatos.gr",
    "internet": "agorasmart.gr", "mobile": "agorasmart.gr",
}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"

SLUGS = {"dei": "ΔΕΗ", "protergia": "Protergia", "heron": "ΗΡΩΝ", "nrg": "NRG", "enerwave": "Enerwave",
         "eunice": "Eunice", "volton": "Volton", "zenith": "ZeniΘ", "elinoil": "ΕΛΙΝ",
         "ote-estate": "OTE Estate", "fysiko-aerio": "Φυσικό Αέριο ΕΕΕ", "s-energy": "S Energy"}
GAS_PREFIX = [("Φυσικό Αέριο Ελλάδος", "Φυσικό Αέριο ΕΕΕ"), ("Φυσικό Αέριο", "Φυσικό Αέριο ΕΕΕ"),
              ("ΗΡΩΝ", "ΗΡΩΝ"), ("Heron", "ΗΡΩΝ"), ("NRG", "NRG"), ("Protergia", "Protergia"),
              ("ΔΕΗ", "ΔΕΗ"), ("ZeniΘ", "ZeniΘ"), ("Zenith", "ZeniΘ"), ("ΖΕΝΙΘ", "ZeniΘ"),
              ("ΕΛΙΝ", "ΕΛΙΝ"), ("ελίν", "ΕΛΙΝ"), ("Enerwave", "Enerwave"), ("Volton", "Volton"),
              ("Eunice", "Eunice"), ("EUNICE", "Eunice")]
TELCOS = ["Vodafone", "Nova", "Telekom", "Cosmote", "Inalan", "Starlink", "Frog Mobile", "Cyta", "Wind"]

# προγράμματα που δεν τα δικαιούται κάθε νοικοκυριό
EXCLUDE_WORDS = ("φοιτητ", "student", "μόνο για", "αντλία θερμότητας", "heatpump", "drivegreen", "heatgreen",
                 "ηλεκτρικού αυτοκινήτου", "κατόχους ev", "συμψηφισμ", "εκτός κατάταξης", "ήλιος")


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "el-GR,el;q=0.9"})
    try:
        import certifi  # πιστοποιητικά https (απαραίτητα στο Android)
        ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001
        ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        raw = r.read()
        enc = r.headers.get_content_charset() or "utf-8"
    return raw.decode(enc, errors="replace")


def num(s):
    if s is None:
        return None
    s = str(s).strip().replace("€", "").replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


# ------------------------------------------------------------------ ρεύμα
def parse_electricity(text):
    data = json.loads(text)
    out = []
    for prov in data.get("providers", []):
        pname = SLUGS.get(prov.get("slug"), prov.get("name", "?"))
        for p in prov.get("plans", []):
            if p.get("pricingStatus") != "priced" or not p.get("monthlyCost"):
                continue
            ttype = {"stable": "Σταθερό (μπλε)", "floating": "Κυμαινόμενο (κίτρινο)",
                     "special": "Ειδικό (πράσινο)"}.get(p.get("tariffType"))
            if not ttype:
                continue  # νυχτερινά/δυναμικά θέλουν ειδικό μετρητή
            blob = " ".join(str(p.get(k) or "") for k in ("name", "notes", "discountCondition")).lower()
            if any(w in blob for w in EXCLUDE_WORDS):
                continue
            mc = {int(k): (v.get("withDiscount"), v.get("base")) for k, v in p["monthlyCost"].items()}
            out.append({
                "provider": pname, "name": p.get("name"), "type": ttype,
                "price": p.get("priceWithDiscount") or p.get("pricePerKwh"),
                "price_base": p.get("pricePerKwh"),
                "fee": p.get("monthlyFee"), "fee_bands": None, "tiers": None, "tiers_base": None,
                "mc": mc, "months": p.get("contractMonths") or 0,
                "condition": p.get("discountCondition") or "",
                "url": p.get("officialSourceUrl") or prov.get("website") or "",
                "price_month": p.get("priceMonth") or "",
            })
    if len(out) < 10:
        raise ValueError("Βρέθηκαν πολύ λίγα τιμολόγια ρεύματος")
    return out


# ------------------------------------------------------------------ φυσικό αέριο
def _split_prices(cell):
    toks = re.findall(r"\d+,\d+", re.sub(r"(?<=\d)(?=0,\d)", " ", cell))
    return [num(t) for t in toks]


def _gas_provider(name):
    for pre, canon in GAS_PREFIX:
        if name.startswith(pre):
            return canon, name[len(pre):].strip()
    return name.split(" ")[0], " ".join(name.split(" ")[1:])


def parse_gas(html):
    """Διαβάζει τους πίνακες τιμών αερίου. Δουλεύει όποια κελιά (th/td) κι αν χρησιμοποιεί η σελίδα."""
    root = mini_html.parse(html)
    out, tables_seen = [], 0
    for table in root.find_all("table"):
        heads = None
        for tr in table.find_all("tr"):
            texts = [c.text() for c in tr.cells()]
            low = [t.lower() for t in texts]
            # γραμμή-επικεφαλίδα: έχει «€/kWh» και καμία τιμή
            if any("€/kwh" in t for t in low) and not any(re.search(r"\d,\d{3}", t) for t in texts):
                heads = low
                tables_seen += 1
                continue
            if heads is None or len(texts) < 4:
                continue
            if any("φόρμουλα" in h or "τύπος υπολογ" in h for h in heads):
                continue  # τιμές με φόρμουλα TTF, όχι συγκεκριμένη τιμή

            def g(key):
                i = next((i for i, h in enumerate(heads) if key in h), None)
                return texts[i] if i is not None and i < len(texts) else ""
            kind = "Κυμαινόμενο" if any("μήνας" in h for h in heads) else "Σταθερό"
            raw = re.sub(r"\s*Φθηνότερο\s*", " ", g("πάροχος") or texts[0]).strip()
            prov, pname = _gas_provider(raw)
            prices = [x for x in _split_prices(g("€/kwh")) if x and 0.01 < x < 0.5]
            if not prices:
                continue
            fees = [num(x) for x in re.findall(r"\d+[,.]\d+", g("πάγιο"))]
            cond = g("προϋπόθεση")
            dual = bool(re.search(r"ρεύμα|dual|power\+gas", cond, re.I))
            conn_t = g("σύνδεση").lower()
            conn = "K" if "κεντρ" in conn_t else ("B" if "δύο" in conn_t else "A")
            months = num((re.search(r"(\d+)\s*μήν", g("διάρκεια")) or [None, None])[1])
            base = prices[0]
            disc = prices[-1] if len(prices) > 1 else None
            out.append({
                "provider": prov, "name": pname, "type": kind,
                "price": disc if (disc and not dual) else base,
                "price_dual": disc if (disc and dual) else None,
                "fee": (fees[-1] if fees else 0.0), "conn": conn, "months": int(months or 0),
                "condition": cond if cond not in ("-", "–") else "", "price_month": g("μήνας"),
                "url": URLS["gas"],
            })
    if len(out) < 5:
        if not tables_seen:
            raise ValueError("η σελίδα δεν έχει πια πίνακα τιμών (άλλαξε μορφή)")
        raise ValueError(f"βρέθηκαν μόνο {len(out)} τιμολόγια")
    return out


# ------------------------------------------------------------------ internet / κινητή
BADGES = ("Φθηνότερο", "Fiber", "5G Home", "Δορυφορικό", "🛰", "Απεριόριστα", "VDSL")


def _items(html):
    root = mini_html.parse(html)
    lis = [li for li in root.find_all("li") if "€/μήνα" in li.text()]
    leaf = [li for li in lis if not any("€/μήνα" in x.text() for x in li.find_all("li"))]
    return [li.text(lines=True) for li in leaf]


def _title(lines):
    t = lines[0]
    changed = True
    while changed:
        changed = False
        for b in BADGES:
            if t.endswith(b) and len(t) > len(b) + 2:
                t, changed = t[: -len(b)].strip(), True
    return t


def _provider(full):
    m = re.search(r"(" + "|".join(TELCOS) + r")\s*·", full)
    return m.group(1) if m else None


def _price(full):
    ps = re.findall(r"(\d+,\d{2})\s*€\s*/\s*μήνα", full)
    return num(ps[-1]) if ps else None


def _promo(full):
    m = re.search(r"Πρώτοι\s+(\d+)\s+μήνες:\s*(\d+,\d{2})", full)
    return (num(m.group(2)), int(m.group(1))) if m else None


def _onetime(full):
    m = re.findall(r"\+(\d+)\s*€\s*(?:τέλος ενεργοποίησης|ενεργοποίηση|εφάπαξ)", full)
    m2 = re.findall(r"\(€(\d+)\s*αποστολή\)", full)
    return sum(float(x) for x in m + m2)


def parse_internet(html):
    out = []
    for lines in _items(html):
        full = " \n ".join(lines)
        prov, price = _provider(full), _price(full)
        sp = re.search(r"(\d{2,5})\s*Mbps\s*download", full)
        if not prov or not price or not sp:
            continue
        with_mob = re.search(r"(\d+,\d{2})€ με κινητή \w+ \((\d+,\d{2})€ χωρίς\)", full)
        pwm = None
        if with_mob:
            pwm, price = num(with_mob.group(1)), num(with_mob.group(2))
        tech = "Δορυφορικό" if "Δορυφορ" in full else ("4G/5G" if re.search(r"FWA|5G Home|4G", full) else "Fiber/VDSL")
        note = ""
        if prov == "Inalan":
            note = "Μόνο σε περιοχές κάλυψης Inalan"
        elif "χωρίς δέσμευση" in full:
            note = "Χωρίς δέσμευση"
        out.append({"provider": "Telekom" if prov == "Cosmote" else prov, "name": _title(lines).replace(prov, "").strip() or _title(lines),
                    "tech": tech, "speed": int(sp.group(1)), "price": price, "price_with_mobile": pwm,
                    "onetime": _onetime(full), "promo": _promo(full), "note": note, "url": URLS["internet"]})
    if len(out) < 5:
        raise ValueError("Βρέθηκαν πολύ λίγα πακέτα internet")
    return out


def parse_mobile(html):
    out = []
    for lines in _items(html):
        full = " \n ".join(lines)
        prov, price = _provider(full), _price(full)
        if not prov or not price:
            continue
        if re.search(r"∞\s*data|Απεριόριστα GB|Απεριόριστα data", full):
            gb = 9999.0
        else:
            m = re.search(r"(\d+(?:,\d+)?)\s*GB", full)
            gb = num(m.group(1)) if m else 0.0
        later = None
        esc = re.search(r"€\s?(\d+[.,]\d{2}) μήνες 1-12, €\s?(\d+[.,]\d{2}) μήνες 13-24", full)
        if esc:
            price, later = num(esc.group(1)), num(esc.group(2))
        alone = None
        mg = re.search(r"MagentaONE \(χωρίς:?\s*(\d+(?:,\d+)?)\s*€\)", full)
        if mg:
            alone = num(mg.group(1))
        out.append({"provider": "Telekom" if prov == "Cosmote" else prov, "name": _title(lines),
                    "type": "Καρτοκινητό" if "καρτοκινητ" in full.lower() else "Συμβόλαιο",
                    "gb": gb, "unlimited_voice": ("Απεριόριστα λεπτά" in full or "απεριόριστη φωνή" in full.lower())
                    and "μη απεριόριστη" not in full.lower(),
                    "price": price, "price_later": later, "price_alone": alone, "url": URLS["mobile"]})
    if len(out) < 5:
        raise ValueError("Βρέθηκαν πολύ λίγα πακέτα κινητής")
    return out


# ------------------------------------------------------------------ kilovatora.gr (2η πηγή, στοιχεία ΡΑΑΕΥ / ΕΕΤΤ)
GR_MONTHS = {"ιαν": 1, "φεβ": 2, "μαρ": 3, "απρ": 4, "μαϊ": 5, "μαΐ": 5, "μαι": 5, "ιουν": 6, "ιουλ": 7,
             "αυγ": 8, "σεπ": 9, "οκτ": 10, "νοε": 11, "δεκ": 12}
KV_SLUGS = {"deh": "ΔΕΗ", "elin": "ΕΛΙΝ", "zenith": "ZeniΘ", "hrwn": "ΗΡΩΝ", "fysiko-aerio": "Φυσικό Αέριο ΕΕΕ",
            "eunice": "Eunice", "ote-estate": "OTE Estate", "protergia": "Protergia", "solar-energy": "S Energy",
            "nrg": "NRG", "volton": "Volton", "volterra": "Volterra", "enerwave": "Enerwave", "efa-energy": "EFA Energy",
            "cosmote": "Telekom", "vodafone": "Vodafone", "nova": "Nova", "inalan": "Inalan"}
KV_STALE = ("ήταν εμπορικά διαθέσιμο", "εμπορικά διαθέσιμο έως", "εμπορικά διαθέσιμο από", "διαθέσιμο έως",
            "διατίθετο", "φοιτητ", "student", "συμψηφισμ", "μόνο data", "αφορά στην κατηγορία")
KV_TYPES = {"σταθερό": "Σταθερό (μπλε)", "κυμαινόμενο": "Κυμαινόμενο (κίτρινο)", "ειδικό": "Ειδικό (πράσινο)"}


def _kv_month_ok(text, max_age=2):
    import datetime
    m = re.search(r"(Ιαν|Φεβ|Μαρ|Απρ|Μα[ϊΐι]|Ιουν|Ιουλ|Αυγ|Σεπ|Οκτ|Νοε|Δεκ)\w*\.?\s+(20\d\d)", text)
    if not m:
        return True
    mon = GR_MONTHS.get(m.group(1).lower()[:4]) or GR_MONTHS.get(m.group(1).lower()[:3])
    t = datetime.date.today()
    return (t.year * 12 + t.month) - (int(m.group(2)) * 12 + (mon or t.month)) <= max_age


def _kv_rows(html):
    """Επιστρέφει λίστες (header->κείμενο, όνομα, πάροχος, πλήρες κείμενο γραμμής)."""
    root = mini_html.parse(html)
    out = []
    for table in root.find_all("table"):
        heads = [th.text().lower() for th in table.find_all("th")]
        if not any("πρόγραμμα" in h for h in heads):
            continue
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 4:
                continue
            cells = {heads[i]: td.text() for i, td in enumerate(tds) if i < len(heads)}
            link = next((a for td in tds for a in td.find_all("a") if "/paketo/" in a.attrs.get("href", "")), None)
            if link is None:
                continue
            href = link.attrs.get("href", "")
            m = re.search(r"/paketo/([a-z0-9-]+?)-(?:revma|aerio|statheri|kiniti)/", href) or \
                re.search(r"/paketo/([a-z0-9-]+)/\d+", href)
            slug = m.group(1) if m else ""
            prov = KV_SLUGS.get(slug, slug.replace("-", " ").title())
            out.append((cells, link.text(), prov, " ".join(cells.values()), href))
    return out


def _cell(cells, key):
    return next((v for k, v in cells.items() if key in k), "")


def parse_kv_electricity(html):
    out = []
    for cells, name, prov, full, href in _kv_rows(html):
        low = full.lower()
        price = num(_cell(cells, "€/kwh"))
        if price is None or not (0.05 < price < 0.6) or any(w in low for w in KV_STALE) or not _kv_month_ok(full):
            continue
        ttype = KV_TYPES.get(_cell(cells, "τύπος").strip().lower())
        if not ttype:
            continue
        out.append({"provider": prov, "name": name, "type": ttype, "price": price, "price_base": price,
                    "fee": num(_cell(cells, "πάγιο")) or 0.0, "fee_bands": None, "tiers": None, "tiers_base": None,
                    "mc": None, "months": 0, "condition": _cell(cells, "σημειώσ")[:160],
                    "url": "https://kilovatora.gr" + href if href.startswith("/") else href, "price_month": ""})
    if len(out) < 10:
        raise ValueError("Βρέθηκαν πολύ λίγα τρέχοντα τιμολόγια ρεύματος")
    return out


def parse_kv_gas(html):
    out, stale = [], 0
    for cells, name, prov, full, href in _kv_rows(html):
        low = full.lower()
        price = num(_cell(cells, "€/kwh"))
        if price is None or not (0.01 < price < 0.5) or any(w in low for w in KV_STALE):
            continue
        if not _kv_month_ok(full):
            stale += 1
            continue
        dual = bool(re.search(r"σε συνδυασμό|dual|συνδυαστικ", low))
        conn = "K" if re.search(r"κοινόχρηστ|κεντρικ|central|building", name.lower()) else "A"
        out.append({"provider": prov, "name": name, "type": _cell(cells, "τύπος").strip() or "",
                    "price": None if dual else price, "price_dual": price if dual else None,
                    "fee": num(_cell(cells, "πάγιο")) or 0.0, "conn": conn, "months": 0,
                    "condition": _cell(cells, "σημειώσ")[:160], "price_month": "",
                    "url": "https://kilovatora.gr" + href if href.startswith("/") else href})
    if len(out) < 5:
        if stale:
            raise ValueError(f"έχει μόνο παλιές τιμές ({stale} τιμολόγια παλαιότερα των 2 μηνών)")
        raise ValueError("βρέθηκαν πολύ λίγα τρέχοντα τιμολόγια")
    return out


def parse_kv_internet(html):
    out = []
    for cells, name, prov, full, href in _kv_rows(html):
        kind = _cell(cells, "τύπος").strip().lower()
        if kind not in ("σταθερή & internet", "internet"):
            continue  # πακέτα με TV/κινητή δεν συγκρίνονται εδώ
        sp_t = _cell(cells, "ταχύτητα")
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*(gbps|mbps)", sp_t, re.I)
        price = num(_cell(cells, "τιμή"))
        if not m or not price or any(w in full.lower() for w in KV_STALE):
            continue
        speed = int(num(m.group(1)) * (1000 if m.group(2).lower() == "gbps" else 1))
        tech = "Δορυφορικό" if "sat" in name.lower() else (
            "4G/5G" if re.search(r"5g|4g|wireless", name, re.I) else "Fiber/VDSL")
        out.append({"provider": prov, "name": name, "tech": tech, "speed": speed, "price": price,
                    "price_with_mobile": None, "onetime": 349.0 if "349" in full else 0.0, "promo": None,
                    "note": "", "url": "https://kilovatora.gr" + href if href.startswith("/") else href})
    if len(out) < 5:
        raise ValueError("Βρέθηκαν πολύ λίγα πακέτα internet")
    return out


def parse_kv_mobile(html):
    out = []
    for cells, name, prov, full, href in _kv_rows(html):
        low = full.lower()
        price = num(_cell(cells, "τιμή"))
        if not price or any(w in low for w in KV_STALE):
            continue
        det = _cell(cells, "λεπτομ")
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*GB", name, re.I)
        if "απεριόριστα gb" in det.lower() or "απεριόριστα δεδομένα" in det.lower() or "unlimited all" in name.lower():
            gb = 9999.0
        elif m:
            gb = num(m.group(1))
        else:
            m2 = re.search(r"Data:\s*(\d+(?:[.,]\d+)?)\s*GB", det)
            gb = num(m2.group(1)) if m2 else 0.0
        unl = bool(re.search(r"απεριόριστ\w*\s+(λεπτ|ομιλ|προς)", det.lower())) or "unlimited ομιλία" in name.lower()
        if name.upper().startswith("FROG"):
            prov = "Frog Mobile"
        out.append({"provider": prov, "name": name, "type": _cell(cells, "τύπος").strip() or "Συμβόλαιο",
                    "gb": gb, "unlimited_voice": unl, "price": price, "price_later": None, "price_alone": None,
                    "url": "https://kilovatora.gr" + href if href.startswith("/") else href})
    if len(out) < 5:
        raise ValueError("Βρέθηκαν πολύ λίγα πακέτα κινητής")
    return out


PARSERS = {
    "timesrevmatos_json": parse_electricity, "timesrevmatos_gas": parse_gas,
    "agorasmart_internet": parse_internet, "agorasmart_mobile": parse_mobile,
    "kilovatora_revma": parse_kv_electricity, "kilovatora_aerio": parse_kv_gas,
    "kilovatora_statheri": parse_kv_internet, "kilovatora_kiniti": parse_kv_mobile,
}

# Σειρά προτεραιότητας: αν αποτύχει η 1η πηγή, δοκιμάζεται η επόμενη.
DEFAULT_SOURCES = {
    "electricity": [
        {"name": "timesrevmatos.gr", "url": "https://timesrevmatos.gr/api/plans.json", "parser": "timesrevmatos_json"},
        {"name": "kilovatora.gr (ΡΑΑΕΥ)", "url": "https://kilovatora.gr/revma", "parser": "kilovatora_revma"},
    ],
    "gas": [
        {"name": "timesrevmatos.gr", "url": "https://timesrevmatos.gr/fysiko-aerio/", "parser": "timesrevmatos_gas"},
        {"name": "kilovatora.gr (ΡΑΑΕΥ)", "url": "https://kilovatora.gr/aerio", "parser": "kilovatora_aerio"},
    ],
    "internet": [
        {"name": "agorasmart.gr", "url": "https://agorasmart.gr/internet", "parser": "agorasmart_internet"},
        {"name": "kilovatora.gr (ΕΕΤΤ)", "url": "https://kilovatora.gr/statheri", "parser": "kilovatora_statheri"},
    ],
    "mobile": [
        {"name": "agorasmart.gr", "url": "https://agorasmart.gr/mobile", "parser": "agorasmart_mobile"},
        {"name": "kilovatora.gr (ΕΕΤΤ)", "url": "https://kilovatora.gr/kiniti", "parser": "kilovatora_kiniti"},
    ],
}
SOURCES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ΠΗΓΕΣ.json")


def load_sources():
    try:
        with open(SOURCES_FILE, encoding="utf-8") as f:
            user = json.load(f)
        return {s: user.get(s) or DEFAULT_SOURCES[s] for s in DEFAULT_SOURCES}
    except Exception:  # noqa: BLE001
        return DEFAULT_SOURCES


def update_one(service):
    """Δοκιμάζει τις πηγές με τη σειρά. Επιστρέφει (προγράμματα, όνομα πηγής)."""
    errors = []
    for src in load_sources()[service]:
        try:
            plans = PARSERS[src["parser"]](fetch(src["url"]))
            return plans, src["name"]
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            if "urlopen error" in msg or "timed out" in msg or "Name or service" in msg or "getaddrinfo" in msg:
                msg = "δεν απάντησε (σύνδεση / site εκτός λειτουργίας)"
            elif "HTTP Error" in msg:
                msg = "το site απάντησε με σφάλμα " + msg.split("HTTP Error")[-1].strip()[:40]
            errors.append(f"{src['name']}: {msg[:140]}")
    raise RuntimeError("\n".join(errors))
