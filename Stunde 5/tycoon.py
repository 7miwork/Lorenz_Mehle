"""
╔══════════════════════════════════════════════════════╗
║    BUSINESS TYCOON PRO  —  by Michael (其米）         ║
║    pip install pygame  →  python business_tycoon.py  ║
╚══════════════════════════════════════════════════════╝
"""

import pygame, random, sys, math, json
from dataclasses import dataclass, field
from typing import List, Dict

# ─────────────────────────────────────────────────────
#  FARBEN
# ─────────────────────────────────────────────────────
BG      = (10,  14,  26)
PANEL   = (17,  24,  39)
PANEL2  = (31,  41,  55)
BORDER  = (55,  65,  81)
ACCENT  = (59, 130, 246)
GREEN   = (16, 185, 129)
RED     = (239, 68,  68)
YELLOW  = (245,158,  11)
CYAN    = (6,  182, 212)
GOLD    = (251,191,  36)
WHITE   = (240,240, 248)
MUTED   = (107,114, 128)
ORANGE  = (249,115,  22)
PURPLE  = (139, 92, 246)

pygame.init()
W, H = 1280, 760
screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
pygame.display.set_caption("Business Tycoon Pro — by Michael (其米）")
clock = pygame.time.Clock()

# ─────────────────────────────────────────────────────
#  SCHRIFTEN  (Fallback wenn segoeui fehlt)
# ─────────────────────────────────────────────────────
def _f(size, bold=False):
    for name in ["segoeui","arial","freesansbold" if bold else "freesans","sans"]:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except:
            pass
    return pygame.font.Font(None, size)

F = {
    "xs":  _f(11), "sm": _f(13), "md": _f(15),
    "lg":  _f(17, True), "xl": _f(22, True), "title": _f(28, True),
}

# ─────────────────────────────────────────────────────
#  HILFSFUNKTIONEN
# ─────────────────────────────────────────────────────
def fmt(n: float) -> str:
    n = float(n)
    if abs(n) >= 1e9:  return f"{n/1e9:.2f} Mrd €"
    if abs(n) >= 1e6:  return f"{n/1e6:.2f} Mio €"
    if abs(n) >= 1e3:  return f"{n/1e3:.1f}k €"
    return f"{n:,.0f} €".replace(",",".")

def txt(surf, text, fkey, color, x, y, anchor="topleft", maxw=0):
    f = F[fkey]
    s = str(text)
    if maxw > 0:
        while f.size(s)[0] > maxw and len(s) > 1:
            s = s[:-1]
        if s != str(text): s += "…"
    surf_t = f.render(s, True, color)
    r = surf_t.get_rect(**{anchor: (x, y)})
    surf.blit(surf_t, r)
    return r

def box(surf, color, rect, r=6, width=0):
    pygame.draw.rect(surf, color, rect, width, border_radius=r)

def line(surf, color, p1, p2):
    pygame.draw.line(surf, color, p1, p2)

def sparkline(surf, hist, x, y, w, h, col=None):
    if len(hist) < 2: return
    mn, mx2 = min(hist), max(hist)
    if mx2 == mn: mx2 = mn + 0.001
    pts = [(x + int(i/(len(hist)-1)*w),
            y + h - int((v-mn)/(mx2-mn)*h))
           for i, v in enumerate(hist)]
    c = col or (GREEN if hist[-1] >= hist[0] else RED)
    if len(pts) >= 2:
        pygame.draw.lines(surf, c, False, pts, 2)

def progress_bar(surf, x, y, w, h, frac, color):
    box(surf, PANEL2, (x,y,w,h), 3)
    fw = max(0, min(w, int(w*frac)))
    if fw > 0: box(surf, color, (x,y,fw,h), 3)

def dim_overlay(surf):
    s = pygame.Surface((surf.get_width(), surf.get_height()), pygame.SRCALPHA)
    s.fill((0,0,0,170))
    surf.blit(s,(0,0))

# ─────────────────────────────────────────────────────
#  INPUT-BOX
# ─────────────────────────────────────────────────────
class InputBox:
    def __init__(self, x, y, w, h=34, hint="", numeric=True):
        self.rect  = pygame.Rect(x, y, w, h)
        self.hint  = hint
        self.text  = ""
        self.active= False
        self.numeric = numeric

    def handle(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(ev.pos)
        if ev.type == pygame.KEYDOWN and self.active:
            if ev.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
            elif ev.unicode.isprintable():
                ch = ev.unicode
                if self.numeric:
                    if ch.isdigit() or (ch=='.' and '.' not in self.text):
                        self.text += ch
                else:
                    self.text += ch

    def val(self):
        try: return float(self.text)
        except: return 0.0

    def draw(self, surf):
        col = ACCENT if self.active else BORDER
        box(surf, PANEL2, self.rect, 5)
        box(surf, col, self.rect, 5, 1)
        show = self.text if self.text else self.hint
        color = WHITE if self.text else MUTED
        txt(surf, show, "sm", color, self.rect.x+8, self.rect.centery, "midleft")

    def clear(self):
        self.text = ""

# ─────────────────────────────────────────────────────
#  BUTTON
# ─────────────────────────────────────────────────────
class Btn:
    def __init__(self, x, y, w, h, label, color=None, tc=WHITE, fkey="sm"):
        self.rect  = pygame.Rect(x, y, w, h)
        self.label = label
        self.color = color or ACCENT
        self.tc    = tc
        self.fkey  = fkey
        self.hover = False
        self.active= False

    def draw(self, surf):
        c = self.color
        if self.active: 
            c = GREEN
        elif self.hover: 
            c = tuple(min(255,v+30) for v in self.color)
        
        box(surf, c, self.rect, 6)
        
        # Immer einen Rand zeichnen, damit der Button auf dunklen Bildschirmen nicht verschwindet!
        border_c = GREEN if self.active else BORDER
        box(surf, border_c, self.rect, 6, 1)
        
        # Bei aktivem Zustand (Grün) die Schrift für besseren Kontrast abdunkeln
        txt_col = BG if (self.active and c == GREEN) else self.tc
        
        txt(surf, self.label, self.fkey, txt_col,
            self.rect.centerx, self.rect.centery, "center")

    def update(self, pos):
        self.hover = self.rect.collidepoint(pos)

    def hit(self, ev):
        return (ev.type == pygame.MOUSEBUTTONDOWN
                and ev.button == 1
                and self.rect.collidepoint(ev.pos))

# ─────────────────────────────────────────────────────
#  SPIELZUSTAND-DATEN
# ─────────────────────────────────────────────────────
PROP_CATALOG = [
    ("flat",   "Kleine Wohnung",   "Wohnung",   75_000,    550,    90, 5),
    ("house",  "Einfamilienhaus",  "Haus",     240_000,  1_300,   270, 5),
    ("condo",  "Luxus-Penthouse",  "Penthouse",650_000,  4_000,   600, 5),
    ("office", "Bürogebäude",      "Büro",   1_200_000,  9_000, 1_400, 5),
    ("mall",   "Einkaufszentrum",  "Mall",   3_000_000, 25_000, 3_500, 5),
    ("hotel",  "Luxus-Hotel",      "Hotel",  5_000_000, 40_000, 6_000, 5),
]

COMP_CATALOG = [
    ("cafe",    "Café / Kiosk",       "Café",       15_000,      280,    40, 0.05, 8),
    ("craft",   "Handwerksbetrieb",   "Handwerk",   80_000,    1_100,   180, 0.05, 8),
    ("retail",  "Einzelhandel",        "Handel",    200_000,    2_500,   400, 0.08, 8),
    ("tech",    "Software-Startup",   "Software",  500_000,    7_000,   800, 0.12, 8),
    ("factory", "Fabrik",              "Fabrik",  1_500_000,   18_000, 2_800, 0.06, 8),
    ("media",   "Medienkonzern",       "Medien",  4_000_000,   50_000, 8_000, 0.10, 8),
    ("pharma",  "Pharmaunternehmen",   "Pharma",  8_000_000,  110_000,15_000, 0.14, 8),
    ("ibank",   "Investmentbank",      "Bank",   20_000_000,  300_000,40_000, 0.18, 8),
]

STOCK_CATALOG = [
    ("tg",   "TechGiant",    150.0, 0.13, 0.005, "Tech"),
    ("ac",   "AutoCorp",      85.0, 0.09, 0.018, "Auto"),
    ("ec",   "EnergyCo",     110.0, 0.07, 0.022, "Energie"),
    ("bg",   "BankGroup",     65.0, 0.11, 0.012, "Finanzen"),
    ("ph",   "PharmaHealth", 200.0, 0.10, 0.008, "Gesundheit"),
    ("re",   "RealEstCorp",   90.0, 0.08, 0.025, "Immobilien"),
    ("ai",   "AI-Ventures",  350.0, 0.25, 0.001, "Tech"),
    ("food", "FoodChain",     45.0, 0.06, 0.030, "Konsum"),
]

PHASES = {
    "BOOM":           {"label":"Boom",          "col":GREEN,  "stk":+.05, "rent":+.03, "profit":+.08},
    "STABLE":         {"label":"Stabil",        "col":CYAN,   "stk": .00, "rent": .00, "profit": .00},
    "RECESSION":      {"label":"Rezession",     "col":YELLOW, "stk":-.04, "rent":-.02, "profit":-.05},
    "DEPRESSION":     {"label":"Depression",    "col":RED,    "stk":-.12, "rent":-.12, "profit":-.18}, # Härter!
    "STAGFLATION":    {"label":"Stagflation",   "col":ORANGE, "stk":-.03, "rent":+.02, "profit":-.06},
    "HYPERINFLATION": {"label":"Hyperinflation","col":(236,72,153), "stk":+.02,"rent":+.08,"profit":-.08},
}

ACHIEVEMENTS = [
    ("first",       "Erster Kauf",       "Erste Immobilie oder Firma gekauft", lambda g: len(g.props)+len(g.comps) >= 1),
    ("millionaire", "5-Millionaer",      "Nettovermoegen > 5 Mio €", lambda g: g.net_worth() >= 5_000_000),
    ("tenmio",      "50-Millionaer",     "Nettovermoegen > 50 Mio €", lambda g: g.net_worth() >= 50_000_000),
    ("landlord",    "Immo-Tycoon",       "5 Immobilien besitzen", lambda g: len(g.props) >= 5),
    ("tycoon",      "Monopolist",        "10 Unternehmen besitzen", lambda g: len(g.comps) >= 10),
    ("debtfree",    "Schuldenfrei",      "Alle Schulden getilgt (auf Mittel/Schwer)", lambda g: g.loan == 0 and len(g.nw_hist) > 3 and g.difficulty != 'easy'),
    ("investor",    "Grossinvestor",     "Aktienportfolio > 1 Mio €", lambda g: g.stock_value() >= 1_000_000),
    ("survivor",    "Stahlharte Nerven", "3 Depressionen ueberlebt", lambda g: g._dep_count >= 3),
    ("legend",      "Milliardaer",       "Nettovermoegen > 1 Mrd €", lambda g: g.net_worth() >= 1_000_000_000),
    ("fullhouse",   "Vollvermieter",     "5 Immobilien gleichzeitig vermietet", lambda g: len(g.props) >= 5 and all(not p["vacant"] for p in g.props)),
    ("maxedout",    "Perfektionist",     "3 Firmen auf Max-Level", lambda g: sum(1 for c in g.comps if c["level"] >= c["lvl_max"]) >= 3),
]

# ─────────────────────────────────────────────────────
#  SPIELZUSTAND
# ─────────────────────────────────────────────────────
class GS:
    def __init__(self, difficulty="medium"):
        self.name      = "Investor"
        self.difficulty = difficulty
        
        # Startkapital basierend auf Schwierigkeit
        if difficulty == "easy":
            self.cash = 150_000.0
            self.loan = 0.0
        elif difficulty == "medium":
            self.cash = 50_000.0
            self.loan = 0.0
        else: # hard
            self.cash = 15_000.0
            self.loan = 60_000.0
            
        self.savings   = 0.0
        self.sav_rate  = 0.0035
        self.loan_rate = 0.006

        self.props : List[dict] = []   
        self.comps : List[dict] = []   
        self.stocks: Dict[str,float] = {} 
        self.etf   : float = 0.0          

        self.stock_data = {
            sid: {"name":name,"price":price,"vol":vol,
                  "div":div,"sector":sector,"hist":[price]}
            for sid,name,price,vol,div,sector in STOCK_CATALOG
        }
        self.etf_price = 100.0
        self.etf_hist  = [100.0]

        self.month = 1
        self.year  = 2024

        self.phase    = "STABLE"
        self.phase_dur= 8
        self.base_rate= 5.0
        self.inflation= 0.002
        self.gdp      = 2.0
        self.unemp    = 5.0
        self.sentiment= 50.0

        self.reputation = 50
        self.tax_rate   = 0.25
        self.achiev_done= set()
        self.log  : List[tuple] = []
        self.news : List[str]   = []
        self.nw_hist  : List[float] = []
        self.cf_hist  : List[float] = []

        self._survived_dep = False
        self._dep_count = 0
        self._last_phase = "STABLE"

    def net_worth(self):
        v = self.cash + self.savings
        for p in self.props: v += p["price"]
        for c in self.comps: v += c["val"]
        for sid, qty in self.stocks.items():
            v += qty * self.stock_data[sid]["price"]
        v += self.etf * self.etf_price
        v -= self.loan
        return v

    def stock_value(self):
        v = sum(qty * self.stock_data[sid]["price"]
                for sid, qty in self.stocks.items() if qty > 0)
        return v + self.etf * self.etf_price

    def monthly_income(self):
        i  = sum(p["rent"] for p in self.props if not p["vacant"])
        i += sum(c["profit"] for c in self.comps)
        i += sum(qty * self.stock_data[sid]["price"] * self.stock_data[sid]["div"] / 12
                 for sid, qty in self.stocks.items() if qty > 0)
        i += self.etf * self.etf_price * 0.002 / 12
        i += self.savings * self.sav_rate
        return i

    def monthly_expenses(self):
        e  = sum(p["maint"] for p in self.props)
        e += sum(c["maint"] for c in self.comps)
        e += self.loan * (self.loan_rate + self.base_rate/100/12)
        return e

    def add_log(self, msg, kind="info"):
        self.log.insert(0, (msg, kind))
        if len(self.log) > 80: self.log.pop()

    def add_news(self, msg):
        self.news.insert(0, msg)
        if len(self.news) > 20: self.news.pop()

# ─────────────────────────────────────────────────────
#  SPIELLOGIK (Monatstick)
# ─────────────────────────────────────────────────────
TENANT_TYPES = [
    ("Privat-Mieter",  0.00, 0.03, 12),
    ("Student",       -0.10, 0.10,  6),
    ("Firmenkunde",   +0.25, 0.05, 24),
    ("Luxusmieter",   +0.40, 0.04, 18),
    ("Sozialmieter",  -0.20, 0.01, 36),
]

def make_prop(catalog_row, custom_name=""):
    tid, name, icon, price, rent, maint, lvl_max = catalog_row
    return {
        "id": tid, "name": name, "custom_name": custom_name or name, "icon": icon,
        "price":     float(price),
        "base_rent": float(rent),
        "rent":      float(rent),
        "maint":     float(maint),
        "level": 1, "lvl_max": lvl_max,
        "vacant":  True,       
        "listed":  False,      
        "tenant":  None,       
        "contract_left": 0,    
        "rent_hist": [],
        "for_sale": False,      
        "ask_price": 0.0,
        "market_months": 0
    }

def make_comp(catalog_row, custom_name=""):
    tid, name, icon, price, profit, maint, risk, lvl_max = catalog_row
    return {
        "id":tid, "name":name, "custom_name": custom_name or name, "icon":icon,
        "base_price":float(price),"val":float(price),
        "base_profit":float(profit),"profit":float(profit),
        "maint":float(maint),"risk":risk,
        "level":1,"lvl_max":lvl_max,
        "for_sale": False,      
        "ask_price": 0.0,
        "market_months": 0
    }

def tick(gs: GS):
    gs.month += 1
    if gs.month > 12:
        gs.month = 1
        gs.year += 1
        _year_end(gs)

    _update_economy(gs)
    _update_markets(gs)

    ph = PHASES[gs.phase]
    income = 0.0
    expenses = 0.0

    # ── VERKAUF-MARKT SIMULATION (Immobilien) ──
    for p in list(gs.props):
        if p.get("for_sale"):
            p["market_months"] += 1
            ratio = p["ask_price"] / max(1.0, p["price"])
            phase_mod = {"BOOM": 0.2, "STABLE": 0.0, "RECESSION": -0.1, "DEPRESSION": -0.2}.get(gs.phase, 0.0)
            
            chance = 0.35 + phase_mod - (ratio - 1.0) * 1.5
            chance = max(0.01, min(0.9, chance))
            
            if random.random() < chance:
                gs.cash += p["ask_price"]
                gs.add_log(f"VERKAUFT: {p['custom_name']} fuer {fmt(p['ask_price'])}", "good")
                gs.props.remove(p)
                continue 
            elif p["market_months"] % 3 == 0:
                if ratio > 1.2:
                    gs.add_log(f"Marktbericht: {p['custom_name']} ist potenziellen Kaeufern viel zu teuer.", "warn")
                elif ratio < 0.8:
                    gs.add_log(f"Marktbericht: Viel Interesse an {p['custom_name']} (sehr guenstig!).", "info")
                else:
                    gs.add_log(f"Marktbericht: {p['custom_name']} wartet auf Kaeufer.", "info")

    # ── VERKAUF-MARKT SIMULATION (Unternehmen) ──
    for c in list(gs.comps):
        if c.get("for_sale"):
            c["market_months"] += 1
            ratio = c["ask_price"] / max(1.0, c["val"])
            phase_mod = {"BOOM": 0.2, "STABLE": 0.0, "RECESSION": -0.1, "DEPRESSION": -0.2}.get(gs.phase, 0.0)
            chance = 0.35 + phase_mod - (ratio - 1.0) * 1.5
            chance = max(0.01, min(0.9, chance))
            
            if random.random() < chance:
                gs.cash += c["ask_price"]
                gs.add_log(f"VERKAUFT: {c['custom_name']} fuer {fmt(c['ask_price'])}", "good")
                gs.comps.remove(c)
                continue
            elif c["market_months"] % 3 == 0:
                if ratio > 1.2:
                    gs.add_log(f"Marktbericht: Investor springt ab, {c['custom_name']} zu teuer.", "warn")
                else:
                    gs.add_log(f"Marktbericht: {c['custom_name']} wird weiterhin angeboten.", "info")

    # ── Immobilien ──
    for p in gs.props:
        if p["tenant"] is not None and p["contract_left"] > 0:
            p["contract_left"] -= 1
            if p["contract_left"] == 0:
                tname = TENANT_TYPES[p["tenant"]][0]
                gs.add_log(f"Mietvertrag abgelaufen: {p['custom_name']} ({tname})", "warn")
                p["tenant"]  = None
                p["vacant"]  = True
                p["listed"]  = False

        if p["listed"] and p["vacant"]:
            chance = {"BOOM":0.55,"STABLE":0.40,"RECESSION":0.25,
                      "DEPRESSION":0.05,"STAGFLATION":0.20,"HYPERINFLATION":0.15}.get(gs.phase, 0.30)
            if random.random() < chance:
                weights = [4, 3, 2, 1, 2]
                ti = random.choices(range(len(TENANT_TYPES)), weights=weights)[0]
                tname, bonus, _, months = TENANT_TYPES[ti]
                p["tenant"]        = ti
                p["vacant"]        = False
                p["contract_left"] = months
                p["rent"]          = p["base_rent"] * (1 + bonus)
                gs.add_log(f"Neuer Mieter: {tname} in {p['custom_name']}", "good")

        if not p["vacant"] and p["tenant"] is not None:
            dmg_risk = TENANT_TYPES[p["tenant"]][2]
            if random.random() < dmg_risk * 0.4:
                dmg = p["maint"] * (0.5 + random.random())
                expenses += dmg
                gs.add_log(f"Mieterschaden in {p['custom_name']}: -{fmt(dmg)}", "bad")

        rent = p["rent"] * (1 + ph["rent"]) if not p["vacant"] else 0.0
        income   += rent
        expenses += p["maint"]
        p["rent_hist"].append(round(rent))
        if len(p["rent_hist"]) > 24: p["rent_hist"].pop(0)
        p["price"]     *= 1 + gs.inflation*0.7 + (0.004 if gs.phase=="BOOM" else -0.001)
        p["base_rent"] *= 1 + gs.inflation*0.35
        if not p["vacant"]:
            p["rent"] *= 1 + gs.inflation*0.35

    # ── Unternehmen ──
    rep_bonus = (gs.reputation - 50) / 2000.0
    for c in gs.comps:
        eff = c["base_profit"] * (1 + ph["profit"] + rep_bonus)
        c["profit"] = max(0.0, eff)
        if random.random() < c["risk"] * 0.35:
            dmg = c["profit"] * (0.15 + random.random()*0.25)
            expenses += dmg
            gs.add_log(f"Schadenfall bei {c['custom_name']}: -{fmt(dmg)}", "bad")
        income   += c["profit"]
        expenses += c["maint"]
        c["val"]         *= 1 + gs.inflation*0.4
        c["base_profit"] *= 1 + gs.inflation*0.2

    expenses += gs.loan * (gs.loan_rate + gs.base_rate/100.0/12.0)
    income += gs.savings * gs.sav_rate

    for sid, qty in gs.stocks.items():
        if qty > 0:
            s = gs.stock_data[sid]
            income += qty * s["price"] * s["div"] / 12.0

    income += gs.etf * gs.etf_price * 0.002 / 12.0

    _random_events(gs)

    gross = income - expenses
    tax   = max(0.0, gross * gs.tax_rate)
    expenses += tax

    cf = income - expenses
    gs.cash += cf
    gs.cf_hist.append(cf)
    gs.nw_hist.append(gs.net_worth())
    if len(gs.cf_hist) > 24:  gs.cf_hist.pop(0)
    if len(gs.nw_hist) > 24:  gs.nw_hist.pop(0)

    gs.inflation = 0.001 + random.random()*0.004
    if gs.phase == "HYPERINFLATION": gs.inflation *= 4

    # Zähle Depressionen
    if gs.phase == "DEPRESSION" and gs._last_phase != "DEPRESSION":
        gs._dep_count += 1
    gs._last_phase = gs.phase

    # ── Bankrott-Logik verschärft ──
    max_l = max(0, gs.net_worth()*0.6 - gs.loan)
    if gs.cash < 0 and (-gs.cash > max_l + gs.savings):
        return "bankrott"
    
    return None

def _year_end(gs: GS):
    gs.add_news(f"Jahresabschluss {gs.year-1}: NV {fmt(gs.net_worth())}")
    if gs.net_worth() > 5_000_000:
        wt = (gs.net_worth() - 5_000_000) * 0.005
        gs.cash -= wt
        gs.add_log(f"Vermoegenssteuer: -{fmt(wt)}", "bad")

def _update_economy(gs: GS):
    gs.phase_dur -= 1
    if gs.phase_dur <= 0:
        prev = gs.phase
        r = random.random()
        if   r < 0.08: gs.phase, gs.phase_dur = "DEPRESSION",     random.randint(2,5)
        elif r < 0.22: gs.phase, gs.phase_dur = "RECESSION",      random.randint(3,7)
        elif r < 0.28: gs.phase, gs.phase_dur = "STAGFLATION",    random.randint(2,4)
        elif r < 0.30: gs.phase, gs.phase_dur = "HYPERINFLATION", random.randint(1,3)
        elif r < 0.65: gs.phase, gs.phase_dur = "STABLE",         random.randint(5,10)
        else:          gs.phase, gs.phase_dur = "BOOM",            random.randint(3,6)

        if gs.phase != prev:
            label = PHASES[gs.phase]["label"]
            gs.add_news(f"Wirtschaftswechsel: {label}")
            kind = "good" if gs.phase=="BOOM" else ("bad" if "DEPRESS" in gs.phase else "warn")
            gs.add_log(f"Wirtschaft: {label}", kind)

    delta = {"BOOM":+.06,"STABLE":0,"RECESSION":-.1,
             "DEPRESSION":-.2,"STAGFLATION":0,"HYPERINFLATION":0}
    gs.base_rate = max(0, min(15, gs.base_rate + delta.get(gs.phase,0)))
    gs.loan_rate = 0.004 + gs.base_rate/100.0/12.0

    gs.gdp   += {"BOOM":.15,"STABLE":0,"RECESSION":-.2,"DEPRESSION":-.4,
                 "STAGFLATION":-.1,"HYPERINFLATION":-.15}.get(gs.phase,0)
    gs.unemp += {"BOOM":-.1,"STABLE":0,"RECESSION":.25,"DEPRESSION":.5,
                 "STAGFLATION":.1,"HYPERINFLATION":.1}.get(gs.phase,0)
    gs.gdp   = max(-15, min(12, gs.gdp))
    gs.unemp = max(1,   min(30, gs.unemp))
    gs.sentiment += (random.random()-.48)*8
    gs.sentiment  = max(0, min(100, gs.sentiment))

def _update_markets(gs: GS):
    ph  = PHASES[gs.phase]
    sent= (gs.sentiment-50)/5000.0
    sector_bonus = {
        "Tech":("BOOM",.015), "Energie":("STAGFLATION",.02),
        "Finanzen":("DEPRESSION",-.025), "Gesundheit":(None,.005), "Konsum":(None,.003)
    }
    for sid, s in gs.stock_data.items():
        se = 0.0
        for sec,(cond,val) in sector_bonus.items():
            if s["sector"]==sec and (cond is None or gs.phase==cond):
                se = val
        chg = (random.random()-.5)*2*s["vol"] + ph["stk"] + se + sent
        s["price"] = max(0.5, s["price"]*(1+chg))
        s["hist"].append(round(s["price"],2))
        if len(s["hist"]) > 40: s["hist"].pop(0)

    etf_chg = (random.random()-.48)*.045 + ph["stk"]*.5
    gs.etf_price = max(5, gs.etf_price*(1+etf_chg))
    gs.etf_hist.append(round(gs.etf_price,2))
    if len(gs.etf_hist) > 40: gs.etf_hist.pop(0)

def _random_events(gs: GS):
    events = [
        (0.025, lambda: _ev_fire(gs)),
        (0.020, lambda: _ev_vacancy(gs)),
        (0.015, lambda: _ev_lawsuit(gs)),
        (0.022, lambda: _ev_subsidy(gs)),
        (0.008, lambda: _ev_crash(gs)),
        (0.008, lambda: _ev_rally(gs)),
        (0.016, lambda: _ev_bad_press(gs)),
        (0.016, lambda: _ev_good_press(gs)),
        (0.010, lambda: _ev_tax_audit(gs)),
        (0.018, lambda: _ev_infra(gs)),
        (0.010, lambda: _ev_regulation(gs)),
    ]
    for prob, fn in events:
        if random.random() < prob:
            fn()

def _ev_fire(gs):
    if not gs.props: return
    p = random.choice(gs.props)
    dmg = p["price"]*0.06
    gs.cash -= dmg; p["price"] -= dmg
    gs.add_log(f"Feuer in {p['custom_name']}! -{fmt(dmg)}", "bad")
    gs.add_news("Feuer — Immobilienschaeden!")

def _ev_vacancy(gs):
    occupied = [p for p in gs.props if not p["vacant"]]
    if not occupied: return
    p = random.choice(occupied)
    tname = TENANT_TYPES[p["tenant"]][0] if p["tenant"] is not None else "Mieter"
    p["tenant"]        = None
    p["vacant"]        = True
    p["contract_left"] = 0
    gs.add_log(f"{tname} ausgezogen: {p['custom_name']} leer", "bad")

def _ev_lawsuit(gs):
    if not gs.comps: return
    c = random.choice(gs.comps)
    pen = c["val"]*0.07
    gs.cash -= pen
    gs.add_log(f"Klage vs {c['custom_name']}: -{fmt(pen)}", "bad")

def _ev_subsidy(gs):
    amt = 8_000 + random.random()*45_000
    gs.cash += amt
    gs.add_log(f"Staatliche Foerderung: +{fmt(amt)}", "good")

def _ev_crash(gs):
    for s in gs.stock_data.values(): s["price"] *= 0.80 + random.random()*0.10
    gs.add_log("Marktcrash!", "bad")

def _ev_rally(gs):
    for s in gs.stock_data.values(): s["price"] *= 1.10 + random.random()*0.10
    gs.add_log("Bullenmarkt!", "good")

def _ev_bad_press(gs):
    gs.reputation = max(0, gs.reputation-10)
    gs.add_log("Schlechte Presse: Ruf -10", "bad")

def _ev_good_press(gs):
    gs.reputation = min(100, gs.reputation+8)
    gs.add_log("Positiver Artikel: Ruf +8", "good")

def _ev_tax_audit(gs):
    amt = gs.cash*0.04
    gs.cash -= amt
    gs.add_log(f"Sondersteuer: -{fmt(amt)}", "bad")

def _ev_infra(gs):
    if not gs.props: return
    p = random.choice(gs.props)
    p["price"] *= 1.10
    gs.add_log(f"Stadtentwicklung: {p['custom_name']} +10%", "good")

def _ev_regulation(gs):
    for c in gs.comps:
        c["profit"] *= 0.85; c["base_profit"] *= 0.85
    gs.add_log("Neue Regulierung: Firmengewinne -15%", "bad")

# ─────────────────────────────────────────────────────
#  SCREEN-KLASSEN (Views)
# ─────────────────────────────────────────────────────
class NameScreen:
    def __init__(self):
        self.box = InputBox(W//2-150, H//2-40, 300, 38, "Dein Name", numeric=False)
        self.btn_play = Btn(W//2-70, H//2+100, 140, 42, "Spielen", GREEN, BG, "lg")
        
        self.diff = "medium"
        self.btn_easy = Btn(W//2-165, H//2+30, 100, 36, "Einfach", PANEL2, WHITE, "md")
        self.btn_med  = Btn(W//2-50,  H//2+30, 100, 36, "Mittel",  PANEL2, WHITE, "md")
        self.btn_hard = Btn(W//2+65,  H//2+30, 100, 36, "Schwer",  PANEL2, WHITE, "md")
        self.btn_med.active = True

    def handle(self, ev):
        self.box.handle(ev)
        
        for b, d in [(self.btn_easy, "easy"), (self.btn_med, "medium"), (self.btn_hard, "hard")]:
            if b.hit(ev):
                self.diff = d
                self.btn_easy.active = (d == "easy")
                self.btn_med.active = (d == "medium")
                self.btn_hard.active = (d == "hard")
        
        if self.btn_play.hit(ev) or (ev.type==pygame.KEYDOWN and ev.key==pygame.K_RETURN):
            name = self.box.text.strip() or "Investor"
            return (name, self.diff)
        return None

    def draw(self, surf):
        surf.fill(BG)
        # Die Titeltexte mit besseren Abständen versehen
        txt(surf,"Business Tycoon Pro","title",GOLD, W//2,H//2-140,"center")
        txt(surf,"by Michael (其米）","md",MUTED, W//2,H//2-105,"center")
        txt(surf,"Wie heisst du?","lg",WHITE, W//2,H//2-70,"center")
        
        self.box.draw(surf)
        
        txt(surf,"Schwierigkeit:","sm",MUTED, W//2,H//2-5,"center")
        self.btn_easy.update(pygame.mouse.get_pos()); self.btn_easy.draw(surf)
        self.btn_med.update(pygame.mouse.get_pos()); self.btn_med.draw(surf)
        self.btn_hard.update(pygame.mouse.get_pos()); self.btn_hard.draw(surf)
        
        self.btn_play.update(pygame.mouse.get_pos())
        self.btn_play.draw(surf)

# ─────────────────────────────────────────────────────
#  HAUPTSPIEL
# ─────────────────────────────────────────────────────
TABS = ["Dashboard","Wirtschaft","Aktien","Erfolge","Log"]

class GameScreen:
    def __init__(self, gs: GS):
        self.gs        = gs
        self.tab       = 0
        self.speed     = 2000
        self.paused    = False
        self.last_tick = pygame.time.get_ticks()
        self.modal     = None
        self._news_x   = float(W)
        self._ach_popup= None
        self._inputs   = {}
        self._scroll   = 0

    def update(self):
        return None

    def maybe_tick(self):
        if self.paused or self.modal: return None
        now = pygame.time.get_ticks()
        if now - self.last_tick >= self.speed:
            self.last_tick = now
            result = tick(self.gs)
            self._check_achievements()
            if result == "bankrott": return "bankrott"
        return None

    def _check_achievements(self):
        gs = self.gs
        for aid, title, desc, cond in ACHIEVEMENTS:
            if aid not in gs.achiev_done and cond(gs):
                gs.achiev_done.add(aid)
                gs.add_log(f"Erfolg: {title}", "good")
                self._ach_popup = (title, desc, pygame.time.get_ticks())

    def handle(self, ev):
        for ib in self._inputs.values(): ib.handle(ev)
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE: self._close_modal()
            if ev.key == pygame.K_SPACE and not self.modal: self.paused = not self.paused

        if ev.type != pygame.MOUSEBUTTONDOWN or ev.button != 1: return None
        mx, my = ev.pos
        if ev.type == pygame.MOUSEWHEEL: self._scroll -= ev.y * 30
        if self.modal: return self._handle_modal_click(mx, my)
        return self._handle_main_click(mx, my)

    def _handle_main_click(self, mx, my):
        gs = self.gs
        for i, (ms, lbl) in enumerate([(2000,"1x"),(800,"3x"),(300,"10x")]):
            if pygame.Rect(W-240+i*44, 9, 38, 26).collidepoint(mx,my):
                self.speed = ms; return None
        if pygame.Rect(W-100,9,88,26).collidepoint(mx,my):
            self.paused = not self.paused; return None

        tx = 192
        for i, name in enumerate(TABS):
            tw = F["sm"].size(name)[0]+22
            if pygame.Rect(tx,46,tw,32).collidepoint(mx,my):
                self.tab = i; return None
            tx += tw+2

        sb_clicks = {
            "buy_prop": self._open_buy_prop, "sell_prop": self._open_sell_prop,
            "upg_prop": self._open_upg_prop, "rent_prop": self._open_rent_prop,
            "buy_comp": self._open_buy_comp, "sell_comp": self._open_sell_comp,
            "upg_comp": self._open_upg_comp, "loan": self._open_loan,
            "repay": self._open_repay, "savings": self._open_savings,
            "buy_etf": self._open_buy_etf, "save": self._save_game, "load": self._load_game,
        }
        for key, ry, rh in self._sidebar_rects():
            if pygame.Rect(4, ry, 182, rh).collidepoint(mx,my):
                if key in sb_clicks: sb_clicks[key]()
                return None
        if self.tab == 2: self._handle_stock_click(mx, my)
        return None

    def _open_buy_prop(self):
        self._inputs = {"custom_name": InputBox(0,0,220,34,"Eigener Name (optional)", numeric=False)}
        self.modal = {"type":"buy_prop"}; self._scroll = 0

    def _open_sell_prop(self):
        self._inputs = {"ask_price": InputBox(0,0,160,34,"Dein Preis €", numeric=True)}
        self.modal = {"type":"sell_prop"}; self._scroll = 0

    def _open_upg_prop(self):
        self._inputs = {}; self.modal = {"type":"upg_prop"}; self._scroll = 0

    def _open_rent_prop(self):
        self._inputs = {}; self.modal = {"type":"rent_prop"}; self._scroll = 0

    def _open_buy_comp(self):
        self._inputs = {"custom_name": InputBox(0,0,220,34,"Firmenname (optional)", numeric=False)}
        self.modal = {"type":"buy_comp"}; self._scroll = 0

    def _open_sell_comp(self):
        self._inputs = {"ask_price": InputBox(0,0,160,34,"Dein Preis €", numeric=True)}
        self.modal = {"type":"sell_comp"}; self._scroll = 0

    def _open_upg_comp(self):
        self._inputs = {}; self.modal = {"type":"upg_comp"}; self._scroll = 0

    def _open_loan(self):
        self._inputs = {"amount": InputBox(0,0,220,34,"Betrag in €")}
        self.modal = {"type":"loan"}

    def _open_repay(self):
        self._inputs = {"amount": InputBox(0,0,220,34,"Betrag in €")}
        self.modal = {"type":"repay"}

    def _open_savings(self):
        self._inputs = {"amount": InputBox(0,0,220,34,"Betrag einzahlen")}
        self.modal = {"type":"savings"}

    def _open_buy_stock(self, sid):
        self._inputs = {"qty": InputBox(0,0,180,34,"Anzahl Aktien")}
        self.modal = {"type":"buy_stock","sid":sid}

    def _open_sell_stock(self, sid):
        self._inputs = {"qty": InputBox(0,0,180,34,"Anzahl verkaufen")}
        self.modal = {"type":"sell_stock","sid":sid}

    def _open_buy_etf(self):
        self._inputs = {"qty": InputBox(0,0,180,34,"Anzahl Anteile")}
        self.modal = {"type":"buy_etf"}

    def _close_modal(self):
        self.modal = None; self._inputs = {}

    def _save_game(self):
        gs = self.gs
        data = {k:v for k,v in gs.__dict__.items() if not callable(v) and not k.startswith("__")}
        data["achiev_done"] = list(gs.achiev_done)
        try:
            with open("savegame.json", "w") as f: json.dump(data, f)
            gs.add_log("Spiel erfolgreich gespeichert!", "good")
        except Exception as e: gs.add_log(f"Speicherfehler: {e}", "bad")

    def _load_game(self):
        try:
            with open("savegame.json", "r") as f: data = json.load(f)
            for k, v in data.items():
                if k == "achiev_done": self.gs.achiev_done = set(v)
                else: setattr(self.gs, k, v)
            self.gs.add_log(f"Spielstand geladen: {self.gs.year}, Monat {self.gs.month}", "info")
        except: self.gs.add_log("Fehler beim Laden!", "bad")

    def _handle_modal_click(self, mx, my):
        mt = self.modal.get("type","")
        mw, mh = 660, 520
        bx = (W-mw)//2
        by = (H-mh)//2

        if pygame.Rect(bx+mw-32,by+6,24,24).collidepoint(mx,my):
            self._close_modal(); return None

        gs = self.gs
        if mt == "buy_prop":
            row_h = 72; y0 = by+100
            self._inputs["custom_name"].rect = pygame.Rect(bx+250, by+50, 250, 34)
            for i, row in enumerate(PROP_CATALOG):
                ry = y0 + i*row_h - self._scroll
                if ry+row_h < by+90 or ry > by+mh-20: continue
                if pygame.Rect(bx+mw-110, ry+20, 90, 30).collidepoint(mx,my):
                    price = float(row[3])
                    if gs.cash >= price:
                        gs.cash -= price
                        c_name = self._inputs["custom_name"].text.strip()
                        gs.props.append(make_prop(row, c_name))
                        gs.add_log(f"Immobilie gekauft: {c_name or row[1]}", "good")
                        self._check_achievements()
                    self._close_modal(); return None

        elif mt == "sell_prop":
            row_h = 70; y0 = by+100
            self._inputs["ask_price"].rect = pygame.Rect(bx+250, by+50, 160, 34)
            for i, p in enumerate(gs.props):
                ry = y0 + i*row_h - self._scroll
                if ry+row_h < by+90 or ry > by+mh-20: continue
                if pygame.Rect(bx+mw-120, ry+20, 100, 30).collidepoint(mx,my):
                    if p.get("for_sale"):
                        p["for_sale"] = False
                        gs.add_log(f"{p['custom_name']} vom Markt genommen.", "info")
                    else:
                        amt = self._inputs["ask_price"].val()
                        if amt > 0:
                            p["for_sale"] = True
                            p["ask_price"] = amt
                            p["market_months"] = 0
                            gs.add_log(f"{p['custom_name']} für {fmt(amt)} angeboten.", "info")
                    return None

        elif mt == "buy_comp":
            row_h = 72; y0 = by+100
            self._inputs["custom_name"].rect = pygame.Rect(bx+250, by+50, 250, 34)
            for i, row in enumerate(COMP_CATALOG):
                ry = y0 + i*row_h - self._scroll
                if ry+row_h < by+90 or ry > by+mh-20: continue
                if pygame.Rect(bx+mw-110, ry+20, 90, 30).collidepoint(mx,my):
                    price = float(row[3])
                    if gs.cash >= price:
                        gs.cash -= price
                        c_name = self._inputs["custom_name"].text.strip()
                        gs.comps.append(make_comp(row, c_name))
                        gs.add_log(f"Firma gegründet: {c_name or row[1]}", "good")
                        self._check_achievements()
                    self._close_modal(); return None

        elif mt == "sell_comp":
            row_h = 70; y0 = by+100
            self._inputs["ask_price"].rect = pygame.Rect(bx+250, by+50, 160, 34)
            for i, c in enumerate(gs.comps):
                ry = y0 + i*row_h - self._scroll
                if ry+row_h < by+90 or ry > by+mh-20: continue
                if pygame.Rect(bx+mw-120, ry+20, 100, 30).collidepoint(mx,my):
                    if c.get("for_sale"):
                        c["for_sale"] = False
                        gs.add_log(f"{c['custom_name']} vom Markt genommen.", "info")
                    else:
                        amt = self._inputs["ask_price"].val()
                        if amt > 0:
                            c["for_sale"] = True
                            c["ask_price"] = amt
                            c["market_months"] = 0
                            gs.add_log(f"{c['custom_name']} für {fmt(amt)} angeboten.", "info")
                    return None

        elif mt == "upg_prop":
            row_h = 72; y0 = by+58
            for p in gs.props:
                ry = y0 + gs.props.index(p)*row_h - self._scroll
                if ry+row_h < by+40 or ry > by+mh-20: continue
                cost = p["price"]*0.12
                if not (p["level"] >= p["lvl_max"]) and pygame.Rect(bx+mw-110, ry+20, 90, 30).collidepoint(mx,my):
                    if gs.cash >= cost:
                        gs.cash -= cost; p["level"] += 1; p["price"] *= 1.08
                        p["base_rent"] *= 1.15; p["rent"] *= 1.15; p["maint"] *= 1.06
                    self._close_modal(); return None

        elif mt == "upg_comp":
            row_h = 72; y0 = by+58
            for c in gs.comps:
                ry = y0 + gs.comps.index(c)*row_h - self._scroll
                if ry+row_h < by+40 or ry > by+mh-20: continue
                cost = c["val"]*0.15
                if not (c["level"] >= c["lvl_max"]) and pygame.Rect(bx+mw-110, ry+20, 90, 30).collidepoint(mx,my):
                    if gs.cash >= cost:
                        gs.cash -= cost; c["level"] += 1; c["val"] *= 1.12
                        c["base_profit"] *= 1.22; c["profit"] = c["base_profit"]; c["maint"] *= 1.08
                    self._close_modal(); return None

        elif mt == "rent_prop":
            row_h = 100; y0 = by+58
            for p in gs.props:
                ry = y0 + gs.props.index(p)*row_h - self._scroll
                if ry+row_h < by+40 or ry > by+mh-20: continue
                if pygame.Rect(bx+mw-120, ry+20, 100, 28).collidepoint(mx,my):
                    if p["vacant"]:
                        p["listed"] = not p["listed"]
                    else:
                        penalty = p["rent"] * 2
                        gs.cash -= penalty
                        p["tenant"] = None; p["vacant"] = True; p["listed"] = False; p["contract_left"] = 0
                        gs.add_log(f"Mieter gekündigt: -{fmt(penalty)} Strafe", "bad")
                    self._close_modal(); return None

        elif mt == "loan":
            bx2 = bx+260; by2 = by+130
            self._inputs["amount"].rect = pygame.Rect(bx+30, by+128, 220, 34)
            if pygame.Rect(bx2, by2, 120, 34).collidepoint(mx,my):
                amt = self._inputs["amount"].val()
                max_l = max(0, gs.net_worth()*0.6 - gs.loan)
                if 0 < amt <= max_l and gs.cash + amt > 0:
                    gs.cash += amt; gs.loan += amt
                self._close_modal(); return None

        elif mt == "repay":
            bx2 = bx+260; by2 = by+128
            self._inputs["amount"].rect = pygame.Rect(bx+30, by+128, 220, 34)
            if pygame.Rect(bx2, by2, 120, 34).collidepoint(mx,my):
                amt = min(self._inputs["amount"].val(), gs.cash, gs.loan)
                if amt > 0: gs.cash -= amt; gs.loan  = max(0, gs.loan - amt)
                self._close_modal(); return None
            if pygame.Rect(bx+30, by+180, 160, 34).collidepoint(mx,my):
                amt = min(gs.cash, gs.loan)
                if amt > 0: gs.cash -= amt; gs.loan  = max(0, gs.loan - amt)
                self._close_modal(); return None

        elif mt == "savings":
            self._inputs["amount"].rect = pygame.Rect(bx+30, by+128, 220, 34)
            if pygame.Rect(bx+260, by+128, 120, 34).collidepoint(mx,my):
                amt = self._inputs["amount"].val()
                if 0 < amt <= gs.cash: gs.cash -= amt; gs.savings += amt
                self._close_modal(); return None
            if pygame.Rect(bx+30, by+180, 160, 34).collidepoint(mx,my):
                if gs.savings > 0: gs.cash += gs.savings; gs.savings = 0
                self._close_modal(); return None

        elif mt == "buy_stock":
            sid = self.modal["sid"]
            self._inputs["qty"].rect = pygame.Rect(bx+30, by+130, 180, 34)
            if pygame.Rect(bx+220, by+130, 110, 34).collidepoint(mx,my):
                qty = int(self._inputs["qty"].val()); cost = qty * gs.stock_data[sid]["price"]
                if qty > 0 and gs.cash >= cost:
                    gs.cash -= cost; gs.stocks[sid] = gs.stocks.get(sid, 0.0) + qty
                self._close_modal(); return None

        elif mt == "sell_stock":
            sid = self.modal["sid"]
            self._inputs["qty"].rect = pygame.Rect(bx+30, by+130, 180, 34)
            if pygame.Rect(bx+220, by+130, 110, 34).collidepoint(mx,my):
                qty = int(self._inputs["qty"].val()); owned = gs.stocks.get(sid, 0.0)
                qty = min(qty, int(owned))
                if qty > 0: gs.cash += qty * gs.stock_data[sid]["price"]; gs.stocks[sid] = owned - qty
                self._close_modal(); return None
            if pygame.Rect(bx+30, by+180, 160, 34).collidepoint(mx,my):
                owned = gs.stocks.get(sid, 0.0)
                if owned > 0: gs.cash += owned * gs.stock_data[sid]["price"]; gs.stocks[sid] = 0
                self._close_modal(); return None

        elif mt == "buy_etf":
            self._inputs["qty"].rect = pygame.Rect(bx+30, by+130, 180, 34)
            if pygame.Rect(bx+220, by+130, 110, 34).collidepoint(mx,my):
                qty = self._inputs["qty"].val(); cost = qty * gs.etf_price
                if qty > 0 and gs.cash >= cost: gs.cash -= cost; gs.etf += qty
                self._close_modal(); return None
            if pygame.Rect(bx+30, by+180, 160, 34).collidepoint(mx,my):
                if gs.etf > 0: gs.cash += gs.etf * gs.etf_price; gs.etf = 0
                self._close_modal(); return None

        return None

    def _handle_stock_click(self, mx, my):
        gs = self.gs; x, y, pad = 188, 76, 10
        col_w = (W - x - pad * 3) // 2; row_h = 62
        sids = list(gs.stock_data.keys())
        for i, sid in enumerate(sids):
            rx = x + pad + (i % 2) * (col_w + pad)
            ry = y + 18 + (i // 2) * row_h
            if pygame.Rect(rx, ry, col_w, row_h - 4).collidepoint(mx, my):
                if mx < rx + col_w * 0.65: self._open_buy_stock(sid)
                else: self._open_sell_stock(sid)
                return
        n_rows = (len(sids) // 2) + (1 if len(sids) % 2 else 0)
        ey = y + 18 + n_rows * row_h + 8
        if pygame.Rect(x + pad, ey, W - x - pad * 2, 70).collidepoint(mx, my): self._open_buy_etf()

    def handle_scroll(self, ev):
        if ev.type == pygame.MOUSEWHEEL and self.modal: self._scroll = max(0, self._scroll - ev.y * 30)

    def draw(self):
        screen.fill(BG); self._draw_topbar(); self._draw_sidebar(); self._draw_tabs()
        self._draw_content(); self._draw_newsbar()
        if self.modal: dim_overlay(screen); self._draw_modal()
        if self._ach_popup: self._draw_ach_popup()

    def _draw_topbar(self):
        gs = self.gs
        box(screen, PANEL, (0,0,W,44)); line(screen, BORDER, (0,44),(W,44))
        txt(screen,"Business Tycoon Pro","lg",GOLD, 10,22,"midleft")
        stats = [("Bargeld", fmt(gs.cash), gs.cash>=0), ("Nettoverm.", fmt(gs.net_worth()), True),
                 (f"{gs.month:02d}.{gs.year}","",True), ("Schulden", fmt(gs.loan), gs.loan==0),
                 ("Ruf", str(int(gs.reputation)), gs.reputation>=50)]
        x = 220
        for label,val,good in stats:
            if not val:
                txt(screen, label,"sm",CYAN, x+50,22,"center"); x += 100; continue
            box(screen, PANEL2, (x,6,120,32),16); txt(screen,f"{label}:","xs",MUTED, x+8,22,"midleft")
            txt(screen, val,"sm", GREEN if good else RED, x+112,22,"midright"); x += 128
        for i,(ms,lbl) in enumerate([(2000,"1x"),(800,"3x"),(300,"10x")]):
            r = pygame.Rect(W-240+i*44, 9, 38, 26)
            box(screen,ACCENT if self.speed==ms else PANEL2,r,6)
            box(screen,BORDER,r,6,1); txt(screen,lbl,"sm",WHITE,r.centerx,r.centery,"center")
        pr = pygame.Rect(W-100,9,88,26); box(screen,GREEN if not self.paused else YELLOW,pr,13)
        txt(screen,"Pause" if not self.paused else "Weiter","sm",BG,pr.centerx,pr.centery,"center")

    def _sidebar_rects(self):
        entries = [("__sec_immo__","Immobilien"), ("buy_prop", "  Kaufen"), ("sell_prop", "  Verkaufen/Markt"),
                   ("upg_prop", "  Renovieren"), ("rent_prop", "  Vermieten"), ("__sec_comp__","Unternehmen"),
                   ("buy_comp", "  Gründen"), ("sell_comp", "  Verkaufen/Markt"), ("upg_comp", "  Erweitern"),
                   ("__sec_fin__", "Finanzen"), ("loan", "  Kredit aufnehmen"), ("repay", "  Kredit tilgen"),
                   ("savings", "  Festgeld"), ("buy_etf", "  ETF kaufen"), ("__sec_sys__", "System"),
                   ("save", "  Speichern"), ("load", "  Laden")]
        y = 52; rects = []
        for key, _ in entries:
            if key.startswith("__"): rects.append((key, y, 18)); y += 20
            else: rects.append((key, y, 28)); y += 30
        return rects

    def _draw_sidebar(self):
        box(screen, PANEL, (0,44,188,H-44-20)); line(screen,BORDER,(188,44),(188,H-20))
        entries = {
            "__sec_immo__": "Immobilien", "buy_prop": "  Immo kaufen", "sell_prop": "  Marktplatz (V)",
            "upg_prop": "  Renovieren", "rent_prop": "  Vermieten", "__sec_comp__": "Unternehmen",
            "buy_comp": "  Firma gründen", "sell_comp": "  Marktplatz (V)", "upg_comp": "  Firma erweitern",
            "__sec_fin__": "Finanzen", "loan": "  Kredit aufnehmen", "repay": "  Kredit tilgen",
            "savings": "  Festgeld", "buy_etf": "  ETF kaufen", "__sec_sys__": "System",
            "save": "  Speichern", "load": "  Laden"
        }
        for key, ry, rh in self._sidebar_rects():
            label = entries[key]
            if key.startswith("__"): txt(screen, label.upper(),"xs",MUTED, 10, ry+2)
            else:
                hi = (key == "rent_prop" and any(p["vacant"] for p in self.gs.props))
                box(screen, (60,40,15) if hi else PANEL2, (4,ry,182,rh), 5)
                if hi: box(screen, YELLOW, (4,ry,182,rh), 5, 1)
                txt(screen, label, "sm", YELLOW if hi else WHITE, 12, ry+rh//2, "midleft")

    def _draw_tabs(self):
        box(screen, PANEL, (188,44,W-188,32)); line(screen,BORDER,(188,76),(W,76))
        tx = 194
        for i, name in enumerate(TABS):
            tw = F["sm"].size(name)[0]+22
            if self.tab == i: box(screen,ACCENT,(tx,74,tw,2),0)
            txt(screen,name,"sm",ACCENT if self.tab==i else MUTED,tx+tw//2,60,"center"); tx += tw+2

    def _draw_content(self):
        x,y,w,h = 188,76,W-188,H-76-20
        [self._tab_dashboard, self._tab_economy, self._tab_stocks, self._tab_achievements, self._tab_log][self.tab](x,y,w,h)

    def _tab_dashboard(self, x, y, w, h):
        gs = self.gs; pad = 10; cw = (w-pad*4)//3; ch2 = 90
        for i,(label,val,good) in enumerate([("Bargeld", fmt(gs.cash), gs.cash>=0), ("Nettovermoegen",fmt(gs.net_worth()), True), ("Immobilien", f"{len(gs.props)} Objekte", True), ("Unternehmen", f"{len(gs.comps)} Firmen", True), ("Monat. Einnahmen", fmt(gs.monthly_income()), True), ("Monat. Ausgaben", fmt(gs.monthly_expenses()), False)]):
            row, ci = divmod(i,3); tx2 = x+pad + ci*(cw+pad); ty2 = y+pad + row*(ch2+pad)
            box(screen,PANEL2,(tx2,ty2,cw,ch2),8); box(screen,BORDER,(tx2,ty2,cw,ch2),8,1)
            txt(screen,label,"xs",MUTED,tx2+10,ty2+12); txt(screen,val,"lg",GREEN if good else RED,tx2+10,ty2+42)

        cy3 = y+pad+2*(ch2+pad)+8; ch3 = h - 2*(ch2+pad) - pad*3 - 8
        if gs.props:
            bar_h = 28; box(screen, PANEL2, (x+pad, cy3, w-pad*2, bar_h), 6); box(screen, BORDER,  (x+pad, cy3, w-pad*2, bar_h), 6, 1)
            txt(screen, "Immobilien:", "xs", MUTED, x+pad+8, cy3+14, "midleft"); px2 = x+pad+90
            for p in gs.props:
                pw2 = min(120, (w-pad*2-100) // len(gs.props) - 4)
                col2 = RED if p["vacant"] and not p["listed"] else YELLOW if p["vacant"] else GREEN
                box(screen, col2, (px2, cy3+4, pw2, 20), 4); txt(screen, p["custom_name"][:7], "xs", BG, px2+4, cy3+14, "midleft")
                px2 += pw2 + 4
            cy3 += bar_h + 6; ch3 -= bar_h + 6
        if ch3 > 60 and len(gs.nw_hist) >= 2:
            box(screen,PANEL2,(x+pad,cy3,w-pad*2,ch3),8); box(screen,BORDER,(x+pad,cy3,w-pad*2,ch3),8,1)
            txt(screen,"Nettovermoegen (24 Monate)","xs",MUTED,x+pad+10,cy3+8); sparkline(screen,gs.nw_hist, x+pad+10,cy3+24, w-pad*2-20,ch3-36, CYAN)

    def _tab_economy(self, x, y, w, h):
        gs = self.gs; ph = PHASES[gs.phase]; pad = 12
        box(screen,PANEL2,(x+pad,y+pad,w-pad*2,72),8); pygame.draw.rect(screen,ph["col"],(x+pad,y+pad,5,72),border_radius=2)
        txt(screen,"Aktuelle Wirtschaftsphase","xs",MUTED,x+pad+14,y+pad+10); txt(screen,ph["label"],"xl",ph["col"],x+pad+14,y+pad+36)
        
        iy = y+pad+80; iw2 = (w-pad*4)//3; ih2 = 58
        for i,(label,val,good) in enumerate([("Leitzins", f"{gs.base_rate:.2f}%", gs.base_rate<6), ("BIP-Wachstum", f"{gs.gdp:.1f}%", gs.gdp>0), ("Arbeitslosigkeit",f"{gs.unemp:.1f}%", gs.unemp<8), ("Marktstimmung", f"{int(gs.sentiment)}/100", gs.sentiment>50), ("Inflation", f"{gs.inflation*12*100:.1f}% pa", gs.inflation*12<0.03), ("Kreditrate", f"{gs.loan_rate*12*100:.2f}% pa", True)]):
            row, ci = divmod(i,3); ix2 = x+pad + ci*(iw2+pad); iy2 = iy + row*(ih2+8)
            box(screen,PANEL2,(ix2,iy2,iw2,ih2),6); box(screen,BORDER,(ix2,iy2,iw2,ih2),6,1)
            txt(screen,label,"xs",MUTED,ix2+8,iy2+10); txt(screen,val,"md",GREEN if good else RED,ix2+8,iy2+32)

        py2 = iy + 2*(ih2+8) + 16; pw2 = (w-pad*2-40)//6; txt(screen,"Alle Wirtschaftsphasen","xs",MUTED,x+pad,py2-14)
        for i,(pname,pd) in enumerate(PHASES.items()):
            px2 = x+pad + i*(pw2+8); active = gs.phase == pname
            box(screen,pd["col"] if active else PANEL2,(px2,py2,pw2,40),6); box(screen,pd["col"],(px2,py2,pw2,40),6,2 if active else 1)
            txt(screen,pd["label"][:8],"xs",BG if active else pd["col"],px2+pw2//2,py2+20,"center")

    def _tab_stocks(self, x, y, w, h):
        gs = self.gs; pad = 10; col_w = (w-pad*3)//2; row_h = 62
        for i, sid in enumerate(list(gs.stock_data.keys())):
            s = gs.stock_data[sid]; rx = x+pad + (i%2)*(col_w+pad); ry = y+18 + (i//2)*row_h; qty = gs.stocks.get(sid,0)
            box(screen,PANEL2,(rx,ry,col_w,row_h-4),6); box(screen,BORDER,(rx,ry,col_w,row_h-4),6,1)
            pchg = (s["hist"][-1]/s["hist"][-2]-1)*100 if len(s["hist"])>=2 else 0
            txt(screen,s["name"],"sm",WHITE,rx+8,ry+10); txt(screen,fmt(s["price"]),"sm",CYAN,rx+8,ry+30)
            txt(screen,f"{pchg:+.1f}%","xs",GREEN if pchg>=0 else RED,rx+8,ry+48); txt(screen,f"Div: {s['div']*100:.1f}%","xs",MUTED,rx+col_w//2,ry+10)
            if qty > 0: txt(screen,f"{qty:.0f} Stk = {fmt(qty*s['price'])}","xs",PURPLE,rx+col_w//2,ry+30)
            if len(s["hist"]) >= 2: sparkline(screen,s["hist"],rx+col_w-80,ry+4,72,50)

    def _tab_achievements(self, x, y, w, h):
        gs = self.gs; txt(screen,f"Erfolge {len(gs.achiev_done)}/{len(ACHIEVEMENTS)}","lg",GOLD,x+12,y+10)
        for i,(aid,title,desc,_) in enumerate(ACHIEVEMENTS):
            ay = y+40 + i*52
            if ay+52 > y+h: break
            earned = aid in gs.achiev_done
            box(screen,(31,50,35) if earned else PANEL2,(x+10,ay,w-20,48),7); box(screen,GREEN if earned else BORDER,(x+10,ay,w-20,48),7,1)
            txt(screen,"OK" if earned else "--","sm",GREEN if earned else MUTED,x+24,ay+24,"midleft")
            txt(screen,title,"md" if earned else "sm",WHITE if earned else MUTED,x+60,ay+14); txt(screen,desc,"xs",MUTED,x+60,ay+34)

    def _tab_log(self, x, y, w, h):
        txt(screen,"Aktivitaetslog","lg",GOLD,x+12,y+10)
        for i,(msg,kind) in enumerate(self.gs.log[:(h-40)//24]):
            ly = y+38 + i*24; pygame.draw.rect(screen,{"good":GREEN,"bad":RED,"warn":YELLOW,"info":CYAN}.get(kind,MUTED),(x+10,ly+4,3,16))
            txt(screen,msg,"sm",WHITE,x+18,ly+12,"midleft",w-30)

    def _draw_newsbar(self):
        box(screen,PANEL,(0,H-20,W,20)); line(screen,BORDER,(0,H-20),(W,H-20))
        news_str = "  //  ".join(self.gs.news[:5]) if self.gs.news else "Willkommen!"
        self._news_x -= 1.2
        if self._news_x < -F["sm"].size(news_str)[0]: self._news_x = float(W)
        txt(screen,news_str,"sm",MUTED,int(self._news_x),H-10,"midleft")

    def _draw_modal(self):
        mt = self.modal.get("type",""); mw, mh = 660, 520; bx = (W-mw)//2; by = (H-mh)//2
        box(screen,PANEL,(bx,by,mw,mh),12); box(screen,ACCENT,(bx,by,mw,mh),12,1)
        box(screen,RED,(bx+mw-32,by+6,24,24),12); txt(screen,"X","sm",WHITE,bx+mw-20,by+18,"center")
        
        if mt == "buy_prop": self._draw_m_buy_prop(bx,by,mw,mh)
        elif mt == "sell_prop": self._draw_m_list_prop(bx,by,mw,mh,"Immobilien-Marktplatz")
        elif mt == "upg_prop": self._draw_m_upg_prop(bx,by,mw,mh)
        elif mt == "rent_prop": self._draw_m_rent_prop(bx,by,mw,mh)
        elif mt == "buy_comp": self._draw_m_buy_comp(bx,by,mw,mh)
        elif mt == "sell_comp": self._draw_m_list_comp(bx,by,mw,mh,"Firmen-Marktplatz")
        elif mt == "upg_comp": self._draw_m_upg_comp(bx,by,mw,mh)
        elif mt == "loan": self._draw_m_loan(bx,by,mw,mh)
        elif mt == "repay": self._draw_m_repay(bx,by,mw,mh)
        elif mt == "savings": self._draw_m_savings(bx,by,mw,mh)
        elif mt in ("buy_stock","sell_stock"): self._draw_m_stock(bx,by,mw,mh)
        elif mt == "buy_etf": self._draw_m_etf(bx,by,mw,mh)

    def _draw_m_buy_prop(self, bx, by, mw, mh):
        gs = self.gs; txt(screen,"Immobilie kaufen","lg",GOLD,bx+16,by+16); txt(screen,f"Bargeld: {fmt(gs.cash)}","sm",CYAN,bx+16,by+42)
        txt(screen, "Name vergeben:", "sm", WHITE, bx+140, by+58)
        self._inputs["custom_name"].rect = pygame.Rect(bx+250, by+50, 250, 34); self._inputs["custom_name"].draw(screen)
        
        view = screen.subsurface(pygame.Rect(bx, by+95, mw, mh-105))
        for i, row in enumerate(PROP_CATALOG):
            ry = i*72 - self._scroll
            if ry+72 < 0 or ry > mh-105: continue
            can = gs.cash >= row[3]; box(view, PANEL2 if can else (25,28,38),(8,ry,mw-16,68),7); box(view, GREEN if can else BORDER,(8,ry,mw-16,68),7,1)
            txt(view,f"{row[2]}  {row[1]}","md",WHITE if can else MUTED,18,ry+10); txt(view,f"Preis: {fmt(row[3])}","xs",MUTED,18,ry+32)
            txt(view,f"Netto: {fmt(row[4]-row[5])}/Monat","xs",CYAN,18,ry+50)
            box(view,ACCENT if can else BORDER,(mw-112,ry+20,90,30),6); txt(view,"Kaufen" if can else "Zu teuer","sm",WHITE,mw-67,ry+35,"center")

    def _draw_m_list_prop(self, bx, by, mw, mh, title):
        gs = self.gs; txt(screen,title,"lg",GOLD,bx+16,by+16)
        txt(screen, "Verkaufspreis festlegen:", "sm", WHITE, bx+80, by+58)
        self._inputs["ask_price"].rect = pygame.Rect(bx+250, by+50, 160, 34); self._inputs["ask_price"].draw(screen)
        
        view = screen.subsurface(pygame.Rect(bx, by+95, mw, mh-105))
        for i,p in enumerate(gs.props):
            ry = i*70 - self._scroll
            if ry+70<0 or ry>mh-105: continue
            is_listed = p.get("for_sale")
            box(view, (40,30,10) if is_listed else PANEL2,(8,ry,mw-16,66),7); box(view, YELLOW if is_listed else BORDER,(8,ry,mw-16,66),7,1)
            txt(view,f"{p['custom_name']}","md",WHITE,18,ry+10)
            txt(view,f"Echter Wert: {fmt(p['price'])}","xs",MUTED,18,ry+34)
            if is_listed: txt(view,f"Auf dem Markt für: {fmt(p['ask_price'])} ({p['market_months']} Mon.)","xs",YELLOW,18,ry+48)
            
            box(view,RED if is_listed else GREEN,(mw-120,ry+20,100,30),6)
            txt(view,"Zurückziehen" if is_listed else "Anbieten","sm",WHITE,mw-70,ry+35,"center")

    def _draw_m_buy_comp(self, bx, by, mw, mh):
        gs = self.gs; txt(screen,"Firma gründen","lg",GOLD,bx+16,by+16); txt(screen,f"Bargeld: {fmt(gs.cash)}","sm",CYAN,bx+16,by+42)
        txt(screen, "Name vergeben:", "sm", WHITE, bx+140, by+58)
        self._inputs["custom_name"].rect = pygame.Rect(bx+250, by+50, 250, 34); self._inputs["custom_name"].draw(screen)
        
        view = screen.subsurface(pygame.Rect(bx, by+95, mw, mh-105))
        for i, row in enumerate(COMP_CATALOG):
            ry = i*72 - self._scroll
            if ry+72<0 or ry>mh-105: continue
            can = gs.cash >= row[3]; box(view,PANEL2 if can else (25,28,38),(8,ry,mw-16,68),7); box(view,GREEN if can else BORDER,(8,ry,mw-16,68),7,1)
            txt(view,f"{row[1]}","md",WHITE if can else MUTED,18,ry+10); txt(view,f"Preis: {fmt(row[3])}","xs",MUTED,18,ry+32)
            box(view,ACCENT if can else BORDER,(mw-112,ry+20,90,30),6); txt(view,"Gründen" if can else "Zu teuer","sm",WHITE,mw-67,ry+35,"center")

    def _draw_m_list_comp(self, bx, by, mw, mh, title):
        gs = self.gs; txt(screen,title,"lg",GOLD,bx+16,by+16)
        txt(screen, "Verkaufspreis festlegen:", "sm", WHITE, bx+80, by+58)
        self._inputs["ask_price"].rect = pygame.Rect(bx+250, by+50, 160, 34); self._inputs["ask_price"].draw(screen)
        
        view = screen.subsurface(pygame.Rect(bx, by+95, mw, mh-105))
        for i,c in enumerate(gs.comps):
            ry = i*70 - self._scroll
            if ry+70<0 or ry>mh-105: continue
            is_listed = c.get("for_sale")
            box(view,(40,30,10) if is_listed else PANEL2,(8,ry,mw-16,66),7); box(view,YELLOW if is_listed else BORDER,(8,ry,mw-16,66),7,1)
            txt(view,f"{c['custom_name']}","md",WHITE,18,ry+10)
            txt(view,f"Echter Wert: {fmt(c['val'])}","xs",MUTED,18,ry+34)
            if is_listed: txt(view,f"Auf dem Markt für: {fmt(c['ask_price'])} ({c['market_months']} Mon.)","xs",YELLOW,18,ry+48)
            box(view,RED if is_listed else GREEN,(mw-120,ry+20,100,30),6)
            txt(view,"Zurückziehen" if is_listed else "Anbieten","sm",WHITE,mw-70,ry+35,"center")

    def _draw_m_upg_prop(self, bx, by, mw, mh):
        gs = self.gs; txt(screen,"Immobilie renovieren","lg",GOLD,bx+16,by+16)
        view = screen.subsurface(pygame.Rect(bx, by+50, mw, mh-60))
        for i,p in enumerate(gs.props):
            ry = i*72 - self._scroll; cost = p["price"]*0.12; can = gs.cash >= cost and p["level"] < p["lvl_max"]
            box(view,PANEL2,(8,ry,mw-16,68),7); box(view,BORDER,(8,ry,mw-16,68),7,1)
            txt(view,f"{p['custom_name']}","md",WHITE,18,ry+10); txt(view,f"Kosten: {fmt(cost)}","xs",MUTED,18,ry+32)
            box(view,ACCENT if can else BORDER,(mw-112,ry+22,90,28),6); txt(view,"Renovieren" if can else "Max Lvl","xs",WHITE,mw-67,ry+36,"center")

    def _draw_m_upg_comp(self, bx, by, mw, mh):
        gs = self.gs; txt(screen,"Firma erweitern","lg",GOLD,bx+16,by+16)
        view = screen.subsurface(pygame.Rect(bx, by+50, mw, mh-60))
        for i,c in enumerate(gs.comps):
            ry = i*72 - self._scroll; cost = c["val"]*0.15; can = gs.cash >= cost and c["level"] < c["lvl_max"]
            box(view,PANEL2,(8,ry,mw-16,68),7); box(view,BORDER,(8,ry,mw-16,68),7,1)
            txt(view,c["custom_name"],"md",WHITE,18,ry+10); txt(view,f"Kosten: {fmt(cost)}","xs",MUTED,18,ry+32)
            box(view,ACCENT if can else BORDER,(mw-112,ry+22,90,28),6); txt(view,"Erweitern" if can else "Max Lvl","xs",WHITE,mw-67,ry+36,"center")

    def _draw_m_rent_prop(self, bx, by, mw, mh):
        gs = self.gs; txt(screen, "Vermietung", "lg", GOLD, bx+16, by+16)
        view = screen.subsurface(pygame.Rect(bx, by+54, mw, mh-64))
        for i, p in enumerate(gs.props):
            ry = i * 100 - self._scroll
            bg, bc = ((40,25,25), RED) if p["vacant"] and not p["listed"] else ((40,38,15), YELLOW) if p["vacant"] else ((20,40,28), GREEN)
            box(view, bg, (8, ry, mw-16, 94), 8); box(view, bc, (8, ry, mw-16, 94), 8, 1)
            txt(view, f"{p['custom_name']}", "lg", WHITE, 22, ry+10)
            status = "LEER" if p["vacant"] and not p["listed"] else "SUCHE..." if p["vacant"] else f"VERMIETET ({p['contract_left']} M)"
            txt(view, status, "sm", bc, 22, ry+34)
            btn_col, btn_txt = (GREEN, "Anbieten") if p["vacant"] and not p["listed"] else (YELLOW, "Suche stoppen") if p["vacant"] else (RED, "Kündigen")
            box(view, btn_col, (mw-128, ry+20, 108, 30), 6); txt(view, btn_txt, "sm", WHITE if btn_col==RED else BG, mw-74, ry+35, "center")

    def _draw_m_loan(self, bx, by, mw, mh):
        gs = self.gs; txt(screen,"Kredit aufnehmen","lg",GOLD,bx+16,by+16)
        txt(screen,f"Aktuelle Schulden: {fmt(gs.loan)}","sm",RED,bx+16,by+50); self._inputs["amount"].draw(screen)
        box(screen,ACCENT,(bx+260,by+128,120,34),7); txt(screen,"Aufnehmen","sm",WHITE,bx+320,by+145,"center")

    def _draw_m_repay(self, bx, by, mw, mh):
        txt(screen,"Kredit tilgen","lg",GOLD,bx+16,by+16); self._inputs["amount"].draw(screen)
        box(screen,GREEN,(bx+260,by+128,120,34),7); txt(screen,"Tilgen","sm",WHITE,bx+320,by+145,"center")
        box(screen,YELLOW,(bx+30,by+180,160,34),7); txt(screen,"Alles tilgen","sm",BG,bx+110,by+197,"center")

    def _draw_m_savings(self, bx, by, mw, mh):
        txt(screen,"Festgeld","lg",GOLD,bx+16,by+16); self._inputs["amount"].draw(screen)
        box(screen,ACCENT,(bx+260,by+128,120,34),7); txt(screen,"Einzahlen","sm",WHITE,bx+320,by+145,"center")
        if self.gs.savings > 0: box(screen,YELLOW,(bx+30,by+180,160,34),7); txt(screen,"Auszahlen","sm",BG,bx+110,by+197,"center")

    def _draw_m_stock(self, bx, by, mw, mh):
        mt = self.modal["type"]; txt("Aktie kaufen" if mt=="buy_stock" else "Aktie verkaufen","lg",GOLD,bx+16,by+16); self._inputs["qty"].draw(screen)
        box(screen,ACCENT if mt=="buy_stock" else RED,(bx+220,by+130,110,34),7); txt(screen,"Kaufen" if mt=="buy_stock" else "Verkaufen","sm",WHITE,bx+275,by+147,"center")
        if mt=="sell_stock": box(screen,YELLOW,(bx+30,by+180,160,34),7); txt(screen,"Alles verkaufen","sm",BG,bx+110,by+197,"center")

    def _draw_m_etf(self, bx, by, mw, mh):
        txt(screen,"Welt-ETF","lg",GOLD,bx+16,by+16); self._inputs["qty"].draw(screen)
        box(screen,ACCENT,(bx+220,by+130,110,34),7); txt(screen,"Kaufen","sm",WHITE,bx+275,by+147,"center")
        box(screen,RED,(bx+30,by+180,180,34),7); txt(screen,"Alle Anteile verkaufen","sm",WHITE,bx+120,by+197,"center")

    def _draw_ach_popup(self):
        title,desc,t0 = self._ach_popup; elapsed = pygame.time.get_ticks()-t0
        if elapsed > 4000: self._ach_popup = None; return
        alpha = 255 if elapsed < 3000 else int(255*(1-(elapsed-3000)/1000)); s = pygame.Surface((320,58),pygame.SRCALPHA); s.fill((80,40,140,alpha))
        screen.blit(s,(W-336,H-86)); txt(screen,f"Erfolg: {title}","md",GOLD,W-324,H-72); txt(screen,desc,"xs",MUTED,W-324,H-48)

class BankruptScreen:
    def __init__(self, gs: GS):
        self.gs  = gs
        self.btn = Btn(W//2-90, H//2+80, 180, 40, "Neu starten", GREEN, BG, "lg")

    def handle(self, ev):
        self.btn.update(pygame.mouse.get_pos())
        if self.btn.hit(ev): return "restart"
        return None

    def draw(self, surf):
        surf.fill(BG)
        txt(surf,"BANKROTT","title",RED,W//2,H//2-100,"center")
        txt(surf,"Du bist zahlungsunfaehig und kreditunwuerdig!","lg",WHITE,W//2,H//2-50,"center")
        txt(surf,f"Endvermoegen: {fmt(self.gs.net_worth())}","md",MUTED,W//2,H//2-14,"center")
        txt(surf,f"Gespielte Monate: {(self.gs.year-2024)*12+self.gs.month}","md",MUTED,W//2,H//2+20,"center")
        self.btn.draw(surf)

def main():
    state = "name"
    name_screen = NameScreen()
    game_screen = None; bankr_screen = None; gs = None

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.VIDEORESIZE:
                global W, H; W, H = ev.w, ev.h

            if state == "name":
                res = name_screen.handle(ev)
                if res:
                    name, diff = res
                    gs = GS(diff)
                    gs.name = name
                    gs.add_log(f"Willkommen, {gs.name}! ({diff}) Startkapital: {fmt(gs.cash)}", "info")
                    game_screen = GameScreen(gs); state = "game"
            elif state == "game":
                if ev.type == pygame.MOUSEWHEEL: game_screen.handle_scroll(ev)
                else:
                    if game_screen.handle(ev) == "bankrott":
                        bankr_screen = BankruptScreen(gs); state = "bankrott"
            elif state == "bankrott":
                if bankr_screen.handle(ev) == "restart":
                    state = "name"; name_screen = NameScreen()

        if state == "name": name_screen.draw(screen)
        elif state == "game":
            if game_screen.maybe_tick() == "bankrott":
                bankr_screen = BankruptScreen(gs); state = "bankrott"
            else: game_screen.draw()
        elif state == "bankrott": bankr_screen.draw(screen)

        pygame.display.flip(); clock.tick(60)

if __name__ == "__main__": 
    main()