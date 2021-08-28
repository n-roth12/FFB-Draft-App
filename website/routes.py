from website import app
from flask import render_template, redirect, url_for, flash, request
from website.models import Player, User, Rank
from website.forms import RegisterForm, LoginForm, SwapRankForm, AddTierForm, SwapPosRankForm
from website import db
from flask_login import login_user, logout_user, login_required, current_user
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import re

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

# This route is meant to be used after the scrape route in order to prevent 
# unnecessary scraping. It generates the ADPs and position ranks for each player
# based on the scraped data.
@app.route('/generate')
def generate_route():
    generateAdps()
    generatePosRanks()
    players = Player.query.order_by('adp').all()
    return render_template('home.html', players=players)

@app.route('/rankings', methods=['GET', 'POST'])
@login_required
def rankings_page():
    swap_rank_form = SwapRankForm()
    add_tier_form = AddTierForm()

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'swap-form':
            if swap_rank_form.validate_on_submit():
                swapped_player_id = request.form.get('swapped_player')
                new_rank = int(request.form.get('new_rank'))
                player1_object = Rank.query.filter_by(user_id=current_user.id, player_id=swapped_player_id).first()

                # This triggers when there is no rank change, so nothing needs to happen
                if new_rank == player1_object.custom_rank:
                    pass

                # This triggers when the swapped player is being moved down in the rankings (to a larger rank number)
                elif new_rank > player1_object.custom_rank:
                    pos_rank_changes = []
                    above_players = db.session.query(Rank).filter(Rank.user_id==current_user.id, Rank.custom_rank <= new_rank, Rank.custom_rank > player1_object.custom_rank).order_by(Rank.custom_rank).all()
                    for player in above_players:
                        if player.position == player1_object.position:
                            pos_rank_changes.append(player.custom_pos_rank)
                            player.custom_pos_rank = player.custom_pos_rank - 1
                        player.custom_rank = player.custom_rank - 1
                        db.session.commit()
                    player1_object.custom_rank = new_rank
                    if len(pos_rank_changes) > 0:
                        player1_object.custom_pos_rank = pos_rank_changes[-1]
                    db.session.commit()

                # This triggers when the swapped player is being moved up in the rankings (to a smaller rank number)
                elif new_rank < player1_object.custom_rank:
                    pos_rank_changes = []
                    below_players = db.session.query(Rank).filter(Rank.user_id==current_user.id, Rank.custom_rank >= new_rank, Rank.custom_rank < player1_object.custom_rank).order_by(Rank.custom_rank).all()
                    for player in below_players:
                        if player.position == player1_object.position:
                            pos_rank_changes.append(player.custom_pos_rank)
                            player.custom_pos_rank = player.custom_pos_rank + 1
                        player.custom_rank = player.custom_rank + 1
                        db.session.commit()
                    player1_object.custom_rank = new_rank
                    if len(pos_rank_changes) > 0:
                        player1_object.custom_pos_rank = pos_rank_changes[0]
                    db.session.commit()

            elif swap_rank_form.errors != {}:
                for err_msg in swap_rank_form.errors.values():
                    flash(f'There was an error with swapping ranks {err_msg}', category='danger')

        if form_name == 'tier-form':
            if add_tier_form.validate_on_submit():
                new_tier = add_tier_form.new_tier.data
                new_tier_cutoff = add_tier_form.new_tier_cutoff.data
                players_to_adjust = db.session.query(Rank).filter(Rank.user_id == current_user.id, Rank.custom_rank >= new_tier_cutoff).all()
                for player_rank in players_to_adjust:
                    player_rank.custom_tier = new_tier
                    db.session.commit()        
                flash(f'You successfully added a new tier {new_tier}', category='success')

            elif add_tier_form.errors != {}:
                for err_msg in add_tier_form.errors.values():
                    flash(f'There was an error with creating a new tier {err_msg}', category='danger')
    
    players = db.session.query(Player, Rank.custom_rank, Rank.custom_tier, Rank.custom_pos_rank).join(Rank, Player.id == Rank.player_id).filter(Rank.user_id == current_user.id).order_by(Rank.custom_rank).all()
    max_tier = players[-1].custom_tier
    return render_template('rankings.html', players=players, swap_rank_form=swap_rank_form, max_tier=max_tier, add_tier_form=add_tier_form)

@app.route('/rankings/qb', methods=['GET', 'POST'])
@login_required
def qb_rankings_page():
    swap_pos_rank_form = SwapPosRankForm()
    add_tier_form = AddTierForm()

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'pos-swap-form':
            if swap_pos_rank_form.validate_on_submit():
                swapped_player_id = request.form.get('swapped_player')
                player1_object = Rank.query.filter_by(user_id=current_user.id, player_id=swapped_player_id).first()
                new_pos_rank = int(request.form.get('new_pos_rank'))
                new_rank = db.session.query(Rank).filter(Rank.user_id == current_user.id, Rank.custom_pos_rank == new_pos_rank, Rank.position == player1_object.position).first()
                print(new_rank.player_id)
                new_rank = new_rank.custom_rank

                num_pos_players = len(db.session.query(Player).filter(Player.position == player1_object.position).all())
                if new_pos_rank > num_pos_players:
                    flash('Please enter a position rank between 1 and ' + str(num_pos_players))
                else:
                    # This triggers when there is no rank change, so nothing needs to happen
                    if new_pos_rank == player1_object.custom_pos_rank:
                        pass

                    # This triggers when the swapped player is being moved down in the rankings (to a larger rank number)
                    elif new_pos_rank > player1_object.custom_pos_rank:
                        pos_rank_changes = []
                        above_players = db.session.query(Rank).filter(Rank.user_id==current_user.id, Rank.custom_rank <= new_rank, Rank.custom_rank > player1_object.custom_rank).order_by(Rank.custom_rank).all()
                        for player in above_players:
                            if player.position == player1_object.position:
                                pos_rank_changes.append(player.custom_pos_rank)
                                player.custom_pos_rank = player.custom_pos_rank - 1
                            player.custom_rank = player.custom_rank - 1
                            db.session.commit()
                        player1_object.custom_rank = new_rank
                        if len(pos_rank_changes) > 0:
                            player1_object.custom_pos_rank = pos_rank_changes[-1]
                        db.session.commit()

                    # This triggers when the swapped player is being moved up in the rankings (to a smaller rank number)
                    elif new_pos_rank < player1_object.custom_pos_rank:
                        pos_rank_changes = []
                        below_players = db.session.query(Rank).filter(Rank.user_id==current_user.id, Rank.custom_rank >= new_rank, Rank.custom_rank < player1_object.custom_rank).order_by(Rank.custom_rank).all()
                        for player in below_players:
                            if player.position == player1_object.position:
                                pos_rank_changes.append(player.custom_pos_rank)
                                player.custom_pos_rank = player.custom_pos_rank + 1
                            player.custom_rank = player.custom_rank + 1
                            db.session.commit()
                        player1_object.custom_rank = new_rank
                        if len(pos_rank_changes) > 0:
                            player1_object.custom_pos_rank = pos_rank_changes[0]
                        db.session.commit()

            elif swap_pos_rank_form.errors != {}:
                for err_msg in swap_pos_rank_form.errors.values():
                    flash(f'There was an error with swapping ranks {err_msg}', category='danger')

    qb_players = db.session.query(Player, Rank.custom_rank, Rank.custom_tier, Rank.custom_pos_rank).join(Rank, Player.id == Rank.player_id).filter(Rank.user_id == current_user.id, Player.position == 'QB').order_by(Rank.custom_rank).all()
    max_qb_tier = qb_players[-1].custom_tier
    return render_template('qb_rankings.html', players=qb_players, swap_pos_rank_form=swap_pos_rank_form, max_tier=max_qb_tier, add_tier_form=add_tier_form)

@app.route('/rankings/rb', methods=['GET', 'POST'])
@login_required
def rb_rankings_page():
    swap_pos_rank_form = SwapPosRankForm()
    add_tier_form = AddTierForm()

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'pos-swap-form':
            if swap_pos_rank_form.validate_on_submit():
                swapped_player_id = request.form.get('swapped_player')
                player1_object = Rank.query.filter_by(user_id=current_user.id, player_id=swapped_player_id).first()
                new_pos_rank = int(request.form.get('new_pos_rank'))
                new_rank = db.session.query(Rank).filter(Rank.user_id == current_user.id, Rank.custom_pos_rank == new_pos_rank, Rank.position == player1_object.position).first()
                print(new_rank.player_id)
                new_rank = new_rank.custom_rank

                num_pos_players = len(db.session.query(Player).filter(Player.position == player1_object.position).all())
                if new_pos_rank > num_pos_players:
                    flash('Please enter a position rank between 1 and ' + str(num_pos_players))
                else:
                    # This triggers when there is no rank change, so nothing needs to happen
                    if new_pos_rank == player1_object.custom_pos_rank:
                        pass

                    # This triggers when the swapped player is being moved down in the rankings (to a larger rank number)
                    elif new_pos_rank > player1_object.custom_pos_rank:
                        pos_rank_changes = []
                        above_players = db.session.query(Rank).filter(Rank.user_id==current_user.id, Rank.custom_rank <= new_rank, Rank.custom_rank > player1_object.custom_rank).order_by(Rank.custom_rank).all()
                        for player in above_players:
                            if player.position == player1_object.position:
                                pos_rank_changes.append(player.custom_pos_rank)
                                player.custom_pos_rank = player.custom_pos_rank - 1
                            player.custom_rank = player.custom_rank - 1
                            db.session.commit()
                        player1_object.custom_rank = new_rank
                        if len(pos_rank_changes) > 0:
                            player1_object.custom_pos_rank = pos_rank_changes[-1]
                        db.session.commit()

                    # This triggers when the swapped player is being moved up in the rankings (to a smaller rank number)
                    elif new_pos_rank < player1_object.custom_pos_rank:
                        pos_rank_changes = []
                        below_players = db.session.query(Rank).filter(Rank.user_id==current_user.id, Rank.custom_rank >= new_rank, Rank.custom_rank < player1_object.custom_rank).order_by(Rank.custom_rank).all()
                        for player in below_players:
                            if player.position == player1_object.position:
                                pos_rank_changes.append(player.custom_pos_rank)
                                player.custom_pos_rank = player.custom_pos_rank + 1
                            player.custom_rank = player.custom_rank + 1
                            db.session.commit()
                        player1_object.custom_rank = new_rank
                        if len(pos_rank_changes) > 0:
                            player1_object.custom_pos_rank = pos_rank_changes[0]
                        db.session.commit()

            elif swap_pos_rank_form.errors != {}:
                for err_msg in swap_pos_rank_form.errors.values():
                    flash(f'There was an error with swapping ranks {err_msg}', category='danger')

    rb_players = db.session.query(Player, Rank.custom_rank, Rank.custom_tier, Rank.custom_pos_rank).join(Rank, Player.id == Rank.player_id).filter(Rank.user_id == current_user.id, Player.position == 'RB').order_by(Rank.custom_rank).all()
    max_rb_tier = rb_players[-1].custom_tier
    return render_template('rb_rankings.html', players=rb_players, swap_pos_rank_form=swap_pos_rank_form, max_tier=max_rb_tier, add_tier_form=add_tier_form)

@app.route('/rankings/wr', methods=['GET', 'POST'])
@login_required
def wr_rankings_page():
    swap_pos_rank_form = SwapPosRankForm()
    add_tier_form = AddTierForm()

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'pos-swap-form':
            if swap_pos_rank_form.validate_on_submit():
                swapped_player_id = request.form.get('swapped_player')
                player1_object = Rank.query.filter_by(user_id=current_user.id, player_id=swapped_player_id).first()
                new_pos_rank = int(request.form.get('new_pos_rank'))
                new_rank = db.session.query(Rank).filter(Rank.user_id == current_user.id, Rank.custom_pos_rank == new_pos_rank, Rank.position == player1_object.position).first()
                print(new_rank.player_id)
                new_rank = new_rank.custom_rank

                num_pos_players = len(db.session.query(Player).filter(Player.position == player1_object.position).all())
                if new_pos_rank > num_pos_players:
                    flash('Please enter a position rank between 1 and ' + str(num_pos_players))
                else:
                    # This triggers when there is no rank change, so nothing needs to happen
                    if new_pos_rank == player1_object.custom_pos_rank:
                        pass

                    # This triggers when the swapped player is being moved down in the rankings (to a larger rank number)
                    elif new_pos_rank > player1_object.custom_pos_rank:
                        pos_rank_changes = []
                        above_players = db.session.query(Rank).filter(Rank.user_id==current_user.id, Rank.custom_rank <= new_rank, Rank.custom_rank > player1_object.custom_rank).order_by(Rank.custom_rank).all()
                        for player in above_players:
                            if player.position == player1_object.position:
                                pos_rank_changes.append(player.custom_pos_rank)
                                player.custom_pos_rank = player.custom_pos_rank - 1
                            player.custom_rank = player.custom_rank - 1
                            db.session.commit()
                        player1_object.custom_rank = new_rank
                        if len(pos_rank_changes) > 0:
                            player1_object.custom_pos_rank = pos_rank_changes[-1]
                        db.session.commit()

                    # This triggers when the swapped player is being moved up in the rankings (to a smaller rank number)
                    elif new_pos_rank < player1_object.custom_pos_rank:
                        pos_rank_changes = []
                        below_players = db.session.query(Rank).filter(Rank.user_id==current_user.id, Rank.custom_rank >= new_rank, Rank.custom_rank < player1_object.custom_rank).order_by(Rank.custom_rank).all()
                        for player in below_players:
                            if player.position == player1_object.position:
                                pos_rank_changes.append(player.custom_pos_rank)
                                player.custom_pos_rank = player.custom_pos_rank + 1
                            player.custom_rank = player.custom_rank + 1
                            db.session.commit()
                        player1_object.custom_rank = new_rank
                        if len(pos_rank_changes) > 0:
                            player1_object.custom_pos_rank = pos_rank_changes[0]
                        db.session.commit()

            elif swap_pos_rank_form.errors != {}:
                for err_msg in swap_pos_rank_form.errors.values():
                    flash(f'There was an error with swapping ranks {err_msg}', category='danger')

    wr_players = db.session.query(Player, Rank.custom_rank, Rank.custom_tier, Rank.custom_pos_rank).join(Rank, Player.id == Rank.player_id).filter(Rank.user_id == current_user.id, Player.position == 'WR').order_by(Rank.custom_rank).all()
    max_wr_tier = wr_players[-1].custom_tier
    return render_template('wr_rankings.html', players=wr_players, swap_pos_rank_form=swap_pos_rank_form, max_tier=max_wr_tier, add_tier_form=add_tier_form)

@app.route('/rankings/te', methods=['GET', 'POST'])
@login_required
def te_rankings_page():
    swap_pos_rank_form = SwapPosRankForm()
    add_tier_form = AddTierForm()

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'pos-swap-form':
            if swap_pos_rank_form.validate_on_submit():
                swapped_player_id = request.form.get('swapped_player')
                player1_object = Rank.query.filter_by(user_id=current_user.id, player_id=swapped_player_id).first()
                new_pos_rank = int(request.form.get('new_pos_rank'))
                new_rank = db.session.query(Rank).filter(Rank.user_id == current_user.id, Rank.custom_pos_rank == new_pos_rank, Rank.position == player1_object.position).first()
                print(new_rank.player_id)
                new_rank = new_rank.custom_rank

                num_pos_players = len(db.session.query(Player).filter(Player.position == player1_object.position).all())
                if new_pos_rank > num_pos_players:
                    flash('Please enter a position rank between 1 and ' + str(num_pos_players))
                else:
                    # This triggers when there is no rank change, so nothing needs to happen
                    if new_pos_rank == player1_object.custom_pos_rank:
                        pass

                    # This triggers when the swapped player is being moved down in the rankings (to a larger rank number)
                    elif new_pos_rank > player1_object.custom_pos_rank:
                        pos_rank_changes = []
                        above_players = db.session.query(Rank).filter(Rank.user_id==current_user.id, Rank.custom_rank <= new_rank, Rank.custom_rank > player1_object.custom_rank).order_by(Rank.custom_rank).all()
                        for player in above_players:
                            if player.position == player1_object.position:
                                pos_rank_changes.append(player.custom_pos_rank)
                                player.custom_pos_rank = player.custom_pos_rank - 1
                            player.custom_rank = player.custom_rank - 1
                            db.session.commit()
                        player1_object.custom_rank = new_rank
                        if len(pos_rank_changes) > 0:
                            player1_object.custom_pos_rank = pos_rank_changes[-1]
                        db.session.commit()

                    # This triggers when the swapped player is being moved up in the rankings (to a smaller rank number)
                    elif new_pos_rank < player1_object.custom_pos_rank:
                        pos_rank_changes = []
                        below_players = db.session.query(Rank).filter(Rank.user_id==current_user.id, Rank.custom_rank >= new_rank, Rank.custom_rank < player1_object.custom_rank).order_by(Rank.custom_rank).all()
                        for player in below_players:
                            if player.position == player1_object.position:
                                pos_rank_changes.append(player.custom_pos_rank)
                                player.custom_pos_rank = player.custom_pos_rank + 1
                            player.custom_rank = player.custom_rank + 1
                            db.session.commit()
                        player1_object.custom_rank = new_rank
                        if len(pos_rank_changes) > 0:
                            player1_object.custom_pos_rank = pos_rank_changes[0]
                        db.session.commit()

            elif swap_pos_rank_form.errors != {}:
                for err_msg in swap_pos_rank_form.errors.values():
                    flash(f'There was an error with swapping ranks {err_msg}', category='danger')

    te_players = db.session.query(Player, Rank.custom_rank, Rank.custom_tier, Rank.custom_pos_rank).join(Rank, Player.id == Rank.player_id).filter(Rank.user_id == current_user.id, Player.position == 'TE').order_by(Rank.custom_rank).all()
    max_te_tier = te_players[-1].custom_tier
    return render_template('te_rankings.html', players=te_players, swap_pos_rank_form=swap_pos_rank_form, max_tier=max_te_tier, add_tier_form=add_tier_form)

@app.route('/register', methods=['GET', 'POST'])
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
            rank = Rank(user_id=user_to_create.id, player_id=player.id, custom_rank=player.rank, custom_tier=1, custom_pos_rank=player.position_rank, position=player.position)
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
    players = db.session.query(Player, Rank.custom_rank, Rank.custom_tier).join(Rank, Player.id == Rank.player_id).filter(Rank.user_id == current_user.id).order_by(Rank.custom_rank).all()
    values = db.session.query(Player, Rank.custom_rank, Rank.custom_rank - Player.adp).join(Rank, Player.id == Rank.player_id).filter(Rank.user_id == current_user.id).order_by(Rank.custom_rank - Player.adp).all()
    qbs = db.session.query(Player, Rank.custom_rank, Rank.custom_tier).join(Rank, Player.id == Rank.player_id).filter(Rank.user_id == current_user.id, Player.position == "QB").order_by(Rank.custom_rank).all()
    rbs = db.session.query(Player, Rank.custom_rank, Rank.custom_tier).join(Rank, Player.id == Rank.player_id).filter(Rank.user_id == current_user.id, Player.position == "RB").order_by(Rank.custom_rank).all()
    wrs = db.session.query(Player, Rank.custom_rank, Rank.custom_tier).join(Rank, Player.id == Rank.player_id).filter(Rank.user_id == current_user.id, Player.position == "WR").order_by(Rank.custom_rank).all()
    tes = db.session.query(Player, Rank.custom_rank, Rank.custom_tier).join(Rank, Player.id == Rank.player_id).filter(Rank.user_id == current_user.id, Player.position == "TE").order_by(Rank.custom_rank).all()
    ids = db.session.query(Player.id).all()

    return render_template('draft.html', players=players, values=values, qbs=qbs, rbs=rbs, wrs=wrs, tes=tes, ids=json.dumps(ids))


def scrape():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--disable-notifications")

    fp_scrape(opts)
    sport_news_scrape(opts)
    ffb_calc_scrape(opts)

def fp_scrape(opts):
    print('Scraping Fantasy Pros rankings...')

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

def ffb_calc_scrape(opts):
    print('Scraping Fantasy Football Calculator rankings...')

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








