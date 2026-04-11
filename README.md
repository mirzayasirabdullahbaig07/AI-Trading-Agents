# 🤖 AI Trading Agents

An automated AI-powered trading system designed to analyze market data, generate trading signals, and execute trades using configurable strategies.

---

## 🚀 Features

* 📊 AI-based trading decision making
* 🔌 Integration with Kraken API
* 🧪 Paper trading mode for safe testing
* ⚙️ Configurable trading parameters
* 📈 Modular and extensible architecture

---

## 🗂️ Project Structure

```
AI-Trading-Agents/
│── ai_agent.py        # Core AI trading logic
│── app.py             # Main application entry point
│── config.py          # Configuration settings
│── kraken_client.py   # Kraken API integration
│── paper_trader.py    # Paper trading simulation
│── requirements.txt   # Dependencies
│── .env               # Environment variables
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/mirzayasirabdullahbaig07/AI-Trading-Agents.git
cd AI-Trading-Agents
```

### 2. Create virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate   # On Linux/macOS
venv\Scripts\activate      # On Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in the root directory and add:

```
KRAKEN_API_KEY=your_api_key
KRAKEN_API_SECRET=your_api_secret
```

---

## ▶️ Usage

Run the application:

```bash
python app.py
```

---

## 🧪 Paper Trading

The project includes a paper trading module to simulate trades without risking real money:

```bash
python paper_trader.py
```

---

## 🔧 Configuration

Modify trading parameters inside `config.py`:

* Trading pairs
* Risk management settings
* Strategy parameters

---

## 📌 Future Improvements

* Advanced AI/ML models
* Multi-exchange support
* Backtesting engine
* Web dashboard

---

## 🤝 Contributing

Contributions are welcome! Feel free to fork the repo and submit a pull request.

---

## 📄 License

This project is licensed under the MIT License.

---

## ⚠️ Disclaimer

This project is for educational purposes only. Trading cryptocurrencies involves risk. Use at your own discretion.

---

## 👤 Author

**Mirza Yasir Abdullah Baig**

---
