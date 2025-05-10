from selenium.webdriver import Keys, ActionChains


'''
Кнопка для нажатия сочетания Ctrl и буквы в селениуме
'''
def simulateHotkeyCtrlPlusLetter(browser, letter):
    ActionChains(browser)\
        .key_down(Keys.LEFT_CONTROL)\
        .send_keys(letter)\
        .key_up(Keys.LEFT_CONTROL)\
        .perform()