import asyncio
import aiohttp
import cloudscraper
from bs4 import BeautifulSoup

url_crypto = 'https://www.tradingview.com/markets/cryptocurrencies/prices-all/'
url_stocks = 'https://www.tradingview.com/markets/world-stocks/worlds-largest-companies/'
url_sber_metal = 'https://www.sberbank.com/proxy/services/rates/public/actualIngots'
url_yandex_currencies = 'https://yandex.ru/finance/currencies'

async def fetch_data(url, params=None, headers=None, method='text'):
    if headers is None:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
        headers = scraper.headers
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url=url,params=params) as response:
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
        id = metals_id[str(metal)]
        params = {
            "rateType": "PMR-1",
            "segType": "TRADITIONAL",
            "id": "38",
            "isoCodes[]": id
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
        
        ratelist = response[id]["rateList"]
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
    response = await fetch_data(url_yandex_currencies)
    bs_currencies = BeautifulSoup(response, 'html.parser')
    currencies = bs_currencies.find_all('div', class_='FinanceItemsList-Item', role='listitem')
    cur_text = "\n\n**CURRENCIES MARKET**\n\n"

    for i in range(3):
        cur = currencies[i]
        ticker = cur.find('div', class_="FinanceItemsCard-Subtitle").text
        price = cur.find('div', class_="FinanceItemsCard-RightTitle").text
        performance = cur.find('div', class_="FinanceItemsCard-DeltaRelative").text
        if "-" in performance or "−" in performance:
            pipa = "🔻"
        else:
            pipa = "🟢"

        cur_text += (f'{pipa} — **{ticker}** — {price} ({performance} month)\n\n')
    
    return cur_text


async def markets_main():
    tasks = []
    functions = (crypto, stocks, metals_sber, currencies)
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