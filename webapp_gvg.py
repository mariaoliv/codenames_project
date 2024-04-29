import streamlit as st 
import random
import numpy as np
import json 
import sqlite3
import string
from test_prompts import gen_clue
from test_prompts import gen_guess
from db_functions import *

st.title("Codenames")

# RESTART GAME
def clear_ss():
    for key in ss.keys():
        del ss[key]
with st.columns([2, 1, 2])[1]:
    st.button("New Game", on_click=clear_ss)


conn = sqlite3.connect('codenames.db', timeout=60)
c = conn.cursor()

create_tables()

ss = st.session_state

teams = ["Red", "Blue", "Neutral", "Assassin"]



# Generate words and assign them
def new_game():
    word_list =  open('wordlist-eng.txt', 'r').readlines()
    word_list = [word.strip() for word in word_list]
    words = random.sample(word_list, 25)
    words_dict = {}
    # COPY THIS OVER
    # ______________
    numperteam = [8, 7, 9, 1]
    ctr = 0
    for i in range(len(numperteam)):
        for j in range(numperteam[i]):
            words_dict[words[ctr]] = i
            ctr += 1
    # ______________
    random.shuffle(words)
    ss.words = words
    ss.words_dict = words_dict
    ss.curr_dict = {key:val for key, val in ss.words_dict.items()}
    ss.clicked = {word:False for word in words_dict}
    ss.guessed = {"Red":8, "Blue":7, "Neutral":9, "Assassin":1}
    ss.gs_left = 0
    ss.by_team = {"Red":[], "Blue":[], "Neutral":[], "Assassin":[]}
    ss.error_ct = 0
    for key, val in ss.words_dict.items():   
        ss.by_team[teams[val]].append(key)
    ss.cm_logs = []
    ss.gs_logs = []
    ss.num_turns = 0

if 'words' not in ss:
    new_game()

if "counters" not in ss:
    ss.counters = {"Win": 0, "Loss": 0, "Correct": 0, "Incorrect": 0, "Error": 0}
if "error_ct" not in ss:
    ss.error_ct = 0
# st.write(ss.error_ct)
    


# GAME BOARD BUTTON CALLBACK
def guess(name):
    name = name.upper()
    team = teams[ss.words_dict[name]]
    ss.gs_logs[-1].append(name)
    ss.gs_left -= 1
    ss.guessed[team] -= 1
    del ss.curr_dict[name]
    ss.by_team[team].remove(name)
    ss.clicked[name] = not ss.clicked[name]

    if not ss.guessed[team] and team != "Neutral":
        if team == "Red":
            ss.counters['Correct'] += 1
            ss.counters['Win'] += 1
        else:
            ss.counters['Incorrect'] += 1
            ss.counters['Loss'] += 1
        ss.curr_dict = {}
        ss.game_started = False
        return True
    elif team != "Red":
        ss.counters['Incorrect'] += 1
        ss.gs_left = 0
        return True
    ss.counters['Correct'] += 1
def do_nothing(name):
    pass

if "game_started" not in ss:
    ss.game_started = True

def do_nothing(name):
    pass
bt_guess = do_nothing

# GAME BOARD
cols = st.columns(5)
for i in range(len(ss.words)):
    with(cols[i // 5]):
        name = ss.words[i]
        st.button(label=name, key=name, 
                  on_click=do_nothing, args=[name],
                  disabled=ss.clicked[name])

ss.num_tests = st.slider(label="Number of Tests", min_value=1, max_value=30)
def gvg():
    for i in range(ss.num_tests):
        ss.game_started = True
        while ss.game_started:
            while True:
                try:
                    ss.clue, ss.cm_prompt = gen_clue(ss.by_team['Red'], ss.by_team['Blue'],
                                    ss.by_team['Neutral'], ss.by_team['Assassin'])
                    print(ss.clue)
                    ss.clue = ss.clue.split(": ")
                    ss.clue = ss.clue[1].split(", ")
                    ss.clue[1] = int(ss.clue[1])
                    ss.clue_word, ss.gs_left = ss.clue

                    # st.text(ss.clue)
                    if ss.clue_word.upper() not in ss.words:
                        print("CLUE: " + json.dumps(ss.clue))
                        break
                    ss.error_ct += 1
                except Exception as e:
                    ss.counters['Errors'] += 1
                    print(e)
                    pass
            print(ss.clue_word, ss.gs_left)
            ss.cm_logs.append(ss.clue)
            ss.num_turns += 1
            
            ss.gs_logs.append([])
            while True: 
                try:
                    ss.gs_array, ss.guesser_prompt = gen_guess(clue=ss.clue, board_words = json.dumps([key for key in ss.curr_dict.keys()]))
                    ss.gs_array = json.loads(ss.gs_array)
                    for gs in ss.gs_array:
                        print("guess: " + gs)
                        ss.curr_dict[gs] += 0
                    break
                except Exception as e: 
                    ss.counters['Errors'] += 1
                    ss.gs_array = []
                    print(e)
            for gs in ss.gs_array:
                if guess(gs):
                    break
        new_game()
    st.markdown(ss.counters)
        
with st.columns([2, 1, 2])[1]:
    st.button("Start testing", on_click=gvg, disabled=not ss.game_started)

st.write(ss.guessed)
# REVEAL TEAMS   
rev_teams = st.checkbox(label="Teams", value=True)
if rev_teams: 
    for key, val in ss.by_team.items():
        st.text(key + ": " + json.dumps(val))

for i in range(len(ss.cm_logs)):
    st.text("Clue: ")
    st.text(ss.cm_logs[i])
    st.text("Guesses: ")
    st.text(ss.gs_logs[i])

if not ss.game_started and len(ss.cm_logs):
    st.write("Total turns: ", len(ss.cm_logs))
    for team in ss.by_team.keys():
        st.write(team + " words guessed: " + str(len(ss.by_team[team])))