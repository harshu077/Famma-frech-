import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Fama-French Portfolio Simulator", layout="wide")
st.title("📊 AI-Enhanced Fama-French Portfolio Dashboard")

# === Sidebar: File Uploads ===
st.sidebar.header("Upload Files")
betas_file = st.sidebar.file_uploader("📁 Upload Formatted March 2025 Betas (Excel)", type=["xlsx"])
ff_factors_file = st.sidebar.file_uploader("📁 Upload Fama-French Factor File", type=["xlsx"])
feb_actual_file = st.sidebar.file_uploader("📁 (Optional) Upload Feb 2025 Actual Returns (CSV)", type=["csv"])

if betas_file and ff_factors_file:
    betas_df = pd.read_excel(betas_file)
    ff_df = pd.read_excel(ff_factors_file)
    ff_df.columns = ff_df.columns.str.strip()
    ff_df['Date'] = pd.to_datetime(ff_df['Date'])
    
    # Extract Feb 2025 FF values
    ff_feb = ff_df[ff_df['Date'] == '2025-02-28']
    if ff_feb.empty:
        st.error("❌ Feb 2025 factor values not found in FF file.")
    else:
        ff_vals = ff_feb.iloc[0]
        factors = {
            'Beta_Mkt': ff_vals['Market Premium'],
            'Beta_SMB': ff_vals['SMB'],
            'Beta_HML': ff_vals['HML'],
            'Beta_RMW': ff_vals['RMW'],
            'Beta_CMA': ff_vals['CMA']
        }

        # Compute Expected Return
        betas_df['Expected_March_Return'] = (
            betas_df['Beta_Mkt'] * factors['Beta_Mkt'] +
            betas_df['Beta_SMB'] * factors['Beta_SMB'] +
            betas_df['Beta_HML'] * factors['Beta_HML'] +
            betas_df['Beta_RMW'] * factors['Beta_RMW'] +
            betas_df['Beta_CMA'] * factors['Beta_CMA']
        )

        betas_df['Risk'] = abs(betas_df['Beta_Mkt'])
        betas_df['Return_to_Risk_Score'] = betas_df['Expected_March_Return'] / (betas_df['Risk'] + 1e-6)
        betas_df['Rank_by_Score'] = betas_df['Return_to_Risk_Score'].rank(ascending=False)

        portfolio = betas_df.nsmallest(20, 'Rank_by_Score').copy()
        portfolio['Weight_by_Score'] = portfolio['Return_to_Risk_Score'] / portfolio['Return_to_Risk_Score'].sum()

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

        # === Optional Backtest ===
        if feb_actual_file:
            actual_df = pd.read_csv(feb_actual_file)
            portfolio = portfolio.merge(actual_df, on='Stock', how='left')
            portfolio['Weighted_Feb_Return'] = portfolio['Weight_by_Score'] * portfolio['Actual_Feb_Return']
            total_feb_return = portfolio['Weighted_Feb_Return'].sum()

            st.subheader("📉 Backtest Result (Feb 2025)")
            st.metric(label="Portfolio Return", value=f"{total_feb_return:.2%}")

        # === Download Final Portfolio ===
        st.download_button(
            label="📥 Download Final Portfolio",
            data=portfolio.to_csv(index=False),
            file_name="Final_Portfolio_Simulation.csv",
            mime="text/csv"
        )
else:
    st.info("Please upload both the predicted betas file and the FF factor file to begin.")
