import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pydeck as pdk
import io

# Set Streamlit page configuration
st.set_page_config(page_title="Greenmovement", layout="centered")

# Load and display the logo in the sidebar
logo = "logo.jpg"
st.sidebar.image(logo, use_column_width=True)

st.sidebar.title("Configuration")
input_password = st.sidebar.text_input("Enter Password", type="password")

# Initialize session state for responses if it doesn't exist
if 'responses' not in st.session_state:
    st.session_state['responses'] = []

correct_password = "greenmovement"
if input_password != correct_password:
    st.sidebar.error("Incorrect password. Access denied.")
    st.stop()

model_options = {
    "Llama 70B Versatile": "llama-3.1-70b-versatile",
    "Llama 8B Instant": "llama-3.1-8b-instant",
    "Llama Guard 8B": "llama-guard-3-8b"
}
selected_model = st.sidebar.selectbox("Select Model", list(model_options.keys()))
api_key = st.secrets["groq"]["api_key"]

@st.cache(allow_output_mutation=True)
def load_data(file_path):
    return pd.read_csv(file_path)

data = load_data('datasampah1.csv')
ipal_data = load_data('IPAL.csv')

def assign_lat_lon(data):
    if 'latitude' not in data.columns or 'longitude' not in data.columns:
        num_rows = len(data)
        default_lat = 18.0  # Latitude for Mekong River in Laos
        default_lon = 105.0  # Longitude for Mekong River in Laos
        data['latitude'] = [default_lat] * num_rows
        data['longitude'] = [default_lon] * num_rows

assign_lat_lon(ipal_data)

# Function to generate plots based on user input
def generate_plot(data, plot_type, x_column, y_column):
    plt.figure()
    if plot_type == 'Line':
        plt.plot(data[x_column], data[y_column], marker='o')
    elif plot_type == 'Bar':
        plt.bar(data[x_column], data[y_column])
    elif plot_type == 'Scatter':
        plt.scatter(data[x_column], data[y_column])
    plt.title(f'{plot_type} Plot of {y_column} vs {x_column}')
    plt.xlabel(x_column)
    plt.ylabel(y_column)
    st.pyplot(plt)
    plt.clf()  # Clear the plot figure to free up memory

# Plot configuration
plot_type = st.selectbox("Choose the type of plot:", ["Line", "Bar", "Scatter"])
columns = data.columns.tolist()
x_column = st.selectbox("Select X-axis data:", columns)
y_column = st.selectbox("Select Y-axis data:", columns)

if st.button("Generate Plot"):
    generate_plot(data, plot_type, x_column, y_column)

# Display the map with IPAL data
st.subheader("IPAL Coverage Map")
layer = pdk.Layer(
    "ScatterplotLayer",
    ipal_data,
    get_position='[longitude, latitude]',
    get_color='[255, 0, 0, 160]',  # RGB color code for red
    get_radius=20000,
)
view_state = pdk.ViewState(
    latitude=ipal_data['latitude'].mean(),
    longitude=ipal_data['longitude'].mean(),
    zoom=7,
    pitch=50,
)
st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))

def generate_response(prompt, temperature=0.7):
    from groq import Groq
    client = Groq(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=model_options[selected_model],
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return "I'm sorry, I couldn't generate a response."

question = st.text_input("Ask a question or make a request:")
if question:
    answer = generate_response(question)
    st.session_state.responses.append({"question": question, "answer": answer})

for entry in reversed(st.session_state.responses):
    st.write(f"**Q:** {entry['question']}\n**A:** {entry['answer']}")
    st.write("---")
