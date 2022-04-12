import os, requests, time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import *
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as bs
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import product, repeat
from base64 import b64decode

BASE_PATH = './images'
QUERIES_UNSPLASH = ['1 person', '2 people', '3 people', '4 people',
                '5 people', '6 people', '7 people', '8 people',
                '9 people', 'many people']

QUERIES_GOOGLE = ['people', 'pictures of people', 'some people', 'road with people',
                'people walking', 'family', 'friends', 'workers', 'humans',
                'people eating', 'people in zoo']
SIZE = 10000
SEARCH_ENGINES = ['google', 'duckduckgo']
UNSPLASH = 'https://unsplash.com/'


def initialise():
        options = Options()
        #options.add_argument('window-size=2000,1500')
        options.add_argument('window-position=500, 220')
        driver = webdriver.Chrome(options=options)
        return driver

def search_unsplash(query):
    driver = initialise()
    urls = set()
    url = f"{UNSPLASH}s/photos/{query.replace(' ', '-')}"
    driver.get(url)
                
    count = 0
    while True:
        for _ in range(10):
            scroll(driver)
        soup = bs(driver.page_source, 'html.parser')
        images = soup.findAll('img')
        if len(images) == count:
            break
        images = [i['src'] for i in images[count:]]
        count += len(images)
        urls.update(images)
        print(f'{query} has {len(urls)} images so far')
        if len(urls) > 500:
            break

    driver.close()    
    return urls

def search_google(input_):
    engine, query = input_
    driver = initialise()
    urls = set()
    driver.get(f'https://www.{engine}.com/')
    search = driver.find_element_by_name('q')
    search.send_keys(query, Keys.ENTER)
    driver.find_element_by_link_text('Images').click()
    
    count = 0
    while True:
        for _ in range(10):
            scroll(driver)
        soup = bs(driver.page_source, 'html.parser')
        images = soup.findAll('img')
        if len(images) == count:
            break
        images = images[count:]
        for image in images:
            if image.has_attr('src'):
                urls.add(image['src'])
            elif image.has_attr('data-src'):
               urls.add(image['data-src'])
        count += len(images)
    
    driver.close()
    return urls


def scroll(driver):
    scroll = 'window.scrollTo(0,document.body.scrollHeight)'
    driver.execute_script(scroll)
    try:
        ele = driver.find_element_by_xpath('//button[normalize-space()="Load more photos"]')
        ele.click()
    except Exception as e:
        pass
    time.sleep(1)

def download_image(url, path, index):
    if url[:18] == '//external-content':
        url = 'http:' + url

    if 'http' == url[:4]:
        fname = f'{path}/{index}.jpeg'
        r = requests.get(url)
        img_data = r.content
        if r.status_code == 200:
            with open(fname, 'wb') as f:
                f.write(img_data)
        else:
            with open('failed.txt', 'a') as f:
                f.write(f'{url}\n') 
    
    elif url[:4] == 'data':
        data = url[11:]
        type_ = data.split(';')[0]
        fname = f'{path}/{index}.{type_}'
        code_ = data.split(';')[1].split(',')[0]
        if code_ == 'base64':
            data = data[len(type_) + 8:]
            data = bytes(data, 'utf-8')
            with open(fname, 'wb') as f:
                f.write(b64decode(data))             
        else:
            print('Error={i}, {type_}, {code_}')
    
    else:
        with open('failed.txt', 'a') as f:
            f.write(f'{url}\n') 

def download():
    with ThreadPoolExecutor() as executor:
        google_links = executor.map(search_google, product(SEARCH_ENGINES, QUERIES_GOOGLE))
        unsplash_links = executor.map(search_unsplash, QUERIES_UNSPLASH)

        for (engine, query), results in zip(product(SEARCH_ENGINES, QUERIES_GOOGLE), google_links):
            folder = f'{BASE_PATH}/{engine}/{query}'
            executor.map(download_image, results, repeat(folder), range(len(results)))
        
        for query, results in zip(QUERIES_UNSPLASH, unsplash_links):
            folder = f'{BASE_PATH}/unsplash/{query}'
            executor.map(download_image, results, repeat(folder), range(len(results)))

def check_folders():
    if not os.path.exists(BASE_PATH):
        os.mkdir(BASE_PATH)

    for engine in SEARCH_ENGINES:
        home_folder = os.path.join(BASE_PATH, engine)
        if not os.path.exists(home_folder):
            os.mkdir(home_folder)
        for query in QUERIES_GOOGLE:
            path = os.path.join(home_folder, query)
            if not os.path.exists(path):
                os.mkdir(path)
    
    unsplash_path = os.path.join(BASE_PATH, 'unsplash')
    if not os.path.exists(unsplash_path):
        os.mkdir(unsplash_path)

    for query in QUERIES_UNSPLASH:
        path = os.path.join(unsplash_path, query)
        if not os.path.exists(path):
            os.mkdir(path)

def main():
    check_folders()
    
    start = time.time()
    download()
    end = time.time()
    print(f'Time taken = {(end - start)/60}min')

if __name__ == '__main__':
    main() 
