import re
import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
import logging
import pymongo
from config import *

logging.basicConfig(level=logging.INFO)
#加载启动配置
option = webdriver.ChromeOptions()
option.add_argument('disable-infobars')
#打开chrome浏览器
browser = webdriver.Chrome(chrome_options=option)
#创建等待时长
wait = WebDriverWait(browser, 20)
#创建数据库链接
client = pymongo.MongoClient(MONGO_URL)
#创建数据库
db = client[MONGO_DB]

def search():
    try:
        browser.get('https://www.taobao.com') # 请求首页
        input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))) #通过CSS选择器定位搜索框
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button'))) #通过CSS选择器定位确定按钮是否存在
        input.send_keys('美食') #模拟输入
        submit.click()  #模拟鼠标按钮
        total = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.total')))
        get_products()
        return total[0].text
    except TimeoutException:
        return search()


def next_page(page_number):
    try:
        input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input')))
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))
        input.clear() #清空搜框的内容
        input.send_keys(page_number) #输入页码到搜索框
        submit.click() #翻页操作
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page_number))) #通过CSS选择器定位高亮的数字是否与传入的参数一致
        get_products()
    except TimeoutException:
        return next_page(page_number)

def get_products():
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'#mainsrp-itemlist .items .item')))  #判断宝贝信息是否加载完毕 （CSS选择器的方法,个人理解通过兄弟节点来判断）
    html = browser.page_source  #获取页面源代码
    doc = pq(html) #用PyQuery解析网页
    items = doc('#mainsrp-itemlist .items .item').items() #获取所有选择的内容
    for item in items:   #for循环不断被的给products赋值，所以存入数据库的函数要放到循环里面
        products = {
            'image': item.find('.pic.J_ItemPic img').attr('src'),#通过find方法找到src属性
            'price': item.find('.price').text().replace('\n',' '),
            'deal' : item.find('.deal-cnt').text().replace('\n',' '),
            'title' : item.find('.title').text().replace('\n',' '),
            'shop' : item.find('.shop').text(),
            'location' : item.find('.location').text()
        }
        print(products)
        save_to_mongo(products)
def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('存储到MongoDB成功',result)
    except Exception:
        print('存储到MongoDB失败',result)


def main():
    total = search()
    total = int(re.compile('(\d+)').search(total).group(1))
    logging.info('total={}'.format(total))
    for i in range(2,total+1):
        time.sleep(2)
        next_page(i)

if __name__ == '__main__':
    main()