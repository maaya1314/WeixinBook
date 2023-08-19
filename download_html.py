import time

from WeReadScan import WeRead, BigBookError
from selenium.webdriver import Chrome, ChromeOptions

# options
chrome_options = ChromeOptions()

# now you can choose headless or not
chrome_options.add_argument('--headless')

chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument('disable-infobars')
chrome_options.add_argument('log-level=3')

# launch Webdriver
print('Webdriver launching...')
driver = Chrome(options=chrome_options)
print('Webdriver launched.')

with WeRead(driver) as weread:
    weread.login()  # ? login for grab the whole book
    # weread.scan2html('https://weread.qq.com/web/reader/315323005e001f3153c452b?', show_output=False)
    # time.sleep(3)
    # weread.scan2html('https://weread.qq.com/web/reader/28b3290071feec8528bfcfe?', show_output=False)
    # time.sleep(3)
    start = time.time()
    # 三体（全集）
    # weread.scan2html('https://weread.qq.com/web/reader/ce032b305a9bc1ce0b0dd2a?', show_output=False)
    # 剑来
    # weread.scan2html('https://weread.qq.com/web/reader/8e5326b07153adcf8e53d42?', show_output=False)
    try:
        while True:
            _flag = weread.scan2html('https://weread.qq.com/web/reader/28b3290071feec8528bfcfe?', show_output=False)
            if not _flag:
                break
    except BigBookError as e:
        print(e)
    except Exception as e:
        print(e)
    weread.big_book_sort = 0
    weread.big_book_flag = False
    weread.continue_flag = False
    end = time.time()
    print("costs: ", end - start)
    time.sleep(3)
    driver.close()
