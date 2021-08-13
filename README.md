# xtraderbacktest
This project is a personal backtest system for trading strategy.
http://www.xtradernotebook.com/2021/08/05/%e4%bb%8e%e9%9b%b6%e5%bc%80%e5%a7%8b%ef%bc%8c%e4%b8%80%e6%ad%a5%e4%b8%80%e6%ad%a5%e6%89%93%e9%80%a0%e4%b8%aa%e4%ba%ba%e7%9a%84%e7%ad%96%e7%95%a5%e5%9b%9e%e6%b5%8b%e7%b3%bb%e7%bb%9f%ef%bc%88%e5%bc%80/

# Requirements      
python 3.6.8 in 64bit

The tools might need:       
Microsoft Visual C++ Build Tools(https://visualstudio.microsoft.com/visual-cpp-build-tools/)       

# How to Start      
##  Quick Start   
Here is how to run the demo strategy.   
-   Copy /configuration/sys/system_conf_template.yaml to /configurations/sys/system_conf.yaml
-   Modify the content of /configuration/sys/system_conf.yaml as you need
-   pip3 install -r requirement.txt
-   Modify the demo strategy's configuration in /configurations/strategy/single/demo/AAPL_demo.json
-   Cd /bots
-   python demo_strategy.py

## Basic Start    
### Step 1      
Put the 1min price data in the folder /data/price/SYMBOL_NAME.txt.  
The 1min price data should be in this format:  
date, open,high,low,close,volume,open_interest(optional)
```
2019-02-15 04:40:00,169.31,169.31,169.31,169.31,100
2019-02-15 04:41:00,169.31,169.31,169.31,169.31,300
```
### Step 2      
Save the symbols' configurations in the folder /configurations/symbols_conf/
Here is the stock AAPL template.
```
---
name: AAPL                              # symbol name
point: 0.01                             # point value
tick_size: 0.01                         # tick_size
commission: 0                           # commission in currency
slippage: 0                             # slippage in points
margin_rate: 1                          # margin rate 0.05 = 5%
minimum_tp_sl: 3                        # minimum gap in points between entry price and tpsl price
contract_size: 1                        # contract size
spread: 5                               # the spread(between ask and bid) in points for backtest
type: stock                             # symbol type
exchange: None                          # the trading exchange
t+0: true                               # whether is t+0
swaps:  0                               # the swaps in points
trade_session:                          # tradable session
  sunday: []
  monday:                               # the template of multiple tradable session in one day
  - - '01:00:00'
    - '10:59:59'
  - - '10:59:59'
    - '23:59:59'
  tuesday:
  - - '01:00:00'
    - '23:59:59'
  wednesday:
  - - '01:00:00'
    - '23:59:59'
  thursday:
  - - '01:00:00'
    - '23:59:59'
  friday:
  - - '01:00:00'
    - '23:59:59'
  saturday: []
```
### Step 3  
Put the strategy's parameters in the folder /configurations/strategy/single/(strategy_name)/(symbol_name).json in json format. The template is as below.
```
{
    "account_id":"demo_account",
    "period":"5m",
    "backtest_graininess":"5m",
    "symbols":["AAPL"],
    "platform":"IB",
    "start_date": "2019-10-28 08:47:00",
    "end_date": "2019-10-29 19:59:00",
    "strategy_name_code": "DM",
    "strategy_name": "demo",
    "reverse_mode":"enable",
    "cash":10000,
    "untradable_period":[
        {
            "start":"23:59:59",
            "end":"23:59:59"
        }
    ],
    "tag":"demo",
    "custom":{
        "ma_fast":10,
        "ma_slow":21,
        "lots":1
    }
}
```
The parameters that the strategy used is under the key custom, while the other keys are compulsory.
### Step 4  
Write your own strategy and put it in the folder /bots/. Here is a double ma strategy as demo, which buy stocks when fast ma > slow ma and vice versa.
```
import os
import sys
sys.path.append(os.path.join(os.getcwd().split('xtraderbacktest')[0],'xtraderbacktest'))
import modules.other.logg
import logging 
import modules.common.strategy
import modules.other.sys_conf_loader as sys_conf_loader
import modules.common.technical_indicators as ti
class Bot(modules.common.strategy.Strategy):
    def __init__(self,pars):
        super(Bot,self).__init__(pars)
        
    

    # Handle Tick
    def handle_tick(self, tick):
        
        pass

    # Handle Bar
    def handle_bar(self, bar):
        #logging.info("new bar "+bar["date"])
        #logging.info("current_time " + self.current_time)
        df = self.get_bars(bar["symbol"],30,self.context["period"])
        ma_fast = ti.MA(df,self.pars["ma_fast"]).iloc[-1]
        ma_slow = ti.MA(df,self.pars["ma_slow"]).iloc[-1]
        if ma_fast > ma_slow:
            if len(self.get_current_position(direction="long")) ==0:
                self.open_order(bar["symbol"],"market",self.pars["lots"],"long")
            self.close_all_position(direction="short")
        elif ma_fast < ma_slow:
            if len(self.get_current_position(direction="short")) ==0:
                self.open_order(bar["symbol"],"market",self.pars["lots"],"short")
            self.close_all_position(direction="long")
        pass

if __name__ == "__main__":
    pars = sys_conf_loader.read_configs_json("AAPL_demo.json","/configurations/strategy/single/demo_strategy/")
    backtest = Bot(pars)
    import modules.backtest.scheduler 
    scheduler = modules.backtest.scheduler.Scheduler("backtest")
    scheduler.register_strategy(backtest)
    scheduler.start()
    
```
Then run this (strategy).py in the folder /bots/. And you can find the backtest result in the folder /data/backtest_results/ after finish backtesting.
# Existing Problems     
-   ~~Takes too much time in generating fake ticks.~~   
-   ~~Fake ticks take too much memory.~~

