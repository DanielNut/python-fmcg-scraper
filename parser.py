import base64
import requests
import yadisk
import re
import typing as tp

from bs4 import BeautifulSoup


class Product:
    def __init__(self, url: str, good_name: str, brand_name: str, description: str, images: tp.List[str]):
        self.url = url
        self.good_name = good_name
        self.brand_name = brand_name
        self.description = description
        self.images = images


class Browser:
    """
    Class for searching
    """
    def __init__(self, url: str, selector: tuple):
        self.url = url
        self.selector = selector


class ProductListingBrowser:
    def __init__(self, url: str, products_selector: tuple, page_topic: str, page_number: int = 1):
        self.url = url
        self.product_selector = products_selector
        self.page_topic = page_topic
        self.page_number = page_number

    def get_full_url(self):
        return self.url + self.page_topic + str(self.page_number)

    def increment_page_number(self):
        self.page_number += 1


class ProductBrowser:
    def __init__(self, url: str, goodNameTag: tuple, brandNameTag: tuple, imgTag: tuple, descriptionTag: tuple):
        self.url = url
        self.goodNameTag = goodNameTag
        self.brandNameTag = brandNameTag
        self.imgTag = imgTag
        self.descriptionTag = descriptionTag


class YandexDiskWorker:
    """
    Class for saving product info to specified yandex directory
    """
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
    """
    Class for scraping with random ip
    """
    def __init__(self):
        self.api_key = 'uVRZ8LWAucYxuCrcNy34F4BUfwSR2z7q'

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


def normalizeImage(image):
    image_formatted = image['base64_string'].split(',')[1]
    image_base64 = base64.b64decode(image_formatted)
    return image_base64


class Crawler:
    def __init__(self):
        pass

    def getPage(self, url: str) -> tp.Optional[BeautifulSoup]:
        """
        :param url: url of webpage
        :return: BeautifulSoup object of webpage
        """
        request_handler = RequestHandler()
        try:
            res = request_handler.get(url).text
        except requests.exceptions.RequestException:
            return None
        bs = BeautifulSoup(res)
        return bs

    def getSingleElement(self, page: BeautifulSoup, selector: tuple) -> tp.Optional[str]:
        elem = page.find(*selector)
        if elem:
            return elem
        return None

    def getMultipleElements(self, page: BeautifulSoup, selector: tuple) -> tp.Optional[list]:
        elems = page.find_all(*selector)
        if elems and len(elems) > 0:
            return elems
        return None

    def getUrlListFromPage(self, site: Browser) -> tp.Optional[list]:
        """
        Get list of links for further scraping from middle site page
        :param site: Browser instance of webpage
        :return: list of urls or None if there are no urls
        """
        page = self.getPage(site.url)
        selector = site.selector
        elems = self.getMultipleElements(page, selector)
        urls = []
        for elem in elems:
            urls.append(elem.attrs['src'])
        if urls and len(urls) > 0:
            return urls
        return None

    def parseProductListingPage(self, site: ProductListingBrowser, selector: str) -> tp.Optional[list]:
        """
        Get list of product links for further scraping
        :param site: Browser instance of webpage
        :param selector: css selector string
        :return: list of urls or None if there are no urls
        """
        url = site.url
        page = self.getPage(url)

        #TODO

    def parseProductPage(self, site: ProductBrowser) -> tp.Optional[Product]:
        """
        Get product info, return Product object
        :param site: Browser instance of product webpage
        :param selector: css selector for
        :return:
        """
        page = self.getPage(site.url)

        img_tag = site.imgTag
        good_name_tag = site.goodNameTag
        brand_name_tag = site.brandNameTag
        description_tag = site.descriptionTag

        image_url = page.find(img_tag).attrs['src']
        image_json = self.parseImage(image_url)
        image = normalizeImage(image_json)
        brand_name = page.find(brand_name_tag).get_text()
        good_name = page.find(good_name_tag).get_text()
        description = page.find(description_tag).get_text()

        result = {
            'name': '',
            'description': '',
            'image': image}


    def parseImage(self, url):
        request_handler = RequestHandler()
        res = request_handler.get(url).json()
        return res


if __name__ == "__main__":

    wildberries_selectors = {'main_page': '',
                             'catalog_page': '',
                             'product_listing_page': '',
                             'product_page': ['']}
    cr = Crawler()
    main_page = wildberries_selectors['main_page']
    page = cr.getPage()







# Парсинг страниц:

# Класс Сrawler, содержащий методы открытия сайта по url и поиска
#   Методы: открытия страницы, нахождения разделов, нахождения категорий товаров в разделах,
#           нахождения товаров по категориям, получения данных по этим товарам
# Класс контент, содержащий данные о

# Какие данные нужны:

# Данные товара:
# Название
# Картинка
# Описание

# Данные категории продуктов:
# Название
# Список ссылок на товары (возможно генератор)

# Данные рынка
# Список категорий

# Основная страница - с неё получаем данные о рынках




