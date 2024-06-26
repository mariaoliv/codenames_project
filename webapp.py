import streamlit as st   # type: ignore
import random
import numpy as np
import json 
import sqlite3
import string
from test_prompts import gen_clue
from test_prompts import gen_guess
# from semi_prompts import gen_clue
# from semi_prompts import gen_guess
from db_functions import *
import os

db_file_path = "codenames.db"
if os.path.exists(db_file_path):
    # Open the file in binary mode
    with open(db_file_path, "rb") as file:
        btn = st.download_button(
            label="Download Data",
            data=file,
            file_name="codenames.db",
            mime="application/octet-stream"
        )
else:
    st.error("File not found!")


st.title("Codenames")

# RESTART GAME
def clear_ss():
    for key in ss.keys():
        del ss[key]
    if ("game_id" in ss):
        ss.game_id = generate_unique_game_id()
with st.columns([2, 1, 2])[1]:
    st.button("New Game", on_click=clear_ss)

conn = sqlite3.connect('codenames.db', timeout=60)
c = conn.cursor()

create_tables()
add_triggers()

ss = st.session_state
# Dummy api calls for testing
# def gen_clue():
#     return ["Baseball", 3]

# def gen_guess(words):
#     guess = words[random.randrange(0, 24)]
#     while isinstance(words[guess], int):
#         guess = words[random.randrange(0, 24)]
#     return guess

teams = ["Red", "Blue", "Neutral", "Assassin"]



# Generate words and assign them
if 'words' not in ss:
    word_list =  open('wordlist-eng.txt', 'r').readlines()
    word_list = [word.strip() for word in word_list]
    words = random.sample(word_list, 25)
    words_dict = {}
    numperteam = [8, 7, 9, 1]
    ctr = 0
    for i in range(len(numperteam)):
        for j in range(numperteam[i]):
            words_dict[words[ctr]] = i
            ctr += 1
    words_dict[words[-1]] = 3
    random.shuffle(words)
    ss.words = words
    ss.words_dict = words_dict
    ss.curr_dict = {key:val for key, val in ss.words_dict.items()}

    #st.write("WORD DICT: ", words_dict) #delete later

    # swap these two when all buttons need to be disabled
    ss.clicked = {word:False for word in words_dict}
    ss.all_disabled = {word:True for word in words_dict}
    ss.clicked, ss.all_disabled = ss.all_disabled, ss.clicked
    ss.guessed = {"Red":8, "Blue":7, "Neutral":9, "Assassin":1}
    ss.gs_left = 0
    ss.by_team = {"Red":[], "Blue":[], "Neutral":[], "Assassin":[]}
    ss.error_ct = 0
    for key, val in ss.words_dict.items():   
        ss.by_team[teams[val]].append(key)

if "error_ct" not in ss:
    ss.error_ct = 0
# st.write(ss.error_ct)
if "num_turns" not in ss:
    #new addition
    ss.num_turns = 0

def generate_unique_game_id():
    new_game_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    while check_game_id_exists_in_db(new_game_id):
        new_game_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return new_game_id

# Use this function to set ss.game_id when needed, not at the top level of your script
if 'game_id' not in ss:
    ss.game_id = generate_unique_game_id()

if 'prompt_inserted' not in ss:
    ss.prompt_inserted = False


ss = ss
if 'test' not in ss:
    ss.test = [] 
if 'cm_logs' not in ss:
    ss.cm_logs = []
    ss.gs_logs = []

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
        toggle_board()

        
        if ("prompt_id" not in ss):
            ss.prompt_id = ""

        for key, val in ss.words_dict.items():
            tm = teams[val]
            if (key not in ss.by_team[tm]): #word has been guessed
                insert_word(key, ss.game_id, tm, 1)
            else: #word was not guessed, the value for the guessed column is 0 by default
                insert_word(key, ss.game_id, tm)
        if team == "Red":
            st.text("YOU WIN :)")
            insert_game(game_id=ss.game_id, num_turns=ss.num_turns, win=1)
            if ("guesser_prompt" in ss): #gpt as guesser
                ss.prompt_id = get_prompt_id(ss.guesser_prompt, guesser=True)
            else:
                ss.prompt_id = get_prompt_id(ss.cm_prompt, guesser=False)
            update_prompt_after_win_loss(ss.prompt_id, ss.game_id, True)
        else:
            st.text("YOU LOSE :'(")
            insert_game(game_id=ss.game_id, num_turns=ss.num_turns, win=0)
            if (ss.role == 0): #gpt as guesser
                ss.prompt_id = get_prompt_id(ss.guesser_prompt, guesser=True)
            else:
                ss.prompt_id = get_prompt_id(ss.cm_prompt, guesser=False)
            update_prompt_after_win_loss(ss.prompt_id, ss.game_id, False)

        #ss.game_id = generate_unique_game_id()
        ss.curr_dict = {}

        return True
    elif team != "Red":
        ss.gs_left = 0
        return True

def do_nothing(name):
    pass


if "game_started" not in ss:
    ss.game_started = False
    ss.disable_user_input = True
def toggle_board():
    ss.clicked, ss.all_disabled = ss.all_disabled, ss.clicked
def codemaster():
    ss.role = 0
    ss.disable_user_input = False
    toggle_board()
    ss.game_started = True
def guesser():
    ss.role = 1
    toggle_board()
    ss.game_started = True
cols_play = st.columns([.5, 1, 1, .5], gap="large")
with cols_play[1]: cm_btn = st.button(label = "Play as CodeMaster", on_click=codemaster, disabled=ss.game_started)
with cols_play[2]: g_btn = st.button(label = "Play as Guesser", on_click=guesser, disabled=ss.game_started)


def do_nothing(name):
    pass
bt_guess = do_nothing

if ss.game_started:
    if ss.gs_left == 0:
        # Guesser
        if ss.role and ss.curr_dict:
            # FOR DEVELOPMENT ONLY
            while True:
                try:
                    ss.clue, ss.cm_prompt = gen_clue(ss.by_team['Red'], ss.by_team['Blue'],
                        ss.by_team['Neutral'], ss.by_team['Assassin'], ss.cm_logs)
                    #insert cm prompt
                    ss.clue = ss.clue.split(">")
                    ss.words_to_guess = ss.clue[1]
                    ss.clue = json.loads(ss.clue[0])
                    ss.clue_word, ss.gs_left = ss.clue

                    # st.text(ss.clue)
                    if ss.clue_word.upper() not in ss.words:
                        print("clue: " + json.dumps(ss.clue))
                        print("indicates: " + json.dumps(ss.words_to_guess))
                        break
                    ss.error_ct += 1
                except Exception as e:
                    print(e)
                    pass
            if (ss.prompt_inserted == False):
                insert_prompt(ss.game_id, ss.cm_prompt, False)
                ss.prompt_inserted = True
            print(ss.clue_word, ss.gs_left)
            ss.cm_logs.append(ss.clue)

            insert_turn(ss.game_id, json.dumps(ss.by_team['Red']), json.dumps(ss.by_team['Blue']), json.dumps(ss.by_team['Neutral']), json.dumps(ss.by_team['Assassin']), ss.clue_word, ss.gs_left)
            ss.num_turns += 1
            
            ss.gs_logs.append([])
            bt_guess = guess
        # Codemaster
        # TODO: Get user input for guess
        else:
            if "clue" in ss:
                del ss['clue']
            bt_guess = do_nothing
            ss.disable_user_input = False
    else:
        bt_guess = guess
        if not ss.role:
            bt_guess = do_nothing
            ss.disable_user_input = True



def parse_clue():
    ss.clue = ss.user_input.split(": ")
    ss.clue[1] = int(ss.clue[1])
    ss.clue_word, ss.gs_left = ss.clue
    ss.cm_logs.append(ss.clue)

    insert_turn(ss.game_id, json.dumps(ss.by_team['Red']), json.dumps(ss.by_team['Blue']), json.dumps(ss.by_team['Neutral']), json.dumps(ss.by_team['Assassin']), ss.clue_word, ss.gs_left)
    ss.num_turns += 1

    ss.gs_logs.append([])
    ss.user_input = ""

def call_guesser():
    # FOR DEVELOPMENT ONLY
    try:
        parse_clue()
        print(ss.curr_dict.keys())
        while True: 
            try:
                ss.gs_array, ss.guesser_prompt = gen_guess(clue=ss.clue, board_words = json.dumps([key for key in ss.curr_dict.keys()]))
                ss.gs_array = json.loads(ss.gs_array)
                for gs in ss.gs_array:
                    ss.curr_dict[gs] += 0
                break
            except Exception as e: 
                ss.user_input = ""
                ss.gs_array = []
                print(e)
        if (ss.prompt_inserted == False):
            insert_prompt(ss.game_id, ss.guesser_prompt, True)
            ss.prompt_inserted = True
        for gs in ss.gs_array:
            if guess(gs):
                break
    except Exception as e:
        st.write("Clue Given in Incorrect Format")
        print(e)

    
st.text("You are on the RED TEAM")
st.text("How to play codenames: https://www.youtube.com/watch?v=WErB95Brgbs")
txt_input = st.text_input(label= "Enter Clue",
    key = "user_input",
    label_visibility="collapsed",
    placeholder= "Word: Guesses",
    disabled=ss.disable_user_input,
    autocomplete="off",
    on_change=call_guesser)

if "clue" in ss and ss.curr_dict:
    st.text(ss.clue_word + ": " + str(ss.clue[1])) 
    st.text("Guesses remaining: " + str(ss.gs_left))
elif "role" in ss and not ss.role:
    st.text("Please enter a clue formatted as WORD: NUMBER_OF_GUESSES")

colors = {"Red":"red", "Blue":"blue", "Neutral":"green", "Assassin":"rainbow"}
# GAME BOARD
cols = st.columns(5)
for i in range(len(ss.words)):
    with(cols[i // 5]):
        name = ss.words[i]
        label = name
        if 'role' in ss:
            if not ss.role and not ss.clicked[name] or ss.role and ss.clicked[name]:
                color = colors[teams[ss.words_dict[name]]]
                label = ":{color}[{name}]".format(color = color, name = name)
        st.button(label=label, key=name, 
                  on_click=bt_guess, args=[name],
                  disabled=ss.clicked[name],
                  use_container_width=True
                  )

st.write(ss.guessed)
# REVEAL TEAMS   
if 'role' in ss and not ss.role:
    for key, val in ss.by_team.items():
        st.markdown(("{key}({color}): {val}").format(color=colors[key], val=val, key = key))

for i in range(len(ss.cm_logs)):
    st.text("Clue: ")
    st.text(ss.cm_logs[i])
    st.text("Guesses: ")
    st.text(ss.gs_logs[i])



if not ss.game_started and len(ss.cm_logs):
    ss.write("Total turns: ", len(ss.cm_logs))
    for team in ss.by_team.keys():
        ss.write(team + " words guessed: " + str(len(ss.by_team[team])))
