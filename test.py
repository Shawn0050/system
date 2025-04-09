import yfinance as yf

df = yf.download("^TNX", period="6mo", interval="1h")
df['Close'].plot(title="US 10-Year Treasury Yield (CBOE ^TNX)")

print(df)