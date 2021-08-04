import os
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def main():
    # instantiate an Options object and add the headless argument
    opts = Options()
    opts.add_argument("--headless")

    # instantiate a webdriver
    driver = webdriver.Chrome('/Users/NolanRoth/Desktop/PojectWebsite/chromedriver', chrome_options=opts)

    # load the HTML page
    driver.get('https://www.fantasypros.com/nfl/rankings/consensus-cheatsheets.php')

    javaScript = "window.scrollBy(0,1000);"
    driver.execute_script(javaScript)
    rankings_table = driver.find_element_by_id('ranking-table').find_element_by_tag_name('tbody')
    trs = rankings_table.find_elements_by_class_name('player-row')[:200]

    ranks = []
    names = []
    teams = []
    positions = []

    for tr in trs:
        tds = tr.find_elements_by_tag_name('td')
        ranks.append(tds[0].text)
        names.append(tds[2].find_element_by_tag_name('a').text)
        teams.append(tds[2].find_element_by_tag_name('span').text.replace('(', '').replace(')', ''))
        position_rank = tds[3].text
        positions.append(re.sub('[^a-zA-Z]+', '', position_rank))
        
    rankings = pd.DataFrame({
        'Rank': ranks,
        'Name': names,
        'Team': teams,
        'Position': positions
    })

    rankings['Rank'] = rankings['Rank'].astype(int)



    rankings.to_csv('/Users/NolanRoth/Desktop/PojectWebsite/website/database/fantasy_pros_rankings.csv', index=False)

    driver.quit()