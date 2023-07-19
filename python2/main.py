import nltk
from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()

# things we need for Tensorflow
import numpy as np
import tflearn
import tensorflow as tf
import random

from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin

# restore all of our data structures
import pickle
data = pickle.load( open( "chatbot_redsamurai_medical_training_data", "rb" ) )
words = data['words']
classes = data['classes']
train_x = data['train_x']
train_y = data['train_y']

# import our chat-bot intents file
import json
with open('intents.json') as json_data:
    intents = json.load(json_data)

# Build neural network
net = tflearn.input_data(shape=[None, len(train_x[0])])
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, len(train_y[0]), activation='softmax')
net = tflearn.regression(net)

# Define model and setup tensorboard
model = tflearn.DNN(net, tensorboard_dir='tflearn_chatbot_redsamurai_medical_logs')

def clean_up_sentence(sentence):
    # tokenize the pattern
    sentence_words = nltk.word_tokenize(sentence)
    # stem each word
    sentence_words = [stemmer.stem(word.lower()) for word in sentence_words]
    return sentence_words

# return bag of words array: 0 or 1 for each word in the bag that exists in the sentence
def bow(sentence, words, show_details=True):
    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)
    # bag of words
    bag = [0]*len(words)  
    for s in sentence_words:
        for i,w in enumerate(words):
            if w == s: 
                bag[i] = 1
                if show_details:
                    print ("found in bag: %s" % w)

    return(np.array(bag))
p = bow("Load bood pessure for patient", words)
print (p)
print (classes)
# load our saved model
model.load('./chatbot_redsamurai_medical_model.tflearn')
app = Flask(__name__)
CORS(app)

@app.route("/redsam/api/v1.0/classify", methods=['POST'])
def classify():
    ERROR_THRESHOLD = 0.25
    
    sentence = request.json['sentence']
    
    # generate probabilities from the model
    results = model.predict([bow(sentence, words)])[0]
    # filter out predictions below a threshold
    results = [[i,r] for i,r in enumerate(results) if r>ERROR_THRESHOLD]
    # sort by strength of probability
    results.sort(key=lambda x: x[1], reverse=True)
    
    # retrieve the most probable intent
    if results:
        intent = classes[results[0][0]]
        probability = str(results[0][1])
        response = get_response(intent)
    else:
        response = "Sorry, I'm not sure how to respond to that."
    
    return jsonify({"intent": intent, "probability": probability, "response": response})

# def get_response(intent):
#     for i in intents:
#         if i['tag'] == intent:
#             return random.choice(i['responses'])
#     return "Sorry, I'm not sure how to respond to that."

def get_response(intent):
    
    list_of_intents = intents['intents']
    result = ""
    for i in list_of_intents:
        if i['tag'] == intent:
            result = random.choice(i['responses'])
            break
    return result


# running REST interface
if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5003)
