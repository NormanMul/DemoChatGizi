import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pydeck as pdk
from groq import Groq

# Set Streamlit page configuration
st.set_page_config(page_title="DoaIbu Nutrition Assistant", layout="centered")

# Load and display the logo in the sidebar
logo = "logo.jpg"
st.sidebar.image(logo, use_column_width=True)

st.sidebar.title("Configuration")
input_password = st.sidebar.text_input("Enter Password (password is team's name without capital)", type="password")

# Initialize session state for responses if it doesn't exist
if 'responses' not in st.session_state:
    st.session_state['responses'] = []

correct_password = "doaibu"
if input_password != correct_password:
    st.sidebar.error("Incorrect password. Access denied.")
    st.stop()

# API and model selection
model_options = {
    "Llama 70B Versatile": "llama-3.1-70b-versatile",
    "Llama 8B Instant": "llama-3.1-8b-instant",
    "Llama Guard 8B": "llama-guard-3-8b"
}
selected_model = st.sidebar.selectbox("Select Model", list(model_options.keys()))
api_key = st.secrets["groq"]["api_key"]

# Load IPAL data for geographic representation
ipal_data = pd.read_csv('IPAL.csv')

def assign_lat_lon(data):
    if 'latitude' not in data.columns or 'longitude' not in data.columns:
        num_rows = len(data)
        default_lat = 18.0
        default_lon = 105.0
        data['latitude'] = [default_lat] * num_rows
        data['longitude'] = [default_lon] * num_rows

assign_lat_lon(ipal_data)

# Nutrition Parameter Inputs
st.title("Nutrition Diagnostic Tool")
st.subheader("Enter Health Parameters")

age = st.number_input("Age (years)", min_value=0, max_value=100, value=5)
height = st.number_input("Height (cm)", min_value=30, max_value=250, value=100)
weight = st.number_input("Weight (kg)", min_value=1, max_value=200, value=15)
gender = st.selectbox("Gender", ["Male", "Female"])

# Calculate basic nutritional indicators (BMI, etc.)
bmi = weight / ((height / 100) ** 2)
st.write(f"Calculated BMI: {bmi:.2f}")

def check_nutrition_status(bmi, age):
    if age < 5:
        if bmi < 15:
            return "Underweight (Potential Malnutrition)"
        elif 15 <= bmi < 18:
            return "Normal"
        else:
            return "Overweight"
    elif age < 18:
        if bmi < 16:
            return "Underweight (Risk of Stunting)"
        elif 16 <= bmi < 24:
            return "Normal"
        else:
            return "Overweight"
    else:
        if bmi < 18.5:
            return "Underweight"
        elif 18.5 <= bmi < 24.9:
            return "Normal"
        else:
            return "Overweight"

nutrition_status = check_nutrition_status(bmi, age)
st.write(f"Nutrition Status: {nutrition_status}")

# Map with IPAL data
st.subheader("IPAL Coverage Map")
layer = pdk.Layer(
    "ScatterplotLayer",
    ipal_data,
    get_position='[longitude, latitude]',
    get_color='[255, 0, 0, 160]',
    get_radius=20000,
)
view_state = pdk.ViewState(
    latitude=ipal_data['latitude'].mean(),
    longitude=ipal_data['longitude'].mean(),
    zoom=7,
    pitch=50,
)
st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))

# Question-answer model for nutrition FAQ
def generate_response(prompt, temperature=0.7):
    client = Groq(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=model_options[selected_model],
            messages=[
                {"role": "system", "content": "You are a helpful nutrition assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return "I'm sorry, I couldn't generate a response."

question = st.text_input("Ask a question about nutrition:")
if question:
    answer = generate_response(question)
    st.session_state.responses.append({"question": question, "answer": answer})

for entry in reversed(st.session_state.responses):
    st.write(f"**Q:** {entry['question']}\n**A:** {entry['answer']}")
    st.write("---")
