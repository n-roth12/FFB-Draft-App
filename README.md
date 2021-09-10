# FFB-Draft-App
A web application to help fantasy football players perform better in their drafts.
Wesbite can be viewed at https://ffbdrafthelper.com or https://ffbproject.herokuapp.com.

## Website Pages

### Home Page
Contains the overall draft rankings of the top 200 fantasy football players based on rankings from Fantasy Pros, FFB Calculator, and Sporting News. 

### Rankings Page
This page allows the user to customize the rankings of the top fantasy players, as well as add tiers to their rankings. 

Rankings are customized by pressing the 
swap button next to a player on the rankings list, then entering the rank they would like to move that player to. The player will then be swapped with the player
who is located at the rank that was entered. 

All players start in Tier 1 by default, and the user may add a new tier at a rank of their choosing. The new tier will automatically be set to one greater than
the maximum current tier, and all players below the rank specified will be placed in the new tier. 

### Draft Page
The purpose of this page is to be a companion app for the user while they are participating in a live fantasy football draft. The user will select how many teams
are in the draft, the draft type, and which posiiton they are drafting at. Then they will select what player is drafted at each draft spot, and they will
be given updated information about available draft chooses based on their custom tiers and rankings. 

##### Tools and Technologies: Python, Flask, SQLite, SQLAlchemy, HTML, CSS, Javascript
