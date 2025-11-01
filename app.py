from flask import Flask, render_template, request
from backtest_core.stock_utils import fetch_data
from backtest_core.backtester import Backtester
from backtest_core.optimizer import optimize_ma

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    ticker = request.form['ticker']
    mode = request.form.get('mode', 'manual')

    data = fetch_data(ticker)

    if mode == 'auto':
        opt = optimize_ma(data)
        ma_short, ma_long = opt['MA_Short'], opt['MA_Long']
    else:
        ma_short = int(request.form['ma_short'])
        ma_long = int(request.form['ma_long'])

    stop_loss = float(request.form['stop_loss']) / 100
    take_profit = float(request.form['take_profit']) / 100

    tester = Backtester(data, ma_short, ma_long, 
                        stop_loss_pct=stop_loss, take_profit_pct=take_profit)
    result = tester.run_backtest()

    return render_template('result.html', 
                           ticker=ticker, 
                           ma_short=ma_short, ma_long=ma_long,
                           result=result)

if __name__ == '__main__':
    app.run(debug=True)
