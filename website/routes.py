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
                player1_object = Rank.query.filter_by(
                    user_id=current_user.id, player_id=swapped_player_id).first()

                # This triggers when the swapped player is being moved down in the rankings (to a larger rank number)
                if new_rank > player1_object.custom_rank:
                    pos_rank_changes = []
                    above_players = db.session.query(Rank).filter(
                        Rank.user_id==current_user.id, 
                        Rank.custom_rank <= new_rank, 
                        Rank.custom_rank > player1_object.custom_rank).order_by(
                        Rank.custom_rank).all()
                    for player in above_players:
                        if player.position == player1_object.position:
                            pos_rank_changes.append(player.custom_pos_rank)
                            player.custom_pos_rank = player.custom_pos_rank - 1
                        player.custom_rank = player.custom_rank - 1
                        db.session.commit()
                    player1_object.custom_rank = new_rank
                    if len(pos_rank_changes) > 0:
                        player1_object.custom_pos_rank = pos_rank_changes[-1]
                    player1_object.custom_tier = above_players[-1].custom_tier
                    db.session.commit()

                # This triggers when the swapped player is being moved up in the rankings (to a smaller rank number)
                elif new_rank < player1_object.custom_rank:
                    pos_rank_changes = []
                    below_players = db.session.query(Rank).filter(
                        Rank.user_id==current_user.id, 
                        Rank.custom_rank >= new_rank, 
                        Rank.custom_rank < player1_object.custom_rank).order_by(
                        Rank.custom_rank).all()
                    for player in below_players:
                        if player.position == player1_object.position:
                            pos_rank_changes.append(player.custom_pos_rank)
                            player.custom_pos_rank = player.custom_pos_rank + 1
                        player.custom_rank = player.custom_rank + 1
                        db.session.commit()
                    player1_object.custom_rank = new_rank
                    if len(pos_rank_changes) > 0:
                        player1_object.custom_pos_rank = pos_rank_changes[0]
                    player1_object.custom_tier = below_players[0].custom_tier
                    db.session.commit()

            elif swap_rank_form.errors != {}:
                for err_msg in swap_rank_form.errors.values():
                    flash(f'There was an error with swapping ranks {err_msg}', category='danger')

        if form_name == 'tier-form':
            if add_tier_form.validate_on_submit():
                new_tier = add_tier_form.new_tier.data
                new_tier_cutoff = add_tier_form.new_tier_cutoff.data
                players_to_adjust = db.session.query(Rank).filter(
                    Rank.user_id == current_user.id, 
                    Rank.custom_rank >= new_tier_cutoff).all()
                for player_rank in players_to_adjust:
                    player_rank.custom_tier = new_tier
                    db.session.commit()        
                flash(f'You successfully added a new tier {new_tier}', category='success')

            elif add_tier_form.errors != {}:
                for err_msg in add_tier_form.errors.values():
                    flash(f'There was an error with creating a new tier {err_msg}', category='danger')
    
    players = db.session.query(Player, Rank.custom_rank, Rank.custom_tier, Rank.custom_pos_rank).join(
        Rank, Player.id == Rank.player_id).filter(
        Rank.user_id == current_user.id).order_by(
        Rank.custom_rank).all()
    max_tier = players[-1].custom_tier
    return render_template('rankings.html', players=players, swap_rank_form=swap_rank_form, 
        max_tier=max_tier, add_tier_form=add_tier_form)

@app.route('/rankings/<pos>', methods=['GET', 'POST'])
@login_required
def pos_rankings_page(pos):
    swap_pos_rank_form = SwapPosRankForm()

    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'pos-swap-form':
            if swap_pos_rank_form.validate_on_submit():
                swapped_player_id = request.form.get('swapped_player')
                player1_object = Rank.query.filter_by(user_id=current_user.id, 
                    player_id=swapped_player_id).first()
                new_pos_rank = int(request.form.get('new_pos_rank'))
                new_rank = db.session.query(Rank).filter(
                    Rank.user_id == current_user.id, 
                    Rank.custom_pos_rank == new_pos_rank, 
                    Rank.position == player1_object.position).first()
                new_rank = new_rank.custom_rank

                num_pos_players = len(db.session.query(Player).filter(
                    Player.position == player1_object.position).all())
                if new_pos_rank > num_pos_players:
                    flash('Please enter a position rank between 1 and ' + str(num_pos_players))
                else:
                    # This triggers when there is no rank change, so nothing needs to happen
                    if new_pos_rank == player1_object.custom_pos_rank:
                        pass

                    # This triggers when the swapped player is being moved down in the rankings (to a larger rank number)
                    elif new_pos_rank > player1_object.custom_pos_rank:
                        pos_rank_changes = []
                        above_players = db.session.query(Rank).filter(
                            Rank.user_id==current_user.id, 
                            Rank.custom_rank <= new_rank, 
                            Rank.custom_rank > player1_object.custom_rank).order_by(
                            Rank.custom_rank).all()
                        for player in above_players:
                            if player.position == player1_object.position:
                                pos_rank_changes.append(player.custom_pos_rank)
                                player.custom_pos_rank = player.custom_pos_rank - 1
                            player.custom_rank = player.custom_rank - 1
                            db.session.commit()
                        player1_object.custom_rank = new_rank
                        if len(pos_rank_changes) > 0:
                            player1_object.custom_pos_rank = pos_rank_changes[-1]
                        player1_object.custom_tier = above_players[-1].custom_tier
                        db.session.commit()

                    # This triggers when the swapped player is being moved up in the rankings (to a smaller rank number)
                    elif new_pos_rank < player1_object.custom_pos_rank:
                        pos_rank_changes = []
                        below_players = db.session.query(Rank).filter(
                            Rank.user_id==current_user.id, 
                            Rank.custom_rank >= new_rank, 
                            Rank.custom_rank < player1_object.custom_rank).order_by(
                            Rank.custom_rank).all()
                        for player in below_players:
                            if player.position == player1_object.position:
                                pos_rank_changes.append(player.custom_pos_rank)
                                player.custom_pos_rank = player.custom_pos_rank + 1
                            player.custom_rank = player.custom_rank + 1
                            db.session.commit()
                        player1_object.custom_rank = new_rank
                        if len(pos_rank_changes) > 0:
                            player1_object.custom_pos_rank = pos_rank_changes[0]
                        player1_object.custom_tier = below_players[0].custom_tier
                        db.session.commit()

            elif swap_pos_rank_form.errors != {}:
                for err_msg in swap_pos_rank_form.errors.values():
                    flash(f'There was an error with swapping ranks {err_msg}', category='danger')
                    
    pos_players = db.session.query(Player, Rank.custom_rank, Rank.custom_tier, Rank.custom_pos_rank).join(
        Rank, Player.id == Rank.player_id).filter(
        Rank.user_id == current_user.id, 
        Player.position == pos).order_by(
        Rank.custom_rank).all()
    max_pos_tier = pos_players[-1].custom_tier
    return render_template('pos_rankings.html', players=pos_players, swap_pos_rank_form=swap_pos_rank_form, 
        max_tier=max_pos_tier, position=pos)

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
            rank = Rank(user_id=user_to_create.id, player_id=player.id, 
                custom_rank=player.rank, custom_tier=1, 
                custom_pos_rank=player.position_rank, position=player.position)
            db.session.add(rank)
            db.session.commit()

        login_user(user_to_create)
        flash(f'Account created successfully! You are logged in as {user_to_create.username}', category='success')
        num_users = db.session.query(User).all()
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
@login_required
def draft_page():
    players = db.session.query(Player, Rank.custom_rank, Rank.custom_tier).join(
        Rank, Player.id == Rank.player_id).filter(
        Rank.user_id == current_user.id).order_by(
        Rank.custom_rank).all()

    qbs = db.session.query(Player, Rank.custom_rank, Rank.custom_tier, Player.rank).join(
        Rank, Player.id == Rank.player_id).filter(
        Rank.user_id == current_user.id, Player.position == "QB").order_by(
        Rank.custom_rank - Player.adp).all()

    rbs = db.session.query(Player, Rank.custom_rank, Rank.custom_tier, Player.rank).join(
        Rank, Player.id == Rank.player_id).filter(
        Rank.user_id == current_user.id, Player.position == "RB").order_by(
        Rank.custom_rank - Player.adp).all()

    wrs = db.session.query(Player, Rank.custom_rank, Rank.custom_tier, Player.rank).join(
        Rank, Player.id == Rank.player_id).filter(
        Rank.user_id == current_user.id, Player.position == "WR").order_by(
        Rank.custom_rank - Player.adp).all()

    tes = db.session.query(Player, Rank.custom_rank, Rank.custom_tier, Player.rank).join(
        Rank, Player.id == Rank.player_id).filter(
        Rank.user_id == current_user.id, Player.position == "TE").order_by(
        Rank.custom_rank - Player.adp).all()

    ids = db.session.query(Player.id).all()
    return render_template('draft.html', players=players, qbs=qbs, rbs=rbs, wrs=wrs, tes=tes)


