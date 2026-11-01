"""
Σύμβουλος λογαριασμών: η συμφερότερη λύση με ένα πάτημα, εξοικονόμηση, εκτίμηση κατανάλωσης, εξηγήσεις.
"""
import engine
import store

CATEGORIES = [
    # (κλειδί, τίτλος, εικονίδιο, υπηρεσίες)
    ("electricity", "Ρεύμα", "bolt", ["electricity"]),
    ("gas", "Φυσικό αέριο", "flame", ["gas"]),
    ("internet", "Internet σπιτιού", "wifi", ["internet"]),
    ("mobile", "Κινητή", "phone", ["mobile"]),
    ("energy", "Ρεύμα + Αέριο", "bundle", ["electricity", "gas"]),
    ("telecom", "Internet + Κινητή", "bundle", ["internet", "mobile"]),
    ("all", "Όλα μαζί", "wallet", ["electricity", "gas", "internet", "mobile"]),
]
CAT = {k: (t, i, s) for k, t, i, s in CATEGORIES}


def best_for(d, cat):
    """Η καλύτερη λύση για μια κατηγορία (μία υπηρεσία ή συνδυασμός)."""
    title, icon, services = CAT[cat]
    prof = dict(d["profile"])
    prof["need"] = services
    data = store.data_of(d)
    if len(services) == 1:
        s = services[0]
        rows = engine.ranked(s, data.get(s, []), prof)
        if not rows:
            return None
        best = rows[0]
        return {"total": best["cost"], "items": [{"service": s, "plan": best, "cost": best["cost"],
                                                  "deal": False}],
                "ranked": rows, "per_company": engine.per_company(rows), "separately": best["cost"]}
    res = engine.best_combination(data, prof)
    if not res.get("best"):
        return None
    out = dict(res["best"])
    out["alternatives"] = res.get("alternatives", [])
    out["separately"] = res.get("separately")
    return out


def company_ranking(d, service):
    prof = dict(d["profile"])
    rows = engine.ranked(service, store.data_of(d).get(service, []), prof)
    return engine.per_company(rows), rows


# ------------------------------------------------------------------ εξοικονόμηση
def savings(d, cat, best_total):
    cur = d.get("current", {})
    _, _, services = CAT[cat]
    vals = [cur.get(s) for s in services]
    if any(v in (None, "", 0) for v in vals):
        return None
    try:
        now = sum(float(v) for v in vals)
    except (TypeError, ValueError):
        return None
    m = now - best_total
    return {"now": now, "month": m, "year": m * 12}


# ------------------------------------------------------------------ εκτίμηση κατανάλωσης
def estimate_kwh_month(people, ac, water_electric, cooking_electric, big_house):
    """Χοντρική εκτίμηση μηνιαίας κατανάλωσης ρεύματος (μέσος όρος έτους)."""
    k = 110 + 65 * max(1, people)
    if ac:
        k += 70
    if water_electric:
        k += 110
    if cooking_electric:
        k += 45
    if big_house:
        k += 40
    return int(round(k / 10) * 10)


def estimate_gas_year(m2, heating_gas, water_gas, cooking_gas):
    y = 0
    if heating_gas:
        y += 95 * max(30, m2)
    if water_gas:
        y += 1500
    if cooking_gas:
        y += 400
    return int(round(y / 100) * 100)


# ------------------------------------------------------------------ εξηγήσεις
TARIFF_HELP = [
    ("Μπλε – σταθερό", "Η τιμή της κιλοβατώρας είναι γνωστή από πριν και μένει ίδια για όσο ορίζει η σύμβαση."),
    ("Πράσινο – ειδικό", "Κυμαινόμενη τιμή, που όμως ανακοινώνεται στην αρχή κάθε μήνα: ξέρεις τι πληρώνεις πριν "
                         "καταναλώσεις."),
    ("Κίτρινο – κυμαινόμενο", "Η τελική τιμή εξαρτάται από τη χονδρεμπορική αγορά και γίνεται γνωστή μετά την "
                              "κατανάλωση."),
]

SWITCH_HELP = {
    "electricity": ["Η αλλαγή παρόχου ρεύματος είναι δωρεάν και δεν διακόπτεται η παροχή.",
                    "Χρειάζεσαι: τον αριθμό παροχής (στον λογαριασμό), ταυτότητα, ΑΦΜ.",
                    "Η αίτηση γίνεται online ή σε κατάστημα του νέου παρόχου· εκείνος κάνει τη μεταφορά.",
                    "Πρόσεξε αν το συμβόλαιό σου έχει διάρκεια και ρήτρα πρόωρης αποχώρησης."],
    "gas": ["Η αλλαγή παρόχου φυσικού αερίου είναι επίσης δωρεάν, χωρίς διακοπή.",
            "Χρειάζεσαι: τον κωδικό παροχής (στον λογαριασμό), ταυτότητα, ΑΦΜ."],
    "internet": ["Με τη φορητότητα κρατάς τον αριθμό του σταθερού.",
                 "Έλεγξε τη διαθεσιμότητα ταχύτητας στη διεύθυνσή σου πριν δεσμευτείς.",
                 "Πρόσεξε τη διάρκεια δέσμευσης (συνήθως 24 μήνες) και το κόστος πρόωρης λύσης."],
    "mobile": ["Με τη φορητότητα κρατάς τον αριθμό σου· η μεταφορά γίνεται συνήθως μέσα σε 1 εργάσιμη.",
               "Αν έχεις συμβόλαιο με δέσμευση, έλεγξε πρώτα αν υπάρχει κόστος αποχώρησης."],
}


def plan_lines(service, p):
    """Τα βασικά στοιχεία ενός προγράμματος, για εμφάνιση."""
    L = []
    if service == "electricity":
        L.append(("Τύπος", p.get("type", "")))
        if p.get("price"):
            L.append(("Τιμή", f"{p['price']:.4f} €/kWh".replace(".", ",")))
        L.append(("Πάγιο", "κλιμακωτό" if p.get("fee_bands") else store.eur(p.get("fee") or 0) + "/μήνα"))
        if p.get("condition"):
            L.append(("Προϋπόθεση", p["condition"]))
        if p.get("price_month"):
            L.append(("Τιμή μήνα", p["price_month"]))
    elif service == "gas":
        L.append(("Τύπος", p.get("type", "")))
        if p.get("price"):
            L.append(("Τιμή", f"{p['price']:.4f} €/kWh".replace(".", ",")))
        if p.get("price_dual"):
            L.append(("Με ρεύμα ίδιας εταιρείας", f"{p['price_dual']:.4f} €/kWh".replace(".", ",")))
        L.append(("Πάγιο", store.eur(p.get("fee") or 0) + "/μήνα"))
        if p.get("condition"):
            L.append(("Προϋπόθεση", p["condition"]))
    elif service == "internet":
        L.append(("Τεχνολογία", f"{p.get('tech', '')} · {p.get('speed', '')} Mbps"))
        L.append(("Μηνιαίο", store.eur(p.get("price") or 0)))
        if p.get("price_with_mobile"):
            L.append(("Με κινητή ίδιας εταιρείας", store.eur(p["price_with_mobile"])))
        if p.get("onetime"):
            L.append(("Εφάπαξ", store.eur(p["onetime"])))
        if p.get("note"):
            L.append(("Σημείωση", p["note"]))
    else:
        gb = "απεριόριστα" if p.get("gb", 0) >= 9999 else f"{p.get('gb', 0):g} GB"
        L.append(("Είδος", p.get("type", "")))
        L.append(("Δεδομένα", gb))
        L.append(("Ομιλία", "απεριόριστη" if p.get("unlimited_voice") else "περιορισμένη"))
        L.append(("Μηνιαίο", store.eur(p.get("price") or 0)))
        if p.get("price_later"):
            L.append(("Μετά την προσφορά", store.eur(p["price_later"])))
    months = p.get("months")
    if months:
        L.append(("Διάρκεια", f"{months} μήνες"))
    return L


# ------------------------------------------------------------------ ιστορικό καλύτερων λύσεων
def snapshot(d):
    """Το κόστος της καλύτερης λύσης ανά κατηγορία (για σύγκριση πριν/μετά την ενημέρωση)."""
    out = {}
    for k, *_ in CATEGORIES:
        b = best_for(d, k)
        if b:
            out[k] = round(b["total"], 2)
    return out


def record_history(d, snap):
    import time as _t
    h = d.setdefault("best_history", [])
    h.append({"t": _t.time(), "best": snap})
    d["best_history"] = h[-60:]


def changes(before, after, min_diff=0.3):
    """Κατηγορίες όπου η καλύτερη λύση έγινε φθηνότερη ή ακριβότερη."""
    out = []
    for k, v in after.items():
        if k in before and abs(v - before[k]) >= min_diff:
            out.append((k, v - before[k]))
    return sorted(out, key=lambda x: x[1])


def trend(d, cat, days=30):
    """(πριν από πόσες μέρες, κόστος τότε) για την παλαιότερη καταγραφή μέσα στο διάστημα."""
    import time as _t
    now = _t.time()
    for e in d.get("best_history", []):
        if now - e["t"] <= days * 86400 and cat in e["best"]:
            return int((now - e["t"]) // 86400), e["best"][cat]
    return None


# ------------------------------------------------------------------ η εταιρεία μου & λήξη σύμβασης
def same_company_best(d, service):
    """Το φθηνότερο πρόγραμμα της εταιρείας που έχεις σήμερα (για «να μείνω, αλλά σε καλύτερο πρόγραμμα»)."""
    prov = (d.get("my_provider") or {}).get(service)
    if not prov:
        return None
    rows = engine.ranked(service, store.data_of(d).get(service, []), d["profile"])
    mine = [r for r in rows if r["provider"] == prov]
    return mine[0] if mine else None


def contract_alerts(d, days=45):
    import datetime
    out = []
    for s, txt in (d.get("contract_end") or {}).items():
        try:
            end = datetime.datetime.strptime(txt.strip(), "%d/%m/%Y").date()
        except (ValueError, AttributeError):
            continue
        left = (end - datetime.date.today()).days
        if left <= days:
            out.append((s, left, end))
    return sorted(out, key=lambda x: x[1])
