# things we need for NLP
import nltk
import numpy as np
import tflearn
import tensorflow as tf
import random
import pickle
from nltk.stem.lancaster import LancasterStemmer

stemmer = LancasterStemmer()

# import our chat-bot intents file
import json
with open('intents.json') as json_data:
    intents = json.load(json_data)

words = []
classes = []
documents = []
ignore_words = ['?']

# loop through each sentence in our intents patterns
for intent in intents['intents']:
    for pattern in intent['patterns']:
        # tokenize each word in the sentence
        w = nltk.word_tokenize(pattern)
        # add to our words list
        words.extend(w)
        # add to documents in our corpus
        documents.append((w, intent['tag']))
        # add to our classes list
        if intent['tag'] not in classes:
            classes.append(intent['tag'])

# stem and lower each word and remove duplicates
words = [stemmer.stem(w.lower()) for w in words if w not in ignore_words]
words = sorted(list(set(words)))

# sort classes
classes = sorted(list(set(classes)))

# documents = combination between patterns and intents
print(len(documents), "documents")
# classes = intents
print(len(classes), "classes", classes)
# words = all words, vocabulary
print(len(words), "unique stemmed words", words)

# create our training data
training = []
# create an empty array for our output
output_empty = [0] * len(classes)

# training set, bag of words for each sentence
for doc in documents:
    # initialize our bag of words
    bag = []
    # list of tokenized words for the pattern
    pattern_words = doc[0]
    # stem each word - create base word, in attempt to represent related words
    pattern_words = [stemmer.stem(word.lower()) for word in pattern_words]
    # create our bag of words array with 1, if word match found in current pattern
    for w in words:
        bag.append(1) if w in pattern_words else bag.append(0)

    # output is a '0' for each tag and '1' for current tag (for each pattern)
    output_row = list(output_empty)
    output_row[classes.index(doc[1])] = 1

    training.append([bag, output_row])

# shuffle our features and turn into np.array
random.shuffle(training)
training = np.array(training)

# create train and test lists. X - patterns, Y - intents
train_x = list(training[:, 0])
train_y = list(training[:, 1])

# Build neural network - input data shape, number of words in vocabulary (size of first array element).
net = tflearn.input_data(shape=[None, len(train_x[0])])
# Two fully connected layers with 8 hidden units/neurons - optimal for this task
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, 8)
# number of intents, columns in the matrix train_y
net = tflearn.fully_connected(net, len(train_y[0]), activation='softmax')
# regression to find best parameters, during training
net = tflearn.regression(net)

# Define Deep Neural Network model and setup tensorboard
model = tflearn.DNN(net, tensorboard_dir='tflearn_chatbot_redsamurai_medical_logs')
# Start training (apply gradient descent algorithm)
# n_epoch - number of epoch to run
# Batch size defines number of samples that going to be propagated through the network.
model.fit(train_x, train_y, n_epoch=1000, batch_size=5, show_metric=True)
model.save('chatbot_redsamurai_medical_model.tflearn')


def clean_up_sentence(sentence):
    # tokenize the pattern - split words into an array
    sentence_words = nltk.word_tokenize(sentence)
    # stem each word - create short form for the word
    sentence_words = [stemmer.stem(word.lower()) for word in sentence_words]
    return sentence_words


# return bag of words array: 0 or 1 for each word in the bag that exists in the sentence
def bow(sentence, words, show_details=True):
    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)
    # bag of words - matrix of N words, vocabulary matrix
    bag = [0] * len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:
                # assign 1 if the current word is in the vocabulary position
                bag[i] = 1
                if show_details:
                    print("found in bag: %s" % w)

    return np.array(bag)


p = bow("Load blood pressure for the patient", words)
print(p)
print(classes)
print(model.predict([p]))

# save all of our data structures
pickle.dump({'words': words, 'classes': classes, 'train_x': train_x, 'train_y': train_y},
            open("chatbot_redsamurai_medical_training_data", "wb"))
