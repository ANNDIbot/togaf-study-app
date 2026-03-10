import streamlit as st
import json
import os
import random

st.set_page_config(
    page_title="TOGAF Study App",
    page_icon="📘",
    layout="wide"
)

DATA_DIR = "data"


# =========================
# Data loading
# =========================
def load_json(file_name):
    path = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def normalize_cards(raw):
    if not isinstance(raw, list):
        return []

    result = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            continue

        question = item.get("question_cn") or item.get("question") or ""
        answer = item.get("answer_cn") or item.get("answer") or ""
        module = item.get("module") or "Module 1"
        topic = item.get("topic") or "General"
        card_id = item.get("id") or idx + 1

        if question and answer:
            result.append({
                "id": card_id,
                "module": module,
                "topic": topic,
                "question": question,
                "answer": answer,
            })

    return result


def normalize_quiz(raw):
    if not isinstance(raw, list):
        return []

    result = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            continue

        qid = item.get("id") or idx + 1
        module = item.get("module") or "Module 1 - Core Concepts"
        qtype = item.get("type") or "single"
        question = item.get("question") or ""
        options = item.get("options") or []
        answer = item.get("answer") or []
        explanation = item.get("explanation") or ""

        if question and isinstance(options, list) and len(options) > 0:
            result.append({
                "id": qid,
                "module": module,
                "type": qtype,
                "question": question,
                "options": options,
                "answer": answer,
                "explanation": explanation,
            })

    return result


cards = normalize_cards(load_json("module 1.json"))
quiz_questions = normalize_quiz(load_json("module 1_quiz.json"))


# =========================
# Session state
# =========================
if "study_index" not in st.session_state:
    st.session_state.study_index = 0

if "show_answer" not in st.session_state:
    st.session_state.show_answer = False

if "quiz_index" not in st.session_state:
    st.session_state.quiz_index = 0

if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

if "quiz_user_answer" not in st.session_state:
    st.session_state.quiz_user_answer = None

if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = 0

if "quiz_answered_count" not in st.session_state:
    st.session_state.quiz_answered_count = 0


# =========================
# Sidebar
# =========================
st.sidebar.title("📘 TOGAF 学习工具")

mode = st.sidebar.radio(
    "选择模式",
    ["Study", "Quiz"]
)

st.sidebar.markdown("---")

if mode == "Study":
    st.sidebar.subheader("学习模式")
    st.sidebar.write(f"卡片数量：{len(cards)}")

    if len(cards) > 0 and st.sidebar.button("随机抽一张", use_container_width=True):
        st.session_state.study_index = random.randint(0, len(cards) - 1)
        st.session_state.show_answer = False
        st.rerun()

if mode == "Quiz":
    st.sidebar.subheader("测试模式")
    st.sidebar.write(f"题目数量：{len(quiz_questions)}")
    st.sidebar.write(f"已作答：{st.session_state.quiz_answered_count}")
    st.sidebar.write(f"当前得分：{st.session_state.quiz_score}")

    if len(quiz_questions) > 0 and st.sidebar.button("随机跳题", use_container_width=True):
        st.session_state.quiz_index = random.randint(0, len(quiz_questions) - 1)
        st.session_state.quiz_submitted = False
        st.session_state.quiz_user_answer = None
        st.rerun()

    if st.sidebar.button("重置 Quiz 记录", use_container_width=True):
        st.session_state.quiz_index = 0
        st.session_state.quiz_submitted = False
        st.session_state.quiz_user_answer = None
        st.session_state.quiz_score = 0
        st.session_state.quiz_answered_count = 0
        st.rerun()


# =========================
# Study mode
# =========================
if mode == "Study":
    st.title("TOGAF 学习模式")

    if not cards:
        st.warning("没有读取到学习卡片。请检查 data/module 1.json")
    else:
        if st.session_state.study_index >= len(cards):
            st.session_state.study_index = len(cards) - 1

        card = cards[st.session_state.study_index]

        st.caption(f"Card {st.session_state.study_index + 1} / {len(cards)}")
        st.markdown(f"**Topic:** {card.get('topic', 'General')}")
        st.markdown("---")

        st.subheader("问题")
        st.write(card.get("question", "未找到问题内容"))

        if not st.session_state.show_answer:
            if st.button("显示答案", type="primary"):
                st.session_state.show_answer = True
                st.rerun()
        else:
            st.subheader("答案")
            st.success(card.get("answer", "未找到答案内容"))

        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("⬅ 上一张", use_container_width=True):
                st.session_state.study_index = max(0, st.session_state.study_index - 1)
                st.session_state.show_answer = False
                st.rerun()

        with col2:
            if st.button("随机", use_container_width=True):
                st.session_state.study_index = random.randint(0, len(cards) - 1)
                st.session_state.show_answer = False
                st.rerun()

        with col3:
            if st.button("下一张 ➡", use_container_width=True):
                st.session_state.study_index = min(len(cards) - 1, st.session_state.study_index + 1)
                st.session_state.show_answer = False
                st.rerun()


# =========================
# Quiz mode
# =========================
if mode == "Quiz":
    st.title("TOGAF Quiz 模式")

    if not quiz_questions:
        st.warning("没有读取到测试题。请检查 data/module 1_quiz.json")
    else:
        if st.session_state.quiz_index >= len(quiz_questions):
            st.session_state.quiz_index = len(quiz_questions) - 1

        q = quiz_questions[st.session_state.quiz_index]

        st.caption(f"Question {st.session_state.quiz_index + 1} / {len(quiz_questions)}")
        st.markdown(f"**题型：** {'单选' if q['type'] == 'single' else '多选'}")
        st.markdown("---")
        st.subheader(q["question"])

        option_labels = [f"{chr(65+i)}. {opt}" for i, opt in enumerate(q["options"])]

        user_answer = None

        if q["type"] == "single":
            user_answer = st.radio(
                "请选择一个答案：",
                options=list(range(len(option_labels))),
                format_func=lambda x: option_labels[x],
                index=None,
                key=f"quiz_single_{q['id']}"
            )
        else:
            selected_options = st.multiselect(
                "请选择一个或多个答案：",
                options=list(range(len(option_labels))),
                format_func=lambda x: option_labels[x],
                key=f"quiz_multi_{q['id']}"
            )
            user_answer = selected_options

        st.markdown("")

        if not st.session_state.quiz_submitted:
            if st.button("提交答案", type="primary"):
                st.session_state.quiz_user_answer = user_answer
                st.session_state.quiz_submitted = True

                correct = False
                if q["type"] == "single":
                    correct = (user_answer is not None and [user_answer] == q["answer"])
                else:
                    correct = (sorted(user_answer or []) == sorted(q["answer"]))

                st.session_state.quiz_answered_count += 1
                if correct:
                    st.session_state.quiz_score += 1

                st.rerun()
        else:
            submitted_answer = st.session_state.quiz_user_answer

            if q["type"] == "single":
                is_correct = (submitted_answer is not None and [submitted_answer] == q["answer"])
            else:
                is_correct = (sorted(submitted_answer or []) == sorted(q["answer"]))

            if is_correct:
                st.success("回答正确")
            else:
                st.error("回答错误")

            correct_labels = [option_labels[i] for i in q["answer"]]
            st.markdown("### 正确答案")
            for label in correct_labels:
                st.write(f"- {label}")

            if q["explanation"]:
                st.markdown("### 解析")
                st.info(q["explanation"])

            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("再看一题", use_container_width=True):
                    st.session_state.quiz_index = min(len(quiz_questions) - 1, st.session_state.quiz_index + 1)
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_user_answer = None
                    st.rerun()

            with col2:
                if st.button("随机下一题", use_container_width=True):
                    st.session_state.quiz_index = random.randint(0, len(quiz_questions) - 1)
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_user_answer = None
                    st.rerun()

        st.markdown("---")
        progress = st.session_state.quiz_answered_count / len(quiz_questions) if len(quiz_questions) > 0 else 0
        st.progress(progress)
        st.caption(
            f"当前累计得分：{st.session_state.quiz_score} / {st.session_state.quiz_answered_count}"
        )
