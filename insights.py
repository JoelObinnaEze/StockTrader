def analyse_portfolio(holdings, cash, live_prices):
    positions = []
    for symbol, name, quantity, average_price in holdings:
        live_price = live_prices.get(symbol, average_price)
        market_value = quantity * live_price
        positions.append(
            {
                "symbol": symbol,
                "name": name,
                "quantity": quantity,
                "average_price": average_price,
                "live_price": live_price,
                "market_value": market_value,
                "unrealized_pl": quantity * (live_price - average_price),
            }
        )

    positions.sort(key=lambda position: position["market_value"], reverse=True)
    invested = sum(position["market_value"] for position in positions)
    unrealized_pl = sum(position["unrealized_pl"] for position in positions)
    concentration = positions[0]["market_value"] / invested if invested else 0
    cash_ratio = cash / (cash + invested) if cash + invested else 0

    if not positions:
        brief = "Your capital is fully liquid. Research a symbol before you deploy it."
    elif concentration >= 0.6:
        brief = (
            f"{positions[0]['symbol']} drives {concentration:.0%} of invested value. "
            "Your next trade should reduce, not deepen, that concentration."
        )
    elif cash_ratio >= 0.5:
        brief = (
            f"Cash is {cash_ratio:.0%} of net worth. You have room to act without "
            "forcing a sale."
        )
    else:
        brief = "Exposure is distributed and capital is mostly deployed. Stay selective."

    return {
        "positions": positions,
        "allocation": [
            (position["symbol"], position["market_value"] / invested)
            for position in positions
        ],
        "cash": cash,
        "invested": invested,
        "net_worth": cash + invested,
        "unrealized_pl": unrealized_pl,
        "concentration": concentration,
        "brief": brief,
    }
