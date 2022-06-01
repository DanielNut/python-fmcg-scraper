import time
import json
import csv
import re
import sys
import typing as tp
import argparse

import requests
import PIL
import yadisk
import concurrent.futures
import selenium.common.exceptions
import telegram_send
import io
import pillow_avif

from typing import Tuple, Any
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
from bs4 import BeautifulSoup
from tqdm import tqdm

from main import (
    YandexDiskWorker,
    set_selenium_driver,
    add_url_to_scraped,
    get_directories,
    scroll_page_to_bottom_selenium,
    get_product_links_from_page,
    get_product_data,
    get_product_comments_image_links_selenium,
    normalize_url,
    save_product_data,
    add_url_to_scraped,
)


class MetaCategory:
    def __init__(self, metacat_url: str):
        self.metacat_url = metacat_url
        self.scraped_urls = scraped_urls

    def get_categories(self, driver: webdriver.Firefox):
        driver.get(self.metacat_url)
        categories_li_list = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '.menu-catalog__list-2'))).find_elements(By.TAG_NAME, 'li')
        categories_urls = [cat_li.find_element(By.TAG_NAME, 'a').get_attribute('href')
                           for cat_li in categories_li_list]
        return categories_urls


class CategoryGoods:
    def __init__(self, cat_url, scraped_urls: set):
        self.cat_url = cat_url
        self.scraped_urls = scraped_urls

    def get_subcategories_for_normal_categories(self, category_url, driver: webdriver.Firefox) -> list[str]:
        driver.get(category_url)

        try:
            catalog_page_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#catalog > div.catalog-page__side')))
            catalog_page_ul = catalog_page_div.find_element(By.CLASS_NAME,
                                                            'sidemenu').find_element(By.TAG_NAME, 'ul')
            catalog_li_tags = catalog_page_ul.find_elements(By.TAG_NAME, 'li')
            catalog_li_urls = [tag.find_element(By.TAG_NAME, 'a').get_attribute('href') for tag in catalog_li_tags]
        except (selenium.common.exceptions.TimeoutException,
                selenium.common.exceptions.NoSuchElementException):
            return [driver.current_url]
        subcategories_urls = []
        for subcat_url in catalog_li_urls:
            try:
                driver.get(subcat_url)
                subcat_li_subs = WebDriverWait(driver, 5).until(EC.presence_of_element_located((
                    By.XPATH, '/html/body/div[1]/main/div[2]/div/div/div[5]/div[1]/div/ul/li/ul/li/ul'
                ))).find_elements(By.TAG_NAME, 'li')

                subcategories_urls += [sub.find_element(By.TAG_NAME, 'a').get_attribute('href') for sub in
                                       subcat_li_subs]
            except selenium.common.exceptions.TimeoutException:
                subcategories_urls.append(subcat_url)
        return subcategories_urls

    def get_subcategories_for_suspicious_categories(self, category_url: str, driver: webdriver.Firefox) -> list[str]:
        driver.get(category_url)

    def get_filter_labels(self, subcategory_url: str, driver: webdriver.Firefox):
        driver.get(subcategory_url)
        try:
            buttons_div = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, '.list_left_xsubject')))

            labels = buttons_div.find_elements(By.TAG_NAME, 'label')
            return labels
        except selenium.common.exceptions.TimeoutException:
            return []

    def get_goods_by_filter_of_subcategory(self, current_dir, fil, yadisk_worker, driver):
        fil.click()
        last_page = False
        while not last_page:
            try:
                scroll_page_to_bottom_selenium(driver)
                product_links = get_product_links_from_page(driver)
                prev_url = driver.current_url
                print(f'prev url = {prev_url}')
                for link in product_links:
                    normal_url = normalize_url(link)
                    if normal_url not in self.scraped_urls:
                        print(f'product url = {normal_url}')
                        save_product_data(normal_url, current_dir, yadisk_worker, driver)
                        add_url_to_scraped(normal_url)
                    else:
                        print(f'Такой продукт {normal_url} уже был обработан')
                driver.get(prev_url)
                scroll_page_to_bottom_selenium(driver)
                if not turn_on_next_page_of_product_list(driver):
                    last_page = True
            except selenium.common.exceptions.TimeoutException:
                print('Функция get_goods_by_filter_of_subcategory вылетела с ошибкой')
                pass

    def get_goods(self, driver: webdriver.Firefox, yadisk_worker: YandexDiskWorker):
        subs_urls = self.get_subcategories_for_normal_categories(self.cat_url, driver)
        print('subs_urls = ', subs_urls)
        for sub_url in subs_urls:
            if sub_url not in self.scraped_urls:
                dirs = get_directories(sub_url)
                add_dirs_to_fmcg_wildberries(dirs, yadisk_worker)
                print('dirs = ', dirs)

                filter_labels_count = len(self.get_filter_labels(sub_url, driver))

                for i in range(filter_labels_count):
                    try:
                        product_data_driver = set_selenium_driver()
                        filter_labels = self.get_filter_labels(sub_url, product_data_driver)
                        label = filter_labels[i]
                        filter_name = label.text
                        normal_filter_name = normalize_filter_name(filter_name)
                        product_dir = [dirs[-1] + '/' + normal_filter_name]
                        print('product_dir = ', product_dir)
                        add_dirs_to_fmcg_wildberries(product_dir, yadisk_worker)
                        full_product_dir = 'FMCG/Wildberries/' + dirs[-1] + '/' + normal_filter_name
                        self.get_goods_by_filter_of_subcategory(full_product_dir, label, yadisk_worker,
                                                                product_data_driver)
                        product_data_driver.quit()
                    except IndexError:
                        print('IndexError в функции get_goods')
                        pass
                add_url_to_scraped(sub_url)

    def get_product_data(self, driver):
        pass


def add_filter_name_to_dirs(dirs: list[str], filter_name: str):
    normal_filter_name = normalize_filter_name(filter_name)
    dirs.append(dirs[-1] + '/' + normal_filter_name)


def add_dirs_to_fmcg_wildberries(dirs, yadisk_worker):
    base_dir = 'FMCG/Wildberries/'
    for dir in dirs:
        yadisk_worker.mkdir(base_dir + dir)


def normalize_filter_name(filter_name: str):
    for i in range(len(filter_name)):
        if filter_name[i] == '(':
            normalized_name = filter_name[:i-1]
            return normalized_name


def turn_on_next_page_of_product_list(driver) -> bool:
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH, '/html/body/div[1]/main/div[2]/div/div/div[6]/div[1]/div[5]/div/div/a[7]'))).click()
        return True
    except selenium.common.exceptions.TimeoutException:
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='My example explanation')

    parser.add_argument(
        '-f',
        '--scraped_urls_file',
        type=str,
        default='scraped_urls.csv',
        help='file which contains urls of products and categories which are already scraped'
    )

    parser.add_argument(
        '-u',
        '--category_url',
        type=str,
        default='https://www.wildberries.ru/catalog/pitanie',
        help='category or metacategory url to be parsed'
    )

    parser.add_argument(
        '-m',
        '--metacategory',
        action=argparse.BooleanOptionalAction,
        type=bool,
        default=True,
        help='if category is metacategory. This means that it has extra layer'
    )

    my_namespace = parser.parse_args()

    scraped_urls_file = my_namespace.scraped_urls_file

    category_url = my_namespace.category_url

    is_metacategory = my_namespace.metacategory

    yadisk_worker = YandexDiskWorker()
    scraped_urls = set()
    try:
        with open(scraped_urls_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row:
                    scraped_urls.add(row[0])
    except FileNotFoundError:
        f = open(scraped_urls_file, 'w+')
        f.close()
    driver = set_selenium_driver()

    if is_metacategory:
        metacat = MetaCategory(category_url)
        category_urls = metacat.get_categories(driver)
        for cat_url in category_urls:
            category_handler = CategoryGoods(cat_url, scraped_urls)
            category_handler.get_goods(driver, yadisk_worker)
    else:
        category = CategoryGoods(category_url, scraped_urls)
        category.get_goods(driver, yadisk_worker)

