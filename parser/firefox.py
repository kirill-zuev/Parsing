from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

import time, os, pyperclip
import const, page, migrator

DRIVER_PATH = "C:\\Users\\kp.zuev\\Desktop\\wiki_parser\\geckodriver.exe"
BINARY_PATH = "C:\\Program Files\\Mozilla Firefox\\firefox.exe"


'''
Функция открытия браузера
'''
def initFirefox():
    ops = Options()
    ops.binary_location = BINARY_PATH
    ops.headless = True
    serv = Service(DRIVER_PATH)
    browser = webdriver.Firefox(service=serv, options=ops)
    browser.maximize_window()
    return browser
    

'''
Функция ввода кредов в окна AD (аутентификация в Wiki)
'''
def openYandexWiki(browser, password, federation_id=const.FEDERATION_ITO):
    browser.get(const.WIKI_FEDERATION_LOGIN_PAGE_PREFIX + federation_id)
    login_input = browser.find_element(By.ID, const.LOGIN_INPUT_ID)
    login_input.clear()
    login_input.send_keys(const.MY_LOGIN)
    browser.find_element(By.ID, const.LOGIN_BUTTON_NEXT_ID).click()
    time.sleep(0.5)
    password_input = browser.find_element(By.ID, const.PASSWORD_INPUT_ID)
    password_input.clear()
    password_input.send_keys(password)
    password_input.send_keys(Keys.ENTER)
    time.sleep(0.5)
    print("auth credentials entered")
    time.sleep(5)


'''
Функция прокликивания всех стрелок на открытой странице вики
'''
def clickOnArrowsAndExpands(browser, short_nav_bar_flag=False):
    number_of_attempts = 0
    max_attempts = 15
    time.sleep(1)
    while number_of_attempts < max_attempts:
        try:                     
            clickable = browser.find_element(By.CLASS_NAME, const.ARROW_CLOSED)
            '''  
            проверяем, что за стрелку раскрываем. Если "Личные разделы" — не раскрываем,
            ждём вдруг другие стрелки прогрузились
            '''
            if page.isNextToUsersButton(browser): 
                time.sleep(0.3)
                number_of_attempts += 1
                continue
            time.sleep(0.5)
            clickable.click()
            number_of_attempts = 0
        except Exception as ex:
            try:
                nav_bar = browser.find_element(By.CLASS_NAME, "NavigationTreeScrollable")
                number_of_attempts += 1
                if not short_nav_bar_flag:
                    nav_bar.send_keys(Keys.PAGE_DOWN)
                time.sleep(0.3)
            except Exception as ex_i:
                time.sleep(0.4)

    nav_bar = browser.find_element(By.CLASS_NAME, "NavigationTreeScrollable")
    if not short_nav_bar_flag:
        for i in range(100):
            nav_bar.send_keys(Keys.PAGE_UP)
            pass


'''
Функция чтения дерева от указанной страницы и возврат словаря ссылок
сначала бежим сверху вниз, получаем по порядку все страницы и отступы
В момент запуска надо, чтобы навбар был прокручен до верха
'''
def scanPagesTree(browser, federation=const.FEDERATION_ITO, short_nav_bar_flag=False):
    proto_tree = dict()
    html = page.getPageHtml(browser)
    soup = BeautifulSoup(html, 'html.parser')
    visible_page_links_triangles = soup.find_all(class_=const.PAGE_TRIANGLE)
    number_of_attempts = 0
    max_attempts = 1000
    while number_of_attempts < max_attempts:
        print(number_of_attempts)
        for t in visible_page_links_triangles:
            href = t.find_next_sibling()["href"]
            if "/users/" in href:  # игнорируем личные разделы
                break
            margin_str = t["style"]  # margin-left: Xpx
            # извлекаем X в число
            margin = int(margin_str[margin_str.find(':')+1:margin_str.find('px')])
            level = int(margin/10)  # уровень вложенности
            proto_tree[href] = level
        nav_bar = browser.find_element(By.CLASS_NAME, "NavigationTreeScrollable")
        if not short_nav_bar_flag:
            nav_bar.send_keys(Keys.PAGE_DOWN)
        number_of_attempts += 1
        html = page.getPageHtml(browser)
        soup = BeautifulSoup(html, 'html.parser')
        visible_page_links_triangles = soup.find_all(class_=const.PAGE_TRIANGLE)
    createFolders(proto_tree, federation=federation)
    return proto_tree


'''
Вспомогательная функция для функции scanPagesTree()
Сохраняет для всех URL из левого нав-дерева папки с соотв. именами,
в папку "folders/" в папке проекта
'''
def createFolders(proto_tree, federation=const.FEDERATION_ITO):
    print("Creating folders")
    try:
        strings = []
        f = open("./" + federation + "/pages.txt",'w', encoding='utf-8')
        for href in proto_tree:
            str = href + "\n"
            strings.append(str)
            # для каждого href создаём директорию
            os.makedirs("./" + federation +"/folders" + href, exist_ok=True)
        f.writelines(strings)
        print("pages.txt created")
        f.close()
    except Exception as ex:
        print(ex)
    print("Folders and pages.txt created")


'''
Получение браузером одной страницы Wiki с путем href,
сохранение yfm-файла с разметкой этой страницы в папку с соотв. путем. ("page.yfm")
Возвращаем список строк получившегося файла или None, если не получилось.
'''     
def getAndSaveWikiPageContent(browser, href, ignore_existing=True, federation=const.FEDERATION_ITO):
        target_dir_path = "./" + federation + "/folders" + href  # папка куда надо сохранить страницу и ресурсы
        page_name = "page.yfm"
        md_page_name = "page.md"
        title_file_name = "title.txt"
        if ignore_existing and os.path.exists(target_dir_path + md_page_name):
            print("MD file for page" + target_dir_path + "already exists, skipped." + '\n')
            return None
        if href == "/homepage/krap-team/rms/" or "/homepage/support-systems/" in href or "/homepage/rnd/" in href:
            print("MD file for page" + target_dir_path + "skipped." + '\n')
            return None
        browser.get(const.WIKI_HOST + href + const.WIKI_EDIT_SUFFIX)
        time.sleep(1)
        page_title = ''
        data = ''
        
        try:
            browser.find_element(By.CLASS_NAME, "g-button_selected").click()
        except Exception as ex:
            pass

        # нажимаем на текст в редакторе (const.WIKI_PAGE_EDITOR)
        try:
            dropdown_button = browser.find_element(By.CLASS_NAME, "g-md-editor-settings__dropdown-button")
            dropdown_button.click()
            # mode_help = browser.find_element(By.CLASS_NAME, "g-md-settings-content__mode-help")
            mode_help = browser.find_element(By.CLASS_NAME, "g-menu__item-icon")
            mode_help.click()
            # browser.find_element(By.CLASS_NAME, const.WIKI_PAGE_EDITOR).click()
            # нажимаем ctrl+A, затем ctrl+C
            migrator.simulateHotkeyCtrlPlusLetter(browser, 'a')
            migrator.simulateHotkeyCtrlPlusLetter(browser, 'c')
            # записываем разметку в переменную data
            data = pyperclip.paste()
            data =  "\n".join(data.split("\n")[1:])
        except Exception as ex:
            print(target_dir_path + '\n')
            print(ex)
            f = open(target_dir_path + md_page_name, 'wb')
            f.write((page_title+"\n"+data).encode('utf-8'))
            f.close()
            print("MD saved in: " + target_dir_path + '\n')
            return data
        
        try:
            # нажимаем на заголовок
            browser.find_element(By.CLASS_NAME, const.WIKI_PAGE_TITLE_CLASS).click()
            # нажимаем ctrl+A, затем ctrl+C
            migrator.simulateHotkeyCtrlPlusLetter(browser, 'A')    
            
            migrator.simulateHotkeyCtrlPlusLetter(browser, 'C')
            
            # записываем заголовок в переменную page_title
            page_title = pyperclip.paste()
            index = page_title.find("Обновлено")
            if index != -1:
                page_title = page_title[index:]
            page_title = page_title.replace("© 2025 ООО «Яндекс»", "")
        except Exception as ex:
            print(target_dir_path + '\n')
            print(ex)
            f = open(target_dir_path + md_page_name, 'wb')
            f.write((page_title).encode('utf-8'))
            f.close()
            print("MD saved in: " + target_dir_path + '\n')
            return data

        try:
            # f = open(target_dir_path + page_name, 'wb')
            # f.write(data.encode('utf-8'))
            # f.close()
            # print("YFM saved in: " + target_dir_path + '\n')

            f = open(target_dir_path + md_page_name, 'wb')
            f.write((page_title+"\n"+data).encode('utf-8'))
            f.close()
            print("MD saved in: " + target_dir_path + '\n')

            # f = open(target_dir_path + title_file_name, 'wb')
            # f.write(page_title.encode('utf-8'))
            # f.close()
            return data
        except Exception as ex:
            print(ex)
            return None


'''
Функция для получения списка путей из файла и обхода страниц
'''
def getAndSaveWikiPagesFromListFile(browser, path_to_list_file, exclude_pages_pattern = "", \
                                    include_pages_pattern = "/", ignore_existing=True, federation=const.FEDERATION_ITO):
    hrefs_raw = list()
    hrefs = list()
    # открываем файл со списком ссылок на страницы, считываем в список hrefs
    f = open(path_to_list_file, 'r')
    hrefs_raw = f.readlines()
    f.close()
    for href in hrefs_raw:
        href = href.rstrip('\n')
        if (include_pages_pattern in href) and \
              ((exclude_pages_pattern == "") or \
              (exclude_pages_pattern not in href)):
            hrefs.append(href)
        else:
            pass
    
    for href in hrefs:
        getAndSaveWikiPageContent(browser, href, ignore_existing=ignore_existing, federation=federation)