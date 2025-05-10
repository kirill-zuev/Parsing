import const, firefox

from selenium.webdriver.common.by import By

def rewriteAllPagesAndImages (browser, federation=const.FEDERATION_ITO):
    try:
        firefox.openYandexWiki(browser, password=const.PASSWORD)
        # firefox.clickOnArrowsAndExpands(browser)
        # firefox.scanPagesTree(browser)
        firefox.getAndSaveWikiPagesFromListFile(browser, path_to_list_file="./" + federation + "/pages.txt")
    except Exception as ex:
        print(ex)


if __name__ == '__main__':
    browser = firefox.initFirefox()
    try:
        rewriteAllPagesAndImages(browser)
    except Exception as ex:
        print(ex)
    finally:
        browser.close()
        browser.quit()
        print("Program exit.")