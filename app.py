import streamlit as st
import main

st.title("🐶 Pets Name Generator")

animal_type = st.sidebar.selectbox("Какое у вас домашнее животное?", ("Собака", "Кошка", "Хомяк", "Крыса", "Змея", "Ящерица", "Корова"))

animal_labels = {
    "Собака": "Какого цвета ваша собака?",
    "Кошка": "Какого цвета ваша кошка?",
    "Хомяк": "Какого цвета ваш хомяк?",
    "Крыса": "Какого цвета ваша крыса?",
    "Змея": "Какого цвета ваша змея?",
    "Ящерица": "Какого цвета ваша ящерица?",
    "Корова": "Какого цвета ваша корова?",
}

pet_color = st.sidebar.text_area(
    label=animal_labels[animal_type],
    max_chars=25
)

if pet_color:
    response = main.generate_pet_name(animal_type, pet_color)
    st.text(response)