import httpx
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import locale
import time
from random import uniform
import logging
from logging import StreamHandler

locale.setlocale(locale.LC_ALL, "portuguese_brazil")
log_format = log_format = "%(asctime)s - %(levelname)s: %(message)s"
logging.basicConfig(
    format=log_format,
    level=logging.INFO,
    datefmt="%H:%M:%S",
    handlers=[StreamHandler()],
)

ua = UserAgent()
params = {"direction": "desc", "sort_by": "popularity", "currency": "BRL"}
desired_price = 25.00
game_list = []

with httpx.Client(
    base_url="https://eshop-prices.com", headers={"User-Agent": ua.chrome}
) as client:

    for page in range(1, 11):
        params["page"] = page
        response = client.get(f"/games/on-sale", params={**params, "page": page})
        logging.info(
            f'Efetuado requisição no endpoint "{response.url}" e o código de retorno foi "{response.status_code}"'
        )
        soup = BeautifulSoup(response.content, "html.parser")
        games_list = soup.find_all("a", class_="games-list-item")
        for game in games_list:
            game_name = game.find("h5").text
            game_price = game.find(class_="price-tag")
            game_price.find("del").decompose()
            game_price = game_price.text.strip()
            game_price = game_price.replace("R$", "R$ ")
            monetary_symbol, monetary_value = game_price.split(" ")
            monetary_value = locale.atof(monetary_value)
            game_score_element = game.find("div", class_="game-score")
            if game_score_element:
                game_score_value = game_score_element.attrs["title"]
            else:
                game_score_value = "N/A"
            game_infos = {
                "name": game_name,
                "price": game_price,
                "score": game_score_value,
            }
            if monetary_value <= desired_price:
                game_page_link = game.attrs["href"]
                game_page_response = client.get(
                    game_page_link, params={"currency": "BRL"}
                )
                soup_game_page = BeautifulSoup(
                    game_page_response.content, "html.parser"
                )
                country_table_rows = soup_game_page.find_all("tr", class_="pointer")
                for country_row in country_table_rows:
                    sale_available_until_element = country_row.find("span")
                    if sale_available_until_element:
                        sale_available_until_value = sale_available_until_element.attrs[
                            "title"
                        ]
                        break
                sale_available_until = country_row.find("span").attrs["title"]
                country_name = country_row.find("td", class_=None).text.strip()
                game_infos = {
                    **game_infos,
                    "county": country_name,
                    "sale": sale_available_until,
                }
                game_list.append(game_infos)
                logging.info(f'COLETADO o game "{game_infos}"')
            else:
                logging.info(
                    f'Jogo "{game_infos}" NÃO coletado devido ao valor de R$ {monetary_value} estar acima do esperado R$ {desired_price}'
                )
        request_time_interval = uniform(1, 5)
        logging.info(f"Aguardando o intervalo de {request_time_interval:.2f} segundos")
        time.sleep(request_time_interval)
    logging.info(
        f"Concluída a raspagem com um total de {len(game_list)} jogos retornados"
    )
