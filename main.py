import time
import json
import csv
import re
import typing as tp
import requests
# import PIL
import yadisk
import concurrent.futures
import selenium.common.exceptions
import telegram_send
import io
import pillow_avif

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from webdriver_manager.firefox import GeckoDriverManager

from fake_useragent import UserAgent
from PIL import Image
from tqdm import tqdm


class YandexDiskWorker:
    def __init__(self):
        self.token = 'AQAAAAA4lr32AAfSFTV5rc9Tq0eBhLEHCBqO7-A'
        self.yadisk = yadisk.YaDisk(token=self.token)

    def mkdir(self, path):
        try:
            self.yadisk.mkdir(path)
        except yadisk.exceptions.PathExistsError:
            message = f'Папка {path} Уже существует'
            telegram_send.send(messages=[message])

    def save_info(self, info: dict) -> None:
        path = info['path']
        name = self.normalize_product_name(info['name'])
        print(f'path = {path}')
        print(f'normalized name = {name}')
        # CREATE MAIN FOLDER
        product_path = f'{path}/{name}'
        self.mkdir(product_path)

        # CREATE MAIN PHOTO FOLDER
        main_images_path = f'{product_path}/main_images'
        self.mkdir(main_images_path)

        # CREATE PHOTO FOLDER FOR COMMENTS
        comment_images_path = f'{product_path}/comment_images'
        self.mkdir(comment_images_path)

        # SAVE MAIN PHOTOS
        save_func = self.save_jpg_image
        image_urls = info['image_urls']
        pattern = re.compile('.*\.avif')
        if pattern.match(image_urls[0]):
            save_func = self.save_avif_image
        print(save_func)
        i = 0
        for image_url in info['image_urls']:
            image_path = f'{product_path}/main_images/{i}'
            try:
                save_func(image_url, image_path)
            except yadisk.exceptions.PathExistsError:
                message = f'Картинка \t {image_path} уже существует'
                telegram_send.send(messages=[message])
            i += 1

        # SAVE DESCRIPTION
        description_path = f'{product_path}/description.json'
        try:
            with open('description.json', 'w', encoding='utf8') as file:
                json.dump(info['description'], file, ensure_ascii=False, indent=4)

            self.yadisk.upload('description.json', description_path)
        except yadisk.exceptions.PathExistsError:
            print(f'Описание {description_path} уже существует')

    def save_jpg_image(self, url, path):
        image = requests.get(url).content
        with open('img', 'wb') as f:
            f.write(image)

        self.yadisk.upload('img', path)

    def save_avif_image(self, url: str, path):
        print(url)
        if not url.endswith('gif'):
            image_bytes = requests.get(url).content
            im = io.BytesIO(image_bytes)
            # print('io', im)
            im = Image.open(im)

            with open('img', 'wb') as f:
                f.write(image_bytes)

            # im = self.open_image('img')
            # print(im)
            try:
                im.save('img.jpg')
                self.yadisk.upload('img.jpg', path)
            except (OSError, AttributeError):
                pass

    # def open_image(self, image_path):
    #     try:
    #         image = Image.open(image_path)
    #         return image
    #     except PIL.UnidentifiedImageError:
    #         return

    def save_comment_image_by_name_of_product(self, image, product_path, product_name, image_name):
        product_name = self.normalize_product_name(product_name)
        image_path = f'{product_path}/{product_name}/comment_images/{image_name}'
        try:
            with open('img', 'wb') as f:
                f.write(image)
            self.yadisk.upload('img', image_path)
        except yadisk.exceptions.PathExistsError:
            message = f'Картинка {image_path} уже существует либо такое название уже занято'
            telegram_send.send(messages=[message])

    def normalize_product_name(self, name: str) -> str:
        return name.replace('/', '_').replace(':', '-').replace(' ', '_')


class RequestHandler:
    def __init__(self):
        pass

    def get(self, url):
        try:
            time.sleep(1)
            return requests.get(url, timeout=3)
        except:
            time.sleep(1)
            return requests.get(url, timeout=5)


# class RequestHandler:
#     def __init__(self):
#         self.proxy_list = []
#         self.working_proxies = []
#         with open('proxies.csv', 'r') as f:
#             reader = csv.reader(f)
#             for row in reader:
#                 self.proxy_list.append(row[0])
#         self.get_working_proxies(self.proxy_list)
#
#     def extract(self, proxy):
#         url = 'https://www.wildberries.ru/'
#         try:
#             resp = requests.get(url, proxies={'http': proxy, 'https': proxy}, timeout=3)
#             self.working_proxies.append(proxy)
#         except:
#             pass
#         return proxy
#
#     def get_working_proxies(self, proxies):
#         with concurrent.futures.ThreadPoolExecutor() as executor:
#             executor.map(self.extract, proxies)
#
#     def get(self, url: str):
#         """
#         function for opening url through proxy
#         :param url:
#             url of web page
#         :return:
#             Html text
#         """
#         i = 1
#         proxy = self.working_proxies[i]
#         while i < len(self.working_proxies):
#             try:
#                 proxies = {'http': proxy,
#                            'https': proxy}
#                 print(proxy)
#                 response = requests.get(url, proxies=proxies, timeout=1)
#                 return response
#             except:
#                 proxy = self.working_proxies[i]
#                 i += 1


def get_all_product_data_to_disk(product_url, driver):
    pass


def get_product_data(product_url: str, driver) -> dict:
    driver.get(product_url)
    time.sleep(1)

    # IMPORTANT!!! good_name and description have to be searched before images
    # OR closing of main image preview must be added to get_main_images_urls_from_product_page function
    good_name = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                                '/html/body/div[1]/main/div['
                                                                                '2]/div/div/div[2]/div/div['
                                                                                '2]/h1/span[2]'))).text

    description_text = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                                       '/html/body/div['
                                                                                       '1]/main/div['
                                                                                       '2]/div/div/div[3]/div['
                                                                                       '1]/section[3]/div[2]/div['
                                                                                       '1]/p'))).text

    image_urls = get_main_images_urls_from_product_page(driver)
    # images = get_images_by_links(images_urls)
    # print(image_urls)
    description = {'name': good_name,
                   'url': product_url,
                   'description': description_text}

    info = {'name': good_name,
            'description': description,
            'image_urls': image_urls
            }
    return info


def get_product_comments_image_links_selenium(product_url: str, driver) -> tp.Optional[list]:
    driver.get(product_url)
    time.sleep(1)
    #
    scroll_page_to_bottom_selenium(driver)
    time.sleep(3)
    photos_links = get_photos_links_from_comments_of_product_page_wildberries(driver)
    #
    return photos_links


class WildberriesParser:
    """
    Class for Wildberries site parsing
    """

    # Секции, категории в каждой из секций, в категориях уже товары

    def __init__(self, scraped_urls, is_active=True):
        if is_active:
            self.scraped_urls = scraped_urls
            self.base_urls = {'base': 'https://www.wildberries.ru',
                              'food': 'https://www.wildberries.ru/catalog/pitanie'}
            self.main_yandex_dir = '/FMCG/Wildberries'
            self.current_dir = ''
            self.dirs_to_append = []
            # Обработчик запросов, эта строка обязательно здесь
            self.request_handler = RequestHandler()

            # Заполнение секций товаров ...
            self.sections_urls = {}
            self.get_sections()
        # for section_name, section_url in self.sections_urls.items():
        #     add_url_to_scraped(section_url)

    def get_sections(self):
        sections_json = self.request_handler.get('https://www.wildberries.ru/gettopmenuinner?lang=ru').json()
        menu = sections_json['value']['menu']
        for section in menu:
            url = section['pageUrl']
            if url.startswith('/catalog'):
                section_name = section['name'].lower()
                self.sections_urls[section_name] = self.base_urls['base'] + url

    def get_categories_urls_by_section(self, section_name, driver) -> tp.Optional[list]:
        """
        List of food categories urls
            In format 'https://www.wildberries.ru/catalog/produkty/vkusnye-podarki'
        """
        section_url = self.sections_urls[section_name]
        driver.get(section_url)
        time.sleep(1)

        catalog_div = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME,
                                                                                      'menu-catalog')))
        catalog = catalog_div.find_element(By.CLASS_NAME, 'menu-catalog__list-2')

        if not catalog:
            catalog = driver.find_element(By.CLASS_NAME, 'menu-catalog-second__wrapper')
        if not catalog:
            catalog = driver.find_element(By.CLASS_NAME, 'banners-catalog-custom')
        telegram_send.send(messages=[f'Обрабатывается каталог {catalog}'])
        if not catalog:
            # self.sections[section_name]
            return []
        categories_urls = []
        for link in catalog.find_elements(By.TAG_NAME, 'a'):
            try:
                category_href = link.get_attribute('href')
                categories_urls.append(category_href)
            except:
                pass
        return categories_urls

    def get_products_by_category(self, category_url: str, driver) -> None:
        yandex_disk_worker = YandexDiskWorker()

        self.dirs_to_append = get_directories(category_url)
        self.current_dir = self.main_yandex_dir + '/' + self.dirs_to_append[-1]
        for dir in self.dirs_to_append:
            yandex_disk_worker.mkdir(self.main_yandex_dir + '/' + dir)
        page_id = 1
        category_url_with_page = category_url + f'?page={page_id}'
        telegram_send.send(messages=[f'Обрабатывается страница {category_url_with_page}'])
        driver.get(category_url_with_page)
        time.sleep(1)
        end_of_category = False
        while not end_of_category:
            # bs.find('div', {'id': 'divGoodsNotFound', 'class': ['hide']}):
            goods_not_found = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID,
                                                                                              'divGoodsNotFound')))
            if goods_not_found.get_attribute('class') == 'hide':
                product_card_list = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'catalog-content')))
                all_links = product_card_list.find_elements(By.TAG_NAME, 'a')
                products_urls_from_single_page = []
                pattern = re.compile('.*\/catalog\/.*\/detail\.aspx\?targetUrl=GP')
                for link in all_links:
                    href = link.get_attribute('href')
                    if pattern.match(href):
                        products_urls_from_single_page.append(href)

                for product_url in tqdm(products_urls_from_single_page):
                    # print(product_url)
                    normal_product_url = normalize_url(product_url)
                    if normal_product_url in self.scraped_urls:
                        print(f'url {normal_product_url} is already scraped')
                        continue
                    info = get_product_data(normal_product_url, driver)
                    info['path'] = self.current_dir
                    yandex_disk_worker.save_info(info)
                    image_links = get_product_comments_image_links_selenium(normal_product_url, driver)
                    image_number = 1
                    for link in image_links:
                        image = self.request_handler.get(link).content
                        yandex_disk_worker.save_comment_image_by_name_of_product(image, info['path'],
                                                                                 info['name'], f'{image_number}')
                        image_number += 1
                    add_url_to_scraped(normal_product_url)

                    page_id += 1
                    category_url_with_page = category_url + f'?page={page_id}'
            else:
                end_of_category = True

    def get_goods(self) -> None:
        """
        :return:
        get product data(image, description) and save to specified Yandex disk directory
        """
        # Сделать постраничную загрузку товаров (в категориях не сколько страниц)...
        driver = set_selenium_driver()
        for section_name, section_url in self.sections_urls.items():
            if section_url in self.scraped_urls:
                print(f'Секция {section_name} : {section_url} уже обработана')
                continue
            categories_urls = self.get_categories_urls_by_section(section_name, driver)
            print(f'categories_urls: {categories_urls}')
            for category_url in categories_urls:
                self.get_products_by_category(category_url, driver)
                time.sleep(1)


def save_product_data(product_url, current_yandex_dir, yandex_disk_worker, driver):
    request_handler = RequestHandler()
    info = get_product_data(product_url, driver)
    info['path'] = current_yandex_dir
    yandex_disk_worker.save_info(info)
    image_links = get_product_comments_image_links_selenium(product_url, driver)
    image_number = 1
    for link in image_links:
        image = request_handler.get(link).content
        yandex_disk_worker.save_comment_image_by_name_of_product(image, info['path'],
                                                                 info['name'], f'{image_number}')
        image_number += 1


def get_product_links_from_page(driver) -> list[str]:
    product_card_list = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'catalog-content')))
    all_links = product_card_list.find_elements(By.TAG_NAME, 'a')
    products_urls_from_single_page = []
    pattern = re.compile('.*\/catalog\/.*\/detail\.aspx\?targetUrl=GP')
    for link in all_links:
        href = link.get_attribute('href')
        if pattern.match(href):
            products_urls_from_single_page.append(href)
    return products_urls_from_single_page


def get_directories(category_url: str) -> list:
    path_list = category_url.split('/')
    after_catalog = False
    path = []
    for dir in path_list:
        if after_catalog:
            if path:
                path.append(path[-1] + '/' + dir)
            else:
                path.append(dir)
        if dir == 'catalog':
            after_catalog = True
    print(path)
    return path


def scroll_page_to_bottom_selenium(driver):
    SCROLL_PAUSE_TIME = 0.3
    time.sleep(2)
    # Get scroll height
    step = 500
    y = step
    while True:
        # Scroll down to bottom
        driver.execute_script(f"window.scrollTo(0, {y});")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")

        if y >= new_height:
            break
        y += step


def get_visible_slice_of_photos_from_users_photos_scrollbox_on_product_page_wilberries(driver):
    user_photos = driver.find_element(By.CLASS_NAME, "comments__user-photos")
    photos_div = user_photos.find_element(By.CLASS_NAME, 'swiper-wrapper')
    photos = photos_div.find_elements(By.CLASS_NAME, 'swiper-slide')
    return photos


def get_photos_links_from_comments_of_product_page_wildberries(driver):
    images_preview = get_images_preview(driver)
    links = []
    stop = False
    time.sleep(1)
    if images_preview:
        image = get_image_on_preview(driver)
        links.append(image)
        amount = 110
        i = 0
        while i < amount:
            # i = 0
            try:
                turn_to_next_image_on_preview(driver)
                i += 1
            except (selenium.common.exceptions.ElementNotInteractableException,
                    selenium.common.exceptions.ElementClickInterceptedException):
                another_links = get_images_on_preview(driver)
                links += another_links
                return links
        another_links = get_images_on_preview(driver)
        links += another_links
        return links
    return []


def get_images_preview(driver):
    try:
        user_photos = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME,
                                                                                      "comments__user-photos")))
    except selenium.common.exceptions.TimeoutException:
        print('Не удалось найти фотки в комментах')
        return []
        # driver.find_element(By.CLASS_NAME, "comments__user-photos")
    # TODO: Сделать webdriverwait
    photos_div = user_photos.find_element(By.CLASS_NAME, 'swiper-wrapper')
    photos_div.find_element(By.CLASS_NAME, 'swiper-slide').click()
    # WebDriverWait(driver, 10).until(EC.presence_of_element_located(
    #     photos_div.find_element(By.CLASS_NAME, 'swiper-slide'))).click()
    # photos_div.find_element(By.CLASS_NAME, 'swiper-slide').click()
    try:
        images_preview = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME,
                                                                                     'thumbs-gallery__big-img')))
        return images_preview
    except selenium.common.exceptions.TimeoutException:
        try:
            driver.find_elements(By.CLASS_NAME, 'swiper-slide')[1].click()
            images_preview = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME,
                                                                                             'thumbs-gallery__big-img')))
            return images_preview
        except selenium.common.exceptions.TimeoutException:

            return []


def get_image_on_preview(driver) -> str:
    image_div = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div[1]/div/div/div[1]')
    image_src = image_div.find_element(By.TAG_NAME, 'img').get_attribute('src')
    return image_src


def get_images_on_preview(driver) -> list[str]:
    images_div = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div[1]/div/div')
    images = images_div.find_elements(By.CLASS_NAME, 'swiper-slide')
    images_src = [image.find_element(By.TAG_NAME, 'img').get_attribute('src') for image in images]
    return images_src


def turn_to_next_image_on_preview(driver) -> None:
    driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div[1]/button[2]').click()


def get_main_preview(driver):
    driver.find_element(By.ID, 'imageContainer').click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                    '//*[@id="photo"]')))


def get_image_url_from_main_preview(driver) -> str:
    '/html/body/div[1]/div/div/div[1]/div/div'
    return WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.XPATH, '/html/body/div[1]/div/div/div[1]/div/div/div[1]/img'))).get_attribute('src')


def turn_to_next_image_on_main_preview(driver):
    driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div[1]/button[2]').click()


def get_main_images_urls_from_product_page(driver) -> list[str]:
    get_main_preview(driver)
    time.sleep(1)
    image_urls = []
    last_image = False
    while not last_image:
        try:
            # image_url = get_image_url_from_main_preview(driver)
            # images_urls.append(image_url)
            turn_to_next_image_on_main_preview(driver)
        except:
            last_image = True
    image_wrapper_div = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div/div[1]/div/div')))
    image_divs = image_wrapper_div.find_elements(By.CLASS_NAME, 'swiper-slide')
    image_urls = [image_div.find_element(By.TAG_NAME, 'img').get_attribute('src') for image_div in image_divs]
    print(image_urls)
    return image_urls


def add_url_to_scraped(url):
    with open('scraped_urls.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([f'{url}'])

# TODO
def get_image_by_url(image_url):
    pass


# TODO
def normalize_image():
    pass


def is_url_parsed(url):
    pass


def normalize_url(url: str) -> str:
    if url.startswith('/'):
        url = 'https://www.wildberries.ru' + url
    return url


def set_selenium_driver():
    options = Options()
    ua = UserAgent(verify_ssl=False)
    userAgent = ua.random
    options.add_argument(f'user-agent={userAgent}')
    options.add_argument("--disable-popup-blocking")
    # options.add_argument('headless')

    options = webdriver.FirefoxOptions()
    options.add_argument(f'user-agent={userAgent}')
    options.add_argument('headless')

    # binary = '/home/daniel/Downloads/firefox'

    gecko = "~/Downloads/geckodriver"
    firefox_binary = FirefoxBinary(gecko)
    # browser = webdriver.Firefox(firefox_binary=binary)
    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()))
    # driver = webdriver.Firefox(firefox_binary=firefox_binary, executable_path=gecko, options=options)
    return driver


def get_images_by_links(images_links):
    rh = RequestHandler()
    images = []
    for image_url in images_links:
        image = rh.get(image_url).content
        images.append(image)
    return images


if __name__ == "__main__":
    scraped_urls = set()
    with open('scraped_urls.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row:
                scraped_urls.add(row[0])
    wb = WildberriesParser(scraped_urls)
    wb.get_goods()
