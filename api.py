from openai import OpenAI
import random

# Load your API key from an environment variable
# from dotenv import load_dotenv
# import os
# load_dotenv()

OPENAI_API_KEY = "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"
client = OpenAI(
    api_key = OPENAI_API_KEY 
)

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
assassin_word = ["Pitch"]

def generate_clue(words):
    prompt = f"Act as a spymaster in Codenames game. Provide a one-word clue that relates to these words: {', '.join(words)}."

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

def guess_word(clue, board_words):
    prompt = f"Act as a guesser in Codenames game. Given the clue '{clue}', which of these words: {', '.join(board_words)} is most related?"

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
    selected_words = random.choice(board_words)

    clue = generate_clue(selected_words)
    print(f"Spymaster's Clue: {clue}")
    
    guess = guess_word(clue, board_words)
    print(f"Guesser's Guess: {guess}")