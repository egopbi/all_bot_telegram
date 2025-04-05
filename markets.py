import asyncio
import json

import aiohttp
import cloudscraper
from bs4 import BeautifulSoup

url_crypto = 'https://www.tradingview.com/markets/cryptocurrencies/prices-all/'
url_stocks = 'https://www.tradingview.com/markets/world-stocks/worlds-largest-companies/'
url_stocks_rus = 'https://scanner.tradingview.com/russia/scan?label-product=markets-screener'
url_sber_metal = 'https://www.sberbank.com/proxy/services/rates/public/actualIngots'
url_currencies = 'https://ratestats.com/'

async def fetch_data(url, params=None, data=None, headers=None, is_post=False, method='text'):
    if headers is None:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
        headers = scraper.headers
    async with aiohttp.ClientSession(headers=headers) as session:
        if is_post:
            async with session.post(url=url, data=data) as response:
                    return await response.json()

        async with session.get(url=url, params=params) as response:
            if method == 'text':
                return await response.text()
            elif method == 'json':
                return await response.json()
            else:
                raise ValueError('There is no method "%s"', method)
            

async def crypto():
    response = await fetch_data(url_crypto)

    bs_crypto = BeautifulSoup(response, 'html.parser')
    currencies = bs_crypto.find('tbody', {'tabindex': '100'})
    cur_rows = currencies.find_all('tr', class_='row-RdUXZpkv listRow') 
    crypto_text = ("\n\n**CRYPTO MARKETS**\n\n")
    for i in range(10):
        cur = cur_rows[i]
        name = cur.find('a').text
        price = (cur.find_all('td'))[2].text
        performance = (cur.find_all('td'))[3].text

        if "-" in performance or "−" in performance:
            pipa = "🔻"
        else:
            pipa = "🟢"

        market_cap = ((cur.find_all('td'))[4].text).replace("\u202f", " ")
        crypto_text+=(f"{pipa} **${name}** — {price} ({performance}) | 💰 {market_cap}\n\n")
    
    return crypto_text


async def stocks():
    response = await fetch_data(url_stocks)

    bs_stocks = BeautifulSoup(response, 'html.parser')
    currencies = bs_stocks.find('tbody', {'tabindex': '100'})
    cur_rows = currencies.find_all('tr', class_='row-RdUXZpkv listRow')

    stocks_text = ('\n\n**STOCKS MARKETS**\n\n')
    for i in range(20):
        cur = cur_rows[i]
            
        price = (cur.find_all('td'))[3].text
        market_cap = ((cur.find_all('td'))[2].text).replace("\u202f", " ")
        performance = (cur.find_all('td'))[4].text
        if "-" in performance or "−" in performance:
            pipa = "🔻"
        else:
            pipa = "🟢"

        ticker = cur.find('a').text
        if ticker.isdigit():
            name = (cur.find('sup')).text
            stocks_text+=(f"{pipa} — **${ticker}** ({name}) - {price} ({performance}) | 💰 {market_cap}\n\n")

        else:
            stocks_text+=(f"{pipa} — **${ticker}** - {price} ({performance}) | 💰 {market_cap}\n\n")

    return stocks_text


async def stocks_rus():
    scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
    headers = {
        **scraper.headers,
        "Accept": "application/json",
        "Content-Type": "text/plain;charset=UTF-8",
        "Origin": "https://ru.tradingview.com",
        "Referer": "https://ru.tradingview.com/",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    data = {
        "columns": [
            "close", 
            "Perf.1M", 
            "market_cap_basic", 
            "fundamental_currency_code",
            "logoid",
            "name",
            "change",
        ],
        "ignore_inknown_fields": False,
        "options": {"lang":"ru"},
        'preset': "volume_leaders",
        "range": [0, 20],
        "sort": {"nullsFirst": False, "sortBy": "market_cap_basic", "sortOrder": "desc"},
    }

    response = await fetch_data(
        url_stocks_rus, 
        data=json.dumps(data), 
        headers=headers, 
        is_post=True,
        method='json',
    )
    stocks_list = response['data']
    stocks_text = ('\n\n**RUSSIAN STOCKS MARKETS**\n\n')
    for i in range(20):
        ticker = stocks_list[i]['d'][5]
        performance = round(stocks_list[i]['d'][6], 2)
        if performance < 0:
            pipa = "🔻"
        else:
            pipa = "🟢"
        valute = stocks_list[i]['d'][3]
        price = stocks_list[i]['d'][0]
        name =  str(stocks_list[i]['d'][4])
        market_cap = round(stocks_list[i]['d'][2] / 1000000000)
        stocks_text+=(f"{pipa} — **${ticker}** ({name.upper()})- {price} ({performance}%) | 💰 {market_cap} **B** {valute}\n\n")
    
    return stocks_text


async def metals_sber():
    metals = ("Ag", "Au", "Pt", "Pd")

    metals_id = {
        "Ag": "A99",
        "Au": "A98",
        "Pt": "A76",
        "Pd": "A33"
    }

    tasks = []
    metals_text = ('\n\n**METALS SBER INGOTS**\n\n')

    async def metal_info(metal):
        m_id = metals_id[str(metal)]
        params = {
            "rateType": "PMR-1",
            "segType": "TRADITIONAL",
            "id": "38",
            "isoCodes[]": m_id
        }
        headers_metals = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://www.sberbank.com",
            "X-Requested-With": "XMLHttpRequest"
        }

        response = await fetch_data(
            url=url_sber_metal, 
            params=params, 
            headers=headers_metals, 
            method='json'
            )
        
        ratelist = response[m_id]["rateList"]
        price_sell = 0
        for offer in ratelist:
            if int(offer['mass']) == 100:
                price_sell_raw = int(offer['rateSell'])
                price_sell = f'{price_sell_raw:,}'
        
        metal_text = (f'🇷🇺 **{metal}** — {price_sell} ₽ for 100g\n\n')

        return metal_text

        
    for metal in metals:
        tasks.append(asyncio.create_task(metal_info(metal)))

    list_metal_texts = await asyncio.gather(*tasks)
    for metal_text in list_metal_texts:
        metals_text += metal_text
    
    return metals_text


async def currencies():
    cur_text = "\n\n**CURRENCIES MARKET**\n\n"
    response = await fetch_data(url=url_currencies)
    bs_currencies = BeautifulSoup(response, 'html.parser')
    tickers_raw = bs_currencies.find_all('a', class_="b-rates__ticker-name b-rates__legend_small")
    names = [ticker.text for ticker in tickers_raw]

    prices_block = bs_currencies.find('div', class_="row b-rates__item_highlighted b-rates_small-text")
    prices_raw = prices_block.find_all('div', class_='b-rates__amount')
    prices = [float(price.find('span').text.replace(",", '.')).__round__(2) for price in prices_raw]

    periods = bs_currencies.find_all('div', class_= "row b-rates__item")
    m_period = periods[2]
    performances_raw = m_period.find_all('div', class_='b-rates__amount')
    performances = [float(
        per.find('div', class_="b-rates__delta")
        .text
        .replace(",", ".")
    ).__round__(2)*-1 for per in performances_raw]

    for cur in zip(names, prices, performances):
        name, price, performance = cur[0], cur[1], cur[2]
        if performance < 0:
            pipa = "🔻"
        else:
            pipa = "🟢"

        cur_text += (f'{pipa} — **{name.upper()}** — {price} ₽ ({performance}% month)\n\n')
    
    return cur_text


async def markets_main():
    tasks = []
    functions = (crypto, stocks, stocks_rus, metals_sber, currencies)
    for fun in functions:
        tasks.append(asyncio.create_task(fun()))

    response_raw = await asyncio.gather(*tasks)
    response = "📊 **Market Overview: Crypto, Stocks, Metals & Currencies**"
    for market in response_raw:
        response += market
        if market != response_raw[-1]:
            response += "##############################"
    return response

if __name__ == "__main__":
    asyncio.run(markets_main())