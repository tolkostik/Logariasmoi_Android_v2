"""
Ενσωματωμένες τιμές (στιγμιότυπο 21/10/2026), ώστε το πρόγραμμα να δείχνει αποτελέσματα
από την πρώτη στιγμή. Το κουμπί «ΕΝΗΜΕΡΩΣΗ ΟΛΩΝ» τις αντικαθιστά με τις τρέχουσες.
Ρεύμα/αέριο: τιμές προμήθειας χωρίς ΦΠΑ και ρυθμιζόμενες χρεώσεις.
Internet/κινητή: τελικές μηνιαίες τιμές.
"""
SNAPSHOT_DATE = "21/10/2026"

S, F, G = "Σταθερό (μπλε)", "Κυμαινόμενο (κίτρινο)", "Ειδικό (πράσινο)"
B1 = [(150, 7.95), (None, 15.9)]

# (πάροχος, πρόγραμμα, τύπος, τιμή με έκπτωση, τιμή χωρίς, πάγιο ή κλίμακες παγίου,
#  κλίμακες τιμής με έκπτωση, κλίμακες τιμής χωρίς, μήνες, προϋπόθεση)
_EL = [
    ("ΔΕΗ", "myHome Enter", S, .145, .145, 7.5, None, None, 12, ""),
    ("ΔΕΗ", "myHome Maxima", S, .151, .151, 13.5, [(600, .151), (None, .139)], None, 18, ""),
    ("Φυσικό Αέριο ΕΕΕ", "MAXI HOME Safe", S, .149, .259, 8.9, None, None, 12, "Εμπρόθεσμη πληρωμή, έως 700 kWh/μήνα"),
    ("Enerwave", "Reward Stable Max 24M 2.0", S, .129, .26, 15.9, None, None, 24, "Έκπτωση συνέπειας"),
    ("ΗΡΩΝ", "Blue More Home", S, .145, .286, 12.9, None, None, 24, "Έκπτωση συνέπειας"),
    ("NRG", "nrg fixed on time 24M", S, .145, .286, 12.9, None, None, 24, "Έκπτωση συνέπειας"),
    ("ΕΛΙΝ", "Power On! Blue 12M", S, .1599, .1599, 8.9, None, None, 12, ""),
    ("ΗΡΩΝ", "Blue Smart More Home", S, .139, .286, B1, None, None, 24, "Έκπτωση συνέπειας"),
    ("NRG", "nrg adjust 24M", S, .139, .286, B1, None, None, 24, "Έκπτωση συνέπειας"),
    ("ZeniΘ", "Power Home Prime 2Y", S, .139, .299, 15.9, None, None, 24, "Έκπτωση συνέπειας"),
    ("Volton", "Blue Fixed Plus 24M", S, .165, .28, 9.9, None, None, 24, "Έκπτωση συνέπειας"),
    ("Enerwave", "Reward Stable Zero 24M 2.0", S, .199, .26, 0, None, None, 24, "Έκπτωση συνέπειας"),
    ("ΗΡΩΝ", "Blue Simple More Home", S, .199, .199, 0, None, None, 24, ""),
    ("Volton", "Blue Fixed Plus 18M", S, .165, .28, 10.9, None, None, 18, "Έκπτωση συνέπειας"),
    ("Volton", "Blue Fixed Plus 12M", S, .165, .28, 12.9, None, None, 12, "Έκπτωση συνέπειας"),
    ("Enerwave", "Reward Stable 12M 4.0", S, .169, .26, 9.9, None, None, 12, "Έκπτωση συνέπειας"),
    ("Eunice", "Home SECURE Start", S, .145, .145, 8, [(150, .145), (None, .21)], None, 12, ""),
    ("ΗΡΩΝ", "Blue Generous Max Home", S, .168, .286, 11.9, None, None, 18, "Έκπτωση συνέπειας"),
    ("Eunice", "Home SECURE 2.0", S, .19, .19, 6, None, None, 12, ""),
    ("ΗΡΩΝ", "Blue Smart Home", S, .158, .286, B1, None, None, 12, "Έκπτωση συνέπειας"),
    ("NRG", "nrg adjust 3.0", S, .158, .286, B1, None, None, 12, "Έκπτωση συνέπειας"),
    ("ZeniΘ", "Power Home Fixed Safe 12M", S, .159, .159, 15.9, None, None, 12, ""),
    ("Protergia", "Value Balance 12M", S, .139, .139, 10.9, [(150, .139), (None, .219)], None, 12, ""),
    ("Protergia", "Value Sure 12M 4.0", S, .177, .247, 11.9, None, None, 12, "Έκπτωση συνέπειας"),
    ("ZeniΘ", "Power Home Fixed Scale", S, .1723, .1723, 14.9, None, None, 12, ""),
    ("ZeniΘ", "Power Home Fixed Prime", S, .189, .189, 13.9, None, None, 12, ""),
    ("Protergia", "Value Standard 2.0", F, .184, .224, 5, None, None, 12, "Έκπτωση συνέπειας"),
    ("Φυσικό Αέριο ΕΕΕ", "MAXI HOME 200", F, .178, .178, 9.9, None, None, 0, ""),
    ("NRG", "nrg on time 4U", F, .20649, .22399, 5, None, None, 0, "Έκπτωση συνέπειας"),
    ("NRG", "nrg prime 4U", F, .21599, .21599, 2.5, None, None, 0, ""),
    ("NRG", "nrg free", F, .22508, .22508, 0, None, None, 0, ""),
    ("Φυσικό Αέριο ΕΕΕ", "MAXI HOME 10", F, .216, .216, 5, None, None, 0, ""),
    ("ΕΛΙΝ", "Power On! Home Zero", F, .2332, .2332, 0, None, None, 0, ""),
    ("NRG", "nrg @ cost+", F, .18899, .18899, [(250, 7.1), (450, 13.9), (650, 19.9), (None, 24.9)], None, None, 0, ""),
    ("Protergia", "Value Bright 2.0", F, .21914, .23114, 5, None, None, 0, "Έκπτωση συνέπειας"),
    ("Φυσικό Αέριο ΕΕΕ", "MAXI HOME", F, .221, .221, 5, None, None, 0, ""),
    ("ZeniΘ", "Power Home Select", F, .2259, .2259, 5, None, None, 0, ""),
    ("Enerwave", "Smart Zero", F, .24323, .24323, 0, None, None, 0, ""),
    ("Protergia", "Value Lite 2.0", F, .24414, .24414, 0, None, None, 0, ""),
    ("ZeniΘ", "Power Home Light", F, .2419, .2419, .99, None, None, 0, ""),
    ("Enerwave", "Reward Saver", F, .219, .219, 7.9, None, None, 0, ""),
    ("Enerwave", "Smart", F, .22913, .22913, 5, None, None, 0, ""),
    ("ZeniΘ", "Power Home Save 3.0", F, .2319, .2319, 5, None, None, 0, ""),
    ("ΗΡΩΝ", "Yellow One Home", F, .24382, .26722, 5, None, None, 0, "Έκπτωση συνέπειας"),
    ("ΔΕΗ", "myHome 4All", F, .2461, .2461, 5, [(500, .2461), (None, .3021)], None, 12, ""),
    ("NRG", "nrg simple 3.0", F, .256, .256, 5, None, None, 0, ""),
    ("Eunice", "Βασικός Τιμοκατάλογος Home", F, .25632, .25632, 5, None, None, 0, ""),
    ("Enerwave", "Core", F, .259, .259, 7.9, None, None, 0, ""),
    ("ΗΡΩΝ", "Basic Home", G, .1476, .1476, 5, None, None, 0, "Εμπρόθεσμη εξόφληση"),
    ("ΔΕΗ", "Γ1/Γ1Ν Ειδικό", G, .15913, .22737, 5, [(200, .15913), (None, .21997)],
     [(200, .22737), (None, .25437)], 0, "Εμπρόθεσμη εξόφληση + myΔΕΗ"),
    ("Protergia", "Value Special", G, .184, .267, 5, None, None, 0, "Έκπτωση συνέπειας"),
    ("OTE Estate", "Estate Home Green", G, .216, .216, 5, None, None, 0, ""),
    ("S Energy", "Ειδικό Τιμολόγιο", G, .2346, .2346, 5, None, None, 0, ""),
    ("Φυσικό Αέριο ΕΕΕ", "Οικιακό (Ειδικό)", G, .239, .239, 5, None, None, 0, ""),
    ("ΕΛΙΝ", "Power On! Home Green", G, .2526, .2526, 5, None, None, 0, ""),
    ("NRG", "Ειδικό Τιμολόγιο nrg", G, .259, .299, 5, None, None, 0, "Έκπτωση συνέπειας"),
    ("Volton", "Green Ειδικό", G, .2737, .2737, 4.9, None, None, 0, ""),
    ("Enerwave", "Ειδικό Τιμολόγιο Οικιακό", G, .179, .179, 5, [(100, .179), (None, .339)], None, 0, ""),
    ("ZeniΘ", "Power Home Start", G, .225, .225, 5, [(100, .225), (None, .347)], None, 0, ""),
]

# (πάροχος, πρόγραμμα, τύπος, τιμή, τιμή με ρεύμα ίδιου παρόχου, πάγιο, σύνδεση A/K/B, μήνες)
_GAS = [
    ("ΗΡΩΝ", "Gas Blue Plus Home", "Σταθερό", .0499, None, 14.9, "A", 18),
    ("NRG", "nrg fixed GAS 1.0 18M", "Σταθερό", .0499, None, 14.9, "A", 18),
    ("Protergia", "Value Gas Sure 2.0", "Σταθερό", .0529, .0499, 14.9, "A", 12),
    ("ΔΕΗ", "myHome GasControl", "Σταθερό", .052, None, 14.9, "A", 18),
    ("ZeniΘ", "Gas Home Prime 2Y", "Σταθερό", .089, .059, 11.9, "A", 24),
    ("ZeniΘ", "Gas Home Steady 12M", "Σταθερό", .089, .059, 14.9, "A", 12),
    ("ΔΕΗ", "myBuilding GasControl", "Σταθερό", .065, None, 14.9, "K", 18),
    ("Protergia", "Value Gas Standard (αυτόνομο)", "Κυμαινόμενο", .0683, None, 5, "A", 0),
    ("Protergia", "Value Gas Standard (κοινόχρηστο)", "Κυμαινόμενο", .0683, None, 5, "K", 0),
    ("Φυσικό Αέριο ΕΕΕ", "Οικιακό Πλήρες Extra", "Κυμαινόμενο", .0691, None, 4.5, "B", 24),
    ("ZeniΘ", "Gas Home Now", "Κυμαινόμενο", .0766, None, 4.0, "A", 24),
    ("ZeniΘ", "Gas Central Easy", "Κυμαινόμενο", .0908, .0779, 0, "K", 0),
    ("ΕΛΙΝ", "Gas On! Home Easy", "Κυμαινόμενο", .0813, .0783, 4.5, "A", 0),
    ("ΕΛΙΝ", "Gas On! Κοινόχρηστο Easy", "Κυμαινόμενο", .0813, .0783, 5, "K", 0),
    ("ΕΛΙΝ", "Gas On! Home Relax", "Κυμαινόμενο", .0793, None, 6, "A", 0),
    ("ΗΡΩΝ", "Gas Max Home", "Κυμαινόμενο", .0793, None, 4.3, "A", 0),
    ("Protergia", "Value Gas Flex (αυτόνομο)", "Κυμαινόμενο", .0823, .0803, 7, "A", 0),
    ("Protergia", "Value Gas Flex (κοινόχρηστο)", "Κυμαινόμενο", .0823, .0803, 7, "K", 0),
    ("ZeniΘ", "Gas Home Pulse", "Κυμαινόμενο", .0887, .0843, 4.5, "A", 0),
    ("ZeniΘ", "Gas Home Save", "Κυμαινόμενο", .0957, .0909, 4.5, "A", 0),
    ("ZeniΘ", "Gas Central Save", "Κυμαινόμενο", .0957, .0909, 0, "K", 0),
    ("ΗΡΩΝ", "Gas Max Share", "Κυμαινόμενο", .0913, None, 0, "K", 0),
    ("ΗΡΩΝ", "Gas Pass Home", "Κυμαινόμενο", .1133, None, 3.4, "A", 0),
]

# (πάροχος, πρόγραμμα, τεχνολογία, Mbps, €/μήνα, €/μήνα με κινητή ίδιου παρόχου, εφάπαξ €, προσφορά (€, μήνες), σημείωση)
_NET = [
    ("Vodafone", "Wireless Home via 4G", "4G/5G", 150, 20.95, None, 40, None, ""),
    ("Nova", "Fiber 100", "Fiber/VDSL", 100, 21.0, None, 0, None, ""),
    ("Nova", "5G Home Internet 100", "4G/5G", 100, 21.0, None, 0, None, ""),
    ("Vodafone", "Full Fiber 300 Plus", "Fiber/VDSL", 300, 24.22, 22.80, 6, None, ""),
    ("Nova", "Fiber 300", "Fiber/VDSL", 300, 23.0, None, 0, None, ""),
    ("Vodafone", "Fiber 100", "Fiber/VDSL", 100, 24.90, None, 0, None, ""),
    ("Vodafone", "Wireless Home via 5G", "4G/5G", 250, 24.90, None, 0, None, ""),
    ("Vodafone", "50 (VDSL)", "Fiber/VDSL", 50, 25.0, None, 0, None, ""),
    ("Nova", "Fiber 500", "Fiber/VDSL", 500, 26.0, None, 0, None, ""),
    ("Vodafone", "Full Fiber 500 Plus", "Fiber/VDSL", 500, 28.35, 26.90, 6, None, ""),
    ("Telekom", "Fiber 300 Unlimited", "Fiber/VDSL", 300, 27.90, None, 0, None, ""),
    ("Inalan", "300", "Fiber/VDSL", 300, 28.0, None, 0, (12.0, 12), "Μόνο σε περιοχές κάλυψης Inalan"),
    ("Nova", "5G Home Internet 300", "4G/5G", 300, 28.0, None, 0, None, ""),
    ("Vodafone", "Full Fiber 1Gbps Plus", "Fiber/VDSL", 1000, 31.33, 29.90, 6, None, ""),
    ("Nova", "Fiber 1 Giga", "Fiber/VDSL", 1000, 31.0, None, 0, None, ""),
    ("Telekom", "Fiber 500 Unlimited", "Fiber/VDSL", 500, 31.90, None, 0, None, ""),
    ("Inalan", "1 Gbps", "Fiber/VDSL", 1000, 34.0, None, 0, None, "Μόνο σε περιοχές κάλυψης Inalan"),
    ("Starlink", "100", "Δορυφορικό", 100, 35.0, None, 20, None, "Παντού, χωρίς δέσμευση"),
    ("Telekom", "Fiber 1 Gbps Unlimited", "Fiber/VDSL", 1000, 35.90, None, 0, None, ""),
    ("Telekom", "5G WiFi 300", "4G/5G", 300, 35.90, None, 349, None, "Εξοπλισμός 349€ εφάπαξ"),
    ("Nova", "5G Home Internet 500", "4G/5G", 500, 39.0, None, 0, None, ""),
    ("Starlink", "200", "Δορυφορικό", 200, 45.0, None, 20, None, "Παντού, χωρίς δέσμευση"),
    ("Nova", "Fiber 3 Giga", "Fiber/VDSL", 3000, 54.0, None, 0, None, ""),
    ("Starlink", "Max", "Δορυφορικό", 400, 65.0, None, 20, None, "Παντού, χωρίς δέσμευση"),
    ("Telekom", "Fiber 3Gbps Unlimited", "Fiber/VDSL", 3000, 70.39, None, 0, None, ""),
]

# (πάροχος, πρόγραμμα, τύπος, GB (9999=απεριόριστα), απεριόριστη ομιλία, €/μήνα,
#  €/μήνα μετά τον 12ο μήνα, €/μήνα χωρίς internet ίδιου παρόχου)
_MOB = [
    ("Frog Mobile", "National Combo", "Καρτοκινητό", 10, False, 8.90, None, None),
    ("Nova", "Q Star AUTO 500", "Καρτοκινητό", 4, False, 10.70, None, None),
    ("Nova", "Q Star Big AUTO", "Καρτοκινητό", 6.5, True, 11.60, None, None),
    ("Vodafone", "CU Combo Flow", "Καρτοκινητό", 1.5, False, 11.80, None, None),
    ("Frog Mobile", "National Combo M", "Καρτοκινητό", 14, False, 11.80, None, None),
    ("Nova", "Q Star Large AUTO", "Καρτοκινητό", 10.5, True, 12.50, None, None),
    ("Frog Mobile", "National Combo XL", "Καρτοκινητό", 48, False, 13.50, None, None),
    ("Telekom", "What's Up Unlimited Calls 5GB", "Καρτοκινητό", 5, True, 13.60, None, None),
    ("Telekom", "What's Up Unlimited Calls 10GB", "Καρτοκινητό", 10, True, 14.50, None, None),
    ("Vodafone", "CU Combo Stream", "Καρτοκινητό", 15, True, 14.50, None, None),
    ("Nova", "Q Star Huge AUTO", "Καρτοκινητό", 20.5, True, 16.10, None, None),
    ("Vodafone", "RED 10GB", "Συμβόλαιο", 10, True, 16.60, 22.14, None),
    ("Nova", "Unlimited+ 5GB", "Συμβόλαιο", 5, True, 18.00, None, None),
    ("Telekom", "What's Up Unlimited Calls 20GB", "Καρτοκινητό", 20, True, 18.10, None, None),
    ("Vodafone", "CU Combo Ocean", "Καρτοκινητό", 30, True, 18.10, None, None),
    ("Vodafone", "RED 20GB", "Συμβόλαιο", 20, True, 19.00, 25.31, None),
    ("Vodafone", "RED 80GB", "Συμβόλαιο", 80, True, 19.93, 26.57, None),
    ("Telekom", "NEO 50GB", "Συμβόλαιο", 50, True, 21.00, None, None),
    ("Nova", "Unlimited+ 20GB", "Συμβόλαιο", 20, True, 23.00, None, None),
    ("Vodafone", "RED Unlimited", "Συμβόλαιο", 9999, True, 23.22, 30.95, None),
    ("Telekom", "GIGAMAX 9GB", "Συμβόλαιο", 9, True, 24.00, None, 39.0),
    ("Nova", "Unlimited+ 40GB", "Συμβόλαιο", 40, True, 25.00, None, None),
    ("Telekom", "GIGAMAX 18GB", "Συμβόλαιο", 18, True, 28.00, None, 44.0),
    ("Nova", "Unlimited All", "Συμβόλαιο", 9999, True, 30.00, None, None),
    ("Telekom", "GIGAMAX 35GB", "Συμβόλαιο", 35, True, 32.00, None, 49.0),
    ("Telekom", "NEO Unlimited", "Συμβόλαιο", 9999, True, 33.00, None, None),
    ("Telekom", "GIGAMAX 70GB", "Συμβόλαιο", 70, True, 36.00, None, 54.0),
    ("Telekom", "GIGAMAX Unlimited", "Συμβόλαιο", 9999, True, 41.00, None, 70.0),
]

WEBSITES = {
    "ΔΕΗ": "https://www.dei.gr", "Protergia": "https://www.protergia.gr", "ΗΡΩΝ": "https://www.heron.gr",
    "NRG": "https://www.nrg.gr", "Enerwave": "https://www.enerwave.gr", "Eunice": "https://eunice-power.gr",
    "Volton": "https://www.volton.gr", "ZeniΘ": "https://www.zenith.gr", "ΕΛΙΝ": "https://www.elin.gr",
    "Φυσικό Αέριο ΕΕΕ": "https://www.fysikoaerioellados.gr", "OTE Estate": "https://www.cosmote.gr",
    "S Energy": "https://www.senergy.gr", "Vodafone": "https://www.vodafone.gr", "Nova": "https://www.nova.gr",
    "Telekom": "https://www.telekom.gr", "Inalan": "https://www.inalan.gr", "Starlink": "https://www.starlink.com/gr",
    "Frog Mobile": "https://www.frogmobile.gr",
}


def _site(p):
    return WEBSITES.get(p, "")


def electricity():
    out = []
    for (p, n, t, pd, pb, fee, tiers, tiers_b, months, cond) in _EL:
        out.append({
            "provider": p, "name": n, "type": t, "price": pd, "price_base": pb,
            "fee": fee if not isinstance(fee, list) else None,
            "fee_bands": fee if isinstance(fee, list) else None,
            "tiers": tiers, "tiers_base": tiers_b, "mc": None, "months": months,
            "condition": cond, "url": _site(p), "price_month": "Οκτ 2026",
        })
    return out


def gas():
    return [{"provider": p, "name": n, "type": t, "price": pr, "price_dual": pdual, "fee": fee,
             "conn": c, "months": m, "url": _site(p)} for (p, n, t, pr, pdual, fee, c, m) in _GAS]


def internet():
    return [{"provider": p, "name": n, "tech": tech, "speed": sp, "price": pr, "price_with_mobile": pwm,
             "onetime": one, "promo": promo, "note": note, "url": _site(p)}
            for (p, n, tech, sp, pr, pwm, one, promo, note) in _NET]


def mobile():
    return [{"provider": p, "name": n, "type": t, "gb": gb, "unlimited_voice": uv, "price": pr,
             "price_later": later, "price_alone": alone, "url": _site(p)}
            for (p, n, t, gb, uv, pr, later, alone) in _MOB]


def all_data():
    return {"electricity": electricity(), "gas": gas(), "internet": internet(), "mobile": mobile()}
