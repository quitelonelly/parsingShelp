import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from scrapy.selector import Selector
from pymongo import MongoClient
import time

class OrderSpider(scrapy.Spider):
    name = "order"
    allowed_domains = ["shelp-student.ru"]
    start_urls = ["https://shelp-student.ru/orders"]

    def __init__(self, *args, **kwargs):
        super(OrderSpider, self).__init__(*args, **kwargs)
        chrome_options = Options()

        chrome_options.add_argument("--headless")  
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        # Создаем соединение с MongoDB
        self.cluster = MongoClient("localhost", 27017)
        self.collection = self.cluster.one_database.one_collection

    def parse(self, response):
        self.driver.get(response.url)
        time.sleep(5)  # Ждем загрузки страницы (можно настроить в зависимости от скорости загрузки)

        while True:
            sel = Selector(text=self.driver.page_source)
            orders = sel.css('div.ol_item')

            for order in orders:
                order_name = order.css('div.ol_i_title a::text').get()
                order_discipline = order.css('div.ol_i_tags a.btn.btn_grey_transparent.order-buttons span::text')[1].get()
                order_term = order.css('div.ol_i_meta span.ol_i_meta--dateto::text').get()
                if order_name and order_discipline:
                    order = {
                        'Название заказа': order_name.strip(),
                        'Дисциплина': order_discipline.strip(),
                        'Срок сдачи': order_term.strip()
                    }
                    # Записываем заказ в MongoDB
                    self.collection.insert_one(order)
                    yield order
                    
            try:
                next_page_link = self.driver.find_element(By.CSS_SELECTOR, 'div.pagination a.next')
                next_page_link.click()
                print(f"Перешли на следующую страницу")
                time.sleep(5)  # Ждем загрузки следующей страницы
            except:
                break  # Если кнопки "Следующая страница" нет, выходим из цикла

    def closed(self, reason):
        self.driver.quit()