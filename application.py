from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
import logging
import os
import requests
import re
import pandas as pd
import pymongo
from pymongo.mongo_client import MongoClient

#logging.basicConfig(filename="scrapper.log" , level=logging.INFO)

application = app = Flask(__name__)

@app.route("/", methods = ['GET'])
def homepage():
    return render_template("index.html")

@app.route("/review" , methods = ['POST' , 'GET'])
def index():
    if request.method == 'POST':
        try:
            input_text = request.form['content']
            input_text = input_text.replace(" ", "")
            url = f'https://www.youtube.com/@{input_text}/videos'

            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"}
            response = requests.get(url, headers=headers)
            print(response.status_code)
            response_text = response.text
            vid_titles = re.findall('"title":{"runs":\[{"text":".*?"', response_text)
            vid_thumbnails = re.findall(r"https://i.ytimg.com/vi/[A-Za-z0-9_-]{11}/[A-Za-z0-9_]{9}.jpg", response_text)
            vid_links = re.findall(r"watch\?v=[A-Za-z0-9_-]{11}", response_text)
            pattern3 = re.compile(r"[0-9]+(\.[0-9]+)?[a-zA-Z]*K views")
            pattern4 = re.compile(r"\d+ (minutes|hours|hour|days|day|weeks|week|years|year) ago")
            matches1 = pattern3.finditer(response_text)
            matches2 = pattern4.finditer(response_text)
            vid_viewcounts=[]
            vid_ages=[]
            count = 0
            for match1,match2 in zip(matches1,matches2):
                vid_ages.append(match2[0])
                vid_viewcounts.append(match1[0])

            titles = vid_titles[0:10]
            thumbnails = list(dict.fromkeys(vid_thumbnails))
            links = vid_links[0:10]
            viewcounts=vid_viewcounts[0:20:2]
            ages=vid_ages[0:20:2]

            details_list=[]

            for title,thumbnail,link,viewcount,age in zip(titles,thumbnails,links,viewcounts,ages):
                details_dict={
                "title":title.split('"')[-2], "thumbnail": thumbnail, "link": "https://www.youtube.com/"+link,
                "viewcount": viewcount, "age": age
                }
                details_list.append(details_dict)

            df = pd.DataFrame(details_list)


            uri = "mongodb+srv://HimanshuT:HimanshuT@cluster0.ckppjbd.mongodb.net/?retryWrites=true&w=majority"

            client = MongoClient(uri)

            db = client['Youtube_scrap']
            review_col = db['Youtube_scrap_data']
            review_col.insert_many(details_list)

            try:
                client.admin.command('ping')
                print("Pinged your deployment. You successfully connected to MongoDB!")
            except Exception as e:
                print(e)


            return jsonify(df.to_dict('records'))
        except Exception as e:
            logging.exception("Error occured in index route!")
            return render_template("error.html")

if __name__ == '__main__':
    app.run(host="0.0.0.0")
