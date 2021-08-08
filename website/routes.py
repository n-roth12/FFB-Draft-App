from website import app
from flask import render_template, redirect, url_for, flash, request
from website.models import Player, User, Rank
from website.forms import RegisterForm, LoginForm, SwapRankForm 
from website import db
from flask_login import login_user, logout_user, login_required, current_user
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
# this is a test

@app.route('/')
@app.route('/home')  
def home_page():
    players = Player.query.order_by('rank').all()
    return render_template('home.html', players=players)

# Route specifically dedicated to clearing and reconstructing database
# from website scrapes. Entering this route will delete all database information
# including registered users and players.
@app.route('/scrape')
def scrape_route():
    db.drop_all()
    db.create_all()
    db.session.commit()
    scrape()
    generateAdps()
    generatePosRanks()
    players = Player.query.order_by('rank').all()
    return render_template('home.html', players=players)

@app.route('/rankings', methods=['GET', 'POST'])
@login_required
def rankings_page():
    swap_rank_form = SwapRankForm()

    if request.method == "POST":
        if swap_rank_form.validate_on_submit():
            swapped_player_id = request.form.get('swapped_player')
            new_rank = request.form.get('new_rank')
            player1_object = Rank.query.filter_by(user_id=current_user.id, player_id=swapped_player_id).first()
            player2_object = Rank.query.filter_by(user_id=current_user.id, custom_rank=new_rank).first()
            old_rank = player1_object.custom_rank
            player1_object.custom_rank = new_rank
            player2_object.custom_rank = old_rank
            db.session.commit()

            flash('You swapped rank !', category='success')
        else:
            flash('Please enter the rank of a player! ', category='danger')

    #ranks = Rank.query.filter_by(user_id=current_user.id).order_by('custom_rank')

    players = db.session.query(Player, Rank.custom_rank).join(Rank, Player.id == Rank.player_id).order_by(Rank.custom_rank).all()
    return render_template('rankings.html', players=players, swap_rank_form=swap_rank_form)

@app.route('/rankings/qb', methods=['GET', 'POST'])
@login_required
def qb_rankings_page():
    swap_rank_form = SwapRankForm()

    qb_players = Player.query.filter_by(position='QB').order_by('rank')
    return render_template('qb_rankings.html', players=qb_players, swap_rank_form=swap_rank_form)

@app.route('/rankings/rb', methods=['GET', 'POST'])
@login_required
def rb_rankings_page():
    swap_rank_form = SwapRankForm()

    rb_players = Player.query.filter_by(position='RB').order_by('rank')
    return render_template('rb_rankings.html', players=rb_players, swap_rank_form=swap_rank_form)

@app.route('/rankings/wr', methods=['GET', 'POST'])
@login_required
def wr_rankings_page():
    swap_rank_form = SwapRankForm()

    wr_players = Player.query.filter_by(position='WR').order_by('rank')
    return render_template('wr_rankings.html', players=wr_players, swap_rank_form=swap_rank_form)

@app.route('/rankings/te', methods=['GET', 'POST'])
@login_required
def te_rankings_page():
    swap_rank_form = SwapRankForm()

    te_players = Player.query.filter_by(position='TE').order_by('rank')
    return render_template('te_rankings.html', players=te_players, swap_rank_form=swap_rank_form)

@app.route('/register', methods=['GET', 'POST'])    # needed so that this route can handle post requests
def register_page():
    form = RegisterForm()
    players = Player.query.order_by('rank').all()

    if form.validate_on_submit():
        user_to_create = User(username=form.username.data,
            email_address=form.email_address.data,
            password=form.password1.data)
        db.session.add(user_to_create)
        db.session.commit()
        for player in players:
            rank = Rank(user_id=user_to_create.id, player_id=player.id, custom_rank=player.rank)
            db.session.add(rank)
            db.session.commit()

        login_user(user_to_create)
        flash(f'Account created successfully! You are logged in as {user_to_create.username}', category='success')


        return redirect(url_for('rankings_page'))

    # checking if there are no errors from the validations
    if form.errors != {}:
        for err_msg in form.errors.values():
            flash(f'There was an error with creating a user: {err_msg}', category='danger')

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()

    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()
        if attempted_user and attempted_user.check_password_correction(attempted_password=form.password.data):
            login_user(attempted_user)
            flash(f'Success! You are logged in as: {attempted_user.username}', category='success')
            return redirect(url_for('rankings_page'))
        else:
            flash('Username and password not found. Please try again.', category='danger')

    return render_template('login.html', form=form)

@app.route('/logout')
def logout_page():
    logout_user()
    flash('You have been logged out!', category='info')
    return redirect(url_for("home_page"))

@app.route('/draft')
def draft_page():
    players = Player.query.order_by('rank').all()
    swap_rank_form = SwapRankForm()
    return render_template('draft.html', players=players, swap_rank_form=swap_rank_form)


def scrape():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--disable-notifications")

    #fp_scrape(opts)
    sport_news_scrape(opts)
    ffb_calc_scrape(opts)

def fp_scrape(opts):
    print('Scraping fantasy pros rankings...')

    driver = webdriver.Chrome('/Users/NolanRoth/Desktop/ProjectWebsite/chromedriver', chrome_options=opts)
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
        player =  Player(name=names[i], team=teams[i], position=positions[i], fp_rank=fp_ranks[i])
        db.session.add(player)
        db.session.commit()


    print('Completed scraping fantasy pros ranks!')
    driver.quit()

def ffb_calc_scrape(opts):
    print('Scraping fantasy football calculator...')

    driver = webdriver.Chrome('/Users/NolanRoth/Desktop/ProjectWebsite/chromedriver', chrome_options=opts)
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
        #    player =  Player(name=names[i], team=teams[i], position=positions[i], ffb_calc_rank=ffb_calc_ranks[i])
        #    db.session.add(player)
        #    db.session.commit()
        else:
            p1.ffb_calc_rank = ffb_calc_ranks[i]
            db.session.commit()

    print('Completed scraping fantasy football calculator!')
    driver.quit()

def sport_news_scrape(opts):
    print('Scraping Sporting News rankings...')

    driver = webdriver.Chrome('/Users/NolanRoth/Desktop/ProjectWebsite/chromedriver', chrome_options=opts)
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
        #    pass
            player =  Player(name=names[i], team=teams[i], position=positions[i], sport_news_rank=sport_news_ranks[i])
            db.session.add(player)
            db.session.commit()
        else:
            p1.sport_news_rank = sport_news_ranks[i]
            db.session.commit()

    print('Completed scraping sporting news ranks!')
    driver.quit()

def generateAdps():
    players = Player.query.all()

    for player in players:
        sum_ranks = 0
        count = 0
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








