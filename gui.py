import threading
from datetime import datetime

import customtkinter as ctk
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from database import initialize_database
from insights import analyse_portfolio
from portfolio import Portfolio
from stock import Stock
from stock_api import StockAPI
from user import User


COLORS = {
    "canvas": "#0A0C0F",
    "sidebar": "#0E1116",
    "panel": "#12161C",
    "panel_alt": "#171C23",
    "line": "#252C35",
    "text": "#F4F1E8",
    "muted": "#8D96A3",
    "faint": "#596270",
    "accent": "#D8FF5F",
    "accent_hover": "#C5EB54",
    "cyan": "#58D5E8",
    "loss": "#FF746C",
    "warning": "#F5C96A",
}
FONT = "Segoe UI"
MONO = "Cascadia Mono"


def format_money(value):
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def format_signed_money(value):
    return f"{'+' if value >= 0 else '-'}${abs(value):,.2f}"


def clear(widget):
    for child in widget.winfo_children():
        child.destroy()


class StockTradingApp(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("dark")
        super().__init__(fg_color=COLORS["canvas"])
        self.title("StockTrader // Market Workstation")
        self.geometry("1400x720")
        self.minsize(1220, 650)

        self.user = None
        self.current_page = None
        self.live_prices = {}
        self.active_quote = None
        self.nav_buttons = {}
        self.show_auth()

    def show_auth(self):
        self.user = None
        clear(self)
        self.grid_columnconfigure(0, weight=6)
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(0, weight=1)

        story = ctk.CTkFrame(self, fg_color=COLORS["sidebar"], corner_radius=0)
        story.grid(row=0, column=0, sticky="nsew")
        story.grid_columnconfigure(0, weight=1)
        story.grid_rowconfigure(3, weight=1)

        brand = ctk.CTkFrame(story, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=52, pady=(42, 0))
        ctk.CTkLabel(
            brand,
            text="ST / 01",
            font=(MONO, 15, "bold"),
            text_color=COLORS["accent"],
        ).pack(side="left")
        ctk.CTkLabel(
            brand,
            text="PAPER MARKET SYSTEM",
            font=(MONO, 11),
            text_color=COLORS["muted"],
        ).pack(side="right")

        ctk.CTkLabel(
            story,
            text="TRADE THE\nTHESIS.",
            justify="left",
            anchor="w",
            font=(FONT, 58, "bold"),
            text_color=COLORS["text"],
        ).grid(row=1, column=0, sticky="ew", padx=52, pady=(92, 12))
        ctk.CTkLabel(
            story,
            text="A deliberate simulator for researching ideas,\nallocating virtual capital, and reading risk clearly.",
            justify="left",
            anchor="w",
            font=(FONT, 17),
            text_color=COLORS["muted"],
        ).grid(row=2, column=0, sticky="ew", padx=56)

        features = ctk.CTkFrame(story, fg_color="transparent")
        features.grid(row=3, column=0, sticky="sew", padx=52, pady=44)
        for index, (title, body) in enumerate(
            [
                ("01  MARKET CONTEXT", "Latest quotes and focused price research."),
                ("02  CAPITAL CONTROL", "Cash-aware orders with guarded trade logic."),
                ("03  SIGNAL ENGINE", "Local, deterministic portfolio intelligence."),
            ]
        ):
            row = ctk.CTkFrame(features, fg_color="transparent")
            row.pack(fill="x", pady=(0, 22))
            ctk.CTkFrame(row, width=4, height=42, fg_color=COLORS["line"]).pack(
                side="left", padx=(0, 16)
            )
            text = ctk.CTkFrame(row, fg_color="transparent")
            text.pack(side="left", fill="x")
            ctk.CTkLabel(
                text,
                text=title,
                anchor="w",
                font=(MONO, 11, "bold"),
                text_color=COLORS["text"],
            ).pack(fill="x")
            ctk.CTkLabel(
                text,
                text=body,
                anchor="w",
                font=(FONT, 13),
                text_color=COLORS["muted"],
            ).pack(fill="x", pady=(4, 0))

        form_wrap = ctk.CTkFrame(self, fg_color=COLORS["canvas"], corner_radius=0)
        form_wrap.grid(row=0, column=1, sticky="nsew")
        form_wrap.grid_columnconfigure(0, weight=1)
        form_wrap.grid_rowconfigure(0, weight=1)

        form = ctk.CTkFrame(form_wrap, fg_color="transparent")
        form.grid(row=0, column=0, sticky="ew", padx=48, pady=64)
        ctk.CTkLabel(
            form,
            text="ENTER WORKSPACE",
            anchor="w",
            font=(MONO, 12, "bold"),
            text_color=COLORS["accent"],
        ).pack(fill="x")
        ctk.CTkLabel(
            form,
            text="Your market desk\nis ready.",
            justify="left",
            anchor="w",
            font=(FONT, 34, "bold"),
            text_color=COLORS["text"],
        ).pack(fill="x", pady=(14, 28))

        self.auth_mode = ctk.StringVar(value="SIGN IN")
        ctk.CTkSegmentedButton(
            form,
            values=["SIGN IN", "CREATE ACCOUNT"],
            variable=self.auth_mode,
            fg_color=COLORS["panel"],
            selected_color=COLORS["panel_alt"],
            selected_hover_color=COLORS["line"],
            unselected_color=COLORS["panel"],
            unselected_hover_color=COLORS["panel_alt"],
            text_color=COLORS["text"],
            font=(MONO, 11, "bold"),
        ).pack(fill="x", pady=(0, 26))

        ctk.CTkLabel(
            form, text="USERNAME", anchor="w", font=(MONO, 10), text_color=COLORS["muted"]
        ).pack(fill="x", pady=(0, 7))
        self.username_entry = ctk.CTkEntry(
            form,
            height=48,
            placeholder_text="your handle",
            fg_color=COLORS["panel"],
            border_color=COLORS["line"],
            text_color=COLORS["text"],
            font=(FONT, 14),
        )
        self.username_entry.pack(fill="x")

        ctk.CTkLabel(
            form, text="PASSWORD", anchor="w", font=(MONO, 10), text_color=COLORS["muted"]
        ).pack(fill="x", pady=(20, 7))
        self.password_entry = ctk.CTkEntry(
            form,
            height=48,
            placeholder_text="8 characters minimum",
            show="•",
            fg_color=COLORS["panel"],
            border_color=COLORS["line"],
            text_color=COLORS["text"],
            font=(FONT, 14),
        )
        self.password_entry.pack(fill="x")
        self.password_entry.bind("<Return>", lambda _event: self._submit_auth())

        self.auth_error = ctk.CTkLabel(
            form,
            text="",
            anchor="w",
            wraplength=360,
            font=(FONT, 12),
            text_color=COLORS["loss"],
        )
        self.auth_error.pack(fill="x", pady=(12, 0))

        ctk.CTkButton(
            form,
            text="OPEN STOCKTRADER  →",
            height=50,
            command=self._submit_auth,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["canvas"],
            font=(MONO, 12, "bold"),
        ).pack(fill="x", pady=(16, 14))
        ctk.CTkLabel(
            form,
            text="Simulation only · Market data may be delayed",
            font=(FONT, 11),
            text_color=COLORS["faint"],
        ).pack()
        self.username_entry.focus_set()

    def _submit_auth(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            self.auth_error.configure(text="Enter both a username and password.")
            return
        if self.auth_mode.get() == "CREATE ACCOUNT" and len(password) < 8:
            self.auth_error.configure(text="Use at least 8 characters for a new account.")
            return

        user = (
            User.register(username, password)
            if self.auth_mode.get() == "CREATE ACCOUNT"
            else User.login(username, password)
        )
        if not user:
            message = (
                "That username is unavailable."
                if self.auth_mode.get() == "CREATE ACCOUNT"
                else "Those credentials do not match an account."
            )
            self.auth_error.configure(text=message)
            return

        self.user = user
        self.show_workspace()

    def show_workspace(self):
        clear(self)
        self.grid_columnconfigure(0, weight=0, minsize=230)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=230, fg_color=COLORS["sidebar"], corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(2, weight=1)

        logo = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo.grid(row=0, column=0, sticky="ew", padx=24, pady=(30, 36))
        ctk.CTkLabel(
            logo,
            text="ST",
            width=40,
            height=40,
            corner_radius=8,
            fg_color=COLORS["accent"],
            text_color=COLORS["canvas"],
            font=(MONO, 14, "bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            logo,
            text="STOCKTRADER\nWORKSTATION",
            justify="left",
            font=(MONO, 10, "bold"),
            text_color=COLORS["text"],
        ).pack(side="left", padx=12)

        nav = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav.grid(row=1, column=0, sticky="ew", padx=14)
        pages = [
            ("overview", "01   Overview"),
            ("trade", "02   Trade"),
            ("portfolio", "03   Portfolio"),
            ("activity", "04   Activity"),
            ("research", "05   Research"),
        ]
        self.nav_buttons = {}
        for page, label in pages:
            button = ctk.CTkButton(
                nav,
                text=label,
                anchor="w",
                height=42,
                corner_radius=7,
                fg_color="transparent",
                hover_color=COLORS["panel_alt"],
                text_color=COLORS["muted"],
                font=(MONO, 11, "bold"),
                command=lambda target=page: self.show_page(target),
            )
            button.pack(fill="x", pady=3)
            self.nav_buttons[page] = button

        profile = ctk.CTkFrame(sidebar, fg_color=COLORS["panel"], corner_radius=10)
        profile.grid(row=3, column=0, sticky="sew", padx=14, pady=18)
        ctk.CTkLabel(
            profile,
            text="PAPER MODE",
            anchor="w",
            font=(MONO, 9, "bold"),
            text_color=COLORS["accent"],
        ).pack(fill="x", padx=14, pady=(14, 3))
        ctk.CTkLabel(
            profile,
            text=self.user.username.upper(),
            anchor="w",
            font=(FONT, 14, "bold"),
            text_color=COLORS["text"],
        ).pack(fill="x", padx=14)
        ctk.CTkLabel(
            profile,
            text=f"Cash {format_money(self.user.balance)}",
            anchor="w",
            font=(FONT, 11),
            text_color=COLORS["muted"],
        ).pack(fill="x", padx=14, pady=(2, 12))
        ctk.CTkButton(
            profile,
            text="Sign out",
            height=32,
            fg_color=COLORS["panel_alt"],
            hover_color=COLORS["line"],
            text_color=COLORS["muted"],
            font=(FONT, 11),
            command=self.show_auth,
        ).pack(fill="x", padx=10, pady=(0, 10))

        main = ctk.CTkFrame(self, fg_color=COLORS["canvas"], corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        topbar = ctk.CTkFrame(main, height=72, fg_color=COLORS["canvas"], corner_radius=0)
        topbar.grid(row=0, column=0, sticky="ew", padx=30)
        topbar.grid_columnconfigure(1, weight=1)
        self.page_context = ctk.CTkLabel(
            topbar,
            text="WORKSPACE / OVERVIEW",
            anchor="w",
            font=(MONO, 10, "bold"),
            text_color=COLORS["muted"],
        )
        self.page_context.grid(row=0, column=0, sticky="w")

        quick = ctk.CTkFrame(topbar, fg_color="transparent")
        quick.grid(row=0, column=1, sticky="e", padx=22)
        self.quick_symbol = ctk.CTkEntry(
            quick,
            width=180,
            height=36,
            placeholder_text="Jump to symbol",
            fg_color=COLORS["panel"],
            border_color=COLORS["line"],
            font=(MONO, 11),
        )
        self.quick_symbol.pack(side="left")
        self.quick_symbol.bind("<Return>", self._quick_search)
        ctk.CTkButton(
            quick,
            text="GO",
            width=44,
            height=36,
            command=self._quick_search,
            fg_color=COLORS["panel_alt"],
            hover_color=COLORS["line"],
            text_color=COLORS["accent"],
            font=(MONO, 10, "bold"),
        ).pack(side="left", padx=(6, 0))

        self.content = ctk.CTkScrollableFrame(
            main,
            fg_color=COLORS["canvas"],
            corner_radius=0,
            scrollbar_button_color=COLORS["line"],
            scrollbar_button_hover_color=COLORS["faint"],
        )
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.show_page("overview")

    def _quick_search(self, _event=None):
        symbol = self.quick_symbol.get().strip()
        if not symbol:
            return
        self.show_page("trade")
        self.trade_symbol.delete(0, "end")
        self.trade_symbol.insert(0, symbol)
        self._search_quote()

    def show_page(self, page):
        self.current_page = page
        self.page_context.configure(text=f"WORKSPACE / {page.upper()}")
        for name, button in self.nav_buttons.items():
            active = name == page
            button.configure(
                fg_color=COLORS["panel_alt"] if active else "transparent",
                text_color=COLORS["text"] if active else COLORS["muted"],
            )
        clear(self.content)
        {
            "overview": self._build_overview,
            "trade": self._build_trade,
            "portfolio": self._build_portfolio,
            "activity": self._build_activity,
            "research": self._build_research,
        }[page]()

    def _page(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        page.pack(fill="both", expand=True, padx=30, pady=(10, 34))
        return page

    def _heading(self, parent, eyebrow, title, body, action=None):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 24))
        text = ctk.CTkFrame(header, fg_color="transparent")
        text.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            text,
            text=eyebrow,
            anchor="w",
            font=(MONO, 10, "bold"),
            text_color=COLORS["accent"],
        ).pack(fill="x")
        ctk.CTkLabel(
            text,
            text=title,
            anchor="w",
            font=(FONT, 30, "bold"),
            text_color=COLORS["text"],
        ).pack(fill="x", pady=(4, 3))
        ctk.CTkLabel(
            text,
            text=body,
            anchor="w",
            font=(FONT, 13),
            text_color=COLORS["muted"],
        ).pack(fill="x")
        if action:
            ctk.CTkButton(
                header,
                text=action[0],
                width=142,
                height=38,
                command=action[1],
                fg_color=COLORS["panel_alt"],
                hover_color=COLORS["line"],
                text_color=COLORS["accent"],
                font=(MONO, 10, "bold"),
            ).pack(side="right")

    def _panel(self, parent):
        return ctk.CTkFrame(
            parent,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["line"],
            corner_radius=10,
        )

    def _metric(self, parent, column, label, value, note, tone=None, row=0):
        card = self._panel(parent)
        card.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=(0 if column == 0 else 5, 5),
            pady=(0, 8),
        )
        ctk.CTkLabel(
            card,
            text=label,
            anchor="w",
            font=(MONO, 9, "bold"),
            text_color=COLORS["muted"],
        ).pack(fill="x", padx=16, pady=(15, 5))
        ctk.CTkLabel(
            card,
            text=value,
            anchor="w",
            font=(FONT, 22, "bold"),
            text_color=tone or COLORS["text"],
        ).pack(fill="x", padx=16)
        ctk.CTkLabel(
            card,
            text=note,
            anchor="w",
            font=(FONT, 10),
            text_color=COLORS["faint"],
        ).pack(fill="x", padx=16, pady=(3, 15))

    def _empty(self, parent, label, title, body):
        ctk.CTkLabel(
            parent,
            text=label,
            font=(MONO, 10, "bold"),
            text_color=COLORS["accent"],
        ).pack(pady=(34, 8))
        ctk.CTkLabel(
            parent,
            text=title,
            font=(FONT, 20, "bold"),
            text_color=COLORS["text"],
        ).pack()
        ctk.CTkLabel(
            parent,
            text=body,
            wraplength=440,
            justify="center",
            font=(FONT, 12),
            text_color=COLORS["muted"],
        ).pack(pady=(6, 34))

    def _portfolio_analysis(self):
        return analyse_portfolio(
            Portfolio(self.user.id).get_portfolio(), self.user.balance, self.live_prices
        )

    def _build_overview(self):
        page = self._page()
        self._heading(
            page,
            f"{datetime.now():%A, %B %d}".upper(),
            f"Good to see you, {self.user.username}.",
            "A compact read on capital, exposure, and what deserves attention.",
            ("REFRESH PRICES", self._refresh_prices),
        )

        analysis = self._portfolio_analysis()
        metrics = ctk.CTkFrame(page, fg_color="transparent")
        metrics.pack(fill="x", pady=(0, 12))
        for column in range(2):
            metrics.grid_columnconfigure(column, weight=1)
        self._metric(metrics, 0, "NET WORTH", format_money(analysis["net_worth"]), "Cash + marked positions")
        self._metric(metrics, 1, "CASH RESERVE", format_money(analysis["cash"]), "Immediately deployable")
        self._metric(metrics, 0, "INVESTED", format_money(analysis["invested"]), "Current marked value", row=1)
        pl_tone = COLORS["cyan"] if analysis["unrealized_pl"] >= 0 else COLORS["loss"]
        self._metric(
            metrics,
            1,
            "UNREALIZED P/L",
            format_signed_money(analysis["unrealized_pl"]),
            "Versus average cost",
            pl_tone,
            row=1,
        )

        split = ctk.CTkFrame(page, fg_color="transparent")
        split.pack(fill="x", pady=(0, 12))
        split.grid_columnconfigure(0, weight=2)
        split.grid_columnconfigure(1, weight=1)

        allocation = self._panel(split)
        allocation.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        ctk.CTkLabel(
            allocation,
            text="CAPITAL MAP",
            anchor="w",
            font=(MONO, 10, "bold"),
            text_color=COLORS["muted"],
        ).pack(fill="x", padx=18, pady=(17, 2))
        ctk.CTkLabel(
            allocation,
            text="Allocation by marked value",
            anchor="w",
            font=(FONT, 18, "bold"),
            text_color=COLORS["text"],
        ).pack(fill="x", padx=18, pady=(0, 16))
        if analysis["allocation"]:
            for symbol, share in analysis["allocation"][:6]:
                row = ctk.CTkFrame(allocation, fg_color="transparent")
                row.pack(fill="x", padx=18, pady=7)
                ctk.CTkLabel(
                    row,
                    text=symbol,
                    width=64,
                    anchor="w",
                    font=(MONO, 11, "bold"),
                    text_color=COLORS["text"],
                ).pack(side="left")
                bar = ctk.CTkProgressBar(
                    row,
                    height=8,
                    progress_color=COLORS["cyan"],
                    fg_color=COLORS["line"],
                )
                bar.pack(side="left", fill="x", expand=True, padx=10)
                bar.set(share)
                ctk.CTkLabel(
                    row,
                    text=f"{share:.0%}",
                    width=46,
                    anchor="e",
                    font=(MONO, 10),
                    text_color=COLORS["muted"],
                ).pack(side="right")
            ctk.CTkLabel(
                allocation,
                text="Marked with loaded prices; cost basis is used until refresh.",
                anchor="w",
                font=(FONT, 10),
                text_color=COLORS["faint"],
            ).pack(fill="x", padx=18, pady=(12, 17))
        else:
            self._empty(allocation, "NO EXPOSURE", "Capital is fully liquid", "Search for a symbol in Trade when you have a thesis worth testing.")

        signal = self._panel(split)
        signal.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        ctk.CTkLabel(
            signal,
            text="LOCAL SIGNAL ENGINE",
            anchor="w",
            font=(MONO, 10, "bold"),
            text_color=COLORS["accent"],
        ).pack(fill="x", padx=18, pady=(17, 2))
        ctk.CTkLabel(
            signal,
            text="Portfolio brief",
            anchor="w",
            font=(FONT, 18, "bold"),
            text_color=COLORS["text"],
        ).pack(fill="x", padx=18, pady=(0, 14))
        ctk.CTkLabel(
            signal,
            text=analysis["brief"],
            anchor="w",
            justify="left",
            wraplength=300,
            font=(FONT, 13),
            text_color=COLORS["muted"],
        ).pack(fill="x", padx=18)
        ctk.CTkLabel(
            signal,
            text="CONCENTRATION",
            anchor="w",
            font=(MONO, 9, "bold"),
            text_color=COLORS["faint"],
        ).pack(fill="x", padx=18, pady=(24, 7))
        risk = ctk.CTkProgressBar(
            signal,
            height=8,
            progress_color=(
                COLORS["loss"] if analysis["concentration"] >= 0.6 else COLORS["accent"]
            ),
            fg_color=COLORS["line"],
        )
        risk.pack(fill="x", padx=18)
        risk.set(analysis["concentration"])
        ctk.CTkLabel(
            signal,
            text="Deterministic read · Not investment advice",
            anchor="w",
            font=(FONT, 9),
            text_color=COLORS["faint"],
        ).pack(fill="x", padx=18, pady=(10, 17))

        positions = self._panel(page)
        positions.pack(fill="x")
        self._positions_table(positions, analysis["positions"], limit=5)

    def _positions_table(self, parent, positions, limit=None, include_actions=False):
        ctk.CTkLabel(
            parent,
            text="OPEN POSITIONS",
            anchor="w",
            font=(MONO, 10, "bold"),
            text_color=COLORS["muted"],
        ).pack(fill="x", padx=18, pady=(17, 4))
        if not positions:
            self._empty(parent, "EMPTY BOOK", "No positions yet", "Your first filled paper order will appear here.")
            return

        table = ctk.CTkFrame(parent, fg_color="transparent")
        table.pack(fill="x", padx=18, pady=(7, 15))
        columns = ["SYMBOL", "SHARES", "AVG COST", "LAST", "VALUE", "P/L"]
        if include_actions:
            columns.append("")
        for column in range(len(columns)):
            table.grid_columnconfigure(column, weight=1)
        for column, title in enumerate(columns):
            ctk.CTkLabel(
                table,
                text=title,
                anchor="w" if column == 0 else "e",
                font=(MONO, 9, "bold"),
                text_color=COLORS["faint"],
            ).grid(row=0, column=column, sticky="ew", padx=6, pady=(0, 9))

        for row_index, position in enumerate(positions[:limit] if limit else positions, start=1):
            values = [
                position["symbol"],
                str(position["quantity"]),
                format_money(position["average_price"]),
                format_money(position["live_price"]),
                format_money(position["market_value"]),
                format_signed_money(position["unrealized_pl"]),
            ]
            for column, value in enumerate(values):
                tone = COLORS["text"]
                if column == 5:
                    tone = COLORS["cyan"] if position["unrealized_pl"] >= 0 else COLORS["loss"]
                ctk.CTkLabel(
                    table,
                    text=value,
                    anchor="w" if column == 0 else "e",
                    font=(MONO, 10, "bold" if column == 0 else "normal"),
                    text_color=tone,
                ).grid(row=row_index, column=column, sticky="ew", padx=6, pady=9)
            if include_actions:
                ctk.CTkButton(
                    table,
                    text="SELL",
                    width=58,
                    height=28,
                    fg_color=COLORS["panel_alt"],
                    hover_color=COLORS["line"],
                    text_color=COLORS["warning"],
                    font=(MONO, 9, "bold"),
                    command=lambda selected=position: self._sell_position(selected),
                ).grid(row=row_index, column=6, sticky="e", padx=6, pady=5)

    def _refresh_prices(self):
        holdings = Portfolio(self.user.id).get_portfolio()
        symbols = [holding[0] for holding in holdings]
        if not symbols:
            return

        def load():
            prices = {}
            for symbol in symbols:
                quote = StockAPI.get_stock(symbol)
                if quote:
                    prices[symbol] = quote["price"]
            return prices

        def done(prices):
            self.live_prices.update(prices or {})
            if self.current_page == "overview":
                self.show_page("overview")

        self._run_async(load, done)

    def _build_trade(self):
        page = self._page()
        self._heading(
            page,
            "EXECUTION DESK",
            "Research. Size. Execute.",
            "Paper orders use the latest available close and settle immediately.",
        )

        search = self._panel(page)
        search.pack(fill="x", pady=(0, 12))
        search.grid_columnconfigure(0, weight=1)
        self.trade_symbol = ctk.CTkEntry(
            search,
            height=46,
            placeholder_text="Enter a symbol — AAPL, NVDA, MSFT",
            fg_color=COLORS["panel_alt"],
            border_color=COLORS["line"],
            font=(MONO, 12, "bold"),
        )
        self.trade_symbol.grid(row=0, column=0, sticky="ew", padx=(16, 8), pady=16)
        self.trade_symbol.bind("<Return>", lambda _event: self._search_quote())
        self.quote_button = ctk.CTkButton(
            search,
            text="LOAD QUOTE",
            width=132,
            height=46,
            command=self._search_quote,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["canvas"],
            font=(MONO, 10, "bold"),
        )
        self.quote_button.grid(row=0, column=1, padx=(0, 16), pady=16)

        shortcuts = ctk.CTkFrame(page, fg_color="transparent")
        shortcuts.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            shortcuts,
            text="QUICK LOAD",
            font=(MONO, 9, "bold"),
            text_color=COLORS["faint"],
        ).pack(side="left", padx=(2, 10))
        for symbol in ["AAPL", "MSFT", "NVDA", "AMD", "TSLA"]:
            ctk.CTkButton(
                shortcuts,
                text=symbol,
                width=62,
                height=28,
                fg_color="transparent",
                hover_color=COLORS["panel_alt"],
                border_width=1,
                border_color=COLORS["line"],
                text_color=COLORS["muted"],
                font=(MONO, 9, "bold"),
                command=lambda ticker=symbol: self._load_shortcut(ticker),
            ).pack(side="left", padx=3)

        body = ctk.CTkFrame(page, fg_color="transparent")
        body.pack(fill="x")
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        self.quote_result = self._panel(body)
        self.quote_result.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.order_ticket = self._panel(body)
        self.order_ticket.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self._render_quote()
        self.trade_symbol.focus_set()

    def _load_shortcut(self, symbol):
        self.trade_symbol.delete(0, "end")
        self.trade_symbol.insert(0, symbol)
        self._search_quote()

    def _search_quote(self):
        symbol = self.trade_symbol.get().strip()
        if not symbol:
            self._trade_message("Enter a symbol to load a quote.", COLORS["warning"])
            return
        self.quote_button.configure(state="disabled", text="LOADING…")

        def done(quote):
            if self.current_page != "trade":
                return
            self.quote_button.configure(state="normal", text="LOAD QUOTE")
            self.active_quote = quote
            self._render_quote()

        self._run_async(lambda: StockAPI.get_stock(symbol), done)

    def _render_quote(self):
        clear(self.quote_result)
        clear(self.order_ticket)
        if not self.active_quote:
            self._empty(
                self.quote_result,
                "QUOTE FEED",
                "Awaiting a symbol",
                "Load a ticker to inspect the latest close and prepare a paper order.",
            )
            self._empty(
                self.order_ticket,
                "ORDER TICKET",
                "No active quote",
                "Quantity and buying power controls appear after a valid quote.",
            )
            return

        quote = self.active_quote
        ctk.CTkLabel(
            self.quote_result,
            text="LATEST AVAILABLE QUOTE",
            anchor="w",
            font=(MONO, 10, "bold"),
            text_color=COLORS["cyan"],
        ).pack(fill="x", padx=22, pady=(22, 7))
        ctk.CTkLabel(
            self.quote_result,
            text=quote["symbol"],
            anchor="w",
            font=(MONO, 36, "bold"),
            text_color=COLORS["text"],
        ).pack(fill="x", padx=22)
        ctk.CTkLabel(
            self.quote_result,
            text=quote["name"],
            anchor="w",
            font=(FONT, 14),
            text_color=COLORS["muted"],
        ).pack(fill="x", padx=22, pady=(2, 28))
        ctk.CTkLabel(
            self.quote_result,
            text=format_money(quote["price"]),
            anchor="w",
            font=(FONT, 46, "bold"),
            text_color=COLORS["accent"],
        ).pack(fill="x", padx=22)
        ctk.CTkLabel(
            self.quote_result,
            text="Latest close · Data may be delayed",
            anchor="w",
            font=(FONT, 10),
            text_color=COLORS["faint"],
        ).pack(fill="x", padx=22, pady=(4, 24))

        ctk.CTkLabel(
            self.order_ticket,
            text="BUY ORDER",
            anchor="w",
            font=(MONO, 10, "bold"),
            text_color=COLORS["accent"],
        ).pack(fill="x", padx=20, pady=(20, 16))
        ctk.CTkLabel(
            self.order_ticket,
            text="QUANTITY",
            anchor="w",
            font=(MONO, 9),
            text_color=COLORS["muted"],
        ).pack(fill="x", padx=20, pady=(0, 6))
        self.order_quantity = ctk.CTkEntry(
            self.order_ticket,
            height=44,
            placeholder_text="Whole shares",
            fg_color=COLORS["panel_alt"],
            border_color=COLORS["line"],
            font=(MONO, 12),
        )
        self.order_quantity.pack(fill="x", padx=20)
        self.order_quantity.bind("<KeyRelease>", lambda _event: self._update_order_total())
        self.order_quantity.bind("<Return>", lambda _event: self._buy_quote())
        self.order_total = ctk.CTkLabel(
            self.order_ticket,
            text="EST. TOTAL  —",
            anchor="w",
            font=(MONO, 10, "bold"),
            text_color=COLORS["text"],
        )
        self.order_total.pack(fill="x", padx=20, pady=(16, 4))
        ctk.CTkLabel(
            self.order_ticket,
            text=f"BUYING POWER  {format_money(self.user.balance)}",
            anchor="w",
            font=(MONO, 9),
            text_color=COLORS["muted"],
        ).pack(fill="x", padx=20)
        self.order_status = ctk.CTkLabel(
            self.order_ticket,
            text="",
            anchor="w",
            wraplength=330,
            font=(FONT, 11),
            text_color=COLORS["loss"],
        )
        self.order_status.pack(fill="x", padx=20, pady=(12, 0))
        ctk.CTkButton(
            self.order_ticket,
            text=f"BUY {quote['symbol']}  →",
            height=46,
            command=self._buy_quote,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["canvas"],
            font=(MONO, 11, "bold"),
        ).pack(fill="x", padx=20, pady=(14, 20))
        self.order_quantity.focus_set()

    def _trade_message(self, message, tone):
        if hasattr(self, "order_status") and self.order_status.winfo_exists():
            self.order_status.configure(text=message, text_color=tone)

    def _update_order_total(self):
        try:
            quantity = int(self.order_quantity.get())
            total = self.active_quote["price"] * quantity
            text = f"EST. TOTAL  {format_money(total)}" if quantity > 0 else "EST. TOTAL  —"
        except ValueError:
            text = "EST. TOTAL  —"
        self.order_total.configure(text=text)

    def _buy_quote(self):
        try:
            quantity = int(self.order_quantity.get())
        except ValueError:
            self._trade_message("Enter a positive whole-share quantity.", COLORS["loss"])
            return
        quote = self.active_quote
        stock = Stock(quote["symbol"], quote["name"], quote["price"])
        if not self.user.buy_stock(stock, quantity):
            self._trade_message("Order rejected. Check quantity and buying power.", COLORS["loss"])
            return
        self.live_prices[stock.symbol] = stock.price
        self._trade_message(
            f"Filled {quantity} {stock.symbol} at {format_money(stock.price)}.", COLORS["cyan"]
        )
        self.order_quantity.delete(0, "end")
        self._update_order_total()

    def _build_portfolio(self):
        page = self._page()
        self._heading(
            page,
            "POSITION CONTROL",
            "Know what you own.",
            "Average cost, marked value, and exits in one place.",
        )
        analysis = self._portfolio_analysis()
        metrics = ctk.CTkFrame(page, fg_color="transparent")
        metrics.pack(fill="x", pady=(0, 12))
        for column in range(3):
            metrics.grid_columnconfigure(column, weight=1)
        self._metric(metrics, 0, "POSITIONS", str(len(analysis["positions"])), "Distinct holdings")
        self._metric(metrics, 1, "MARKED VALUE", format_money(analysis["invested"]), "Latest loaded prices")
        self._metric(
            metrics,
            2,
            "OPEN P/L",
            format_signed_money(analysis["unrealized_pl"]),
            "Versus weighted average cost",
            COLORS["cyan"] if analysis["unrealized_pl"] >= 0 else COLORS["loss"],
        )
        self.portfolio_status = ctk.CTkLabel(
            page,
            text="",
            anchor="w",
            font=(FONT, 11),
            text_color=COLORS["cyan"],
        )
        self.portfolio_status.pack(fill="x", pady=(0, 8))
        panel = self._panel(page)
        panel.pack(fill="x")
        self._positions_table(panel, analysis["positions"], include_actions=True)

    def _sell_position(self, position):
        dialog = ctk.CTkInputDialog(
            title=f"Sell {position['symbol']}",
            text=f"Shares to sell (owned: {position['quantity']}):",
        )
        raw_quantity = dialog.get_input()
        if raw_quantity is None:
            return
        try:
            quantity = int(raw_quantity)
        except ValueError:
            self.portfolio_status.configure(
                text="Enter a positive whole-share quantity.",
                text_color=COLORS["loss"],
            )
            return
        stock = Stock(position["symbol"], position["name"], position["live_price"])
        if not self.user.sell_stock(stock, quantity):
            self.portfolio_status.configure(
                text="Sell rejected. Check the quantity and position size.",
                text_color=COLORS["loss"],
            )
            return
        self.show_page("portfolio")

    def _build_activity(self):
        page = self._page()
        self._heading(
            page,
            "AUDIT TRAIL",
            "Every decision leaves a record.",
            "A reverse-chronological ledger of filled paper orders.",
        )
        transactions = self.user.transaction_history.get_transactions()
        panel = self._panel(page)
        panel.pack(fill="x")
        if not transactions:
            self._empty(panel, "NO FILLS", "The ledger is clean", "Completed paper orders will appear here with their execution time and price.")
            return

        ctk.CTkLabel(
            panel,
            text=f"ORDER LEDGER  /  {len(transactions)} FILLS",
            anchor="w",
            font=(MONO, 10, "bold"),
            text_color=COLORS["muted"],
        ).pack(fill="x", padx=18, pady=(17, 10))
        table = ctk.CTkFrame(panel, fg_color="transparent")
        table.pack(fill="x", padx=18, pady=(0, 16))
        columns = ["SIDE", "SYMBOL", "QUANTITY", "PRICE", "EXECUTED"]
        for column in range(5):
            table.grid_columnconfigure(column, weight=1)
        for column, title in enumerate(columns):
            ctk.CTkLabel(
                table,
                text=title,
                anchor="w" if column < 2 else "e",
                font=(MONO, 9, "bold"),
                text_color=COLORS["faint"],
            ).grid(row=0, column=column, sticky="ew", padx=8, pady=(0, 8))
        for row, trade in enumerate(transactions, start=1):
            values = [
                trade["type"],
                trade["stock"],
                str(trade["quantity"]),
                format_money(trade["price"]),
                trade["timestamp"],
            ]
            for column, value in enumerate(values):
                tone = COLORS["text"]
                if column == 0:
                    tone = COLORS["cyan"] if trade["type"] == "BUY" else COLORS["warning"]
                ctk.CTkLabel(
                    table,
                    text=value,
                    anchor="w" if column < 2 else "e",
                    font=(MONO, 10, "bold" if column in (0, 1) else "normal"),
                    text_color=tone,
                ).grid(row=row, column=column, sticky="ew", padx=8, pady=9)

    def _build_research(self):
        page = self._page()
        self._heading(
            page,
            "PRICE RESEARCH",
            "Interrogate the trend.",
            "A clean closing-price view for validating a trade thesis.",
        )
        tools = self._panel(page)
        tools.pack(fill="x", pady=(0, 12))
        tools.grid_columnconfigure(0, weight=1)
        self.research_symbol = ctk.CTkEntry(
            tools,
            height=44,
            placeholder_text="Symbol",
            fg_color=COLORS["panel_alt"],
            border_color=COLORS["line"],
            font=(MONO, 11, "bold"),
        )
        self.research_symbol.grid(row=0, column=0, sticky="ew", padx=(16, 8), pady=16)
        self.research_symbol.bind("<Return>", lambda _event: self._load_research())
        self.research_period = ctk.CTkSegmentedButton(
            tools,
            values=["1M", "3M", "1Y"],
            fg_color=COLORS["panel_alt"],
            selected_color=COLORS["line"],
            selected_hover_color=COLORS["faint"],
            unselected_color=COLORS["panel_alt"],
            unselected_hover_color=COLORS["line"],
            text_color=COLORS["text"],
            font=(MONO, 9, "bold"),
        )
        self.research_period.set("1M")
        self.research_period.grid(row=0, column=1, padx=8, pady=16)
        self.research_button = ctk.CTkButton(
            tools,
            text="RUN STUDY",
            width=120,
            height=44,
            command=self._load_research,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["canvas"],
            font=(MONO, 10, "bold"),
        )
        self.research_button.grid(row=0, column=2, padx=(8, 16), pady=16)

        self.research_chart = self._panel(page)
        self.research_chart.pack(fill="both", expand=True)
        self._empty(
            self.research_chart,
            "RESEARCH CANVAS",
            "Choose a symbol and horizon",
            "The latest daily closing series will render here without changing your positions.",
        )
        self.research_symbol.focus_set()

    def _load_research(self):
        symbol = self.research_symbol.get().strip().upper()
        if not symbol:
            return
        period = {"1M": "1mo", "3M": "3mo", "1Y": "1y"}[self.research_period.get()]
        self.research_button.configure(state="disabled", text="LOADING…")

        def done(history):
            if self.current_page != "research":
                return
            self.research_button.configure(state="normal", text="RUN STUDY")
            self._render_research(symbol, history)

        self._run_async(lambda: StockAPI.get_history(symbol, period), done)

    def _render_research(self, symbol, history):
        clear(self.research_chart)
        if history is None:
            self._empty(
                self.research_chart,
                "NO DATA",
                f"Could not load {symbol}",
                "Check the symbol or your network connection, then run the study again.",
            )
            return

        closes = history["Close"]
        first, last = float(closes.iloc[0]), float(closes.iloc[-1])
        change = (last / first - 1) * 100 if first else 0
        summary = ctk.CTkFrame(self.research_chart, fg_color="transparent")
        summary.pack(fill="x", padx=20, pady=(18, 0))
        ctk.CTkLabel(
            summary,
            text=symbol,
            font=(MONO, 20, "bold"),
            text_color=COLORS["text"],
        ).pack(side="left")
        ctk.CTkLabel(
            summary,
            text=format_money(last),
            font=(FONT, 22, "bold"),
            text_color=COLORS["text"],
        ).pack(side="left", padx=18)
        ctk.CTkLabel(
            summary,
            text=f"{change:+.2f}%",
            font=(MONO, 11, "bold"),
            text_color=COLORS["cyan"] if change >= 0 else COLORS["loss"],
        ).pack(side="left")

        figure = Figure(figsize=(9, 4.8), dpi=100, facecolor=COLORS["panel"])
        axis = figure.add_subplot(111)
        axis.set_facecolor(COLORS["panel"])
        axis.plot(history.index, closes, color=COLORS["accent"], linewidth=2)
        axis.fill_between(history.index, closes, min(closes), color=COLORS["accent"], alpha=0.07)
        axis.spines[["top", "right", "left"]].set_visible(False)
        axis.spines["bottom"].set_color(COLORS["line"])
        axis.tick_params(axis="x", colors=COLORS["muted"], labelsize=8, length=0)
        axis.tick_params(axis="y", colors=COLORS["muted"], labelsize=8, length=0)
        axis.grid(axis="y", color=COLORS["line"], linewidth=0.7, alpha=0.7)
        axis.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        figure.tight_layout(pad=2)

        canvas = FigureCanvasTkAgg(figure, master=self.research_chart)
        canvas.draw()
        canvas.get_tk_widget().configure(bg=COLORS["panel"], highlightthickness=0)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _run_async(self, job, on_success):
        def run():
            try:
                result = job()
            except Exception:
                result = None
            self.after(0, lambda: on_success(result))

        threading.Thread(target=run, daemon=True).start()


if __name__ == "__main__":
    initialize_database()
    app = StockTradingApp()
    app.mainloop()
