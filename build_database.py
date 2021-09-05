from website.models import Player, User, Rank
from website import db
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import os
import re

def build():
    db.drop_all()
    db.create_all()
    db.session.commit()
    scrape()
    generateAdps()
    generatePosRanks()

def scrape():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-notifications")

    #driver = webdriver.Chrome(executable_path=os.path.join(os.path.dirname(os.getcwd()), "chromedriver.exe"))
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

    fp_scrape(chrome_options, driver)
    sport_news_scrape(chrome_options, driver)
    ffb_calc_scrape(chrome_options, driver)

def fp_scrape(opts, driver):
    print('Scraping Fantasy Pros rankings...')

    driver.get('https://www.fantasypros.com/nfl/rankings/consensus-cheatsheets.php')

    javaScript = "window.scrollBy(0,1000);"
    driver.execute_script(javaScript)
    rankings_table = driver.find_element_by_id('ranking-table').find_element_by_tag_name('tbody')
    trs = rankings_table.find_elements_by_class_name('player-row')[:200]

    names = []
    teams = []
    positions = []
    fp_ranks = []

    for tr in trs:
        tds = tr.find_elements_by_tag_name('td')
        rank = int(tds[0].text)
        names.append(tds[2].find_element_by_tag_name('a').text)
        teams.append(tds[2].find_element_by_tag_name('span').text.replace('(', '').replace(')', ''))
        position_rank = tds[3].text
        positions.append(re.sub('[^a-zA-Z]+', '', position_rank))
        fp_ranks.append(rank)
    
    for i in range(len(names)):
        p1 = Player.query.filter_by(name=names[i]).first()
        if p1 == None:
            player =  Player(name=names[i], team=teams[i], position=positions[i], fp_rank=fp_ranks[i])
            db.session.add(player)
            db.session.commit()
        else:
            p1.fp_rank = fp_ranks[i]
            db.session.commit()

    print('Completed scraping Fantasy Pros rankings!')
    driver.quit()

def ffb_calc_scrape(opts, driver):
    print('Scraping Fantasy Football Calculator rankings...')

    #driver = webdriver.Chrome('/Users/NolanRoth/Desktop/ProjectWebsite/chromedriver', chrome_options=opts)
    driver.get('https://fantasyfootballcalculator.com/rankings/ppr')

    body = driver.find_element_by_id('kt_content')
    rankings_table = body.find_element_by_class_name('table')
    trs = driver.find_elements_by_tag_name('tr')[1:]

    names = []
    teams = []
    positions = []
    ffb_calc_ranks = []

    for tr in trs:
        tds = tr.find_elements_by_tag_name('td')
        rank = tds[0].text.replace('.', '')
        name = tds[1].find_element_by_tag_name('a').text
        team = tds[2].text
        position = tds[3].text

        names.append(name)
        teams.append(team)
        positions.append(position)
        ffb_calc_ranks.append(rank)


    for i in range(len(names)):
        p1 = Player.query.filter_by(name=names[i]).first()
        if p1 == None:
            pass
        # This is being passed right now because some of the websites use different
        # name abreviations for the same players, causing problems
        #    player =  Player(name=names[i], team=teams[i], position=positions[i], ffb_calc_rank=ffb_calc_ranks[i])
        #    db.session.add(player)
        #    db.session.commit()
        else:
            p1.ffb_calc_rank = ffb_calc_ranks[i]
            db.session.commit()

    print('Completed scraping Fantasy Football Calculator rankings!')
    driver.quit()

def sport_news_scrape(opts, driver):
    print('Scraping Sporting News rankings...')

    #driver = webdriver.Chrome('chromedriver', chrome_options=opts)
    driver.get('https://www.sportingnews.com/us/fantasy/news/2021-fantasy-football-rankings-top-200-cheat-sheet/1mz21lwlgdyfa1asbqdsrib2az')

    body = driver.find_element_by_class_name('article-body')
    table = body.find_element_by_tag_name('tbody')
    trs = table.find_elements_by_tag_name('tr')[1:]

    names = []
    positions = []
    teams = []
    sport_news_ranks = []

    for tr in trs:
        data = tr.find_elements_by_tag_name('td')
        rank = int(data[0].text)
        name_and_team = data[1].text.split(', ')
        names.append(name_and_team[0])
        if len(name_and_team) > 1:
            teams.append(name_and_team[1])
        else:
            teams.append(None)
        positions.append(data[2].text)
        sport_news_ranks.append(rank)

    for i in range(len(names)):
        p1 = Player.query.filter_by(name=names[i]).first()
        if p1 == None:
            pass
        # This is being passed right now because some of the websites use different
        # name abreviations for the same players, causing problems
        #    player =  Player(name=names[i], team=teams[i], position=positions[i], sport_news_rank=sport_news_ranks[i])
        #    db.session.add(player)
        #    db.session.commit()
        else:
            p1.sport_news_rank = sport_news_ranks[i]
            db.session.commit()

    print('Completed scraping Sporting News ranksings!')
    driver.quit()

def generateAdps():
    players = Player.query.all()

    for player in players:
        sum_ranks = 0
        count = 0
        if player.fp_rank:
            sum_ranks += player.fp_rank
            count += 1
        if player.ffb_calc_rank:
            sum_ranks += player.ffb_calc_rank
            count += 1
        if player.sport_news_rank:
            sum_ranks += player.sport_news_rank
            count += 1

        adp = sum_ranks / count
        player.adp = adp
        db.session.commit()

def generatePosRanks():
    players = Player.query.order_by('adp').all()
    ovr_count = 0
    qb_count = 0
    rb_count = 0
    wr_count = 0
    te_count = 0

    for player in players:
        pos = player.position
        ovr_count += 1
        player.rank = ovr_count
        if pos == 'QB':
            qb_count += 1
            player.position_rank = qb_count
        elif pos == 'RB':
            rb_count += 1
            player.position_rank = rb_count
        elif pos == 'WR':
            wr_count += 1
            player.position_rank = wr_count
        else:
            te_count += 1
            player.position_rank = te_count
        db.session.commit()

if __name__ == '__main__':
    build()


