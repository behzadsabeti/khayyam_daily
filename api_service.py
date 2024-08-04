import requests
import random
import json

def get_random_poem():

    get_a_random_poem_url = "https://api.ganjoor.net/api/ganjoor/poem/random?poetId=3"
    random_poem = requests.get(get_a_random_poem_url)
    # poem_id = str(random_poem.json()["id"])
    plain_text = random_poem.json()["plainText"]
    id_ = random_poem.json()["id"]
    return {"plain_text": plain_text, "id": id_}   

def get_random_poem_recitation(poem_id):
    get_a_poem_info_by_id_url = "https://api.ganjoor.net/api/ganjoor/poem/"
    poem_info = requests.get(get_a_poem_info_by_id_url + str(poem_id)).json()
    recitations = poem_info["recitations"]
    mp3urls = [item["mp3Url"] for item in recitations]
    random_url = random.choice(mp3urls)
    return random_url

def get_random_poem_eng():
    num = random.randint(0,100)
    with open("eng_poems.json", "r") as file:
        poems = json.load(file)

    return poems[str(num)]   

