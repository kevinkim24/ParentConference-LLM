#!/usr/bin/env python

#-------------------------------------------------------------------
# run.py
# Author: Kevin Kim
#-------------------------------------------------------------------

import flask
import urllib
from flask_cors import CORS
import sys
import io
import base64
#import database
#import auth

import subprocess, tempfile, os
import ast # for block security
# ------------------- LLM -----------------
from openai import OpenAI
local_model = "google/gemma-4-e4b" # local model setting
# -------------------------------------------------------------------
app = flask.Flask(__name__, template_folder='static/templates', static_folder='static')
CORS(app)
app.secret_key = os.environ['APP_SECRET_KEY']

# -------------------------------------------------------------------

# Index/homepage goes straight to chat
@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    html_code = flask.render_template('chat/chat.html')
    response = flask.make_response(html_code)
    return response

# -------------------------------------------------------------------
class chatSession:
    def __init__(self,client,model,system_message):
        self.client = client
        self.model = model
        self.messages = [
            {"role": "system","content":system_message}
        ]

    def message(self, prompt: str, temperature = 0.1):
        self.messages.append({"role": "user","content": prompt})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=temperature
            )
        reply = response.choices[0].message.content
        self.messages.append({"role": "assistant","content":reply})

        return reply

# Make Client using LM Studio
client = OpenAI(
    base_url="http://localhost:1234/v1",  # LM Studio
    api_key=""  
)

# Get LLM response
def query_llm(session, prompt: str) -> str:
    return session.message(prompt)

# Chat Personality Settings ---------------------------------------
# Right now, refreshing doesn't change session. 
personality_dict = {'greenButton': "You are Mr. James, the father of an 8th grader named Jeff. You answer with short responses. Your last name is James. You don't use your first name, which is unknown. Jeff is very timid and wimpy. He has been struggling in class lately and been getting bullied at school. He is easy to pick on. He doesn't have many friends. You have high expectations for Jeff and for his teacher to make him feel better. You are a scary, intimidating presence. You'are an ex-marine. You want to make sure the teacher puts in the work and time necessary so Jeff can get back on track. You want to know that the teacher truly cares for Jeff and will do whatever it takes for him to belong. Once you feel that the teacher has shown that they care, you will finish the meeting.",
                        'blueButton':"You are Mrs. Johnson, the mom of a ninth grader named Mariah who is struggling to learn in class. You are in a parent-teacher conference with her teacher. You will speak with the teacher and stop the meeting once your conversation is sufficient. Don't answer with too long of a response. Use medium-length. You are a very rough, unkind parent who is extremely pessimistic about your student's teacher. You are quite emotional, and have a lot you want to offload. You want to make sure Mariah feels safe at school. She had a racist encounter with a classmate named Brian. Mariah has an IEP. Once you think the teacher understands Mariah's IEP and truly cares about her wellbeing, you will stop the meeting and thank the teacher. Remember, there must be an end to the conversation."}
personality_button_id = "blueButton"
session = chatSession(client,model="google/gemma-3-4b",system_message=personality_dict[personality_button_id])
# ----------------------------------------------

# For loading the html
@app.route('/chat', methods=['GET'])
def chat():
    html_code = flask.render_template('chat/chat.html')
    response = flask.make_response(html_code)
    return response

# For query handling
@app.route('/chat/query',methods=['POST'])
def query():
    global session
    global personality_button_id
    global personality_dict

    prompt_json = flask.request.get_json()
    prompt = prompt_json.get("prompt", "").strip()
    new_personality_button_id = prompt_json.get("personality")
    
    # make new session with new personality if new button selected. 
    if new_personality_button_id != personality_button_id:
        personality_button_id = new_personality_button_id
        session = chatSession(client,model=local_model,system_message=personality_dict[personality_button_id])
    
    try:
        response = query_llm(session,prompt)
        print(flask.jsonify({"response": response}))
        return flask.jsonify({"response": response})
    except Exception as e:
        return flask.jsonify({"error": str(e)}), 500

# -------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5002)
