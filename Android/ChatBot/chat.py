import socket
import json
import pickle
import numpy as np
import torch
import pygame
from gtts import gTTS
import speech_recognition as sr
import os
import random
from tensorflow.keras.models import load_model
from transformers import BertTokenizer, BertForSequenceClassification

ENABLE_TTS = False
pygame_initialized = False

# Get the absolute path of the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Load BERT model and tokenizer
try:
    bert_model_dir = os.path.join(script_dir, "intent_classifier")
    tokenizer = BertTokenizer.from_pretrained(bert_model_dir)
    bert_model = BertForSequenceClassification.from_pretrained(bert_model_dir)
    print(f"BERT Model loaded successfully from: {bert_model_dir}")
except Exception as e:
    print(f"Error loading BERT model: {e}")
    exit(1)

# Load LSTM model, vectorizer, and label encoder
try:
    lstm_model_path = os.path.join(script_dir, "chatbot_model_LSTM.keras")
    vectorizer_path = os.path.join(script_dir, "vectorizer_LSTM.pkl")
    label_encoder_path = os.path.join(script_dir, "label_encoder_LSTM.pkl")
    
    lstm_model = load_model(lstm_model_path)
    with open(vectorizer_path, 'rb') as f:
        vectorizer = pickle.load(f)
    with open(label_encoder_path, 'rb') as f:
        label_encoder = pickle.load(f)
    
    print(f"LSTM Model and associated files loaded successfully from {script_dir}")
except Exception as e:
    print(f"Error loading LSTM model or associated files: {e}")
    exit(1)

# Load intents data
try:
    intents_path = os.path.join(script_dir, 'intents.json')
    with open(intents_path, 'r') as file:
        data = json.load(file)
        intents = data.get('intents', [])
except Exception as e:
    print(f"Error loading intents.json: {e}")
    intents = []

# Map tags to responses
tag_to_responses = {intent['tag']: intent['responses'] for intent in intents}

# Speech recognizer
recognizer = sr.Recognizer()

# Track previous intent and responses
previous_intent = None
used_responses = {}
listening = False

def preprocess_input(message):
    input_vector = vectorizer.transform([message]).toarray()
    input_vector = input_vector.reshape(1, 1, input_vector.shape[1])
    return input_vector

def predict_intent_bert(user_input):
    inputs = tokenizer(user_input, return_tensors='pt', padding=True, truncation=True, max_length=128)
    with torch.no_grad():
        outputs = bert_model(**inputs)
    logits = outputs.logits
    predicted_class = torch.argmax(logits, dim=-1).item()
    return list(tag_to_responses.keys())[predicted_class] if predicted_class < len(tag_to_responses) else None

def predict_intent_lstm(user_input):
    processed_input = preprocess_input(user_input)
    predictions = lstm_model.predict(processed_input)
    predicted_class = np.argmax(predictions, axis=1)[0]
    return label_encoder.inverse_transform([predicted_class])[0]

def get_response(intent_tag):
    responses = tag_to_responses.get(intent_tag, ["I'm sorry, I don't understand."])
    if intent_tag not in used_responses:
        used_responses[intent_tag] = set()
    unused_responses = [r for r in responses if r not in used_responses[intent_tag]]
    if unused_responses:
        response = random.choice(unused_responses)
    else:
        used_responses[intent_tag].clear()
        response = random.choice(responses)
    used_responses[intent_tag].add(response)
    return response




def toggle_tts():
    global ENABLE_TTS
    ENABLE_TTS = not ENABLE_TTS
    print(f"TTS is now {'ON' if ENABLE_TTS else 'OFF'}")
    return ENABLE_TTS


# def speak(text):
#     if not ENABLE_TTS:
#         return
#     tts = gTTS(text=text, lang='en', slow=False)
#     tts.save("response.mp3")
#     pygame.mixer.init()
#     pygame.mixer.music.load("response.mp3")
#     pygame.mixer.music.play()
#     while pygame.mixer.music.get_busy():
#         pygame.time.Clock().tick(10)

def speak(text):
    global pygame_initialized

    if not ENABLE_TTS:
        return

    print(f"Chatbot (TTS): {text}")
    try:
        # Initialize Pygame mixer only once
        if not pygame_initialized:
            pygame.mixer.init()
            pygame_initialized = True

        # Use a temporary filename
        filename = "response.mp3"

        # Generate speech
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(filename)

        # Load and play the MP3
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

        # Wait until playing is finished
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        # Optionally stop the music after done
        pygame.mixer.music.stop()

    except Exception as e:
        print(f"Error in speak(): {e}")




# Listening function to capture voice input
def listen():
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        audio = recognizer.listen(source)
        text = recognizer.recognize_google(audio)
        return f"AUDIO_TEXT: {text}"  # Add the prefix "AUDIO_TEXT" to the recognized text

# Server setup
HOST = '127.0.0.1'
PORT = 5800
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(5)

print(f"Chatbot server running on {HOST}:{PORT}...")
model_type = "lstm"

while True:
     
    client_socket, addr = server_socket.accept()
    print(f"Connected to {addr}")
    
    print(f"Model type set to: {model_type}")
    
    while True:
        try:
            client_message = client_socket.recv(1024).decode().strip()
            
            if client_message.lower() == "toggle tts":
                state = toggle_tts()
                speak(response)  
                continue

            if client_message:
                print(f"Received client message: {client_message}")
                print(f"received")

                if client_message.lower() in ["llm", "lstm"]:
                    model_type = client_message.lower()
                    print(f"Model type updated to: {model_type}")
                    continue

                # Handle requests for alternative solutions
                if any(phrase in client_message.lower() for phrase in 
                       ['another solution', 'another one', 'can you provide another', 'another', 'any other solution', 'i need to fix it']):
                    print("OK - Detected 'another solution' request")
                    if previous_intent:
                        response = get_response(previous_intent)  # Fixed function call
                        print(f"Sending alternative response: {response}")
                        client_socket.send((response + "\n").encode())
                        speak(response)  # Speak the response
                        continue
                    else:
                        response = "I'm sorry, I don't have a previous solution to offer."
                        print(f"Sending response: {response}")
                        client_socket.send((response + "\n").encode())
                        speak(response)  # Speak the response
                        continue

                # Start listening
                if client_message.lower() == "start recording":
                    listening = True
                    response = "I'm now listening. Please speak."
                    print(f"Sending response: {response}")
                    client_socket.send((response + "\n").encode())
                    ENABLE_TTS = True
                    speak(response)
                    ENABLE_TTS = False
                    
                    if listening:
                        try:
                            data = listen()  # Get voice input
                            if data:
                                print(f"Recognized: {data}")
                                client_socket.send((data + "\n").encode())
                                print(f"SENT")

                                if any(phrase in data.lower() for phrase in ['exit', 'quit', 'bye']):
                                    print("Exit command detected in voice input.")
                                    response = "Goodbye! Have a great day!"
                                    print(f"Sending response: {response}")
                                    client_socket.send((response + "\n").encode())
                                    speak(response)
                                    break

                        except sr.UnknownValueError:
                            print("Could not understand audio.")
                            response = "I couldn't understand that."
                            client_socket.send((response + "\n").encode())
                        except sr.RequestError as e:
                            print(f"Could not request results from Google Speech Recognition service; {e}")
                            response = "Service error. Please try again."
                            client_socket.send((response + "\n").encode())
                        except Exception as e:
                            print(f"Error during voice input: {e}")
                            response = "I couldn't understand that."
                            client_socket.send((response + "\n").encode())
                    continue

                # Stop listening
                elif client_message.lower() == "stop recording":
                    listening = False
                    response = "Stopped listening. You can send text input now."
                    print(f"Sending response: {response}")
                    speak(response)
                    continue

                # Handle text-based input
                if client_message.lower() not in ['start recording', 'stop recording', 'exit', 'quit', 'bye']:
                    print("Handling text-based input...")
                    intent_tag = predict_intent_bert(client_message) if model_type == "llm" else predict_intent_lstm(client_message)
                    response = get_response(intent_tag) if intent_tag else "I don't understand."

                    print(f"Sending response: {response}")
                    client_socket.send((response + "\n").encode())
                    print(f"SENT")
                    speak(response)  # Speak the response

                    if intent_tag:
                        previous_intent = intent_tag

                # Handle exit commands
                if client_message.lower() in ['exit', 'quit', 'bye']:
                    response = "Goodbye! Have a great day!"
                    print(f"Sending response: {response}")
                    client_socket.send((response + "\n").encode())
                    speak(response)
                    break

        except Exception as e:
            print(f"Error: {e}")
            break

    client_socket.close()
    print("Client disconnected.")
    
 