from openai import OpenAI
import random

from dotenv import load_dotenv
import os

# Load your API key from an environment variable
load_dotenv()
OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
client = OpenAI(api_key=OPEN_AI_API_KEY)

# Define the Codenames board (25 words for simplicity)
board_words = [
    "Egypt", "Pitch", "Deck", "Well", "Fair",
    "Tooth", "Staff", "Bill", "Shot", "King",
    "Pan", "Square", "Press", "Seal", "Bear",
    "Spike", "Center", "Face", "Palm", "Crane",
    "Rock", "Stick", "Tag", "Disease", "Yard"
]

# Teams' words (for simplicity, not used in clue generation/guessing logic here)
team_red_words = ["Egypt", "Pitch", "Deck", "Well", "Fair", "Tooth", "Staff", "Bill", "Shot"]
team_blue_words = ["King", "Pan", "Square", "Press", "Seal", "Bear", "Spike", "Center", "Face"]
neutral_words = ["Palm", "Crane", "Rock", "Stick", "Tag", "Disease", "Yard"]
assassin_word = ["Battery"] #was originally "Pitch" but that is a red team word so i wanted it to be different

def gen_clue(red_words, blue_words, neutral_words, assassin_word):
    #prompt = f"Act as a spymaster in Codenames game. Provide a one-word clue that relates to these words: {', '.join(words)}."
    prompt = f"""
    You are a codemaster in a codenames game and your job is to 
    give a clue at the end of this prompt the format "Word: Number" (For example "Bird: 3") 
    Your clue may not be any of these words. 
    These are the good words: {red_words} 
    These are the bad words: {blue_words}
    These are the neutral words: {neutral_words}
    This is the instant death word: {assassin_word}.
    Your clue may not have appeard in any of these words.
    The clue must strongly associate with any number of good words, 
    weakly associate with the bad words, may associate with the neutral words,
    and have no association with the instant death word.
    The number you give should be the number of words your clue aims to indicate. 
    The clue must be in the format "Word:Number". For example "Bird: 3"
    Do not return aynthing else."""
    # prompt = f"""Act as a spymaster for the red team in Codenames game. 
    # The red team words are {red_words}. 
    # The blue team words are {blue_words}. 
    # The neutral words are {neutral_words}.
    # The assassin word is {assassin_word}.
    # Generate a clue for the red team Codenames based on these words.
    # Check your knowledge base for the rules of the codenames game.
    # Your clue must abide by these rules. For example one of the rules is
    # that the word must not appear in red team, blue team, neutral, or assassin.
    # The clue must be in the format "Word:Number". For example "Bird: 3"
    # Do not return aynthing else."""


    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {
                "role" : "user", 
                "content" : prompt,
            }, 
        ],
    )

    clue = response.choices[0].message.content
    return clue

def gen_guess(clue, board_words):
    prompt = f"""Act as a guesser in Codenames game. 
    You are given the clue: '{clue}' and the list of words on the 
    board: {', '.join(board_words)}.
    Give your guesses in a python array format: "[Guess1, Guess2, Guess3, etc.]". 
    The number of guesses must match the number provided in the clue.
    Each guess must be a word on the game board: {', '.join(board_words)}.
    The guesses must be ordered from your best guess to your worst guess.
    Do not return anything else besides your array of guesses."""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {
                "role" : "user", 
                "content" : prompt,
            }, 
        ],
    )

    guess = response.choices[0].message.content
    return guess



# Example gameplay loop for one round
if __name__ == "__main__":
    #selected_words = random.choice(board_words)

    #clue = generate_clue(selected_words)
    clue = gen_guess(team_red_words, team_blue_words, neutral_words, assassin_word)
    print(f"Spymaster's Clue: {clue}")
    
    guess = gen_clue(clue, board_words)
    print(f"Guesser's Guess: {guess}")