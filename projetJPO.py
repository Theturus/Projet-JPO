# Projet : Analyse des paroles de chansons et détection d'humeurs

# Étape 1 : Importer les bibliothèques nécessaires
import streamlit as st
import requests
import pandas as pd
from textblob import TextBlob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
from deep_translator import GoogleTranslator
from langdetect import detect
import nltk
from nltk.corpus import stopwords
import re

# Télécharger les stopwords
nltk.download('stopwords')
stop_words = set(stopwords.words('french') + stopwords.words('english'))

# API Spotify et Genius
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import lyricsgenius

# Étape 2 : Configuration des clés API
SPOTIFY_CLIENT_ID = "96a695d876914d709d1644eca8be9e32"
SPOTIFY_CLIENT_SECRET = "7571e5745d264574836f9073f689d086"
GENIUS_API_KEY = "IE-umvWO_0Q3yUjoe8B5ReXwim4DUuzeV0mrg2NVwDcJIErP63Q1imzUV1TVsRSR"

# Initialisation des clients API
spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))
genius = lyricsgenius.Genius(GENIUS_API_KEY, timeout=20)

# Étape 3 : Fonctions principales

def get_song_preview_url(artist, title):
    try:
        results = spotify.search(q=f"track:{title} artist:{artist}", type="track", limit=1)
        if results['tracks']['items']:
            return results['tracks']['items'][0]['preview_url']
        return None
    except Exception:
        return None

def clean_lyrics(raw_lyrics):
    raw_lyrics = re.sub(r"ContributorsTranslations.*", "", raw_lyrics, flags=re.DOTALL)
    raw_lyrics = re.sub(r"\[.*?\]", "", raw_lyrics)
    return "\n".join([line.strip() for line in raw_lyrics.split("\n") if line.strip()])

def get_song_lyrics(artist, title):
    try:
        song = genius.search_song(title, artist)
        if song:
            return clean_lyrics(song.lyrics)
        return "Paroles non trouvées."
    except Exception as e:
        return f"Erreur inattendue : {str(e)}"

def detect_language(text):
    try:
        return detect(text)
    except Exception:
        return "unknown"

def remove_stopwords(lyrics, language):
    try:
        stop_words = set(stopwords.words(language))
    except Exception:
        stop_words = set()  # Si la langue n'est pas supportée
    words = lyrics.split()
    return " ".join([word for word in words if word.lower() not in stop_words])

def analyze_sentiment(lyrics):
    blob = TextBlob(lyrics)
    sentiment = blob.sentiment.polarity
    return "Positif" if sentiment > 0 else "Négatif" if sentiment < 0 else "Neutre"

def clean_and_filter_lyrics(lyrics):
    words = lyrics.split()
    return " ".join([word.lower() for word in words if word.lower() not in stop_words and len(word) > 2])

def generate_wordcloud(lyrics):
    filtered_lyrics = clean_and_filter_lyrics(lyrics)
    if not filtered_lyrics.strip():
        st.warning("Le texte des paroles est vide ou ne contient aucun mot significatif après le nettoyage.")
        return
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(filtered_lyrics)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    st.pyplot(plt)

def generate_word_frequency(lyrics):
    filtered_lyrics = clean_and_filter_lyrics(lyrics)
    words = filtered_lyrics.split()
    freq = Counter(words).most_common(10)
    df = pd.DataFrame(freq, columns=['Mot', 'Fréquence'])
    st.bar_chart(df.set_index('Mot'))

# Étape 4 : Interface utilisateur avec Streamlit
st.title("Analyse des paroles de chansons et détection d'humeurs")
st.write("Donnez-nous une chanson, et nous analyserons ses paroles pour détecter l'humeur associée !")

# Exemple prédéfini
def show_example():
    example_artist = "Ed Sheeran"
    example_title = "Shape of You"
    st.subheader(f"Exemple : {example_artist} - {example_title}")

    lyrics = get_song_lyrics(example_artist, example_title)
    if lyrics.startswith("Erreur") or lyrics == "Paroles non trouvées.":
        st.error("Impossible de récupérer les paroles pour l'exemple.")
        return

    st.text_area("Paroles de l'exemple", lyrics, height=200)

    language = detect_language(lyrics)
    filtered_lyrics = remove_stopwords(lyrics, language)
    sentiment = analyze_sentiment(filtered_lyrics)

    st.write(f"Humeur détectée : **{sentiment}**")
    st.subheader("Nuage de mots")
    generate_wordcloud(filtered_lyrics)
    st.subheader("Fréquence des mots")
    generate_word_frequency(filtered_lyrics)

    preview_url = get_song_preview_url(example_artist, example_title)
    if preview_url:
        st.audio(preview_url)
    else:
        st.warning("Aucun extrait audio disponible.")

show_example()

st.markdown("---")
st.subheader("Analyse personnalisée")

artist = st.text_input("Nom de l'artiste :")
title = st.text_input("Titre de la chanson :")

if st.button("Analyser"):
    if artist and title:
        lyrics = get_song_lyrics(artist, title)
        if lyrics.startswith("Erreur") or lyrics == "Paroles non trouvées.":
            st.error("Impossible de récupérer les paroles. Veuillez vérifier le titre ou l'artiste.")
        else:
            st.text_area("Paroles", lyrics, height=200)
            language = detect_language(lyrics)
            filtered_lyrics = remove_stopwords(lyrics, language)
            sentiment = analyze_sentiment(filtered_lyrics)
            st.write(f"Humeur détectée : **{sentiment}**")
            st.subheader("Nuage de mots")
            generate_wordcloud(filtered_lyrics)
            st.subheader("Fréquence des mots")
            generate_word_frequency(filtered_lyrics)

            preview_url = get_song_preview_url(artist, title)
            if preview_url:
                st.audio(preview_url)
            else:
                st.warning("Aucun extrait audio disponible.")
    else:
        st.warning("Veuillez entrer le nom de l'artiste et le titre de la chanson.")
