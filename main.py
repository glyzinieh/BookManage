import json
import os
import urllib.request

import pandas as pd
import requests
from flask import Flask, redirect, render_template, request
from PIL import Image
from pyzbar.pyzbar import decode
from werkzeug import secure_filename

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/record/')
def record():
    return render_template('record.html')

@app.route('/upload/', methods=['GET', 'POST'])
def Upload():
    file = request.files['file']
    filename = secure_filename(file.filename)
    extension = os.path.splitext(filename)
    save = 'upload' + extension[1]
    file.save(save)
    try:
        code = decode(Image.open(file))
        code = code[0][0].decode('utf-8', 'ignore')
        os.remove(save)
        return redirect('/get/?isbn='+code)
    except:
        os.remove(save)
        return redirect('/get/?isbn=')

@app.route('/get/')
def AcquireData():
    isbn = request.args.get('isbn')
    url = 'https://api.openbd.jp/v1/get?isbn=' + isbn
    res = urllib.request.urlopen(url)
    # json_loads() でPythonオブジェクトに変換
    data = json.loads(res.read().decode('utf-8'))
    msg = ''
    if data[0] == None:
        title = ''
        publisher = ''
        series = ''
        volume = ''
        author = ''
        pubdate = ''
        cover = ''
        text = ''
        msg = msg + '該当データが見つかりませんでした。'
    else:
        try:
            title = data[0]['summary']['title']
            publisher = data[0]['summary']['publisher']
            series = data[0]['summary']['series']
            volume = data[0]['summary']['volume']
            author = data[0]['summary']['author']
            pubdate = data[0]['summary']['pubdate']
            cover = data[0]['summary']['cover']
            text = ''
            for count in data[0]['onix']['CollateralDetail']['TextContent']:
                text += count['Text']
            df = pd.read_csv('data.csv',usecols=['isbn'])
            isbn = int(isbn)
            if isbn in df.values:
                msg = msg + 'このISBNは登録済みです。重複登録されてしまいますがよろしいですか。'
        except KeyError:
            pass
    return render_template('get.html', msg=msg, isbn=isbn, title=title, publisher=publisher, series=series, volume=volume, author=author, pubdate=pubdate, cover=cover, text=text)

@app.route('/save/', methods=['GET', 'POST'])
def save():
    cover = request.form['cover']
    isbn = request.form['isbn']
    title = request.form['title']
    publisher = request.form['publisher']
    series = request.form['series']
    volume = request.form['volume']
    author = request.form['author']
    pubdate = request.form['pubdate']
    text = request.form['text']
    location = request.form['location']
    writing = pd.DataFrame([[cover,isbn,title,publisher,series,volume,author,pubdate,text,location]])
    writing.to_csv("data.csv", index=False, encoding="utf-8", mode='a', header=False)
    return render_template('save.html', isbn=isbn, title=title, publisher=publisher, series=series, volume=volume, author=author, pubdate=pubdate, cover=cover, text=text, location=location)

@app.route('/search/')
def search():
    return render_template('search.html')

@app.route('/favicon.ico/')
def favicon():
    return app.send_static_file('favicon.ico')

@app.errorhandler(404)
def error_handler(error):
    return render_template('error.html', name=error.name, code=error.code),404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(port=port)
