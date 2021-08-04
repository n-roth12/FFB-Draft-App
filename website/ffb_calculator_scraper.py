import os
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def main():
    # instantiate an Options object and add the headless argument
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--disable-notifications")

    # instantiate a webdriver
    driver = webdriver.Chrome('/Users/NolanRoth/Desktop/PojectWebsite/chromedriver', chrome_options=opts)

    # load the HTML page
    driver.get('https://fantasyfootballcalculator.com/rankings/ppr')

    #javaScript = "window.scrollBy(0,1000);"
    #driver.execute_script(javaScript)
    body = driver.find_element_by_id('kt_content')
    rankings_table = body.find_element_by_class_name('table')
    trs = driver.find_elements_by_tag_name('tr')[1:]

    ranks = []
    names = []
    teams = []
    positions = []

    for tr in trs:
        tds = tr.find_elements_by_tag_name('td')
        ranks.append(tds[0].text.replace('.', ''))
        names.append(tds[1].find_element_by_tag_name('a').text)
        teams.append(tds[2].text)
        positions.append(tds[3].text)

    rankings = pd.DataFrame({
        'Rank': ranks,
        'Name': names,
        'Team': teams,
        'Position': positions
    })

    rankings['Rank'] = rankings['Rank'].astype(int)

    rankings.to_csv('/Users/NolanRoth/Desktop/PojectWebsite/website/database/ffb_calculator_rankings.csv', index=False)

    driver.quit()