import streamlit as st
import json
import os
import random

st.set_page_config(
    page_title="TOGAF Study",
    page_icon="📚",
    layout="wide"
)

# ======================
# Load card data
# ======================

DATA_PATH = "data"

def load_cards():
    cards = []
    for file in os.listdir(DATA_PATH):
        if file.endswith(".json"):
            with open(os.path.join(DATA_PATH, file), "r", encoding="utf-8") as f:
                cards.extend(json.load(f))
    return cards


cards = load_cards()

modules = sorted(list(set(card["module"] for card in cards)))


# ======================
# Sidebar
# ======================

st.sidebar.title("TOGAF 学习")

selected_module = st.sidebar.selectbox(
    "选择学习模块",
    modules
)

module_cards = [c for c in cards if c["module"] == selected_module]

st.sidebar.write(f"卡片数量: {len(module_cards)}")

if "index" not in st.session_state:
    st.session_state.index = 0

if "show_answer" not in st.session_state:
    st.session_state.show_answer = False


if st.sidebar.button("随机开始"):
    st.session_state.index = random.randint(0, len(module_cards)-1)
    st.session_state.show_answer = False


# ======================
# Card display
# ======================

card = module_cards[st.session_state.index]

st.title(selected_module)

st.markdown("---")

st.subheader("问题")

st.write(card["question_cn"])

st.write("")

if not st.session_state.show_answer:

    if st.button("显示答案"):
        st.session_state.show_answer = True

else:

    st.subheader("答案")

    st.success(card["answer_cn"])


st.markdown("---")

# ======================
# Navigation
# ======================

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("⬅ 上一张"):
        st.session_state.index = max(0, st.session_state.index - 1)
        st.session_state.show_answer = False
        st.rerun()

with col2:
    if st.button("随机"):
        st.session_state.index = random.randint(0, len(module_cards)-1)
        st.session_state.show_answer = False
        st.rerun()

with col3:
    if st.button("下一张 ➡"):
        st.session_state.index = min(len(module_cards)-1, st.session_state.index + 1)
        st.session_state.show_answer = False
        st.rerun()


st.markdown("---")

st.caption(
    f"Card {st.session_state.index + 1} / {len(module_cards)}"
)
