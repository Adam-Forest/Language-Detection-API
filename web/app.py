from flask import Flask
from flask import request
from flask import render_template
from flask import send_from_directory
from keras.models import Sequential
from keras.layers import Activation, Dense, Dropout
from unidecode import unidecode

import numpy as np
import pandas as pd
import os

from tensorflow.keras.models import load_model

# these variables need to match original training stats
max_letters=12
char_count=104
char_count2=26

# the languages used in training
label_names=['english', 'french', 'german', 'romanian']

# network to predict, must match one used for training
network = Sequential()
network.add(Dense(200, input_dim=(char_count*max_letters)-1, activation='sigmoid'))
network.add(Dense(150, activation='sigmoid'))
network.add(Dense(100, activation='sigmoid'))
network.add(Dense(100, activation='sigmoid'))
network.add(Dense(len(label_names), activation='softmax'))

network.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

# load trained weights
network = load_model("./lang_detect.hdf5")

# network to predict, must match one used for training
network2 = Sequential()
network2.add(Dense(512, input_dim=(char_count2*max_letters)-1))
network2.add(Activation('relu'))
network2.add(Dropout(0.5))
network2.add(Dense(512, activation='sigmoid'))
network2.add(Dropout(0.4))
network2.add(Dense(512, activation='sigmoid'))
network2.add(Dropout(0.3))
network2.add(Dense(len(label_names), activation='softmax'))

network2.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

# load trained weights
network2 = load_model("./lang_detect_n2.hdf5")

# network to predict, must match one used for training
network3 = Sequential()
network3.add(Dense(512, input_dim=(char_count*max_letters)-1))
network3.add(Activation('relu'))
network3.add(Dropout(0.5))
network3.add(Dense(512, activation='sigmoid'))
network3.add(Dropout(0.4))
network3.add(Dense(512, activation='sigmoid'))
network3.add(Dropout(0.3))
network3.add(Dense(len(label_names), activation='softmax'))

network3.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

# load trained weights
network3 = load_model("./lang_detect_n_sorted.hdf5")

# use to convert input to vector in style used for training (one_hot_encoding)
def convert_dic_to_vector(dic, max_word_length,chars_count):
    new_list = []
    for word in dic:
        vec = ''
        n = len(word)
        for i in range(n):
            current_letter = word[i]
            ind = ord(current_letter)-97
            #ind = ord(current_letter)
            placeholder = (str(0)*ind) + str(1) + str(0)*((chars_count-1)-ind)
            vec = vec + placeholder
        if n < max_word_length:
            excess = max_word_length-n
            vec = vec +str(0)*chars_count*excess
        new_list.append(vec)
   # print(len(new_list))
    return new_list

# function takes word to guess, encodes it, returns 3 guesses and avg of 3 guesses
def predict_word(word):
    dic = []
    guess = []
    guess2 = []
    guess3 = []
    guess_avg = []
    guess_primary = []

    # spacces were not used in taining and are not encoded in matrix
    word_trunc=word[:11].replace(" ", "")
    word_trunc=unidecode(word_trunc)

    dic.append(word_trunc)
    
    # all sets of 3 variables for guesses could be merged into arrays in future but was easier to degub as is

    # make sure char_count matches one used for training
    vct_str = convert_dic_to_vector(dic, max_letters-1, char_count)
    vct_str2 = convert_dic_to_vector(dic, max_letters-1, char_count2)
    vct_str3 = convert_dic_to_vector(dic, max_letters-1, char_count2)

    vct = np.zeros((1, (char_count * max_letters)-1))
    vct2 = np.zeros((1, (char_count2 * max_letters)-1))
    vct3 = np.zeros((1, (char_count2 * max_letters)-1))
    #print(vct)
    #print(vct2)
    #print(vct3)
    count = 0
    count2 = 0
    count3 = 0
    #print(len(vct_str[0]))
    for digit in vct_str[0]:
        vct[0,count] = int(digit)
        count += 1
    for digit2 in vct_str2[0]:
        vct2[0,count2] = int(digit2)
        count2 += 1
    for digit3 in vct_str3[0]:
        vct3[0,count3] = int(digit3)
        count3 += 1

    # get prediction percents    
    prediction_vct = network.predict(vct)
    prediction2_vct = network2.predict(vct2)
    prediction3_vct = network3.predict(vct3)
    #print(prediction_vct)
    #print(prediction2_vct)
    #print(prediction3_vct)

    # get best prediction for winner highlight
    prediction_winner = network.predict_classes(vct)
    prediction_winner2 = network2.predict_classes(vct2)
    prediction_winner3 = network3.predict_classes(vct3)

    langs = list(label_names)

    avg_conf_top=0
    avg_conf=0

    for i in range(len(label_names)):
        lang = langs[i]
        winner=0
        winner2=0
        winner3=0

        score = prediction_vct[0][i]
        score2 = prediction2_vct[0][i]
        score3 = prediction3_vct[0][i]
        if i == prediction_winner[0]:
            winner=1
        if i == prediction_winner2[0]:
            winner2=1
        if i == prediction_winner3[0]:
            winner3=1
        
        #guess["language"+str(i)]=lang
        #guess["confidence"+str(i)]=str(round(100*score, 2)) + '%'

        guess.append({
            "winner" : winner,
            "word": word, 
            "language": lang, 
            "confidence":round(100*score, 1),
            })

        guess2.append({
            "winner" : winner2,
            "word": word, 
            "language": lang, 
            "confidence":round(100*score2, 1),
            })

        guess3.append({
            "winner" : winner3,
            "word": word, 
            "language": lang, 
            "confidence":round(100*score3, 1),
            })

        guess_avg.append({
            "winner" : 0,
            "word": word, 
            "language": lang, 
            "confidence":round(((100*score)+(100*score2)+(100*score3))/3, 1),
            })

        # to picjk average winner
        avg_conf=round(((100*score)+(100*score2)+(100*score3))/3, 1)
        if avg_conf > avg_conf_top:
            avg_conf_top=avg_conf
            # print(f"{avg_conf} > {avg_conf_top}")

    # to set average winner
    for guesses in guess_avg:
        if guesses["confidence"]>=avg_conf_top:
            # print(guesses["confidence"])
            # print(">=")
            # print(avg_conf_top)
            guesses["winner"]=1

    #print(prediction_winner)    
    #print(prediction_winner2)
    #print(lang + ': ' + str(round(100*score, 2)) + '%')

    #print(prediction_winner[0])
    return guess, guess2, guess3, guess_avg

# Flask Setup
app = Flask(__name__, static_url_path='')

################# Flask Routes ###################
@app.route('/', methods=['GET', 'POST'])
def root():
    if request.method == 'POST':
        word = request.form.get("word","")
        robots=predict_word(word)
        return render_template('index.html', robots=robots, word=word)
    
    return render_template('index.html', robots="")

@app.route('/about')
def about():
	return app.send_static_file('about.html')

@app.route('/charts')
def charts():
	return app.send_static_file('charts.html')

if __name__ == "__main__":
    #debug=True
    app.run()