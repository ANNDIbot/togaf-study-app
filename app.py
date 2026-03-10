import streamlit as st
import json
import os
import random
from pathlib import Path

st.set_page_config(
    page_title="TOGAF Study App",
    page_icon="📘",
    layout="wide"
)

DATA_DIR = Path("data")


# =========================
# Helpers
# =========================
def load_json(path: Path):
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def normalize_cards(raw, fallback_module="Unknown Module"):
    if not isinstance(raw, list):
        return []

    result = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            continue

        question = item.get("question_cn") or item.get("question") or ""
        answer = item.get("answer_cn") or item.get("answer") or ""
        module = item.get("module") or fallback_module
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


def normalize_quiz(raw, fallback_module="Unknown Module"):
    if not isinstance(raw, list):
        return []

    result = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            continue

        qid = item.get("id") or idx + 1
        module = item.get("module") or fallback_module
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


def infer_module_name_from_filename(file_name: str):
    # "module 1.json" -> "Module 1"
    # "module 2_quiz.json" -> "Module 2"
    base = file_name.replace("_quiz", "").replace(".json", "").strip()
    return base.title()


def load_all_data():
    all_cards = []
    all_quiz = []

    if not DATA_DIR.exists():
        return all_cards, all_quiz

    for file_path in sorted(DATA_DIR.glob("*.json")):
        file_name = file_path.name.lower()
        fallback_module = infer_module_name_from_filename(file_path.name)

        raw = load_json(file_path)

        if "_quiz" in file_name:
            all_quiz.extend(normalize_quiz(raw, fallback_module=fallback_module))
        else:
            all_cards.extend(normalize_cards(raw, fallback_module=fallback_module))

    return all_cards, all_quiz


def unique_modules(cards, quiz):
    names = set()
    for item in cards:
        names.add(item["module"])
    for item in quiz:
        names.add(item["module"])
    return sorted(names)


def get_cards_by_module(cards, module_name):
    return [c for c in cards if c["module"] == module_name]


def get_quiz_by_module(quiz, module_name):
    return [q for q in quiz if q["module"] == module_name]


def reset_study_state():
    st.session_state.study_index = 0
    st.session_state.show_answer = False


def reset_quiz_state(keep_score=False):
    st.session_state.quiz_index = 0
    st.session_state.quiz_submitted = False
    st.session_state.quiz_user_answer = None
    if not keep_score:
        st.session_state.quiz_score = 0
        st.session_state.quiz_answered_count = 0


# =========================
# Load data
# =========================
cards, quiz_questions = load_all_data()
module_names = unique_modules(cards, quiz_questions)


# =========================
# Session state
# =========================
if "selected_module" not in st.session_state:
    st.session_state.selected_module = module_names[0] if module_names else ""

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


if st.session_state.selected_module not in module_names and module_names:
    st.session_state.selected_module = module_names[0]


# =========================
# Sidebar
# =========================
st.sidebar.title("📘 TOGAF 学习工具")

if module_names:
    selected_module = st.sidebar.selectbox(
        "选择模块",
        module_names,
        index=module_names.index(st.session_state.selected_module)
    )
else:
    selected_module = ""

if selected_module != st.session_state.selected_module:
    st.session_state.selected_module = selected_module
    reset_study_state()
    reset_quiz_state(keep_score=False)
    st.rerun()

mode = st.sidebar.radio("选择模式", ["Study", "Quiz"])

module_cards = get_cards_by_module(cards, selected_module)
module_quiz = get_quiz_by_module(quiz_questions, selected_module)

st.sidebar.markdown("---")
st.sidebar.write(f"当前模块：**{selected_module or '无'}**")
st.sidebar.write(f"学习卡片：{len(module_cards)}")
st.sidebar.write(f"测试题：{len(module_quiz)}")


# =========================
# Study mode
# =========================
if mode == "Study":
    st.title("TOGAF 学习模式")

    if not module_cards:
        st.warning(f"没有读取到 {selected_module} 的学习卡片。")
    else:
        if st.sidebar.button("随机抽一张", use_container_width=True):
            st.session_state.study_index = random.randint(0, len(module_cards) - 1)
            st.session_state.show_answer = False
            st.rerun()

        if st.session_state.study_index >= len(module_cards):
            st.session_state.study_index = len(module_cards) - 1

        card = module_cards[st.session_state.study_index]

        st.caption(f"{selected_module} · Card {st.session_state.study_index + 1} / {len(module_cards)}")
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
                st.session_state.study_index = random.randint(0, len(module_cards) - 1)
                st.session_state.show_answer = False
                st.rerun()

        with col3:
            if st.button("下一张 ➡", use_container_width=True):
                st.session_state.study_index = min(len(module_cards) - 1, st.session_state.study_index + 1)
                st.session_state.show_answer = False
                st.rerun()


# =========================
# Quiz mode
# =========================
if mode == "Quiz":
    st.title("TOGAF Quiz 模式")

    if not module_quiz:
        st.warning(f"没有读取到 {selected_module} 的测试题。")
    else:
        st.sidebar.markdown("---")
        st.sidebar.write(f"已作答：{st.session_state.quiz_answered_count}")
        st.sidebar.write(f"当前得分：{st.session_state.quiz_score}")

        if st.sidebar.button("随机跳题", use_container_width=True):
            st.session_state.quiz_index = random.randint(0, len(module_quiz) - 1)
            st.session_state.quiz_submitted = False
            st.session_state.quiz_user_answer = None
            st.rerun()

        if st.sidebar.button("重置 Quiz 记录", use_container_width=True):
            reset_quiz_state(keep_score=False)
            st.rerun()

        if st.session_state.quiz_index >= len(module_quiz):
            st.session_state.quiz_index = len(module_quiz) - 1

        q = module_quiz[st.session_state.quiz_index]

        st.caption(f"{selected_module} · Question {st.session_state.quiz_index + 1} / {len(module_quiz)}")
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
                key=f"quiz_single_{selected_module}_{q['id']}"
            )
        else:
            user_answer = st.multiselect(
                "请选择一个或多个答案：",
                options=list(range(len(option_labels))),
                format_func=lambda x: option_labels[x],
                key=f"quiz_multi_{selected_module}_{q['id']}"
            )

        if not st.session_state.quiz_submitted:
            if st.button("提交答案", type="primary"):
                st.session_state.quiz_user_answer = user_answer
                st.session_state.quiz_submitted = True

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
                if st.button("下一题", use_container_width=True):
                    st.session_state.quiz_index = min(len(module_quiz) - 1, st.session_state.quiz_index + 1)
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_user_answer = None
                    st.rerun()

            with col2:
                if st.button("随机下一题", use_container_width=True):
                    st.session_state.quiz_index = random.randint(0, len(module_quiz) - 1)
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_user_answer = None
                    st.rerun()

        st.markdown("---")
        progress = st.session_state.quiz_answered_count / len(module_quiz) if len(module_quiz) > 0 else 0
        st.progress(progress)
        st.caption(f"当前累计得分：{st.session_state.quiz_score} / {st.session_state.quiz_answered_count}")
