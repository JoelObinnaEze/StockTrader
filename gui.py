import customtkinter as ctk
from user import User
from stock_api import StockAPI
from stock import Stock
from portfolio import Portfolio
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from price import get_stock_price
import yfinance as yf
import matplotlib.dates as mdates

class StockTradingApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.user = None
        self.login_screen()
        self.title("\U0001F4B0 Stock Trading Simulator")
        self.geometry("800x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.current_frame = None

    def login_screen(self):
        self.clear_screen()

        login_frame = ctk.CTkFrame(self)
        login_frame.pack(pady=80, padx=60, fill="both", expand=True)

        ctk.CTkLabel(login_frame, text="Welcome to StockSim!", font=("Arial", 24, "bold")).pack(pady=20)

        ctk.CTkLabel(login_frame, text="Username:").pack(pady=(10, 5))
        username_entry = ctk.CTkEntry(login_frame)
        username_entry.pack()

        ctk.CTkLabel(login_frame, text="Password:").pack(pady=(20, 5))
        password_entry = ctk.CTkEntry(login_frame, show="*")
        password_entry.pack()

        caps_warning = ctk.CTkLabel(login_frame, text="", text_color="yellow")
        caps_warning.pack(pady=5)

        def check_caps_lock(event):
            char = event.char
            shift_pressed = event.state & 0x0001
            if char.isalpha():
                if char.isupper() and not shift_pressed:
                    caps_warning.configure(text="Warning: CAPS LOCK is ON")
                elif char.islower() and shift_pressed:
                    caps_warning.configure(text="Warning: CAPS LOCK is ON")
                else:
                    caps_warning.configure(text="")
            else:
                caps_warning.configure(text="")

        password_entry.bind("<KeyRelease>", check_caps_lock)
        password_entry.bind("<FocusIn>", lambda e: caps_warning.configure(text=""))

        error_label = ctk.CTkLabel(login_frame, text="", text_color="red")
        error_label.pack()

        def final_login(username, password):
            if User.login(username, password) is not False:
                self.login(username, password)
            else:
                error_label.configure(text="\u274C Invalid login")

        def final_register(username, password):
            if User.register(username, password) is not False:
                self.register(username, password)
            else:
                error_label.configure(text="\u26A0 Username already exists")

        button_frame = ctk.CTkFrame(login_frame)
        button_frame.pack(pady=20)

        ctk.CTkButton(button_frame, text="Login", width=140,
                      command=lambda: final_login(username_entry.get(), password_entry.get())).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Register", width=140,
                      command=lambda: final_register(username_entry.get(), password_entry.get())).pack(side="left", padx=10)


    def login(self, username, password):
        user = User.login(username, password)
        if user:
            self.user = user
            self.show_dashboard()

    def register(self, username, password):
        user = User.register(username, password)
        if user:
            self.user = user
            self.show_dashboard()

    def logout(self):
        self.user = None
        self.login_screen()
                
    def show_dashboard(self):
        self.clear_screen()
        self.create_navbar()
        self.show_frame(self.dashboard_frame)


    def show_dash(self):
        self.clear_screen()
        self.create_navbar()

        

    def search_stock(self, symbol):
        stock_data = StockAPI.get_stock(symbol)
        if stock_data:
            stock = Stock(stock_data['symbol'], stock_data['name'], stock_data['price'])
            self.search_result.configure(text=f"{stock.symbol} ({stock.name}) - ${stock.price:.2f}", fg_color="transparent")

            # If button already exists, update it
            if hasattr(self, "buy_button") and self.buy_button.winfo_exists():
                self.buy_button.configure(text=f"Buy {stock.symbol}",
                                        command=lambda: self.buy_stock(stock))
            else:
                # If `self.buy_button` does NOT exist, create it
                self.buy_button = ctk.CTkButton(self.search_frame, 
                                                text=f"Buy {stock.symbol}", 
                                                command=lambda: self.buy_stock(stock))
                self.buy_button.pack(pady = 10)
        else:
            self.search_result.configure(text="Stock not found.", fg_color="red")

    def buy_stock(self, stock):
            # Create an input dialog to ask for quantity
            dialog = ctk.CTkInputDialog(title="Buy Stock", text="Enter quantity:")
            quantity = dialog.get_input()

            if quantity:
                try:
                    quantity = int(quantity)  # Ensure input is an integer
                    success = self.user.buy_stock(stock, quantity)
                    if success:
                        ctk.CTkLabel(self, text=f"Bought {quantity} shares of {stock.symbol}", fg_color="green").pack()
                        self.show_dashboard()
                    else:
                        ctk.CTkLabel(self, text="Insufficient balance", fg_color="red").pack()
                except ValueError:
                    ctk.CTkLabel(self, text="Invalid input. Please enter a number.", fg_color="red").pack()

    def show_portfolio(self):
        for widget in self.portfolio_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self, text="Portfolio").pack()
        self.message_label = ctk.CTkLabel(self.portfolio_frame, text="", anchor="s")
        self.message_label.pack(pady=5)

        portfolio = Portfolio(self.user.id)
        stocks = portfolio.get_portfolio()

        if stocks:
            for stock in stocks:
                symbol, name, quantity, price = stock
                value = quantity * price
                label = ctk.CTkLabel(self, text=f"{symbol} ({name}): {quantity} @ ${price:.2f} = ${value:.2f}")
                label.pack()

                # Sell button for each stock
                sell_button = ctk.CTkButton(self, text=f"Sell {symbol}", 
                                        command=lambda s=symbol, q=quantity: self.sell_stock(s, q))
                sell_button.pack()
        else:
            ctk.CTkLabel(self, text="No stocks in portfolio.").pack()

    def show_transaction_history(self):
        for widget in self.history_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self, text="Transaction History", font=("Arial", 20)).pack(pady=10)

        transactions = self.user.transaction_history.get_transactions()

        if not transactions:
            ctk.CTkLabel(self, text="No transactions found.").pack(pady=5)
            return

        # Create a frame to hold the transactions
        frame = ctk.CTkScrollableFrame(self, height=400)
        frame.pack(expand=True, fill="both", pady=10)

        for transaction in transactions:
            text = f"{transaction['timestamp']}: {transaction['type']} {transaction['quantity']} x {transaction['stock']} @ ${transaction['price']:.2f}"
            ctk.CTkLabel(frame, text=text, anchor="w").pack(fill="x", pady=2)


    def sell_stock(self, symbol, owned):
        # Clear any previous message
        self.message_label.configure(text="")

        # Create an input dialog to ask for quantity
        stock_data = StockAPI.get_stock(symbol)
        if stock_data:
            stock = Stock(stock_data['symbol'], stock_data['name'], stock_data['price'])

        dialog = ctk.CTkInputDialog(title="Sell Stock", text=f"Enter quantity to sell ({symbol}):")
        quantity = dialog.get_input()

        if quantity:
            try:
                quantity = int(quantity)
                if quantity > owned:
                    self.message_label.configure(
                        text="You cannot sell more than you own.",
                        fg_color="red"
                    )
                    self.after(3000, lambda: self.message_label.configure(text="", fg_color="transparent"))
                    return

                success = self.user.sell_stock(stock, quantity)
                if success:
                    self.show_dashboard()
                else:
                    self.message_label.configure(
                        text="Invalid quantity",
                        fg_color="red"
                    )
                    self.after(3000, lambda: self.message_label.configure(text="", fg_color="transparent"))
            except ValueError:
                self.message_label.configure(
                    text="Invalid input. Please enter a number.",
                    fg_color="red"
                )
                self.after(3000, lambda: self.message_label.configure(text="", fg_color="transparent"))

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    def create_navbar(self):
        navbar = ctk.CTkFrame(self, height=40)
        navbar.pack(side="top", fill="x")

        self.nav_buttons = {}  # Store button references

        def select_button(selected_btn):
            """Highlight the selected button and reset others."""
            for btn in self.nav_buttons.values():
                btn.configure(fg_color="gray")  # Reset all buttons
            selected_btn.configure(fg_color="#007BFF")  # Highlight selected

        # Navigation Buttons
        self.nav_buttons['dashboard'] = ctk.CTkButton(navbar, text="Dashboard",
            command=lambda: [self.show_dash(), self.show_frame(self.dashboard_frame, load_dashboard=True), select_button(self.nav_buttons['dashboard'])])
        
        self.nav_buttons['portfolio'] = ctk.CTkButton(navbar, text="Portfolio",
            command=lambda: [self.show_dash(), self.show_frame(self.portfolio_frame, load_portfolio=True), select_button(self.nav_buttons['portfolio'])])
        
        self.nav_buttons['search'] = ctk.CTkButton(navbar, text="Buy Stocks",
            command=lambda: [self.show_dash(), self.show_frame(self.search_frame), select_button(self.nav_buttons['search'])])
        
        self.nav_buttons['history'] = ctk.CTkButton(navbar, text="Transaction History",
            command=lambda: [self.show_dash(), self.show_frame(self.history_frame, load_history=True), select_button(self.nav_buttons['history'])])
        
        self.nav_buttons['growth'] = ctk.CTkButton(navbar, text="Stock Growth",
            command=lambda: [self.show_dash(), self.show_frame(self.growth_frame, load_growth=True), select_button(self.nav_buttons['growth'])])
        
        # Layout
        for i, key in enumerate(self.nav_buttons):
            self.nav_buttons[key].pack(side="left", padx=10, pady=5, expand=True, fill="both")

        # Logout button
        self.logout_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        self.logout_frame.pack(side="bottom", anchor="e", padx=10, pady=10)
        ctk.CTkButton(self.logout_frame, text="Logout", command=self.logout, fg_color="red").pack(anchor="e")

        # Select default button (Dashboard)
        select_button(self.nav_buttons['dashboard'])

        # Create frames for each section
        self.dashboard_frame = self.create_dashboard_frame()
        self.portfolio_frame = self.create_portfolio_frame()
        self.search_frame = self.create_search_frame()
        self.history_frame = self.create_history_frame()
        self.growth_frame = self.create_growth_frame()


    def create_dashboard_frame(self):        
        frame = ctk.CTkFrame(self, width=800, height=500)
        frame.pack_propagate(False)
        
        ctk.CTkLabel(frame, text="DASHBOARD", font=("Arial", 16, "bold")).pack(pady=5)
        balance_label = ctk.CTkLabel(frame, text=f"Account Balance: ${self.user.balance:.2f}", font=("Arial", 16, "bold"))
        balance_label.pack(pady=5)

        portfolio = Portfolio(self.user.id)
        stocks = portfolio.get_portfolio()
        
        if not stocks:
            ctk.CTkLabel(frame, text="No stocks in portfolio.").pack()
            return frame
             
        stock_values = []
        stock_labels = []
        
        for stock in stocks:
            symbol, name, quantity, price = stock
            value = quantity * price
            stock_values.append(value)
            stock_labels.append(f"{symbol} ({name})")
            
            live_price = float(get_stock_price(symbol))

            if live_price != "N/A":
                pl = (live_price - price) * quantity  # Profit/Loss calculation
            else:
                pl = "N/A"

            stock_info = f"{name} ({symbol}) | Qty: {quantity} | Buy: {price:.2f} | Live: {live_price} | P/L: {pl}"
            stock_label = ctk.CTkLabel(frame, text=stock_info, font=("Arial", 14), text_color="white")
            stock_label.pack()
        
        # Create Matplotlib pie chart
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.pie(stock_values, labels=stock_labels, autopct='%1.1f%%', startangle=140)
        ax.set_title("Portfolio Distribution")
        
        chart_canvas = FigureCanvasTkAgg(fig, master=frame)
        chart_canvas.draw()
        chart_canvas.get_tk_widget().pack(pady=10)
        
        return frame

    def show_growth(self):
        for widget in self.portfolio_frame.winfo_children():
            widget.destroy()

        frame = self.growth_frame

        ctk.CTkLabel(frame, text="Stock Growth", font=("Arial", 18, "bold")).pack(pady=10)

        input_frame = ctk.CTkFrame(frame)
        input_frame.pack(pady=5)

        ctk.CTkLabel(input_frame, text="Stock Symbol:").pack(side="left", padx=(0, 10))
        symbol_entry = ctk.CTkEntry(input_frame)
        symbol_entry.pack(side="left")

        error_label = ctk.CTkLabel(frame, text="", text_color="red")
        error_label.pack()

        chart_canvas_container = ctk.CTkFrame(frame)
        chart_canvas_container.pack(fill="both", expand=True, pady=5)

        def plot_growth(symbol):
            symbol = symbol.upper()
            try:
                stock_data = yf.download(symbol, period="1mo", interval="1d")

                if stock_data.empty:
                    error_label.configure(text="No data found for this symbol.")
                    return

                plt.figure(figsize=(8, 4))
                plt.plot(stock_data.index, stock_data['Close'], marker='o', linestyle='-', color='cyan')
                plt.title(f"{symbol} Price Over Last Month")
                plt.xlabel("Date")
                plt.ylabel("Closing Price")
                plt.grid(True)
                
                # Format x-axis dates
                ax = plt.gca()
                ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))  # Show one label per week
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))    # Format as 'Apr 10'
                plt.xticks(rotation=0)

                # Clear old canvas
                for widget in chart_canvas_container.winfo_children():
                    widget.destroy()

                fig = plt.gcf()
                canvas = FigureCanvasTkAgg(fig, master=chart_canvas_container)
                canvas.draw()
                canvas.get_tk_widget().pack()

                error_label.configure(text="")  # Clear error
            except Exception as e:
                error_label.configure(text=f"Error: {str(e)}")

        ctk.CTkButton(frame, text="Show Growth", command=lambda: plot_growth(symbol_entry.get())).pack(pady=5)


        
    def create_portfolio_frame(self):
        frame = ctk.CTkFrame(self, width=800, height=500)
        return frame
    
    def create_growth_frame(self):
        frame = ctk.CTkFrame(self, width=800, height=500)
        return frame
        
    def create_search_frame(self):
        frame = ctk.CTkFrame(self, width=800, height=500)
        self.search_result = ctk.CTkLabel(frame, text="")
        self.search_result.pack()
        self.search_entry = ctk.CTkEntry(frame) 
        self.search_entry.pack()
        ctk.CTkButton(frame, text="Search Stock", command=lambda: self.search_stock(self.search_entry.get())).pack()
        return frame
        
    def create_history_frame(self):
        frame = ctk.CTkFrame(self, width=800, height=500)
        return frame

    def show_frame(self, frame, load_portfolio=False, load_history=False, load_dashboard=False, load_growth=False):
        # Forget the current frame
        if self.current_frame is not None:
            self.current_frame.pack_forget()

        # Load data only when necessary
        if load_portfolio and frame == self.portfolio_frame:
            self.show_portfolio()

        if load_history and frame == self.history_frame:
            self.show_transaction_history()

        if load_dashboard and frame == self.dashboard_frame:
            self.show_dashboard()

        if load_growth and frame == self.growth_frame:
            self.show_growth()

        frame.pack(expand=True, fill="both")
        self.current_frame = frame

if __name__ == "__main__":
    app = StockTradingApp()
    app.mainloop()
