import requests
from bs4 import BeautifulSoup
import io
import logging

class YadScrap:
    def __init__(self, url: str):
        self.url = url
        self.apartments = {}
        self.session = requests.Session()
        self.session.headers = {
            'cookie': 'adoric_goals=%5B%225ae5882c307a8fbd0017c1c5%22%5D; adoric_user=1; adoric_uniq_day_id=5ee850da0c7d3b0010427925; _ga=GA1.3.368393247.1557131802; __gads=ID=6cb00dbbe33ac9b3:T=1557131803:S=ALNI_MZugNl7Z1ZHmImf3DhxsJpLGtkqaw; __ssds=3; __ssuzjsr3=a9be0cd8e; __uzmaj3=d2f84d95-09fa-427c-b0e0-3dc97068ba06; __uzmbj3=1573994697; _hjid=18db03ed-5067-4a33-91c3-48e9f640ceca; use_elastic_search=1; y2018-2-cohort=68; leadSaleRentFree=33; bc.visitorToken=6601812280777191424; _fbp=fb.2.1590058161151.979472068; historyprimaryarea=hamerkaz_area; historysecondaryarea=bikat_ono; UTGv2=D-h4e765dc4d8c942b9888a4bf7224e4bbc893; __uzma=14ddcc7e-b231-4b6b-b471-0bc4e33fcc61; __uzmb=1591266391; abTestKey=90; _gid=GA1.3.932071071.1592283353; yad2upload=520093706.27765.0000; server_env=production; y2_cohort_2020=35; y2session=GE6yCk2VGtgCQppkK8Kp3eFNY98JKH7zkQtDjrJX; _hjAbsoluteSessionInProgress=1; __uzmd=1592284104; favorites_userid=chj331863561; _gat_UA-708051-1=1; __uzmcj3=5872613316303; __uzmdj3=1592284104; __uzmc=9411232879317',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
            }
        self.get_initial_data()

    def _get_feed_items(self):

        logging.debug(f"cookies before get items {requests.utils.dict_from_cookiejar(self.session.cookies)}")
        page = self.session.get(self.url)
        logging.debug(f"cookies after get items {requests.utils.dict_from_cookiejar(self.session.cookies)}")
        soup = BeautifulSoup(page.text)
        feed = soup.find("div", {"class": "feed_list"})
        return feed.find_all("div", {"class": "feeditem table"})

    def get_initial_data(self):
        feed_items = self._get_feed_items()
        for feed_item in feed_items:
            a_id = feed_item.div.attrs['item-id']
            try:
                img_url = feed_item.img.attrs['src']
                img = requests.get(fr"https:{img_url}", stream=True)
                img_io = io.BytesIO(img.content)
            except Exception as e:
                img_io = ""
                logging.exception(f"Exception occurred during fetching the image {e}")
            try:
                self.apartments[a_id] = {
                    "address": feed_item.find("span", {"class": "title"}).text.strip(),
                    "area": feed_item.find("span", {"class": "subtitle"}).text.strip(),
                    "price": feed_item.find("div", {"class": "price"}).text.strip(),
                    "url": f"https://www.yad2.co.il/item/{a_id}",
                    "img": img_io
                }
            except Exception as e:
                logging.exception(f"Exception occurred during adding apartment {e}")

    def check_for_news(self):
        feed_items = self._get_feed_items()
        news = {}
        for feed_item in feed_items:
            a_id = feed_item.div.attrs['item-id']
            if a_id not in self.apartments:
                try:
                    img_url = feed_item.img.attrs['src']
                    img = requests.get(fr"https:{img_url}", stream=True)
                    img_io = io.BytesIO(img.content)
                except Exception as e:
                    img_io = ""
                    logging.exception(f"Exception occurred during fetching the image {e}")
                try:
                    news[a_id] = {
                        "address": feed_item.find("span", {"class": "title"}).text.strip(),
                        "area": feed_item.find("span", {"class": "subtitle"}).text.strip(),
                        "price": feed_item.find("div", {"class": "price"}).text.strip(),
                        "url": f"https://www.yad2.co.il/item/{a_id}",
                        "img": img_io,
                        "reason": "New apartment"
                    }
                    self.apartments[a_id] = {
                        "address": feed_item.find("span", {"class": "title"}).text.strip(),
                        "area": feed_item.find("span", {"class": "subtitle"}).text.strip(),
                        "price": feed_item.find("div", {"class": "price"}).text.strip(),
                        "url": f"https://www.yad2.co.il/item/{a_id}",
                        "img": img_io
                    }
                except Exception as e:
                    logging.exception(f"Exception occurred during adding new apartment {e}")
            else:
                try:
                    if self.apartments[a_id]["price"] != feed_item.find("div", {"class": "price"}).text.strip():
                        old_price = self.apartments[a_id]['price']
                        self.apartments[a_id]['price'] = feed_item.find("div", {"class": "price"}).text.strip()
                        news[a_id] = self.apartments[a_id]
                        news[a_id]["reason"] = f"Price change from {old_price} to {self.apartments[a_id]['price']}"
                except Exception as e:
                    logging.exception(f"Exception occurred during adding changed apartment {e}")
            if len(news) > 6:
                logging.info("too match news!")
                return []
        return news

    
if __name__ == '__main__':
    import time
    y = YadScrap('https://www.yad2.co.il/realestate/rent?city=2620&rooms=3-5&price=-1-4600')
    for _ in range(10):
        y.check_for_news()
        time.sleep(10)