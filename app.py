import streamlit as st
import pandas as pd
import yfinance as yf
import fundamentals
import technical
import scanner_plotting
import os
import ai_validator

st.set_page_config(page_title="Cup & Handle Scanner", layout="wide")

st.title("📈 Cup and Handle Pattern Scanner")
st.markdown("""
This tool scans the S&P 500 for stocks that match the **Cup and Handle (Forming)** pattern.
It filters for High Quality stocks (**Market Cap > $5B**, **Profitable**, **Positive PE**).
""")

# Sidebar controls
st.sidebar.header("Scan Settings")
limit_options = [10, 25, 50, 100, 500]
limit = st.sidebar.select_slider("Number of Stocks to Scan", options=limit_options, value=25)

st.sidebar.divider()
st.sidebar.header("🤖 AI Verification")
# Default key provided by user
default_key = "AIzaSyDnvcDEimBNlhf6FhaQWspmU-XVF8k-mnA"
api_key = st.sidebar.text_input("Gemini API Key (Optional)", value=default_key, type="password", help="Get a free key at aistudio.google.com")

run_btn = st.sidebar.button("Run Scanner", type="primary")

if run_btn:
    st.write(f"### Scanning top {limit} stocks...")
    
    # 1. Fundamentals
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    status_text.text("Step 1: Fetching and filtering fundamentals...")
    
    def update_progress(current, total, ticker):
        progress = current / total
        progress_bar.progress(progress)
        status_text.text(f"Step 1: Checking fundamentals for {ticker} ({current}/{total})...")

    # Pass the callback to the function
    candidates = fundamentals.get_filtered_universe(limit=limit, progress_callback=update_progress)
    
    # Reset progress for step 2
    progress_bar.progress(0)
    
    if not candidates:
        st.error("No stocks passed the fundamental filter.")
    else:
        st.success(f"Found {len(candidates)} stocks with strong fundamentals.")
        
        # 2. Technicals
        status_text.text(f"Step 2: Analyzing charts for {len(candidates)} candidates...")
        
        results = []
        
        for i, ticker in enumerate(candidates):
            # Update progress
            progress = (i + 1) / len(candidates)
            progress_bar.progress(progress)
            status_text.text(f"Checking {ticker} ({i+1}/{len(candidates)})...")
            
            try:
                # Download data
                df = yf.download(ticker, period="2y", interval="1d", progress=False, multi_level_index=False)
                
                if df.empty or len(df) < 200:
                    continue
                
                found, details = technical.find_cup_and_handle(df)
                
                if found:
                    details['ticker'] = ticker
                    
                    # Generate Plot
                    plot_path = scanner_plotting.plot_cup_and_handle(df, ticker, details)
                    details['plot_path'] = plot_path
                    
                    # Get info
                    try:
                        info = yf.Ticker(ticker).info
                        details['name'] = info.get('shortName', 'N/A')
                        details['sector'] = info.get('sector', 'N/A')
                        details['market_cap_B'] = round(info.get('marketCap', 0) / 1e9, 1)
                        details['pe_ratio'] = info.get('trailingPE', 'N/A')
                    except:
                        pass
                    
                    # AI Verification
                    if api_key and plot_path:
                        status_text.text(f"🤖 AI Analyzing chart for {ticker}...")
                        ai_resp = ai_validator.analyze_chart(plot_path, api_key)
                        details['ai_analysis'] = ai_resp
                        
                    results.append(details)
                    
            except Exception as e:
                # print(f"Error {ticker}: {e}")
                pass
        
        progress_bar.empty()
        status_text.empty()
        
        if results:
            st.balloons()
            st.write(f"### 🎉 Found {len(results)} Matches!")
            
            # Display as a dataframe
            df_res = pd.DataFrame(results)
            
            # SORT BY WIN PROBABILITY (High to Low)
            if 'win_probability_score' in df_res.columns:
                df_res = df_res.sort_values(by='win_probability_score', ascending=False)
            
            cols = ['ticker', 'win_probability_score', 'name', 'sector', 'suggested_entry', 'stop_loss', 'target_price', 'rr_ratio']
            cols = [c for c in cols if c in df_res.columns]
            
            st.dataframe(df_res[cols], use_container_width=True)
            
            st.write("### Top Opportunities (Sorted by Probability)")
            
            # Display charts in a grid
            # Iterate through the SORTED dataframe to show best first
            records = df_res.to_dict('records')
            
            for res in records:
                c1, c2 = st.columns([1, 2])
                with c1:
                    score = res.get('win_probability_score', 0)
                    st.subheader(f"{res['ticker']}")
                    
                    # Probability Badge
                    if score >= 80:
                        st.success(f"🔥 High Probability Score: {score}/100")
                    elif score >= 60:
                        st.warning(f"⚖️ Medium Probability Score: {score}/100")
                    else:
                        st.info(f"Score: {score}/100")

                    st.write(f"**Name:** {res.get('name', '')}")
                    st.write(f"**Sector:** {res.get('sector', '')}")
                    
                    st.markdown("#### 🎯 Trade Setup")
                    c_enter, c_stop, c_tgt = st.columns(3)
                    c_enter.metric("Entry", f"${res.get('suggested_entry', 0)}")
                    c_stop.metric("Stop Loss", f"${res.get('stop_loss', 0)}")
                    c_tgt.metric("Target", f"${res.get('target_price', 0)}")
                    
                    st.metric("Risk/Reward Ratio", f"1 : {res.get('rr_ratio', 0)}")
                    
                    if 'ai_analysis' in res:
                        st.divider()
                        st.markdown("#### 🤖 AI Verification")
                        st.info(res['ai_analysis'])
                
                with c2:
                    if res.get('plot_path') and os.path.exists(res['plot_path']):
                        st.image(res['plot_path'], caption=f"{res['ticker']} Setup")
                    else:
                        st.warning("Chart image not available.")
                st.divider()
                
        else:
            st.warning("No Cup and Handle patterns found in this batch.")

else:
    st.info("Select the number of stocks and click 'Run Scanner' to start.")
