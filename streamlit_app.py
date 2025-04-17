import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# === App settings ===
st.set_page_config(page_title="Fama-French Suggested Portfolios", layout="wide")
st.title("📊 Fama-French Portfolio")

# === Load files directly from local /data/ folder ===
DATA_FOLDER = "./data/"

betas_file = os.path.join(DATA_FOLDER, "Formatted_March2025_Betas.xlsx")
ff_factors_file = os.path.join(DATA_FOLDER, "FINAL FF FACTOR.xlsx")
feb_actual_file = os.path.join(DATA_FOLDER, "Feb2025_Actual_Returns.csv")  # optional

# === Load data ===
try:
    betas_df = pd.read_excel(betas_file)
    ff_df = pd.read_excel(ff_factors_file)
except Exception as e:
    st.error(f"❌ Error loading files: {e}")
    st.stop()

# === Clean FF factor file ===
ff_df.columns = ff_df.columns.str.strip()
ff_df['Date'] = pd.to_datetime(ff_df['Date'])

# === Extract Feb 2025 FF values ===
ff_feb = ff_df[ff_df['Date'] == '2025-02-28']
if ff_feb.empty:
    st.error("❌ Feb 2025 factor values not found in FF file.")
    st.stop()

ff_vals = ff_feb.iloc[0]
factors = {
    'Beta_Mkt': ff_vals['Market Premium'],
    'Beta_SMB': ff_vals['SMB'],
    'Beta_HML': ff_vals['HML'],
    'Beta_RMW': ff_vals['RMW'],
    'Beta_CMA': ff_vals['CMA']
}

# === Compute Expected March Return ===
betas_df['Expected_March_Return'] = (
    betas_df['Beta_Mkt'] * factors['Beta_Mkt'] +
    betas_df['Beta_SMB'] * factors['Beta_SMB'] +
    betas_df['Beta_HML'] * factors['Beta_HML'] +
    betas_df['Beta_RMW'] * factors['Beta_RMW'] +
    betas_df['Beta_CMA'] * factors['Beta_CMA']
)

# === Risk and Return-to-Risk Calculation ===
betas_df['Risk'] = abs(betas_df['Beta_Mkt'])
betas_df = betas_df[betas_df['Expected_March_Return'] > 0].copy()  # filter positive return stocks only
betas_df['Return_to_Risk_Score'] = betas_df['Expected_March_Return'] / (betas_df['Risk'] + 1e-6)
betas_df['Rank_by_Score'] = betas_df['Return_to_Risk_Score'].rank(ascending=False)

# === Select Top 20 Portfolio ===
portfolio = betas_df.nsmallest(20, 'Rank_by_Score').copy()
portfolio['Weight_by_Score'] = portfolio['Return_to_Risk_Score'] / portfolio['Return_to_Risk_Score'].sum()

# === Show Portfolio Summary ===
st.subheader("📈 Portfolio Summary")
st.dataframe(portfolio[['Stock', 'Expected_March_Return', 'Risk', 'Return_to_Risk_Score', 'Weight_by_Score']])

# === Plot Efficient Frontier ===
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(betas_df['Risk'], betas_df['Expected_March_Return'], label='All Stocks', alpha=0.4)
ax.scatter(portfolio['Risk'], portfolio['Expected_March_Return'], color='red', label='Selected Portfolio')
ax.set_xlabel("Risk (Beta_Mkt)")
ax.set_ylabel("Expected Return")
ax.set_title("Efficient Frontier: Return vs Risk")
ax.legend()
ax.grid(True)
st.pyplot(fig)

# === Optional: Backtest Portfolio using Feb Returns ===
if os.path.exists(feb_actual_file):
    actual_df = pd.read_csv(feb_actual_file)
    portfolio = portfolio.merge(actual_df, on='Stock', how='left')
    portfolio['Weighted_Feb_Return'] = portfolio['Weight_by_Score'] * portfolio['Actual_Feb_Return']
    total_feb_return = portfolio['Weighted_Feb_Return'].sum()

    st.subheader("📉 Backtest Result (Feb 2025)")
    st.metric(label="Portfolio Return", value=f"{total_feb_return:.2%}")
else:
    st.info("⚡ Feb2025 Actual Return file not found. Skipping backtest step.")

# === Download Portfolio ===
st.download_button(
    label="📥 Download Final Portfolio",
    data=portfolio.to_csv(index=False),
    file_name="Final_Portfolio_Simulation.csv",
    mime="text/csv"
)
