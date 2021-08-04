import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def main():
    # instantiate an Options object and add the headless argument
    opts = Options()
    opts.add_argument("--headless")

    # instantiate a webdriver
    driver = webdriver.Chrome('/Users/NolanRoth/Desktop/PojectWebsite/chromedriver', chrome_options=opts)

    # load the HTML page
    driver.get('https://www.sportingnews.com/us/fantasy/news/2021-fantasy-football-rankings-top-200-cheat-sheet/1mz21lwlgdyfa1asbqdsrib2az')

    #javaScript = "window.scrollBy(0,1000);"
    #driver.execute_script(javaScript)
    body = driver.find_element_by_class_name('article-body')
    table = body.find_element_by_tag_name('tbody')
    trs = table.find_elements_by_tag_name('tr')[1:]

    ranks = []
    names = []
    positions = []

    for tr in trs:
        data = tr.find_elements_by_tag_name('td')
        ranks.append(data[0].text)
        name_and_team = data[1].text.split(', ')
        names.append(name_and_team[0])
        positions.append(data[2].text)
        

    rankings = pd.DataFrame({
        'Rank': ranks,
        'Name': names,
        'Position': positions
    })

    rankings['Rank'] = rankings['Rank'].astype(int)

    rankings.to_csv('/Users/NolanRoth/Desktop/PojectWebsite/website/database/sporting_news_rankings.csv', index=False)

    driver.quit()