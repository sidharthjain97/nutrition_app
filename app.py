from flask import Flask, request, redirect, url_for, session, g, render_template
import sqlite3
import os
from datetime import datetime
from database import connect_db, get_db

app = Flask(__name__)

app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'thisisasecret!'

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/', methods=['GET','POST'])
def index():
    db = get_db()
    if request.method == 'POST':
        date = request.form['date']

        dt = datetime.strptime(date, '%Y-%m-%d')
        database_dt = datetime.strftime(dt, '%Y%m%d')

        db.execute('insert into log_date (entry_date) values(?)', [database_dt])
        db.commit()

    cur = db.execute('select log_date.entry_date, sum(food.protein) as protein, sum(food.carbohydrates) as carbohydrates, sum(food.fat) as fat, sum(food.calories) as calories from log_date left join food_date on log_date.id = food_date.log_date_id left join food on food.id = food_date.food_id group by log_date.entry_date order by entry_date desc')
    results = cur.fetchall()

    date_results = []

    for i in results:
        single_date = {}
        
        single_date['entry_date'] = i['entry_date']
        single_date['protein'] = i['protein']
        single_date['carbohydrates'] = i['carbohydrates']
        single_date['fat'] = i['fat']
        single_date['calories'] = i['calories']

        d = datetime.strptime(str(i['entry_date']), '%Y%m%d')
        single_date['pretty_date'] = datetime.strftime(d, '%B %d, %Y')
        
        date_results.append(single_date)

    return render_template('home.html', results=date_results)


@app.route('/view/<date>', methods=['GET','POST'])
def view(date):
    db = get_db()
    cur = db.execute('select id, entry_date from log_date where entry_date=?', [date])
    date_results = cur.fetchone()

    if request.method == 'POST':
        food_name = request.form['food-select']
        food_name_cur = db.execute('select id from food where name=?', [food_name])
        food_name_results = food_name_cur.fetchone()

        db.execute('insert into food_date (food_id, log_date_id) values (?,?)', [food_name_results['id'], date_results['id']])
        db.commit()

    d = datetime.strptime(str(date_results['entry_date']), '%Y%m%d')
    pretty_date = datetime.strftime(d, '%B %d, %Y')

    food_cur = db.execute('select id, name from food')
    food_results = food_cur.fetchall()

    log_cur = db.execute('select food.name, food.protein, food.carbohydrates, food.fat, food.calories from log_date left join food_date on log_date.id = food_date.log_date_id left join food on food.id = food_date.food_id where log_date.entry_date=?', [date])

    log_results = log_cur.fetchall()

    totals = {}

    totals['protein'] = 0
    totals['carbohydrates'] = 0
    totals['fat'] = 0
    totals['calories'] = 0
    
    for food in log_results:
        if food['protein'] is None:
            totals['protein']=0
        else:    
            totals['protein'] += food['protein']

        if food['carbohydrates'] is None:
            totals['carbohydrates']=0
        else:
            totals['carbohydrates'] += food['carbohydrates']

        if food['fat'] is None:
            totals['fat']=0
        else:
            totals['fat'] += food['fat']

        if food['calories'] is None:
            totals['calories']=0
        else:
            totals['calories'] += food['calories']

    return render_template('day.html', entry_date=date_results['entry_date'] ,pretty_date=pretty_date, food_results=food_results, log_results=log_results, totals=totals)


@app.route('/add_food', methods=['GET','POST'])
def add_food():
    db = get_db()

    if request.method == 'POST':
        name = request.form['food-name']
        protein = int(request.form['protein'])
        carbohydrates = int(request.form['carbohydrates'])
        fat = int(request.form['fat'])

        calories = protein * 4 + carbohydrates * 4 + fat * 9

        
        db.execute('insert into food (name, protein, carbohydrates, fat, calories) values (?,?,?,?,?)', [name, protein, carbohydrates, fat, calories])

        db.commit()

    cur = db.execute('select name, protein, carbohydrates, fat, calories from food')
    results = cur.fetchall()

    return render_template('add_food.html', results=results)


if __name__ == '__main__':
    app.run()

