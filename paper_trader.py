"""
paper_trader.py  —  Simple paper trading engine (no real money).
"""

from datetime import datetime


class PaperTrader:
    def __init__(self, balance=10_000.0):
        self.state = {
            "balance":         balance,
            "initial_balance": balance,
            "positions":       {},   # pair -> {qty, avg_entry}
            "trades":          [],
            "realized_pnl":    0.0,
        }

    def load(self, state):
        self.state = state

    def dump(self):
        return self.state

    # ── BUY ──────────────────────────────────────────────────────────────────
    def buy(self, pair, price, usd_amount, signal):
        usd_amount = min(usd_amount, self.state["balance"])
        if usd_amount <= 0:
            return {"ok": False, "msg": "No balance"}

        fee = usd_amount * 0.0026
        qty = (usd_amount - fee) / price
        self.state["balance"] -= usd_amount

        pos = self.state["positions"]
        if pair in pos:
            total = pos[pair]["qty"] + qty
            avg   = (pos[pair]["qty"] * pos[pair]["avg_entry"] + qty * price) / total
            pos[pair] = {"qty": total, "avg_entry": avg}
        else:
            pos[pair] = {"qty": qty, "avg_entry": price}

        trade = self._record("BUY", pair, price, qty, usd_amount, fee, 0, signal)
        return {"ok": True, "trade": trade}

    # ── SELL ─────────────────────────────────────────────────────────────────
    def sell(self, pair, price, signal):
        pos = self.state["positions"]
        if pair not in pos:
            return {"ok": False, "msg": f"No position in {pair}"}

        qty   = pos[pair]["qty"]
        gross = qty * price
        fee   = gross * 0.0026
        net   = gross - fee
        pnl   = net - qty * pos[pair]["avg_entry"]

        self.state["balance"]      += net
        self.state["realized_pnl"] += pnl
        del pos[pair]

        trade = self._record("SELL", pair, price, qty, net, fee, pnl, signal)
        return {"ok": True, "trade": trade, "pnl": pnl}

    # ── HELPERS ──────────────────────────────────────────────────────────────
    def _record(self, typ, pair, price, qty, usd, fee, pnl, signal):
        t = {
            "id":         len(self.state["trades"]) + 1,
            "type":       typ,
            "pair":       pair,
            "price":      price,
            "qty":        qty,
            "usd":        usd,
            "fee":        fee,
            "pnl":        pnl,
            "confidence": signal.get("confidence", 0),
            "time":       datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        }
        self.state["trades"].append(t)
        return t

    def portfolio_value(self, prices):
        pos_val = sum(
            p["qty"] * prices.get(pair, p["avg_entry"])
            for pair, p in self.state["positions"].items()
        )
        return self.state["balance"] + pos_val

    def unrealized_pnl(self, prices):
        return sum(
            p["qty"] * (prices.get(pair, p["avg_entry"]) - p["avg_entry"])
            for pair, p in self.state["positions"].items()
        )

    def return_pct(self, prices):
        val = self.portfolio_value(prices)
        return (val - self.state["initial_balance"]) / self.state["initial_balance"] * 100
