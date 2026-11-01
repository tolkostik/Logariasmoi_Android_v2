"""Υπολογισμός κόστους, φθηνότερου ανά εταιρεία και καλύτερου συνδυασμού."""
import itertools

INF = float("inf")

SERVICES = ["electricity", "gas", "internet", "mobile"]
LABELS = {"electricity": "Ρεύμα", "gas": "Φυσικό αέριο", "internet": "Internet σπιτιού", "mobile": "Κινητή"}

DEFAULTS = {
    "need": ["electricity", "gas", "internet", "mobile"],
    "kwh_month": 300, "gas_kwh_year": 6000, "heating": "Αυτόνομη",
    "min_mbps": 100, "min_gb": 10, "unlimited_voice": True, "mobile_lines": 1, "mobile_type": "Όλα",
    "keep_discounts": True,
    "el_types": ["Σταθερό (μπλε)", "Κυμαινόμενο (κίτρινο)", "Ειδικό (πράσινο)"],
    "net_techs": ["Fiber/VDSL", "4G/5G"],
    "exclude_providers": ["Inalan"],
}


# ------------------------------------------------------------------ ρεύμα
def _band_fee(bands, kwh):
    for upto, fee in bands:
        if upto is None or kwh <= upto:
            return fee
    return bands[-1][1]


def _tiered(tiers, kwh):
    cost, prev = 0.0, 0
    for upto, price in tiers:
        top = kwh if upto is None else min(kwh, upto)
        if top > prev:
            cost += (top - prev) * price
            prev = top
        if upto is None or kwh <= upto:
            break
    return cost


def _interp(points, x):
    xs = sorted(points)
    if x <= xs[0]:
        x0, x1 = xs[0], xs[1]
    elif x >= xs[-1]:
        x0, x1 = xs[-2], xs[-1]
    else:
        x0 = max(p for p in xs if p <= x)
        x1 = min(p for p in xs if p >= x)
        if x0 == x1:
            return points[x0]
    y0, y1 = points[x0], points[x1]
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def electricity_cost(p, kwh, keep):
    if p.get("mc"):
        col = 0 if keep else 1
        pts = {k: (v[col] if v[col] is not None else v[0]) for k, v in p["mc"].items()}
        return max(0.0, _interp(pts, kwh))
    tiers = p.get("tiers") if keep else (p.get("tiers_base") or p.get("tiers"))
    if tiers:
        energy = _tiered(tiers, kwh)
        if not keep and not p.get("tiers_base") and p.get("price") and p.get("price_base"):
            energy *= p["price_base"] / p["price"]
    else:
        energy = kwh * (p["price"] if keep else (p.get("price_base") or p["price"]))
    fee = _band_fee(p["fee_bands"], kwh) if p.get("fee_bands") else (p.get("fee") or 0.0)
    return energy + fee


# ------------------------------------------------------------------ κόστος μιας επιλογής
def plan_cost(service, p, prof, partner_ok=False):
    """Μηνιαίο κόστος. partner_ok=True όταν υπάρχει και η άλλη υπηρεσία από τον ίδιο πάροχο."""
    if service == "electricity":
        return electricity_cost(p, prof["kwh_month"], prof["keep_discounts"])
    if service == "gas":
        price = p["price_dual"] if (partner_ok and p.get("price_dual")) else p.get("price")
        if price is None:
            return INF  # διατίθεται μόνο μαζί με ρεύμα της ίδιας εταιρείας
        return (price * prof["gas_kwh_year"] + (p.get("fee") or 0) * 12) / 12
    if service == "internet":
        price = p["price_with_mobile"] if (partner_ok and p.get("price_with_mobile")) else p["price"]
        if p.get("promo"):
            pp, months = p["promo"]
            price = (pp * months + price * max(0, 24 - months)) / 24
        return price + (p.get("onetime") or 0) / 24
    if service == "mobile":
        price = p["price"]
        if p.get("price_alone") and not partner_ok:
            price = p["price_alone"]
        if p.get("price_later"):
            price = (price + p["price_later"]) / 2  # μέσος όρος 24μήνου
        return price * max(1, int(prof.get("mobile_lines", 1)))
    raise ValueError(service)


PARTNER = {"gas": "electricity", "internet": "mobile", "mobile": "internet"}


def has_partner_deal(service, p):
    return bool(p.get("price_dual") or p.get("price_with_mobile") or p.get("price_alone"))


# ------------------------------------------------------------------ φίλτρα
def eligible(service, plans, prof):
    ex = set(prof.get("exclude_providers") or [])
    out = []
    for p in plans:
        if p["provider"] in ex:
            continue
        if service == "electricity" and p["type"] not in prof["el_types"]:
            continue
        if service == "gas":
            want = "K" if prof["heating"] == "Κεντρική" else "A"
            if p.get("conn") not in (want, "B"):
                continue
        if service == "internet":
            if p["speed"] < prof["min_mbps"] or p["tech"] not in prof["net_techs"]:
                continue
        if service == "mobile":
            if p["gb"] < prof["min_gb"] or (prof["unlimited_voice"] and not p["unlimited_voice"]):
                continue
            if prof["mobile_type"] != "Όλα" and p["type"] != prof["mobile_type"]:
                continue
        out.append(p)
    return out


def ranked(service, plans, prof):
    """Όλα τα κατάλληλα προγράμματα με κόστος (μόνα τους), φθηνότερο πρώτο."""
    rows = [dict(p, cost=plan_cost(service, p, prof),
                 cost_partner=plan_cost(service, p, prof, True) if has_partner_deal(service, p) else None)
            for p in eligible(service, plans, prof)]
    rows = [r for r in rows if r["cost"] < INF or (r["cost_partner"] or INF) < INF]
    rows.sort(key=lambda r: min(r["cost"], r["cost_partner"] or INF))
    return rows


def per_company(rows):
    best = {}
    for r in sorted((r for r in rows if r["cost"] < INF), key=lambda r: r["cost"]):
        if r["provider"] not in best:
            best[r["provider"]] = r
    return sorted(best.values(), key=lambda r: r["cost"])


# ------------------------------------------------------------------ καλύτερος συνδυασμός
def best_combination(data, prof, top=8):
    need = [s for s in SERVICES if s in prof["need"]]
    lists, missing = {}, []
    for s in need:
        rows = ranked(s, data.get(s, []), prof)
        if not rows:
            missing.append(s)
            continue
        cand, seen = [], set()
        for r in per_company(rows):  # ο φθηνότερος κάθε παρόχου
            if r["provider"] not in seen:
                cand.append(r)
                seen.add(r["provider"])
        deals = sorted([r for r in rows if r["cost_partner"] is not None], key=lambda r: r["cost_partner"])
        best_deal = {}
        for r in deals:
            best_deal.setdefault(r["provider"], r)
        for r in best_deal.values():
            if r not in cand:
                cand.append(r)
        lists[s] = cand
    svc = [s for s in need if s in lists]
    if not svc:
        return {"best": None, "alternatives": [], "missing": missing}
    results = []
    for combo in itertools.product(*(lists[s] for s in svc)):
        chosen = dict(zip(svc, combo))
        items, total = [], 0.0
        for s, p in chosen.items():
            partner = PARTNER.get(s)
            ok = partner in chosen and chosen[partner]["provider"] == p["provider"]
            c = plan_cost(s, p, prof, ok)
            items.append({"service": s, "plan": p, "cost": c, "deal": ok and has_partner_deal(s, p)})
            total += c
        results.append({"total": total, "items": items})
    results = [r for r in results if r["total"] < INF]
    if not results:
        return {"best": None, "alternatives": [], "missing": missing}
    results.sort(key=lambda r: r["total"])
    uniq, keys = [], set()
    for r in results:
        k = tuple((i["service"], i["plan"]["provider"], i["plan"]["name"]) for i in r["items"])
        if k not in keys:
            keys.add(k)
            uniq.append(r)
        if len(uniq) >= top:
            break
    separately = sum(min((r["cost"] for r in ranked(s, data.get(s, []), prof)), default=0) for s in svc)
    return {"best": uniq[0], "alternatives": uniq[1:], "missing": missing, "separately": separately}
