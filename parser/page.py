import const
from bs4 import BeautifulSoup


'''
Функция получения из драйвера тела страницы в html
'''
def getPageHtml(driver):
    html = driver.page_source
    return html


'''
Функция проверки, не собирается ли браузер щелкнуть на раскрывашку около страницы "личные разделы пользователей"
'''
def isNextToUsersButton(browser):
    checkable_href = "/users/"
    html = getPageHtml(browser)
    soup = BeautifulSoup(html, 'html.parser')
    closed_arrow = soup.find_all(class_=const.ARROW_CLOSED)[0]
    nav_item = closed_arrow.parent.find_next_sibling()
    nav_item_href = nav_item["href"]
    return checkable_href in nav_item_href