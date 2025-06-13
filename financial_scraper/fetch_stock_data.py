import yfinance as yf

def fetch_stock_info(ticker="AAPL"):
    stock = yf.Ticker(ticker)
    hist = stock.history(period="5d")
    print(f"=== Histórico (5 dias) de {ticker} ===")
    print(hist, "\n")
    print("=== Notícias recentes via yfinance ===")
    for n in stock.news[:5]:
        print(f"- {n.get('title')} ({n.get('publisher')})")
        print(f"  {n.get('link')}")

if __name__ == "__main__":
    fetch_stock_info("AAPL")
