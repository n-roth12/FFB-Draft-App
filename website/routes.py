from website import app
from flask import render_template, redirect, url_for, flash, request
from website.models import Player, User
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

@app.route('/rankings', methods=['GET', 'POST'])
@login_required
def rankings_page():
    swap_rank_form = SwapRankForm()

    if request.method == "POST":
        if swap_rank_form.validate_on_submit():
            swapped_player = request.form.get('swapped_player')
            new_rank = request.form.get('new_rank')
            player1_object = Player.query.filter_by(name=swapped_player).first()
            player2_object = Player.query.filter_by(rank=new_rank).first()
            old_rank = player1_object.rank
            player1_object.rank = new_rank
            player2_object.rank = old_rank
            db.session.commit()
            flash('You swapped ' + player1_object.name + ' with ' + player2_object.name +'!', category='success')
        else:
            flash('Please enter the rank of a player! ', category='danger')

    
    players = Player.query.order_by('rank').all()
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

    if form.validate_on_submit():
        user_to_create = User(username=form.username.data,
            email_address=form.email_address.data,
            password=form.password1.data)
        db.session.add(user_to_create)
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

    fp_scrape(opts)
    ffb_calc_scrape(opts)
    sport_news_scrape(opts)

def fp_scrape(opts):
    print('Scraping fantasy pros rankings...')

    driver = webdriver.Chrome('/Users/NolanRoth/Desktop/ProjectWebsite/chromedriver', chrome_options=opts)
    driver.get('https://www.fantasypros.com/nfl/rankings/consensus-cheatsheets.php')

    javaScript = "window.scrollBy(0,1000);"
    driver.execute_script(javaScript)
    rankings_table = driver.find_element_by_id('ranking-table').find_element_by_tag_name('tbody')
    trs = rankings_table.find_elements_by_class_name('player-row')[:200]

    ranks = []
    names = []
    teams = []
    positions = []
    fp_ranks = []

    for tr in trs:
        tds = tr.find_elements_by_tag_name('td')
        rank = int(tds[0].text)
        ranks.append(rank)
        names.append(tds[2].find_element_by_tag_name('a').text)
        teams.append(tds[2].find_element_by_tag_name('span').text.replace('(', '').replace(')', ''))
        position_rank = tds[3].text
        positions.append(re.sub('[^a-zA-Z]+', '', position_rank))
        fp_ranks.append(rank)
    
    for i in range(len(ranks)):
        p1 = Player.query.filter_by(name=names[i]).first()
        if p1 == None:
            player =  Player(rank=ranks[i], name=names[i], team=teams[i], position=positions[i], fp_rank=fp_ranks[i])
            db.session.add(player)
            db.session.commit()
        else:
            p1.fp_rank = fp_ranks[i]
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

    ranks = []
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

        ranks.append(rank)
        names.append(name)
        teams.append(team)
        positions.append(position)
        ffb_calc_ranks.append(rank)


    for i in range(len(ranks)):
        p1 = Player.query.filter_by(name=names[i]).first()
        if p1 == None:
            pass
        #    player =  Player(rank=ranks[i], name=names[i], team=teams[i], position=positions[i], ffb_calc_rank=ffb_calc_ranks[i])
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

    ranks = []
    names = []
    positions = []
    teams = []
    sport_news_ranks = []

    for tr in trs:
        data = tr.find_elements_by_tag_name('td')
        rank = int(data[0].text)
        ranks.append(rank)
        name_and_team = data[1].text.split(', ')
        names.append(name_and_team[0])
        if len(name_and_team) > 1:
            teams.append(name_and_team[1])
        else:
            teams.append(None)
        positions.append(data[2].text)
        sport_news_ranks.append(rank)

    for i in range(len(ranks)):
        p1 = Player.query.filter_by(name=names[i]).first()
        if p1 == None:
            pass
        #    player =  Player(rank=ranks[i], name=names[i], team=teams[i], position=positions[i], sport_news_rank=sport_news_ranks[i])
        #    db.session.add(player)
        #    db.session.commit()
        else:
            p1.sport_news_rank = sport_news_ranks[i]
            db.session.commit()

    print('Completed scraping sporting news ranks!')
    driver.quit()






