import streamlit as st
import speech_recognition as sr
import openai
import threading
from gtts import gTTS
from pydub import AudioSegment
import pygame
import io
import os
import glob
import queue
from datetime import datetime
import re

# OpenAI API 키 설정
openai.api_key = st.text_input("OpenAI API", type="password")

def play_audio(filename):
    try:
        # pygame 믹서 초기화
        pygame.mixer.init()
        # 음악 로드
        pygame.mixer.music.load(filename)
        # 음악 재생
        pygame.mixer.music.play()
        # 음악이 끝날 때까지 대기
        while pygame.mixer.music.get_busy() == True:
            continue    

    except Exception as e:
        print(f"Error in play_audio: {e}")

# 글로벌 변수
text_queue = queue.Queue()
should_stop = threading.Event()

def speak_text(oriText):
    try:
        now = datetime.now().strftime("%Y%m%d%H%M%S")

        # 영어 TTS 파일 생성
        text = oriText.split('[')[0].strip()
        tts_en = gTTS(text=text, lang='en')
        filename_en = f"output_en_{now}.mp3"
        tts_en.save(filename_en)

        # 한국어 TTS 파일 생성
        match = re.search(r'\[(.*?)\]', oriText)
        if match:
            text = match.group(1).strip()
        else:
            pass        
        tts_ko = gTTS(text=text, lang='ko')
        filename_ko = f"output_ko_{now}.mp3"
        tts_ko.save(filename_ko)

        play_audio(filename_en)
        # play_audio(filename_ko)

    except Exception as e:
        print(f"Error in speak_text: {e}")


def get_chatgpt_response(user_input):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an english teacher. You have to tell me your opinions in english. And, you translate that into Korean enclosed in square brackets. Next, if there is a word in high school or higher, tell me 출력형식 ""the English word: its meaning in Korean"""},
                {"role": "user", "content": user_input}
            ],
            max_tokens=1000,
            n=1,
            stop=None,
            temperature=0.5
        )
        chatgpt_response = response['choices'][0]['message']['content'].strip()
        return chatgpt_response
    except Exception as e:
        st.error(f"Error in get_chatgpt_response: {e}")
        text_queue.put(("Error", f"Error communicating with ChatGPT: {e}"))
        return None

def recognize_speech():
    recognizer = sr.Recognizer()
    while not should_stop.is_set():
        with sr.Microphone() as source:
            #st.write("Listening...")
            try:
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=60)
                text = recognizer.recognize_google(audio)
                st.write(f"You: {text}")
                text_queue.put(("You", text))
                if text.lower() == "quit":
                    should_stop.set()
                    break
                chatgpt_response = get_chatgpt_response(text)
                if chatgpt_response:
                    st.write(f"ChatGPT: {chatgpt_response}")
                    text_queue.put(("ChatGPT", chatgpt_response))
                    speak_text(chatgpt_response)

            except sr.UnknownValueError:
                pass
                #st.error("Could not understand the audio")
            except sr.RequestError as e:
                pass
                #st.error(f"Could not request results; {e}")
            except Exception as e:
                pass
                #st.error(f"Error in recognize_speech: {e}")

def main():
    st.title("AI Teacher")
    recognize_speech()

if __name__ == '__main__':
    main()