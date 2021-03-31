import requests as req
import time
from env import ALPHA_AV_API_KEY, NEWS_API, TELEGRAM_BOT_API
from newsapi import NewsApiClient

# CLient Initialization
newsapi = NewsApiClient(api_key=NEWS_API)

# Const Initializations
# Add crypto code and name to the list
CRYPTOS = [["BTC","Bitcoin"]]
EXCHANGE_RATE = "CURRENCY_EXCHANGE_RATE"
DAILY_RATES = "DIGITAL_CURRENCY_DAILY"
CRYPTO_HEALTH = "CRYPTO_RATING"


def get_EXC_data(sym: str):
    """
    This function takes a crypto symbol returns a dictionary of the fetched exchange data.
    """
    params = {
        "function": EXCHANGE_RATE,
        "from_currency": sym,
        "to_currency": "USDT",
        "apikey": ALPHA_AV_API_KEY
    }
    res = req.get(url="https://www.alphavantage.co/query", params=params)
    res.raise_for_status()
    data = res.json()
    data = data["Realtime Currency Exchange Rate"]
    data = {"from":data["1. From_Currency Code"],"to":data["3. To_Currency Code"],"rate":data["5. Exchange Rate"]}
    return data


def get_Daily_data(sym: str):
    """
    This function takes a crypto symbol returns a dictionary of the fetched daily data.
    """
    params = {
        "function": DAILY_RATES,
        "symbol": sym,
        "market": "USD",
        "apikey": ALPHA_AV_API_KEY
    }
    res = req.get(url="https://www.alphavantage.co/query", params=params)
    res.raise_for_status()
    data = res.json()["Time Series (Digital Currency Daily)"]
    data = list(data.items())[:31]
    day0 = data[0]
    day1 = data[1]
    day3 = data[3]
    day7 = data[7]
    day30 = data[30]
    dailyChange = ((float(day0[1]['1a. open (USD)']) - float(day1[1]['1a. open (USD)']))/float(day1[1]['1a. open (USD)']))*100
    d3change = ((float(day0[1]['1a. open (USD)']) - float(day3[1]['1a. open (USD)'])) / float(day3[1]['1a. open (USD)'])) * 100
    d7change = ((float(day0[1]['1a. open (USD)']) - float(day7[1]['1a. open (USD)'])) / float(day7[1]['1a. open (USD)'])) * 100
    d30change = ((float(day0[1]['1a. open (USD)']) - float(day30[1]['1a. open (USD)'])) / float(day30[1]['1a. open (USD)'])) * 100
    data = {
        "market_cap":day0[1]["6. market cap (USD)"],
        "vol":day0[1]["5. volume"],
        "opn_price":day0[1]['1a. open (USD)'],
        "dailyChange":round(dailyChange,2),
        "d3change":round(d3change,2),
        "d7change":round(d7change,2),
        "d30change":round(d30change,2),
    }
    return data




def get_Health_data(sym: str):
    """
    This function takes a crypto symbol returns a dictionary of the fetched health data.
    """
    params = {
        "function": CRYPTO_HEALTH,
        "symbol": sym,
        "apikey": ALPHA_AV_API_KEY
    }
    res = req.get(url="https://www.alphavantage.co/query", params=params)
    res.raise_for_status()
    try:
        data = res.json()["Crypto Rating (FCAS)"]
    except:
        data = {"rating":"Unavailable", "score":"unavailable"}
    else:
        data = {"rating":data["3. fcas rating"], "score":data["4. fcas score"]}
    return data

def get_news(coinname):
    top_headlines = newsapi.get_top_headlines(q=coinname,language='en')
    articles = top_headlines["articles"][:5]
    results = []
    for article in articles:
        ztime = article["publishedAt"]
        date = ztime.split("T")[0]
        time = ztime.split("T")[1].split("Z")[0]
        temp = {
            "source":article["source"]["name"],
            "title": article["title"],
            "url":article["url"],
            "img":article["urlToImage"],
            "time":f"{time}, {date} UTC"

        }
        results.append(temp)

    return(results)

def get_data(currencies):
    results = {}
    for coin in currencies:
        code = coin[0]
        name = coin[1]
        results[code] = [get_EXC_data(code),get_Daily_data(code),get_Health_data(code),get_news(name)]
        time.sleep(60)
    return results

def prepare_messages(data):
    msg_list = []
    for key,value in data.items():
        basic = value[0]
        change = value[1]
        health = value[2]
        news = value[3]
        newsarr = [f"======== News ========\n\n\n"]
        i = 1
        for item in news:
            string = f"""{i}.{item["title"]}
Link- {item["url"]}
Time-{item["time"]}\n\n\n"""
            newsarr.append(string)
            i+=1


        message = f"""Your daily crypto 💰💰💰 alert - Zulkar's Crypto Bot

======== STATS ========

{basic["from"]}/{basic["to"]}
Rate: {basic["rate"]}
Open: {change["opn_price"]}
Daily change: {change["dailyChange"]}%
3 days change: {change["d3change"]}%
Weekly change: {change["d7change"]}%
Monthly change: {change["d30change"]}%
Market cap: {change["market_cap"]}
Volume: {change["vol"]}
Rating: {health["rating"]}
Score: {health["score"]}


"""
        if len(newsarr)>1:
            message = message + "".join(newsarr)
        msg_list.append(message)
    return msg_list


coin_data = get_data(CRYPTOS)
messages = prepare_messages(coin_data)


def send_tele_message(messages):
    res = req.get(url="https://api.telegram.org/"+TELEGRAM_BOT_API+"/getupdates")
    res.raise_for_status()
    data = res.json()["result"]
    chatIDs = []
    for entry in data:
        try:
            chatIDs.append(entry["message"]["chat"]["id"])
        except:
            pass

    chatIDs = list(dict.fromkeys(chatIDs))
    for id in chatIDs:
        for m in messages:
            params = {
                "chat_id":id,
                "text":m
            }
            req.get(url="https://api.telegram.org/" + TELEGRAM_BOT_API + "/sendmessage", params=params)

send_tele_message(messages)

