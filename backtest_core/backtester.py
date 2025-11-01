import pandas as pd
import numpy as np


class Backtester:
    def __init__(self, data, ma_short, ma_long,
                 initial_capital=100000, stop_loss_pct=0.05, take_profit_pct=0.15):
        """
        簡易MA均線回測器
        """
        self.data = data.copy()
        self.ma_short = ma_short
        self.ma_long = ma_long
        self.initial_capital = initial_capital
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.transactions = []
        self.result = {}

    # ------------------------------------------------------------
    def _calculate_ma_signals(self):
        """計算MA均線交叉信號"""
        df = self.data.copy()
        df['MA_Short'] = df['Close'].rolling(self.ma_short).mean()
        df['MA_Long'] = df['Close'].rolling(self.ma_long).mean()
        df['Signal'] = np.where(df['MA_Short'] > df['MA_Long'], 1, -1)
        df['Position_Change'] = df['Signal'].diff()
        df.dropna(inplace=True)
        return df

    # ------------------------------------------------------------
    def run_backtest(self):
        """主回測流程"""
        df = self._calculate_ma_signals().copy()
        capital = self.initial_capital
        shares = 0
        entry_price = 0
        equity_curve = []

        for date, row in df.iterrows():
            price = float(row['Close'])

            # 安全取得 Position_Change（避免 Series 型別）
            val = row.get('Position_Change', 0)
            if isinstance(val, pd.Series):
                val = val.iloc[0]
            try:
                pos_change = 0 if pd.isna(val) else float(val)
            except Exception:
                pos_change = 0

            # ===== 買入條件 (黃金交叉) =====
            if pos_change == 2 and shares == 0:
                shares = capital / price
                capital = 0
                entry_price = price
                self.transactions.append({
                    'Type': 'Buy',
                    'Date': date.strftime("%Y-%m-%d"),
                    'Price': price,
                    'Reason': 'MA黃金交叉'
                })

            # ===== 賣出條件 (死亡交叉 / 停損 / 停利) =====
            elif shares > 0:
                stop_loss_price = entry_price * (1 - self.stop_loss_pct)
                take_profit_price = entry_price * (1 + self.take_profit_pct)

                sell_reason = None
                if pos_change == -2:
                    sell_reason = 'MA死亡交叉'
                elif price <= stop_loss_price:
                    sell_reason = '觸發停損'
                elif price >= take_profit_price:
                    sell_reason = '觸發停利'

                if sell_reason:
                    capital = shares * price
                    profit = (price - entry_price) * shares
                    self.transactions.append({
                        'Type': 'Sell',
                        'Date': date.strftime("%Y-%m-%d"),
                        'Price': price,
                        'Profit': profit,
                        'Reason': sell_reason
                    })
                    shares = 0

            # 記錄每日資產
            total_equity = capital + shares * price
            equity_curve.append({'Date': date, 'Equity': total_equity})

        # ===== 回測結果統計 =====
        if len(df) == 0:
            final_value = self.initial_capital
            total_return = 0.0
        else:
            final_value = capital + shares * df['Close'].iloc[-1]
            total_return = (final_value - self.initial_capital) / self.initial_capital * 100

        df_equity = pd.DataFrame(equity_curve).set_index('Date')
        if not df_equity.empty:
            df_equity['Return'] = df_equity['Equity'].pct_change().fillna(0)
            df_equity['Cumulative_Return'] = (1 + df_equity['Return']).cumprod() - 1
        else:
            df_equity = pd.DataFrame(columns=['Equity', 'Return', 'Cumulative_Return'])

        # ---- 安全重建純股價DataFrame（確保為單層欄位） ----
        price_cols = ['Open', 'High', 'Low', 'Close', 'MA_Short', 'MA_Long']
        clean_df = pd.DataFrame()
        for col in price_cols:
            if col in df.columns:
                # 若該欄是DataFrame（MultiIndex），取第一層
                if isinstance(df[col], pd.DataFrame):
                    clean_df[col] = df[col].iloc[:, 0]
                else:
                    clean_df[col] = df[col]
            else:
                clean_df[col] = np.nan

        self.result = {
            'Final_Value': float(final_value),
            'Total_Return_Pct': float(total_return),
            'Transactions': self.transactions,
            'Equity': df_equity,
            'PriceData': clean_df  # ✅ 確保模板收到的是單層欄位DataFrame
        }
        return self.result

