"""Αποθήκευση τιμών/ρυθμίσεων και προετοιμασία αποτελεσμάτων για την οθόνη."""
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import engine
import seed_data
import sources

DIR = Path(os.environ.get("APPDATA") or Path.home()) / "LogariasmoiSpitiou"
FILE = DIR / "data.json"


def set_dir(path):
    """Στο Android τα δεδομένα αποθηκεύονται στον φάκελο της εφαρμογής."""
    global DIR, FILE
    DIR = Path(path)
    FILE = DIR / "data.json"


def _fix(service, plans):
    for p in plans:
        if p.get("mc"):
            p["mc"] = {int(k): tuple(v) for k, v in p["mc"].items()}
        if p.get("promo"):
            p["promo"] = tuple(p["promo"])
    return plans


def load():
    d = {}
    try:
        d = json.loads(FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        pass
    seed = seed_data.all_data()
    svc = d.get("services", {})
    for s in engine.SERVICES:
        if not svc.get(s, {}).get("plans"):
            svc[s] = {"plans": seed[s], "updated": None, "origin": f"ενσωματωμένες τιμές {seed_data.SNAPSHOT_DATE}"}
        _fix(s, svc[s]["plans"])
    d["services"] = svc
    d["profile"] = {**engine.DEFAULTS, **d.get("profile", {})}
    return d


def save(d):
    DIR.mkdir(parents=True, exist_ok=True)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, FILE)


def update_all(d, progress=lambda s: None):
    """Κατεβάζει όλες τις υπηρεσίες ταυτόχρονα. Επιστρέφει {υπηρεσία: None ή μήνυμα σφάλματος}."""
    errors = {}

    def job(s):
        progress(f"Λήψη: {engine.LABELS[s]}…")
        return (s,) + sources.update_one(s)

    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = [ex.submit(job, s) for s in engine.SERVICES]
        for f in futs:
            try:
                s, plans, origin = f.result()
                d["services"][s] = {"plans": _fix(s, plans), "updated": time.time(), "origin": origin}
                errors[s] = None
            except Exception as e:  # noqa: BLE001
                s = engine.SERVICES[futs.index(f)]
                errors[s] = str(e)[:200]
    d["last_errors"] = {k: v for k, v in errors.items() if v}
    d["last_try"] = time.time()
    save(d)
    return errors


def data_of(d):
    return {s: d["services"][s]["plans"] for s in engine.SERVICES}


def eur(x):
    return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def status_line(d):
    parts = []
    for s in engine.SERVICES:
        info = d["services"][s]
        when = time.strftime("%d/%m %H:%M", time.localtime(info["updated"])) if info.get("updated") else ""
        parts.append(f"{engine.LABELS[s]}: {info['origin']} {when}".strip())
    return "   |   ".join(parts)


def best_report(d):
    """Επιστρέφει λίστα (κείμενο, ετικέτα μορφοποίησης) για την καρτέλα «Καλύτερη επιλογή»."""
    prof = d["profile"]
    data = data_of(d)
    res = engine.best_combination(data, prof)
    out = []
    w = out.append
    if not res["best"]:
        w(("Διάλεξε τουλάχιστον μία υπηρεσία αριστερά.\n", "h2"))
        return out
    b = res["best"]
    w(("Η πιο συμφέρουσα επιλογή για το σπίτι σου\n", "h1"))
    w((f"{eur(b['total'])} τον μήνα   ·   {eur(b['total'] * 12)} τον χρόνο\n\n", "big"))
    for it in b["items"]:
        p = it["plan"]
        w((f"{engine.LABELS[it['service']]}:  ", "label"))
        w((f"{p['provider']} – {p['name']}", "bold"))
        w((f"   {eur(it['cost'])}/μήνα", "money"))
        if it["deal"]:
            w(("   (με έκπτωση συνδυασμού ίδιας εταιρείας)", "deal"))
        w(("\n", None))
    saving = res["separately"] - b["total"]
    if saving > 0.005:
        w((f"\nΟ συνδυασμός γλιτώνει {eur(saving)}/μήνα σε σχέση με το φθηνότερο μεμονωμένο σε κάθε υπηρεσία.\n", "deal"))
    else:
        w(("\nΤα φθηνότερα μεμονωμένα προγράμματα βγαίνουν φθηνότερα από κάθε συνδυαστική προσφορά.\n", "note"))
    if res["missing"]:
        w((f"Δεν βρέθηκε πρόγραμμα με τα κριτήριά σου για: {', '.join(engine.LABELS[s] for s in res['missing'])}.\n", "warn"))

    if res["alternatives"]:
        w(("\nΕπόμενες καλύτερες επιλογές\n", "h2"))
        for a in res["alternatives"][:5]:
            names = ",  ".join(f"{i['plan']['provider']} {i['plan']['name']}" for i in a["items"])
            w((f"{eur(a['total'])}/μήνα  (+{eur(a['total'] - b['total'])})   ", "money"))
            w((names + "\n", None))

    w(("\nΦθηνότερη τιμή ανά εταιρεία\n", "h2"))
    for s in engine.SERVICES:
        if s not in prof["need"]:
            continue
        rows = engine.per_company(engine.ranked(s, data[s], prof))
        w((f"\n{engine.LABELS[s]}\n", "label"))
        for i, r in enumerate(rows, 1):
            extra = ""
            if r.get("cost_partner") is not None and r["cost_partner"] < r["cost"] - 0.005:
                extra = f"   (με συνδυασμό: {eur(r['cost_partner'])})"
            w((f"  {i:>2}. {r['provider']:<18} {eur(r['cost']):>11}/μήνα   {r['name']}{extra}\n", "mono"))
    w(("\nΡεύμα και αέριο: χρέωση προμήθειας χωρίς ΦΠΑ και ρυθμιζόμενες χρεώσεις (αυτές είναι ίδιες σε όλες τις "
       "εταιρείες). Internet και κινητή: τελική τιμή, με τυχόν εφάπαξ κόστος μοιρασμένο σε 24 μήνες και μέσο όρο "
       "24μήνου όπου η τιμή ανεβαίνει μετά τον 12ο μήνα. Πριν αλλάξεις, επιβεβαίωσε την τιμή στην εταιρεία.\n", "note"))
    return out


COLUMNS = {
    "electricity": ["Εταιρεία", "Πρόγραμμα", "Τύπος", "€/kWh", "Πάγιο", "€/μήνα", "€/έτος", "Δέσμευση", "Προϋπόθεση"],
    "gas": ["Εταιρεία", "Πρόγραμμα", "Τύπος", "€/kWh", "€/kWh με ρεύμα ίδιας", "Πάγιο", "€/μήνα", "€/έτος", "Δέσμευση"],
    "internet": ["Εταιρεία", "Πρόγραμμα", "Τεχνολογία", "Mbps", "Τιμή", "Με κινητή ίδιας", "€/μήνα", "€/έτος", "Σημείωση"],
    "mobile": ["Εταιρεία", "Πρόγραμμα", "Τύπος", "GB", "Ομιλία", "Τιμή", "Χωρίς internet ίδιας", "€/μήνα", "€/έτος"],
}


def _n(x, d=4):
    return "" if x is None else f"{x:.{d}f}".replace(".", ",")


def _months(m):
    return f"{int(m)} μήνες" if m else "χωρίς"


def table_rows(service, rows):
    out = []
    for r in rows:
        c = r["cost"]
        if service == "electricity":
            fee = r.get("fee")
            fee_s = "κλιμακωτό" if r.get("fee_bands") else eur(fee or 0)
            vals = [r["provider"], r["name"], r["type"], _n(r.get("price")), fee_s, eur(c), eur(c * 12),
                    _months(r.get("months")), r.get("condition") or ""]
        elif service == "gas":
            vals = [r["provider"], r["name"], r["type"], _n(r.get("price")), _n(r.get("price_dual")),
                    eur(r.get("fee") or 0), eur(c) if c != float("inf") else "μόνο με ρεύμα",
                    eur(c * 12) if c != float("inf") else "", _months(r.get("months"))]
        elif service == "internet":
            vals = [r["provider"], r["name"], r["tech"], r["speed"], eur(r["price"]),
                    eur(r["price_with_mobile"]) if r.get("price_with_mobile") else "", eur(c), eur(c * 12),
                    r.get("note") or ""]
        else:
            gb = "απεριόριστα" if r["gb"] >= 9999 else _n(r["gb"], 1).replace(",0", "")
            vals = [r["provider"], r["name"], r["type"], gb, "απεριόριστη" if r["unlimited_voice"] else "περιορισμένη",
                    eur(r["price"]), eur(r["price_alone"]) if r.get("price_alone") else "", eur(c), eur(c * 12)]
        out.append((vals, r.get("url") or ""))
    return out
