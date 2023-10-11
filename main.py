from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from selenium import webdriver
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from selenium.webdriver.support.wait import WebDriverWait
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords
# еще устанавливаем chromedriver-binary версии, такой же как и Chrome для автоматического задания пути до chromedriver

"""скачиваем стоп слова для word cloud """
nltk.download('stopwords')


def date_js(date):
    """Переводим дату из python в дату javascript,
    это необходимо при формировании строки поиска в браузере"""
    return str(int(time.mktime(date.timetuple())) * 1000)


def obtain_feed_url(start_date, end_date):
    """Формируем строку поиска в браузере по слову
     и фильтруем новости по дате от start_date до end_date"""
    date_str = "{}".format(start_date.year) + "{0:02}".format(start_date.month) + "{0:02}".format(start_date.day)
    return "https://dzen.ru/news/search?filter_date=" + date_js(start_date) + "%2C" + date_js(end_date) \
           + "&issue_tld=ru&sortby=date&text=" \
           + word_to_find + "+date%3A" + date_str + ".." + date_str


def open_all_articles():
    """после загрузки браузера необходимо спуститься вниз
     и открыть следующие статьи при нажатии кнопки 'больше результатов'
     Нужно дождаться момента, когда эта кнопка станет кликабельной"""
    time.sleep(10)
    while True:
        button = browser.find_elements(By.CSS_SELECTOR,
                                       '[class="Button2 Button2_view_action Button2_size_m mg-button '
                                       'mg-load-more__button"]')
        if len(button) > 0:
            WebDriverWait(browser, 20).until(EC.element_to_be_clickable(button[-1])).click()

        else:
            break


def obtain_articles(url):
    """
    После открытия всех статей в браузере для определенного фильтра по времени,
     создаем контейнер для статей в виде DataFrame
     и с помощью find_element By.CSS_SELECTOR находим название каждой статьи и соответствующее ему краткое изложение
     возвращаем полученный DataFrame для определенного дня
    """
    browser.get(url)
    #open_all_articles()
    local_data = pd.DataFrame(columns=["title", "text"])
    articles = browser.find_elements(By.CSS_SELECTOR, 'article')
    for t in range(len(articles)):
        local_data.loc[t] = [articles[t].find_element(By.CSS_SELECTOR, '[class="mg-snippet__title"]').text,
                             articles[t].find_element(By.CSS_SELECTOR, '[class="mg-snippet__text"]').text]
    return local_data


"""запускаем браузер для отрисовки всех элементов, так как сайт динамический"""
browser = webdriver.Chrome()

word_to_find = "игра"
stopwords_to_find = [word_to_find[:-1] + w for w in ["", "а", "у", "е", "ы", "ах"]]

"""Создаем 2 листа дат, по которым будет идти поиск. 
days - это лист конечных дат,
previous_days - это лист начальных дат
"""
now = datetime.utcnow()
period = now - relativedelta(months=1)
i = 0
days = [now]
previous_days = [datetime(now.year, now.month, now.day, 0, 0, 0, 0)]
while days[-1] > period:
    i += 1
    days.append(previous_days[i - 1])
    previous_days.append(previous_days[i - 1] - relativedelta(days=1))

"""Создаем лист всех поисковых строк """
feed_url_container = []
for t in range(len(days) - 1):
    feed_url_container.append(obtain_feed_url(previous_days[t], days[t]))

"""Создаем контейнер всех статей """
article_container = pd.DataFrame(columns=["title", "text"])
"""И дополняем его при каждой новой строке поиска (новая строка поиска соответствует новому дню) """
for url in feed_url_container:
    article_container = pd.concat([article_container, obtain_articles(url)], ignore_index=True)

"""закрываем браузер"""
browser.close()

"""записываем результат в articles.csv"""
file_name = "статьи_{}.csv".format(word_to_find)
article_container.to_csv(file_name, encoding='utf-8-sig')

"""формируем полный текст из всех текстов статей"""
text_combined = ""
for d in article_container.text:
    text_combined += d

"""Формируем word cloud, применяя стоп слова из русского и анг. алфавитов,
и дополнительно убираем поисковое слов и частые слова "также", "это". """
russian_stopwords = stopwords.words("russian")
wordcloud = WordCloud(
    collocations=False,
    stopwords=stopwords_to_find + ["это", "также"] + list(russian_stopwords) + list(
        STOPWORDS),
    background_color="white",
    width=1000,
    height=800).generate(text_combined)

plt.figure(figsize=(13, 13))
plt.imshow(wordcloud)
plt.axis("off")
"""Сохраняем изображение"""
plt.savefig('{}.png'.format(word_to_find))
plt.show()
