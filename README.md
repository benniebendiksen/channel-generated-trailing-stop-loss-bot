# trend-activated-trailing-stop-loss-bot
A Technical Analysis employing test of the Unicorn Binance Trailing Stop Loss Engine within Binance's Futures Exchange

## Installation
Installation can take the form of either creating a Conda environment with the provided yml file or, alternatively 
creating a Python virtual environment.

Take note of either of the two following steps:

### Conda Environment Creation
Make sure to cd into the root directory of trend-activated-trailing-stop-loss-algo to then create a conda 
environment from the environment yaml file:
```
conda env create -f trend_activated_bot_env.yml
```
Then you can activate the newly created environment that now houses the project's dependencies:
```
conda activate trend_activated_algo_env
```

### Virtual Environment Creation
You can alternatively create/load a Python virtual environment from the root directory:
```
$ python3 -m venv trend_activated_bot_env
$ source trend_activated_bot_env/bin/activate
```
Having created this venv without a yml file, you will need to install the non-native libraries relied 
upon by this project, found within the requirements.txt file:
```
$ python3 -m pip install -r requirements.txt
```

### Remote Virtual Machine Use
For now we will want to set up a quick free tier virtual machine instance with Amazon AWS in order to interact with Binance. Instructions for doing so can be found [here](https://github.com/pablobendiksen/trend-activated-trailing-stop-loss-bot/tree/main/_REMOTE_LOGIN)

## Execute
```
$ export API_KEY="aaa"
$ export API_SECRET="bbb"
$ ./main.py
```
