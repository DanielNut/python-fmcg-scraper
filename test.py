import time

import selenium.common.exceptions

from main import RequestHandler
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent


from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

from selenium.webdriver.firefox.firefox_binary import FirefoxBinary


options = Options()
ua = UserAgent(verify_ssl=False)
userAgent = ua.random
options.add_argument(f'user-agent={userAgent}')
options.add_argument("--disable-popup-blocking")
#options.add_argument('headless')

options = webdriver.FirefoxOptions()
options.add_argument(f'user-agent={userAgent}')
options.add_argument('headless')

# binary = '/home/daniel/Downloads/firefox'

firefox_binary = FirefoxBinary()
gecko = "/home/daniel/Downloads/geckodriver"
# browser = webdriver.Firefox(firefox_binary=binary)
# driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()))
driver = webdriver.Firefox(firefox_binary=firefox_binary, executable_path=gecko, options=options)


# driver = webdriver.Firefox()
# driver.get('https://www.wildberries.ru/catalog/34829102/detail.aspx?targetUrl=GP')
# driver.get('https://www.wildberries.ru/catalog/16023990/detail.aspx?targetUrl=XS')
driver.get('https://www.wildberries.ru/catalog/19889788/detail.aspx?targetUrl=XS')

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

# driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
# element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME,
#                                                                           "product-detail__user-activity")))


def get_photos(driver):
    user_photos = driver.find_element(By.CLASS_NAME, "comments__user-photos")
    photos_div = user_photos.find_element(By.CLASS_NAME, 'swiper-wrapper')
    photos = photos_div.find_elements(By.CLASS_NAME, 'swiper-slide')
    return photos


photos = get_photos(driver)
links = []
step_size = 9
stop = False
time.sleep(1)
links += [photo.find_element_by_tag_name('img').get_attribute('src') for photo in photos]
while not stop:
    # try:
    i = 0
    while i < step_size:
        WebDriverWait(driver, 50).until(EC.invisibility_of_element((By.CLASS_NAME,
                                                                    'swiper-slide img-plug swiper-slide-active')))
        # WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.CLASS_NAME,
        #                                                             'sw-slider-user-images'))).click()
        driver.execute_script("arguments[0].click();", WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'sw-slider-user-images'))))
        # driver.execute_script("arguments[0].click();", WebDriverWait(driver, 20).until(
        #     EC.element_to_be_clickable((By.CLASS_NAME, 'swiper-button-next'))))

        # .sw-slider-user-images>button:nth-child(3)
        # element = driver.find_element(By.CLASS_NAME, 'sw-slider-user-images')

        i += 1
    photos = get_photos(driver)
    links_chunk = [photo.find_element_by_tag_name('img').get_attribute('src') for photo in photos]
    if links[-1] == links_chunk[-1]:
        stop = True
        break
    else:
        links += links_chunk
    # except selenium.common.exceptions.NoSuchElementException:
    #     photos = get_photos(driver)
    #     links += [photo.find_element_by_tag_name('img').get_attribute('src') for photo in photos]
    #     stop = True


# comments = driver.find_element(By.CLASS_NAME, 'comments__list')

# comments = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME,
#                                                                           "comments__user-photos")))



# photos = user_photos.

print(links, len(links))#.find_element(By.CLASS_NAME, "comments__user-photos"))
driver.quit()
