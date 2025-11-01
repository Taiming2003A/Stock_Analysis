from backtest_core.backtester import Backtester
import numpy as np

def optimize_ma(data):
    best_score = -1
    best_params = (0, 0)
    for short in range(10, 31, 5):
        for long in range(40, 81, 10):
            if short >= long:
                continue
            tester = Backtester(data, short, long)
            result = tester.run_backtest()
            score = result['Total_Return_Pct']
            if score > best_score:
                best_score = score
                best_params = (short, long)
    return {'MA_Short': best_params[0], 'MA_Long': best_params[1], 'Score': best_score}
