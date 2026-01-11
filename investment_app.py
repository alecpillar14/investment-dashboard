import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Investment Research Dashboard",
    page_icon="📈",
    layout="wide"
)

# Password protection
def check_password():
    """Returns True if the user has entered the correct password."""
    
    # Set your password here
    CORRECT_PASSWORD = "Invest2026"  # Change this to whatever you want
    
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    
    if st.session_state["password_correct"]:
        return True
    
    # Show password input
    st.title("🔒 Investment Research Dashboard")
    st.markdown("Please enter the password to access the dashboard")
    
    password = st.text_input("Password:", type="password", key="password_input")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Login"):
            if password == CORRECT_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("😕 Incorrect password")
    
    return False

# Check password before showing app
if not check_password():
    st.stop()

# Title and description
st.title("📈 Investment Research Dashboard")
st.markdown("**Analyze stocks for 1-5 year investments**")

# Sidebar for user inputs
st.sidebar.header("Stock Selection")

# Input for stock tickers
ticker_input = st.sidebar.text_input(
    "Enter stock ticker(s) - separate multiple with commas:",
    value="AAPL, MSFT, GOOGL"
)

# Parse tickers
tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

# Time period selection
time_period = st.sidebar.selectbox(
    "Select time period for analysis:",
    ["1 Year", "2 Years", "3 Years", "5 Years", "Year-to-Date"]
)

# Map time period to dates
period_map = {
    "1 Year": "1y",
    "2 Years": "2y",
    "3 Years": "3y",
    "5 Years": "5y",
    "Year-to-Date": "ytd"
}

selected_period = period_map[time_period]

# Fetch data button
if st.sidebar.button("Analyze Stocks", type="primary"):
    if not tickers:
        st.error("Please enter at least one stock ticker")
    else:
        st.session_state['analyze'] = True
        st.session_state['tickers'] = tickers
        st.session_state['period'] = selected_period

# Main content
if 'analyze' in st.session_state and st.session_state['analyze']:
    tickers = st.session_state['tickers']
    selected_period = st.session_state['period']
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Price Charts", "💰 Financials", "⚖️ Comparison"])
    
    # Fetch data for all tickers
    stock_data = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, ticker in enumerate(tickers):
        try:
            status_text.text(f"Fetching data for {ticker}... ({idx + 1}/{len(tickers)})")
            stock = yf.Ticker(ticker)
            
            # Fetch data with error handling
            info = stock.info
            history = stock.history(period=selected_period)
            
            # Only add if we got valid data
            if len(history) > 0 and info:
                stock_data[ticker] = {
                    'ticker_obj': stock,
                    'info': info,
                    'history': history,
                    'financials': stock.financials,
                    'balance_sheet': stock.balance_sheet
                }
            else:
                st.warning(f"No data available for {ticker}")
                
        except Exception as e:
            st.warning(f"Could not fetch data for {ticker}: {str(e)}")
        
        # Update progress bar
        progress_bar.progress((idx + 1) / len(tickers))
        
        # Add delay to avoid rate limiting
        import time
        time.sleep(1)
    
    progress_bar.empty()
    status_text.empty()
    
    # Check if we got any data
    if len(stock_data) == 0:
        st.error("⚠️ Could not fetch data for any stocks. This might be due to:")
        st.markdown("""
        - **Rate limiting** - Yahoo Finance limits requests. Wait 5-10 minutes and try again.
        - **Invalid ticker symbols** - Make sure you're using correct symbols (e.g., AAPL, MSFT)
        - **Network issues** - Check your internet connection
        
        Try again in a few minutes with fewer stocks (1-3 tickers).
        """)
        st.stop()
    
    # TAB 1: Overview
    with tab1:
        st.header("Stock Overview")
        
        if len(stock_data) == 0:
            st.info("No stock data available to display")
        else:
            # Display cards for each stock
            cols = st.columns(min(len(stock_data), 3))
        
        for idx, (ticker, data) in enumerate(stock_data.items()):
            with cols[idx % 3]:
                info = data['info']
                history = data['history']
                
                # Get current price and change
                current_price = info.get('currentPrice', 0)
                if current_price == 0 and len(history) > 0:
                    current_price = history['Close'].iloc[-1]
                
                previous_close = info.get('previousClose', 0)
                change = current_price - previous_close
                change_pct = (change / previous_close * 100) if previous_close > 0 else 0
                
                # Display card
                st.subheader(f"{ticker}")
                st.metric(
                    label=info.get('shortName', ticker),
                    value=f"${current_price:.2f}",
                    delta=f"{change_pct:.2f}%"
                )
                
                # Key metrics
                st.markdown(f"""
                **Market Cap:** ${info.get('marketCap', 0):,.0f}  
                **P/E Ratio:** {info.get('trailingPE', 'N/A')}  
                **Dividend Yield:** {info.get('dividendYield', 0)*100:.2f}%  
                **52W High:** ${info.get('fiftyTwoWeekHigh', 'N/A')}  
                **52W Low:** ${info.get('fiftyTwoWeekLow', 'N/A')}  
                **Sector:** {info.get('sector', 'N/A')}
                """)
    
    # TAB 2: Price Charts
    with tab2:
        st.header("Historical Price Performance")
        
        # Create price chart
        fig = go.Figure()
        
        for ticker, data in stock_data.items():
            history = data['history']
            if len(history) > 0:
                fig.add_trace(go.Scatter(
                    x=history.index,
                    y=history['Close'],
                    mode='lines',
                    name=ticker,
                    hovertemplate=f'{ticker}<br>Date: %{{x}}<br>Price: $%{{y:.2f}}<extra></extra>'
                ))
        
        fig.update_layout(
            title=f"Stock Price Comparison - {time_period}",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            hovermode='x unified',
            height=500,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance table
        st.subheader("Performance Summary")
        perf_data = []
        
        for ticker, data in stock_data.items():
            history = data['history']
            if len(history) > 1:
                start_price = history['Close'].iloc[0]
                end_price = history['Close'].iloc[-1]
                total_return = ((end_price - start_price) / start_price) * 100
                
                perf_data.append({
                    'Ticker': ticker,
                    'Start Price': f"${start_price:.2f}",
                    'Current Price': f"${end_price:.2f}",
                    'Total Return': f"{total_return:.2f}%",
                    'Volatility (Std Dev)': f"{history['Close'].std():.2f}"
                })
        
        if perf_data:
            perf_df = pd.DataFrame(perf_data)
            st.dataframe(perf_df, use_container_width=True)
    
    # TAB 3: Financials
    with tab3:
        st.header("Financial Metrics")
        
        # Create comparison table
        financial_data = []
        
        for ticker, data in stock_data.items():
            info = data['info']
            
            financial_data.append({
                'Ticker': ticker,
                'Revenue': f"${info.get('totalRevenue', 0):,.0f}",
                'Net Income': f"${info.get('netIncomeToCommon', 0):,.0f}",
                'Operating Margin': f"{info.get('operatingMargins', 0)*100:.2f}%",
                'Profit Margin': f"{info.get('profitMargins', 0)*100:.2f}%",
                'ROE': f"{info.get('returnOnEquity', 0)*100:.2f}%",
                'Debt/Equity': f"{info.get('debtToEquity', 0):.2f}",
                'Current Ratio': f"{info.get('currentRatio', 0):.2f}",
                'Free Cash Flow': f"${info.get('freeCashflow', 0):,.0f}"
            })
        
        if financial_data:
            fin_df = pd.DataFrame(financial_data)
            st.dataframe(fin_df, use_container_width=True)
        
        # Revenue and earnings charts
        st.subheader("Revenue Comparison")
        
        revenue_data = []
        for ticker, data in stock_data.items():
            info = data['info']
            revenue_data.append({
                'Ticker': ticker,
                'Revenue': info.get('totalRevenue', 0)
            })
        
        if revenue_data:
            rev_df = pd.DataFrame(revenue_data)
            fig_rev = px.bar(
                rev_df,
                x='Ticker',
                y='Revenue',
                title='Total Revenue Comparison',
                labels={'Revenue': 'Revenue ($)'},
                color='Ticker'
            )
            st.plotly_chart(fig_rev, use_container_width=True)
    
    # TAB 4: Comparison
    with tab4:
        st.header("Side-by-Side Comparison")
        
        comparison_metrics = [
            'currentPrice',
            'marketCap',
            'trailingPE',
            'forwardPE',
            'priceToBook',
            'dividendYield',
            'beta',
            'fiftyTwoWeekHigh',
            'fiftyTwoWeekLow',
            'averageVolume'
        ]
        
        comparison_data = {}
        
        for ticker, data in stock_data.items():
            info = data['info']
            ticker_metrics = {}
            
            for metric in comparison_metrics:
                value = info.get(metric, 'N/A')
                if isinstance(value, (int, float)) and metric == 'marketCap':
                    ticker_metrics[metric] = f"${value:,.0f}"
                elif isinstance(value, (int, float)) and metric == 'dividendYield':
                    ticker_metrics[metric] = f"{value*100:.2f}%"
                elif isinstance(value, (int, float)):
                    ticker_metrics[metric] = f"{value:.2f}"
                else:
                    ticker_metrics[metric] = value
            
            comparison_data[ticker] = ticker_metrics
        
        # Create comparison dataframe
        comp_df = pd.DataFrame(comparison_data).T
        comp_df.columns = [
            'Current Price',
            'Market Cap',
            'P/E Ratio (TTM)',
            'Forward P/E',
            'Price/Book',
            'Dividend Yield',
            'Beta',
            '52W High',
            '52W Low',
            'Avg Volume'
        ]
        
        st.dataframe(comp_df, use_container_width=True)
        
        # Valuation comparison chart
        st.subheader("Valuation Metrics")
        
        pe_data = []
        for ticker, data in stock_data.items():
            info = data['info']
            pe = info.get('trailingPE', None)
            if pe and pe > 0 and pe < 100:  # Filter out extreme values
                pe_data.append({
                    'Ticker': ticker,
                    'P/E Ratio': pe
                })
        
        if pe_data:
            pe_df = pd.DataFrame(pe_data)
            fig_pe = px.bar(
                pe_df,
                x='Ticker',
                y='P/E Ratio',
                title='P/E Ratio Comparison',
                color='Ticker'
            )
            st.plotly_chart(fig_pe, use_container_width=True)

else:
    # Welcome screen
    st.info("👈 Enter stock tickers in the sidebar and click 'Analyze Stocks' to begin")
    
    st.markdown("""
    ### Features:
    - **Real-time stock data** from Yahoo Finance
    - **1-5 year historical analysis**
    - **Key financial metrics** (P/E, dividend yield, market cap, etc.)
    - **Interactive price charts**
    - **Side-by-side comparisons**
    - **Financial health indicators**
    
    ### How to use:
    1. Enter one or more stock tickers (e.g., AAPL, MSFT, TSLA)
    2. Select your desired time period
    3. Click "Analyze Stocks"
    4. Explore the different tabs for various insights
    
    ### Example tickers to try:
    - **Tech**: AAPL, MSFT, GOOGL, AMZN, META
    - **Finance**: JPM, BAC, GS, WFC
    - **Healthcare**: JNJ, UNH, PFE, ABBV
    - **Consumer**: WMT, KO, PG, NKE
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Investment Research Dashboard**")
st.sidebar.caption("Data provided by Yahoo Finance")
