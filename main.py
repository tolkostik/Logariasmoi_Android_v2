"""
Λογαριασμοί σπιτιού – η συμφερότερη λύση για ρεύμα, φυσικό αέριο, internet και κινητή, με ένα πάτημα.
"""
import threading
import time
import webbrowser

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty, StringProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import NoTransition, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import platform

import advisor as A
import engine as E
import store as S
import ui_widgets as UW

IS_ANDROID = platform == "android"
TABS = ("home", "compare", "bills", "settings")
TARIFF_CHOICES = {
    "Όλα τα χρώματα": ["Σταθερό (μπλε)", "Κυμαινόμενο (κίτρινο)", "Ειδικό (πράσινο)"],
    "Μόνο μπλε (σταθερή τιμή)": ["Σταθερό (μπλε)"],
    "Μόνο πράσινο (γνωστή τιμή κάθε μήνα)": ["Ειδικό (πράσινο)"],
    "Μόνο κίτρινο (κυμαινόμενη τιμή)": ["Κυμαινόμενο (κίτρινο)"],
    "Μπλε και πράσινο": ["Σταθερό (μπλε)", "Ειδικό (πράσινο)"],
}


def tariff_label(types):
    for k, v in TARIFF_CHOICES.items():
        if sorted(v) == sorted(types):
            return k
    return "Όλα τα χρώματα"
TITLES = {"home": "Λογαριασμοί σπιτιού", "compare": "Όλες οι εταιρείες", "bills": "Τα στοιχεία μου",
          "settings": "Ρυθμίσεις", "result": "Η καλύτερη λύση", "plan": "Πρόγραμμα"}
SICON = {"electricity": "bolt", "gas": "flame", "internet": "wifi", "mobile": "phone"}

KV = """
#:import dp kivy.metrics.dp

<NavItem>:
    orientation: 'vertical'
    padding: 0, dp(6)
    spacing: dp(2)

<Root>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: app.c_bg
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        size_hint_y: None
        height: dp(58)
        padding: dp(8), dp(6)
        spacing: dp(6)
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
                texture: app.grad
        Button:
            text: '<'
            bold: True
            font_size: '24sp'
            size_hint_x: None
            width: dp(46) if app.can_back else 0
            opacity: 1 if app.can_back else 0
            disabled: not app.can_back
            background_normal: ''
            background_color: 1, 1, 1, 0.15
            on_release: app.back()
        Label:
            text: app.title_text
            bold: True
            font_size: '20sp'
            halign: 'left'
            valign: 'middle'
            text_size: self.size
            shorten: True
    ScreenManager:
        id: sm
    BoxLayout:
        id: undo_bar
        size_hint_y: None
        height: 0
        opacity: 0
        padding: dp(8), dp(4)
        spacing: dp(8)
        canvas.before:
            Color:
                rgba: 0.15, 0.17, 0.24, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            id: undo_lbl
            halign: 'left'
            valign: 'middle'
            text_size: self.size
        Button:
            id: undo_btn
            text: 'ΑΝΑΙΡΕΣΗ'
            bold: True
            size_hint_x: None
            width: dp(120)
            background_normal: ''
            background_color: 0.96, 0.62, 0.0, 1
    BoxLayout:
        id: nav
        size_hint_y: None
        height: dp(64)
        canvas.before:
            Color:
                rgba: app.c_card
            Rectangle:
                pos: self.pos
                size: self.size
            Color:
                rgba: app.c_line
            Rectangle:
                pos: self.x, self.top - dp(1)
                size: self.width, dp(1)
"""


class NavItem(ButtonBehavior, BoxLayout):
    pass


class Root(BoxLayout):
    pass


class Tap(ButtonBehavior, BoxLayout):
    pass


# ------------------------------------------------------------------ προστασία από κλεισίματα
from kivy.base import ExceptionHandler, ExceptionManager  # noqa: E402


class _Guard(ExceptionHandler):
    def handle_exception(self, inst):
        try:
            import traceback
            S.DIR.mkdir(parents=True, exist_ok=True)
            with open(S.DIR / "errors.log", "a", encoding="utf-8") as fh:
                fh.write(time.strftime("%d/%m %H:%M ") + "".join(
                    traceback.format_exception(type(inst), inst, inst.__traceback__))[-1500:] + "\n")
        except Exception:  # noqa: BLE001
            pass
        return ExceptionManager.PASS


ExceptionManager.add_handler(_Guard())


def esc(t):
    return str(t).replace("&", "&amp;").replace("[", "&bl;").replace("]", "&br;")


def gr(x):
    t = f"{x:.1f}".replace(".", ",")
    return t[:-2] if t.endswith(",0") else t


def euro(x):
    return f"{x:.2f}".replace(".", ",") + " €"




def money(x):
    return S.eur(x)


class LogariasmoiApp(App):
    title = "Logariasmoi"
    c_bg = ListProperty([0.949, 0.957, 0.973, 1])
    c_card = ListProperty([1, 1, 1, 1])
    c_line = ListProperty([0.88, 0.9, 0.93, 1])
    grad = ObjectProperty(None, allownone=True)
    can_back = BooleanProperty(False)
    title_text = StringProperty("Λογαριασμοί σπιτιού")

    # ================================================================== εκκίνηση
    def build(self):
        S.set_dir(self.user_data_dir)
        self.d = S.load()
        self.d.setdefault("current", {})
        self.d.setdefault("ui", {"theme": "light"})
        UW.set_theme(self.d["ui"].get("theme", "light"))
        self.c_bg, self.c_card, self.c_line = list(UW.C["bg"]), list(UW.C["card"]), list(UW.C["line"])
        Window.clearcolor = UW.C["bg"]
        self.grad = UW.gradient(UW.PRIMARY, UW.PRIMARY2)
        Builder.load_string(KV)
        self.root_w = Root()
        self.sm = self.root_w.ids.sm
        self.sm.transition = NoTransition()
        self.pages = {}
        for name in TITLES:
            scr = Screen(name=name)
            sv = ScrollView(do_scroll_x=False, bar_width=dp(4))
            box = BoxLayout(orientation="vertical", size_hint_y=None, padding=(dp(12), dp(12)), spacing=dp(12))
            box.bind(minimum_height=box.setter("height"))
            sv.add_widget(box)
            scr.add_widget(sv)
            self.sm.add_widget(scr)
            self.pages[name] = (sv, box)
        self.nav_items = {}
        for key, icon, label in (("home", "home", "Καλύτερη λύση"), ("compare", "chart", "Όλες οι εταιρείες"),
                                 ("bills", "wallet", "Τα στοιχεία μου"), ("settings", "gear", "Ρυθμίσεις")):
            it = NavItem()
            ic = UW.Icon(kind=icon, size_hint_y=None, height=dp(26))
            lb = Label(text=label, font_size=sp(11), size_hint_y=None, height=dp(18))
            it.add_widget(ic)
            it.add_widget(lb)
            it.icon, it.lab = ic, lb
            it.bind(on_release=lambda w, k=key: self.tab(k))
            self.root_w.ids.nav.add_widget(it)
            self.nav_items[key] = it
        self.busy = False
        self.status = ""
        self.stack = []
        self.cmp_service = "electricity"
        Window.bind(on_keyboard=self._key)
        self.tab("home")
        last = max([s_.get("updated") or 0 for s_ in self.d["services"].values()] or [0])
        if time.time() - last > 24 * 3600:
            Clock.schedule_once(lambda dt: self.update(), 4)
        return self.root_w

    def on_pause(self):
        return True

    # ================================================================== πλοήγηση
    def page(self, name):
        sv, box = self.pages[name]
        box.clear_widgets()
        sv.scroll_y = 1
        return box

    def show(self, name, push=True):
        if push and self.sm.current != name:
            self.stack.append(self.sm.current)
        self.sm.current = name
        self.title_text = TITLES.get(name, "Λογαριασμοί")
        self.can_back = name not in TABS
        tab = name if name in TABS else (self.stack[0] if self.stack and self.stack[0] in TABS else "home")
        for k, it in self.nav_items.items():
            on = k == tab
            col = UW.PRIMARY if on else UW.C["muted"]
            it.icon.rgba = list(col)
            it.lab.color = col
            it.lab.bold = on

    def tab(self, name):
        self.stack = []
        getattr(self, "build_" + name)()
        self.show(name, push=False)

    def back(self):
        if not self.stack:
            return False
        prev = self.stack.pop()
        if prev in TABS:
            getattr(self, "build_" + prev)()
        self.show(prev, push=False)
        return True

    def _key(self, win, key, *a):
        if key == 27:
            return self.back()
        return False

    # ================================================================== στοιχεία
    def card(self, box, pad=14):
        c = UW.CardBox(pad=pad)
        box.add_widget(c)
        return c

    def btn(self, parent, text, cb, color=None, fg=(1, 1, 1, 1), h=50):
        b = Button(text=text, bold=True, size_hint_y=None, height=dp(h), background_normal="",
                   background_color=color or UW.PRIMARY, color=fg, font_size=sp(15))
        b.bind(on_release=lambda *a: cb())
        parent.add_widget(b)
        return b

    def ghost(self, parent, text, cb, h=44):
        return self.btn(parent, text, cb, color=UW.C["line"], fg=UW.C["ink"], h=h)

    def plan_row(self, parent, service, p, cost, sub="", on_tap=None, highlight=False):
        r = Tap(orientation="horizontal", size_hint_y=None, height=dp(76), spacing=dp(12), padding=(dp(12), dp(10)))

        def bg(*a):
            r.canvas.before.clear()
            with r.canvas.before:
                if highlight:
                    Color(*UW.GOOD)
                    RoundedRectangle(pos=(r.x - dp(2), r.y - dp(2)), size=(r.width + dp(4), r.height + dp(4)),
                                     radius=[dp(18)])
                Color(*UW.C["card"])
                RoundedRectangle(pos=r.pos, size=r.size, radius=[dp(16)])
        r.bind(pos=bg, size=bg)
        a = AnchorLayout(size_hint_x=None, width=dp(48))
        a.add_widget(UW.BrandBadge(p["provider"]))
        r.add_widget(a)
        col = BoxLayout(orientation="vertical")
        t = Label(text=f"[b]{esc(p['provider'])}[/b]  {esc(p['name'])}", markup=True, color=UW.C["ink"],
                  font_size=sp(14), halign="left", valign="middle", shorten=True)
        t.bind(size=lambda w, s: setattr(w, "text_size", s))
        st = Label(text=sub, markup=True, color=UW.C["muted"], font_size=sp(11), halign="left", valign="middle",
                   shorten=True)
        st.bind(size=lambda w, s: setattr(w, "text_size", s))
        col.add_widget(t)
        col.add_widget(st)
        r.add_widget(col)
        price = Label(text=f"[b]{money(cost)}[/b]\n[size=10sp]/μήνα[/size]", markup=True, color=UW.PRIMARY,
                      font_size=sp(17), size_hint_x=None, width=dp(92), halign="right", valign="middle")
        price.bind(size=lambda w, s: setattr(w, "text_size", s))
        r.add_widget(price)
        r.bind(on_release=lambda *x: (on_tap or (lambda: self.open_plan(service, p)))())
        parent.add_widget(r)
        return r

    def share(self, text):
        if not IS_ANDROID:
            try:
                from kivy.core.clipboard import Clipboard
                Clipboard.copy(text)
            except Exception:  # noqa: BLE001
                pass
            return
        try:
            from jnius import autoclass, cast
            Intent = autoclass("android.content.Intent")
            String = autoclass("java.lang.String")
            act = autoclass("org.kivy.android.PythonActivity").mActivity
            i = Intent(Intent.ACTION_SEND)
            i.setType("text/plain")
            i.putExtra(Intent.EXTRA_TEXT, cast("java.lang.CharSequence", String(text)))
            act.startActivity(Intent.createChooser(i, cast("java.lang.CharSequence", String("Κοινοποίηση"))))
        except Exception:  # noqa: BLE001
            pass

    # ================================================================== ενημέρωση τιμών
    def update(self):
        """Κάθε πάτημα ξεκινά νέα ενημέρωση (αν τρέχει ήδη μία, η παλιά αγνοείται)."""
        import copy
        self._utoken = getattr(self, "_utoken", 0) + 1
        token = self._utoken
        self.busy = True
        self.status = "Ενημέρωση… σύνδεση με τις πηγές"
        self._refresh()
        work_d = copy.deepcopy(self.d)
        before = A.snapshot(self.d)
        done_list = []

        def progress(msg):
            def put(dt):
                if self._utoken == token:
                    self.status = msg
                    lbl = getattr(self, "_status_lbl", None)
                    if lbl is not None:
                        lbl.text = msg
            Clock.schedule_once(put)

        def work():
            try:
                errs = S.update_all(work_d, progress)
            except Exception as e:  # noqa: BLE001
                errs = {k: str(e) for k in E.SERVICES}
            Clock.schedule_once(lambda dt: done(errs))

        def done(errs):
            if self._utoken != token:
                return                      # υπάρχει πιο πρόσφατη ενημέρωση
            self.busy = False
            for k in ("current", "ui", "my_provider", "contract_end", "best_history"):
                if k in self.d:
                    work_d[k] = self.d[k]
            work_d["profile"] = self.d["profile"]
            self.d = work_d
            after = A.snapshot(self.d)
            A.record_history(self.d, after)
            self.changes = A.changes(before, after)
            S.save(self.d)
            ok = [E.LABELS[k] for k, v in errs.items() if not v]
            bad = [E.LABELS[k] for k, v in errs.items() if v]
            now = time.strftime("%H:%M")
            if not bad:
                self.status = f"Ενημερώθηκε στις {now}: όλες οι τιμές είναι τρέχουσες."
            elif ok:
                self.status = (f"Ενημερώθηκε στις {now}: {', '.join(ok)}. Για {', '.join(bad)} οι πηγές δεν "
                               f"απάντησαν, κρατήθηκαν οι προηγούμενες τιμές.")
            else:
                self.status = (f"{now}: οι πηγές δεν απάντησαν (έλεγξε το internet). Χρησιμοποιούνται οι "
                               f"αποθηκευμένες τιμές.")
            done_list.append(1)
            self._refresh()

        def watchdog(dt):
            if self._utoken == token and self.busy:
                self.busy = False
                self.status = "Η ενημέρωση άργησε πολύ. Πάτα ξανά «Ενημέρωση τιμών»."
                self._refresh()
        Clock.schedule_once(watchdog, 90)
        threading.Thread(target=work, daemon=True).start()

    def _refresh(self):
        cur = self.sm.current
        if cur in TABS:
            getattr(self, "build_" + cur)()
        elif cur == "result" and getattr(self, "_last_cat", None):
            self.stack and self.stack.pop()
            self.open_result(self._last_cat)

    # ================================================================== ΑΡΧΙΚΗ
    def build_home(self):
        box = self.page("home")
        allbest = A.best_for(self.d, "all")
        hero = BoxLayout(orientation="vertical", size_hint_y=None, padding=(dp(18), dp(16)), spacing=dp(6))
        hero.bind(minimum_height=hero.setter("height"))

        def hbg(*a):
            hero.canvas.before.clear()
            with hero.canvas.before:
                Color(1, 1, 1, 1)
                RoundedRectangle(pos=hero.pos, size=hero.size, radius=[dp(22)], texture=self.grad)
        hero.bind(pos=hbg, size=hbg)
        hero.add_widget(UW.text("Με τις καλύτερες επιλογές σήμερα, όλοι οι λογαριασμοί του σπιτιού σου κοστίζουν",
                                size=14, color=(1, 1, 1, 0.92)))
        if allbest:
            hero.add_widget(UW.text(f"[b]{money(allbest['total'])}[/b] [size=14sp]/μήνα[/size]", size=34,
                                    color=(1, 1, 1, 1)))
            sv = A.savings(self.d, "all", allbest["total"])
            if sv and sv["month"] > 0:
                hero.add_widget(UW.text(f"Γλιτώνεις [b]{money(sv['month'])}/μήνα[/b] · [b]{money(sv['year'])} τον "
                                        f"χρόνο[/b] σε σχέση με σήμερα", size=14, color=(1, 1, 1, 1)))
            elif not sv:
                hero.add_widget(UW.text("Γράψε πόσα πληρώνεις σήμερα στο «Οι λογαριασμοί μου» για να δεις πόσα "
                                        "γλιτώνεις.", size=12, color=(1, 1, 1, 0.85)))
        b = Button(text="ΕΝΗΜΕΡΩΣΗ ΤΙΜΩΝ (σε εξέλιξη…)" if self.busy else "ΕΝΗΜΕΡΩΣΗ ΤΙΜΩΝ", bold=True,
                   size_hint_y=None, height=dp(48), background_normal="", background_color=(1, 1, 1, 0.25))
        b.bind(on_release=lambda *a: self.update())
        hero.add_widget(b)
        last = max([v.get("updated") or 0 for v in self.d["services"].values()] or [0])
        when = (time.strftime("Τιμές της %d/%m/%Y %H:%M", time.localtime(last)) if last else
                "Ενσωματωμένες τιμές (πάτα ενημέρωση)")
        self._status_lbl = UW.text(self.status or when, size=12, color=(1, 1, 1, 0.95))
        hero.add_widget(self._status_lbl)
        box.add_widget(hero)

        for k, diff in (getattr(self, "changes", None) or [])[:4]:
            col = UW.GOOD if diff < 0 else UW.BAD
            word = "φθηνότερη" if diff < 0 else "ακριβότερη"
            ch = self.card(box, pad=10)
            ch.add_widget(UW.text(f"[color={UW.hexc(col)}][b]{A.CAT[k][0]}[/b][/color]: η καλύτερη λύση έγινε {word} "
                                  f"κατά [b]{money(abs(diff))}/μήνα[/b] μετά την ενημέρωση.", size=13))
        for s_, left, end in A.contract_alerts(self.d):
            al = self.card(box, pad=10)
            txt = (f"Η σύμβαση για [b]{E.LABELS[s_]}[/b] έληξε στις {end:%d/%m/%Y}." if left < 0 else
                   f"Η σύμβαση για [b]{E.LABELS[s_]}[/b] λήγει σε [b]{left} ημέρες[/b] ({end:%d/%m/%Y}).")
            al.add_widget(UW.text(txt + " Καλή στιγμή να συγκρίνεις.", size=13, color=UW.WARN))
            self.ghost(al, f"Δες την καλύτερη λύση για {E.LABELS[s_]}", lambda ss=s_: self.open_result(ss), h=40)
        box.add_widget(UW.text("[b]Τι θέλεις να βρεις φθηνότερο;[/b]", size=17))
        box.add_widget(UW.text("Πάτα ένα κουτί: σου δείχνω αμέσως τη συμφερότερη εταιρεία και πόσα γλιτώνεις.",
                               size=12, color=UW.C["muted"]))
        grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for key, title, icon, services in A.CATEGORIES:
            best = A.best_for(self.d, key)
            tile = Tap(orientation="vertical", size_hint_y=None, height=dp(124), padding=(dp(12), dp(10)),
                       spacing=dp(2))

            def tbg(w, *a, k=key):
                w.canvas.before.clear()
                with w.canvas.before:
                    Color(*(UW.PRIMARY if k == "all" else UW.C["card"]))
                    RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(18)])
            tile.bind(pos=tbg, size=tbg)
            on_dark = key == "all"
            ink = (1, 1, 1, 1) if on_dark else UW.C["ink"]
            tile.add_widget(UW.Icon(kind=icon, rgba=list((1, 1, 1, 1) if on_dark else UW.PRIMARY), size_hint_y=None,
                                    height=dp(30)))
            tl = Label(text=f"[b]{title}[/b]", markup=True, color=ink, font_size=sp(14), size_hint_y=None,
                       height=dp(24))
            tile.add_widget(tl)
            if best:
                provs = " + ".join(dict.fromkeys(i["plan"]["provider"] for i in best["items"]))
                tile.add_widget(Label(text=f"[b]{money(best['total'])}[/b]/μήνα", markup=True, color=ink,
                                      font_size=sp(17), size_hint_y=None, height=dp(26)))
                pl = Label(text=provs, color=(1, 1, 1, 0.85) if on_dark else UW.C["muted"], font_size=sp(11),
                           shorten=True, size_hint_y=None, height=dp(18))
                pl.bind(size=lambda w, s: setattr(w, "text_size", s))
                tile.add_widget(pl)
            tile.bind(on_release=lambda w, k=key: self.open_result(k))
            grid.add_widget(tile)
        box.add_widget(grid)
        guide = self.card(box)
        guide.add_widget(UW.text("[b]Πώς δουλεύει[/b]", size=14))
        for line in ("[b]Καλύτερη λύση[/b] (εδώ): η φθηνότερη επιλογή με ένα πάτημα.",
                     "[b]Όλες οι εταιρείες[/b]: γράφημα με όλες τις εταιρείες, για να συγκρίνεις μόνος σου.",
                     "[b]Τα στοιχεία μου[/b]: γράψε πόσα πληρώνεις και πόσο καταναλώνεις, για σωστούς υπολογισμούς.",
                     "[b]Ρυθμίσεις[/b]: ενημέρωση τιμών, εταιρείες που δεν θέλεις, εμφάνιση."):
            guide.add_widget(UW.text("• " + line, size=12))

    # ================================================================== ΑΠΟΤΕΛΕΣΜΑ
    def open_result(self, cat):
        title, icon, services = A.CAT[cat]
        self._last_cat = cat
        best = A.best_for(self.d, cat)
        box = self.page("result")
        if "electricity" in services:
            box.add_widget(UW.text("[b]Τιμολόγια ρεύματος:[/b] πάτα για να δεις μόνο ένα χρώμα", size=13))
            row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            cur_lbl = tariff_label(self.d["profile"]["el_types"])
            for short, key, col in (("Όλα", "Όλα τα χρώματα", UW.PRIMARY),
                                    ("Μπλε", "Μόνο μπλε (σταθερή τιμή)", (0.16, 0.42, 0.85, 1)),
                                    ("Πράσινο", "Μόνο πράσινο (γνωστή τιμή κάθε μήνα)", (0.15, 0.6, 0.3, 1)),
                                    ("Κίτρινο", "Μόνο κίτρινο (κυμαινόμενη τιμή)", (0.85, 0.65, 0.05, 1))):
                on = cur_lbl == key
                bt = Button(text=short, bold=on, background_normal="", font_size=sp(13),
                            background_color=col if on else UW.C["line"], color=(1, 1, 1, 1) if on else UW.C["ink"])

                def pick(w_, k=key):
                    self.d["profile"]["el_types"] = TARIFF_CHOICES[k]
                    S.save(self.d)
                    self.stack and self.stack.pop()
                    self.open_result(cat)
                bt.bind(on_release=pick)
                row.add_widget(bt)
            box.add_widget(row)
        if not best:
            box.add_widget(UW.text("Δεν βρέθηκε πρόγραμμα με τα κριτήριά σου. Άλλαξε τα φίλτρα στο «Οι λογαριασμοί "
                                   "μου».", color=UW.C["muted"]))
            self.show("result")
            return
        c = self.card(box)
        c.add_widget(UW.text(f"[b]{title}[/b] · η συμφερότερη λύση", size=15, color=UW.PRIMARY))
        c.add_widget(UW.text(f"[b]{money(best['total'])}[/b] [size=13sp]/μήνα · {money(best['total'] * 12)} τον "
                             f"χρόνο[/size]", size=30))
        sv = A.savings(self.d, cat, best["total"])
        if sv:
            col = UW.GOOD if sv["month"] > 0 else UW.WARN
            txt = (f"Γλιτώνεις [b]{money(sv['month'])}/μήνα[/b] ([b]{money(sv['year'])}/έτος[/b]) σε σχέση με τα "
                   f"{money(sv['now'])} που πληρώνεις σήμερα." if sv["month"] > 0 else
                   "Πληρώνεις ήδη περίπου όσο η καλύτερη λύση. Μπράβο!")
            c.add_widget(UW.text(txt, size=14, color=col))
        tr = A.trend(self.d, cat)
        if tr and tr[0] >= 1 and abs(tr[1] - best["total"]) >= 0.3:
            word = "πιο φθηνά" if best["total"] < tr[1] else "πιο ακριβά"
            c.add_widget(UW.text(f"Πριν από {tr[0]} ημέρες η καλύτερη λύση ήταν {money(tr[1])}: σήμερα είναι {word}.",
                                 size=12, color=UW.C["muted"]))
        if best.get("separately") and best["separately"] > best["total"] + 0.01:
            c.add_widget(UW.text(f"Ο συνδυασμός σε ίδια εταιρεία γλιτώνει {money(best['separately'] - best['total'])}"
                                 f"/μήνα σε σχέση με χωριστές συμβάσεις.", size=13, color=UW.GOOD))
        for it in best["items"]:
            s_ = it["service"]
            sub = E.LABELS[s_] + (" · [b]έκπτωση συνδυασμού[/b]" if it.get("deal") else "")
            self.plan_row(box, s_, it["plan"], it["cost"], sub, highlight=True)
        if len(services) == 1:
            mine = A.same_company_best(self.d, services[0])
            if mine and mine["provider"] != best["items"][0]["plan"]["provider"]:
                box.add_widget(UW.text(f"[b]Αν μείνεις στον πάροχό σου ({esc(mine['provider'])})[/b], το φθηνότερο "
                                       f"πρόγραμμά του:", size=14))
                self.plan_row(box, services[0], mine, mine["cost"],
                              f"+{money(mine['cost'] - best['total'])}/μήνα από την καλύτερη λύση")
        alts = best.get("alternatives") or []
        if len(services) == 1:
            alts_rows = (best.get("per_company") or [])[1:6]
            if alts_rows:
                box.add_widget(UW.text("[b]Επόμενες καλύτερες εταιρείες[/b]", size=15))
                for r in alts_rows:
                    diff = r["cost"] - best["total"]
                    self.plan_row(box, services[0], r, r["cost"], f"+{money(diff)}/μήνα από την καλύτερη")
            self.ghost(box, "Σύγκριση όλων των εταιρειών", lambda: self._open_compare(services[0]))
        elif alts:
            box.add_widget(UW.text("[b]Άλλοι καλοί συνδυασμοί[/b]", size=15))
            for alt in alts[:3]:
                cc = self.card(box, pad=10)
                provs = " + ".join(f"{i['plan']['provider']}" for i in alt["items"])
                cc.add_widget(UW.text(f"[b]{money(alt['total'])}[/b]/μήνα  (+{money(alt['total'] - best['total'])})\n"
                                      f"[size=12sp]{esc(provs)}[/size]", size=14))
        help_c = self.card(box)
        help_c.add_widget(UW.text("[b]Πώς αλλάζω πάροχο[/b]", size=15))
        for s_ in services:
            for line in A.SWITCH_HELP.get(s_, [])[:2]:
                help_c.add_widget(UW.text("• " + line, size=13))
        text = f"{title}: {money(best['total'])}/μήνα\n" + "\n".join(
            f"- {E.LABELS[i['service']]}: {i['plan']['provider']} {i['plan']['name']} ({money(i['cost'])})"
            for i in best["items"]) + "\n(από την εφαρμογή Λογαριασμοί σπιτιού)"
        self.btn(box, "ΚΟΙΝΟΠΟΙΗΣΗ", lambda: self.share(text))
        box.add_widget(UW.text("Οι τιμές προέρχονται από δημόσιες συγκρίσεις (ΡΑΑΕΥ, ΕΕΤΤ κ.ά.) και μπορεί να "
                               "αλλάξουν. Επιβεβαίωσε πάντα στη σελίδα του παρόχου πριν υπογράψεις.", size=11,
                               color=UW.C["muted"]))
        self.show("result")

    # ================================================================== ΣΥΓΚΡΙΣΗ
    def _open_compare(self, service):
        self.cmp_service = service
        self.tab("compare")

    def build_compare(self):
        box = self.page("compare")
        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        for s_ in E.SERVICES:
            on = s_ == self.cmp_service
            b = Button(text=E.LABELS[s_].replace(" σπιτιού", ""), bold=on, font_size=sp(13), background_normal="",
                       background_color=UW.PRIMARY if on else UW.C["line"], color=(1, 1, 1, 1) if on else UW.C["ink"])
            b.bind(on_release=lambda w, ss=s_: (setattr(self, "cmp_service", ss), self.build_compare()))
            row.add_widget(b)
        box.add_widget(row)
        per, rows = A.company_ranking(self.d, self.cmp_service)
        if not per:
            box.add_widget(UW.text("Δεν υπάρχουν προγράμματα με τα κριτήριά σου.", color=UW.C["muted"]))
            return
        c = self.card(box)
        c.add_widget(UW.text(f"[b]Φθηνότερο πρόγραμμα κάθε εταιρείας[/b] · {E.LABELS[self.cmp_service]}", size=15))
        hi = max(r["cost"] for r in per) or 1
        lo = per[0]["cost"]
        for i, r in enumerate(per[:15]):
            line = Tap(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
            a = AnchorLayout(size_hint_x=None, width=dp(40))
            a.add_widget(UW.BrandBadge(r["provider"], size=(dp(34), dp(34))))
            line.add_widget(a)
            barw = Widget()

            def draw(w, *x, frac=r["cost"] / hi, best=(i == 0)):
                w.canvas.before.clear()
                with w.canvas.before:
                    Color(*(UW.GOOD if best else UW.PRIMARY))
                    RoundedRectangle(pos=(w.x, w.y + dp(10)), size=(w.width * max(0.05, frac), w.height - dp(20)),
                                     radius=[dp(6)])
            barw.bind(pos=draw, size=draw)
            line.add_widget(barw)
            lb = Label(text=f"[b]{money(r['cost'])}[/b]", markup=True, color=UW.C["ink"], font_size=sp(13),
                       size_hint_x=None, width=dp(84), halign="right", valign="middle")
            lb.bind(size=lambda w, s: setattr(w, "text_size", s))
            line.add_widget(lb)
            line.bind(on_release=lambda w, rr=r: self.open_plan(self.cmp_service, rr))
            c.add_widget(line)
        c.add_widget(UW.text(f"Η φθηνότερη εταιρεία γλιτώνει έως {money(hi - lo)}/μήνα σε σχέση με την ακριβότερη.",
                             size=12, color=UW.C["muted"]))
        box.add_widget(UW.text(f"[b]Όλα τα προγράμματα ({len(rows)})[/b]", size=15))
        limit = getattr(self, "_cmp_limit", 25)
        if len(rows) > limit:
            pass
        for r in rows[:limit]:
            sub = r.get("type") or r.get("tech") or ""
            if r.get("cost_partner") is not None and r["cost_partner"] < r["cost"] - 0.005:
                sub += f" · με συνδυασμό {money(r['cost_partner'])}"
            self.plan_row(box, self.cmp_service, r, r["cost"], esc(sub))
        if len(rows) > limit:
            self.ghost(box, f"Δείξε περισσότερα ({len(rows) - limit})",
                       lambda: (setattr(self, "_cmp_limit", limit + 25), self.build_compare()))
        else:
            self._cmp_limit = 25

    # ================================================================== ΠΡΟΓΡΑΜΜΑ
    def open_plan(self, service, p):
        box = self.page("plan")
        c = self.card(box)
        top = BoxLayout(size_hint_y=None, height=dp(64), spacing=dp(12))
        a = AnchorLayout(size_hint_x=None, width=dp(64))
        a.add_widget(UW.BrandBadge(p["provider"], size=(dp(58), dp(58))))
        top.add_widget(a)
        top.add_widget(UW.text(f"[b]{esc(p['provider'])}[/b]\n{esc(p['name'])}", size=16))
        c.add_widget(top)
        c.add_widget(UW.text(f"[b]{money(p['cost'])}[/b] [size=13sp]/μήνα για το προφίλ σου · {E.LABELS[service]}"
                             f"[/size]", size=26, color=UW.PRIMARY))
        if p.get("cost_partner") is not None and p["cost_partner"] < p["cost"] - 0.005:
            c.add_widget(UW.text(f"Με συνδυασμό στην ίδια εταιρεία: [b]{money(p['cost_partner'])}[/b]/μήνα", size=14,
                                 color=UW.GOOD))
        for k, v in A.plan_lines(service, p):
            c.add_widget(UW.text(f"[color={UW.hexc(UW.C['muted'])}]{k}:[/color] [b]{esc(v)}[/b]", size=14))
        if p.get("url"):
            self.btn(box, "ΣΕΛΙΔΑ ΤΟΥ ΠΑΡΟΧΟΥ", lambda: webbrowser.open(p["url"]))
        h = self.card(box)
        h.add_widget(UW.text("[b]Πώς αλλάζω πάροχο[/b]", size=15))
        for line in A.SWITCH_HELP.get(service, []):
            h.add_widget(UW.text("• " + line, size=13))
        if service == "electricity":
            t = self.card(box)
            t.add_widget(UW.text("[b]Τι σημαίνουν τα χρώματα των τιμολογίων[/b]", size=15))
            for k, v in A.TARIFF_HELP:
                t.add_widget(UW.text(f"[b]{k}[/b]: {v}", size=13))
        self.show("plan")

    # ================================================================== ΟΙ ΛΟΓΑΡΙΑΣΜΟΙ ΜΟΥ
    def build_bills(self):
        box = self.page("bills")
        prof = self.d["profile"]
        cur = self.d["current"]
        w = {}

        def line(parent, label, widget, h=46):
            r = BoxLayout(size_hint_y=None, height=dp(h), spacing=dp(8))
            lb = Label(text=label, color=UW.C["ink"], halign="left", valign="middle", font_size=sp(14))
            lb.bind(size=lambda x, v: setattr(x, "text_size", v))
            r.add_widget(lb)
            widget.size_hint_x = 0.42
            r.add_widget(widget)
            parent.add_widget(r)

        c = self.card(box)
        c.add_widget(UW.text("[b]1. Πόσα πληρώνω σήμερα[/b] (€ τον μήνα)", size=15))
        c.add_widget(UW.text("Από τους τελευταίους λογαριασμούς σου. Χρειάζεται για να δεις πόσα γλιτώνεις. Άφησε "
                             "κενό ό,τι δεν έχεις.", size=12, color=UW.C["muted"]))
        myp = self.d.setdefault("my_provider", {})
        ends = self.d.setdefault("contract_end", {})
        for s_ in E.SERVICES:
            c.add_widget(UW.text(f"[b]{E.LABELS[s_]}[/b]", size=14))
            ti = TextInput(text=str(cur.get(s_, "") or ""), hint_text="€/μήνα", input_filter="float", multiline=False)
            w["cur_" + s_] = ti
            line(c, "Πληρώνω (€/μήνα)", ti)
            provs = ["—"] + sorted({p["provider"] for p in self.d["services"][s_]["plans"]})
            sp_ = Spinner(text=myp.get(s_) or "—", values=provs)
            w["prov_" + s_] = sp_
            line(c, "Εταιρεία μου", sp_)
            en = TextInput(text=ends.get(s_, ""), hint_text="ηη/μμ/εεεε", multiline=False)
            w["end_" + s_] = en
            line(c, "Λήξη σύμβασης (αν έχει)", en)
        c2 = self.card(box)
        c2.add_widget(UW.text("[b]2. Πόσο καταναλώνω[/b]", size=15))
        c2.add_widget(UW.text("Γράφεται στον λογαριασμό ρεύματος/αερίου. Αν δεν το ξέρεις, πάτα το κουμπί από κάτω.",
                              size=12, color=UW.C["muted"]))
        kwh = TextInput(text=f"{prof['kwh_month']:g}", input_filter="float", multiline=False)
        w["kwh"] = kwh
        line(c2, "Ρεύμα: kWh τον μήνα", kwh)
        gas = TextInput(text=f"{prof['gas_kwh_year']:g}", input_filter="float", multiline=False)
        w["gas"] = gas
        line(c2, "Αέριο: kWh τον χρόνο", gas)
        heat = Spinner(text=prof["heating"], values=["Αυτόνομη", "Κεντρική"])
        w["heat"] = heat
        line(c2, "Θέρμανση", heat)
        self.ghost(c2, "Δεν ξέρω την κατανάλωσή μου: υπολόγισέ τη", lambda: self._estimator(c2, kwh, gas), h=42)
        c3 = self.card(box)
        c3.add_widget(UW.text("[b]3. Τι θέλω από internet και κινητή[/b]", size=15))
        mb = TextInput(text=f"{prof['min_mbps']:g}", input_filter="float", multiline=False)
        w["mbps"] = mb
        line(c3, "Internet: τουλάχιστον Mbps", mb)
        gb = TextInput(text=f"{prof['min_gb']:g}", input_filter="float", multiline=False)
        w["gb"] = gb
        line(c3, "Κινητή: τουλάχιστον GB", gb)
        lines_ = Spinner(text=str(prof["mobile_lines"]), values=["1", "2", "3", "4", "5"])
        w["lines"] = lines_
        line(c3, "Γραμμές κινητού", lines_)
        uv = CheckBox(active=prof["unlimited_voice"], color=UW.C["ink"])
        w["uv"] = uv
        line(c3, "Απεριόριστη ομιλία", uv)
        mt = Spinner(text=prof["mobile_type"], values=["Όλα", "Συμβόλαιο", "Καρτοκινητό"])
        w["mt"] = mt
        line(c3, "Είδος κινητής", mt)
        fwa = CheckBox(active="4G/5G" in prof["net_techs"], color=UW.C["ink"])
        w["fwa"] = fwa
        line(c3, "Δέχομαι internet 4G/5G", fwa)
        c4 = self.card(box)
        c4.add_widget(UW.text("[b]4. Τιμολόγια ρεύματος[/b]", size=15))
        c4.add_widget(UW.text("Διάλεξε ένα χρώμα, δύο ή όλα. Μπλε: σταθερή τιμή · Πράσινο: η τιμή ανακοινώνεται "
                              "στην αρχή του μήνα · Κίτρινο: κυμαινόμενη, γνωστή μετά την κατανάλωση.", size=12,
                              color=UW.C["muted"]))
        tsp = Spinner(text=tariff_label(prof["el_types"]), values=list(TARIFF_CHOICES), size_hint_y=None,
                      height=dp(46))
        w["tariff"] = tsp
        c4.add_widget(tsp)
        kd = CheckBox(active=prof["keep_discounts"], color=UW.C["ink"])
        w["kd"] = kd
        line(c4, "Πληρώνω πάντα στην ώρα μου (εκπτώσεις)", kd)
        msg = UW.text("", size=13, color=UW.GOOD)

        def f(x, dflt):
            try:
                return float(x.text.replace(",", "."))
            except ValueError:
                return dflt

        def save():
            for s_ in E.SERVICES:
                v = w["cur_" + s_].text.strip()
                cur[s_] = f(w["cur_" + s_], None) if v else None
                pv = w["prov_" + s_].text
                myp[s_] = None if pv == "—" else pv
                ends[s_] = w["end_" + s_].text.strip()
            prof.update(kwh_month=f(w["kwh"], 300), gas_kwh_year=f(w["gas"], 6000), heating=w["heat"].text,
                        min_mbps=f(w["mbps"], 0), min_gb=f(w["gb"], 0), mobile_lines=int(w["lines"].text),
                        unlimited_voice=w["uv"].active, mobile_type=w["mt"].text,
                        net_techs=["Fiber/VDSL"] + (["4G/5G"] if w["fwa"].active else []),
                        el_types=TARIFF_CHOICES[w["tariff"].text],
                        keep_discounts=w["kd"].active)
            S.save(self.d)
            msg.text = "Αποθηκεύτηκε. Πήγαινε στην «Καλύτερη λύση» για τα νέα αποτελέσματα."
        self.btn(box, "ΑΠΟΘΗΚΕΥΣΗ ΚΑΙ ΝΕΟΣ ΥΠΟΛΟΓΙΣΜΟΣ", save, color=UW.GOOD)
        box.add_widget(msg)

    def _estimator(self, parent, kwh_in, gas_in):
        if getattr(self, "_est_open", False):
            return
        self._est_open = True
        e = UW.CardBox(pad=10)
        e.add_widget(UW.text("[b]Γρήγορη εκτίμηση[/b]", size=14))
        people = Spinner(text="3", values=[str(i) for i in range(1, 8)], size_hint_y=None, height=dp(42))
        m2 = TextInput(text="80", input_filter="int", multiline=False, size_hint_y=None, height=dp(42))
        checks = {}
        for k, label in (("ac", "Κλιματιστικά συχνά"), ("we", "Ηλεκτρικός θερμοσίφωνας"),
                         ("ce", "Ηλεκτρική κουζίνα"), ("hg", "Θέρμανση με φυσικό αέριο"),
                         ("wg", "Ζεστό νερό με φυσικό αέριο")):
            r = BoxLayout(size_hint_y=None, height=dp(40))
            cb = CheckBox(active=k in ("we", "ce", "hg"), size_hint_x=None, width=dp(40), color=UW.C["ink"])
            lb = Label(text=label, color=UW.C["ink"], halign="left", valign="middle")
            lb.bind(size=lambda x, v: setattr(x, "text_size", v))
            r.add_widget(cb)
            r.add_widget(lb)
            checks[k] = cb
            e.add_widget(r)
        r1 = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        r1.add_widget(Label(text="Άτομα", color=UW.C["ink"]))
        r1.add_widget(people)
        r1.add_widget(Label(text="m²", color=UW.C["ink"]))
        r1.add_widget(m2)
        e.add_widget(r1)

        def apply():
            try:
                area = int(m2.text or 80)
            except ValueError:
                area = 80
            kwh_in.text = str(A.estimate_kwh_month(int(people.text), checks["ac"].active, checks["we"].active,
                                                   checks["ce"].active, area > 110))
            gas_in.text = str(A.estimate_gas_year(area, checks["hg"].active, checks["wg"].active, False))
            res.text = f"Εκτίμηση: {kwh_in.text} kWh/μήνα ρεύμα, {gas_in.text} kWh/έτος αέριο. Πάτα «Αποθήκευση»."
        self.btn(e, "ΥΠΟΛΟΓΙΣΜΟΣ", apply, h=42)
        res = UW.text("", size=12, color=UW.GOOD)
        e.add_widget(res)
        parent.add_widget(e)

    # ================================================================== ΡΥΘΜΙΣΕΙΣ
    def build_settings(self):
        box = self.page("settings")
        c = self.card(box)
        c.add_widget(UW.text("[b]Τιμές[/b]", size=15))
        for s_ in E.SERVICES:
            info = self.d["services"][s_]
            when = time.strftime("%d/%m/%Y %H:%M", time.localtime(info["updated"])) if info.get("updated") else \
                info.get("origin", "")
            c.add_widget(UW.text(f"{E.LABELS[s_]}: {len(info['plans'])} προγράμματα · {when}", size=13))
        self.btn(c, "ΕΝΗΜΕΡΩΣΗ ΤΩΡΑ (σε εξέλιξη…)" if self.busy else "ΕΝΗΜΕΡΩΣΗ ΤΩΡΑ", self.update, h=46)
        if self.status:
            c.add_widget(UW.text(self.status, size=12, color=UW.C["muted"]))
        c2 = self.card(box)
        c2.add_widget(UW.text("[b]Εξαίρεση εταιρειών[/b] (δεν θα προτείνονται)", size=15))
        provs = sorted({p["provider"] for s_ in E.SERVICES for p in self.d["services"][s_]["plans"]})
        excl = set(self.d["profile"].get("exclude_providers", []))
        for pv in provs:
            r = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
            cb = CheckBox(active=pv in excl, size_hint_x=None, width=dp(40), color=UW.C["ink"])

            def toggle(w, v, name=pv):
                ex = set(self.d["profile"].get("exclude_providers", []))
                (ex.add if v else ex.discard)(name)
                self.d["profile"]["exclude_providers"] = sorted(ex)
                S.save(self.d)
            cb.bind(active=toggle)
            a = AnchorLayout(size_hint_x=None, width=dp(40))
            a.add_widget(UW.BrandBadge(pv, size=(dp(32), dp(32))))
            lb = Label(text=pv, color=UW.C["ink"], halign="left", valign="middle")
            lb.bind(size=lambda x, v: setattr(x, "text_size", v))
            r.add_widget(cb)
            r.add_widget(a)
            r.add_widget(lb)
            c2.add_widget(r)
        c3 = self.card(box)
        c3.add_widget(UW.text("[b]Εμφάνιση[/b]", size=15))
        th = Spinner(text="Σκοτεινό" if self.d["ui"].get("theme") == "dark" else "Φωτεινό",
                     values=["Φωτεινό", "Σκοτεινό"], size_hint_y=None, height=dp(44))
        note = UW.text("", size=12, color=UW.WARN)

        def ch(w, v):
            self.d["ui"]["theme"] = "dark" if v == "Σκοτεινό" else "light"
            S.save(self.d)
            note.text = "Εφαρμόζεται όταν ξανανοίξεις την εφαρμογή."
        th.bind(text=ch)
        c3.add_widget(th)
        c3.add_widget(note)
        c4 = self.card(box)
        c4.add_widget(UW.text("[b]Πηγές[/b]", size=15))
        c4.add_widget(UW.text("Ρεύμα & αέριο: timesrevmatos.gr (ανοιχτά δεδομένα) και kilovatora.gr (στοιχεία "
                              "ΡΑΑΕΥ). Internet & κινητή: agorasmart.gr και kilovatora.gr (στοιχεία ΕΕΤΤ). Αν μια πηγή "
                              "δεν απαντήσει, χρησιμοποιείται η δεύτερη ή οι τελευταίες αποθηκευμένες τιμές. Για "
                              "επίσημο έλεγχο: energycost.gr (ΡΑΑΕΥ) και ΕΕΤΤ.", size=12, color=UW.C["muted"]))
        c4.add_widget(UW.text("Τα σήματα με τα αρχικά είναι της εφαρμογής, για αναγνώριση· δεν είναι τα επίσημα "
                              "λογότυπα των εταιρειών.", size=11, color=UW.C["muted"]))


if __name__ == "__main__":
    LogariasmoiApp().run()
