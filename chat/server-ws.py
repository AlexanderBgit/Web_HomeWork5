import aiohttp
import asyncio
import logging
import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import WebSocketProtocolError
import names
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)

async def get_exchange(date_str):
    try:
        api_url = f'https://api.privatbank.ua/p24api/exchange_rates?json&date={date_str}'

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    currency_data = data.get('exchangeRate', [])

                    if currency_data:
                        result = []
                        for currency in currency_data:
                            name = currency.get('currency', '')
                            buy_rate = currency.get('purchaseRate', '')
                            sale_rate = currency.get('saleRate', '')
                            result.append(f"{name}: buy: {buy_rate}, sale: {sale_rate}")

                        return result
                    else:
                        return [f"Дані про курс валют на {date_str} не знайдені."]
                else:
                    return ["Помилка при отриманні даних."]
    except Exception as e:
        return [f"Помилка: {e}"]

class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')


    async def send_to_clients(self, messages):
        if self.clients:
            [await client.send(message) for message in messages for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except WebSocketProtocolError as err:
            logging.error(err)
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message == 'exchange':
                messages = await get_exchange(datetime.now().strftime('%d.%m.%Y'))
                await self.send_to_clients(messages)
            
            
            elif message.startswith('ecd '): #Exchange Currency Data
                try:
                    num_days = int(message[4:])  # Отримуємо кількість днів з команди
                    if num_days < 1:
                        await ws.send("Помилка: Вкажіть кількість днів більше 0.")
                    else:
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=num_days - 1)  # Початкова дата

                        date_format = '%d.%m.%Y'
                        date_list = [start_date + timedelta(days=i) for i in range(num_days)]
                        date_list = [date.strftime(date_format) for date in date_list]

                        messages = []

                        async def fetch_exchange_rate(date):
                            exchange_rate = await get_exchange(date)
                            messages.extend([f"Курс валют на {date}: ***===================***\n"] + exchange_rate)

                        # Виконуємо асинхронні запити за курсами валют та очікуємо їх результати
                        await asyncio.gather(*[fetch_exchange_rate(date) for date in date_list])

                        await self.send_to_clients(messages)
                        
                except ValueError:
                    await ws.send("Помилка: Вкажіть кількість днів як ціле число (наприклад, 'ecd 5').")
                except Exception as e:
                    await ws.send(f"Помилка: {e}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())
