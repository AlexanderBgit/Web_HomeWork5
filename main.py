import platform
from datetime import datetime, timedelta
import logging
import aiohttp
import asyncio
import time
from wrapper import async_timed


start_time = time.time()


async def request(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                logging.error(f"Error status: {resp.status} for {url}")
        except aiohttp.ClientConnectorError as err:
            logging.error(f"Connection error: {str(err)}")
    return None


async def get_exchange_rates_for_day(date: datetime, base_url):
    date_str = date.strftime("%d.%m.%Y")
    url = f'{base_url}&date={date_str}'
    return await request(url)


@async_timed()
async def get_exchange_rates_for_last_n_days(days: int):
    base_url = 'https://api.privatbank.ua/p24api/exchange_rates?json'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    tasks = []
    for day in range((end_date - start_date).days + 1):
        current_date = start_date + timedelta(days=day)
        tasks.append(get_exchange_rates_for_day(current_date, base_url))

    exchange_rates_data = await asyncio.gather(*tasks)
    return [data for data in exchange_rates_data if data]


@async_timed()
async def main():
    days = int(input('Enter the number of days (1-10): '))
    exchange_rates_data = await get_exchange_rates_for_last_n_days(days)

    if not exchange_rates_data:
        print('Failed to retrieve exchange rate data for the selected days.')
        return
    
    # Cписок валют для вибору
    available_currencies = set()
    for data in exchange_rates_data:
        if 'exchangeRate' in data:
            exchange_rate_list = data['exchangeRate']
            for item in exchange_rate_list:
                currency_name = item.get('currency', 'N/A')
                available_currencies.add(currency_name)
    
    available_currencies_str = ', '.join(available_currencies)
    print(f'Available currencies: {available_currencies_str}')

    # Отримуємо вибрані валюти + за замовчуванням (EUR та USD)
    selected_currencies_input = input('Enter the currencies (space-separated, example, EUR USD): ')
    selected_currencies = selected_currencies_input.split(' ') if selected_currencies_input else []
    # selected_currencies.extend(['EUR', 'USD'])
    
    # Додаємо (EUR та USD) до вибраних валют
    default_currencies = ['EUR', 'USD']
    selected_currencies.extend(default_currencies)

    # Виводимо валюти
    
    selected_currencies_str = ', '.join(selected_currencies)
    print(f'Selected currencies: {selected_currencies_str}')



    end_time = time.time()  # Зупинка таймера
    execution_time = end_time - start_time  # Обчислення
    print(f"time: {execution_time} seconds")



    # Словник для зберігання валют за датою
    currency_data_by_date = {}

    for data in exchange_rates_data:
        if 'exchangeRate' in data:
            exchange_rate_list = data['exchangeRate']
            for item in exchange_rate_list:
                date = data.get('date', 'N/A')
                currency_name = item.get('currency', 'N/A')
                sale_rate = item.get('saleRateNB', 'N/A')
                purchase_rate = item.get('purchaseRateNB', 'N/A')
                
                # Перевіряємо, чи є валюта у списку
                if currency_name in selected_currencies:
                    if date not in currency_data_by_date:
                        currency_data_by_date[date] = []
                    currency_data_by_date[date].append(f"Currency: {currency_name}, Sale Rate: {sale_rate}, Purchase Rate: {purchase_rate}")
        
        else:
            print(f"No exchange rate data available for {data.get('date', 'N/A')}.")

    # Результат у форматі
    for date, currency_info in currency_data_by_date.items():
        print(date)
        for info in currency_info:
            print(info)



if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

