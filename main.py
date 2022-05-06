import base64
import requests
import yadisk
import re
import typing as tp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



from bs4 import BeautifulSoup



class YandexDiskWorker:
    def __init__(self):
        self.token = 'AQAAAAA4lr32AAfSFTV5rc9Tq0eBhLEHCBqO7-A'
        self.yadisk = yadisk.YaDisk(token=self.token)

    def save_info(self, info: dict) -> None:
        try:
            self.yadisk.mkdir(f'/FMCG/Wildberries/{info["name"]}')
        except yadisk.exceptions.PathExistsError:
            print('Папка Уже существует')

        try:
            with open('img', 'wb') as f:
                f.write(info['image'])
            self.yadisk.upload('img', f'/FMCG/Wildberries/{info["name"]}/{info["name"]}')
        except yadisk.exceptions.PathExistsError:
            print('Картинка Уже существует')

        try:
            with open('description.txt', 'w') as f:
                f.write(info['description'])
            self.yadisk.upload('description.txt', f'/FMCG/Wildberries/{info["name"]}/{info["name"]}.txt')
        except yadisk.exceptions.PathExistsError:
            print('Описание уже существует')


class RequestHandler:
    def __init__(self):
        self.api_key = 'G2UlPfVQr2ZLrwXz418tLNambJe5jqSm'

    def get(self, url: str):
        """
        function for opening url through proxy
        :param url:
            url of web page
        :return:
            Html text
        """
        api_url = "https://api.webscrapingapi.com/v1"
        params = {
            "api_key": self.api_key,
            "url": url
        }
        response = requests.get(api_url, params=params)
        return response


class WildberriesParser:
    """
    Class for Wildberries site parsing
    """

    # Секции, категории в каждой из секций, в категориях уже товары

    def __init__(self):
        self.base_urls = {'base': 'https://www.wildberries.ru',
                          'food': 'https://www.wildberries.ru/catalog/pitanie'}

        # Обработчик запросов, эта строка обязательно здесь
        self.request_handler = RequestHandler()

        # Заполнение секций товаров ...
        self.sections_urls = {}
        self.get_sections()

    def get_sections(self):
        sections_json = self.request_handler.get('https://www.wildberries.ru/gettopmenuinner?lang=ru').json()
        menu = sections_json['value']['menu']
        for section in menu:
            url = section['pageUrl']
            if url.startswith('/catalog'):
                section_name = section['name'].lower()
                self.sections_urls[section_name] = self.base_urls['base'] + url

    def get_categories_urls_by_section(self, section_name) -> tp.Optional[list]:
        """
        List of food categories urls
            In format 'https://www.wildberries.ru/catalog/produkty/vkusnye-podarki'
        """
        section_url = self.sections_urls[section_name]
        html = self.request_handler.get(section_url).text
        bs = BeautifulSoup(html, 'html.parser')
        catalog = bs.find('ul', {'class': 'menu-catalog__list-2'})
        if not catalog:
            catalog = bs.find('ul', {'class': 'menu-catalog-second__wrapper'})
        if not catalog:
            catalog = bs.find('div', {'class': 'banners-catalog-custom'})
        if not catalog:
            # self.sections[section_name]
            return []
        categories_urls = []
        for link in catalog.find_all('a'):
            if 'href' in link.attrs:
                category_href = str(link.attrs['href'])
                category_name = category_href.split('/')[-1]
                full_url = self.base_urls['base'] + category_href
                categories_urls.append(full_url)
                return categories_urls

    def get_products_by_category(self, category_url: str) -> None:
        yandex_disk_worker = YandexDiskWorker()
        page_id = 1
        category_url_with_page = category_url + f'?page={page_id}'
        html = self.request_handler.get(category_url_with_page).text
        bs = BeautifulSoup(html, 'html.parser')

        while bs.find('div', {'id': 'divGoodsNotFound', 'class': ['hide']}):
            product_links = bs.find_all('a', href=re.compile('\/catalog\/.*\/detail\.aspx\?targetUrl=GP'))

            products_urls_from_single_page = [a.attrs['href'] for a in product_links]
            for product_url in products_urls_from_single_page:
                info = self.get_product_data(product_url)
                yandex_disk_worker.save_info(info)

            page_id += 1
            category_url_with_page = category_url + f'?page={page_id}'
            html = self.request_handler.get(category_url_with_page).text
            bs = BeautifulSoup(html, 'html.parser')

    def get_product_data(self, product_url: str) -> dict:
        driver = webdriver.Firefox()
        driver.get("http://somedomain/url_that_delays_loading")
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "myDynamicElement"))
            )
        finally:
            driver.quit()
        normal_url = normalize_url(product_url)
        product_html = self.request_handler.get(normal_url).text
        product_soup = BeautifulSoup(product_html, 'html.parser')

        good_name = product_soup.find('span', {'data-link': 'text{:product^goodsName}'})
        # brand_name = product_soup.find('span', {'data-link': 'text{:product^brandName}'})

        formatted_name = good_name.contents[0].split('/')[0].split(':')[0]

        description = product_soup.find('p', {'class': 'collapsable__text',
                                              'data-link': 'text{:product^description}'})
        description_text = ''
        if description.contents:
            description_text = description.contents[0]

        image_relative_url = product_soup.find('div', {'class': "current"}).find('img').attrs['src']
        image_full_url = 'https:' + image_relative_url

        image = self.request_handler.get(image_full_url).json()
        image_base64 = base64.b64decode(image['base64_string'].split(',')[1])

        info = {'name': formatted_name,
                'description': description_text,
                'image': image_base64
                }
        return info

    def get_goods(self) -> None:
        """
        :return:
        get product data(image, description) and save to specified Yandex disk directory
        """
        # Сделать постраничную загрузку товаров (в категориях не сколько страниц)...

        for section_name, section_url in self.sections_urls.items():
            categories_urls = self.get_categories_urls_by_section(section_name)
            for category_url in categories_urls:
                self.get_products_by_category(category_url)


def isUrlParsed(url):
    pass


def normalize_url(url: str) -> str:
    if url.startswith('/'):
        url = 'https://www.wildberries.ru' + url
    return url


if __name__ == "__main__":
    wb = WildberriesParser()
    wb.get_goods()
