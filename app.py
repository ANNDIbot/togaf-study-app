import json
from pathlib import Path
import streamlit as st


# =========================
# Basic page config
# =========================
st.set_page_config(
    page_title="TOGAF Study App",
    page_icon="📘",
    layout="wide",
)


# =========================
# Helpers
# =========================
DATA_DIR = Path("data")


def load_json_file(file_path: Path):
    if not file_path.exists():
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return normalize_cards(raw)
    except Exception:
        return []


def normalize_cards(raw):
    if not isinstance(raw, list):
        return []

    normalized = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            continue

        question = item.get("question_cn") or item.get("question") or ""
        answer = item.get("answer_cn") or item.get("answer") or ""
        module = item.get("module") or "Unknown Module"
        topic = item.get("topic") or "General"
        card_id = item.get("id") or idx + 1

        if question and answer:
            normalized.append(
                {
                    "id": card_id,
                    "module": module,
                    "topic": topic,
                    "question_cn": question,
                    "answer_cn": answer,
                }
            )
    return normalized


def load_default_cards():
    cards = []
    if DATA_DIR.exists():
        for file_path in sorted(DATA_DIR.glob("*.json")):
            cards.extend(load_json_file(file_path))
    return dedupe_cards(cards)


def dedupe_cards(cards):
    seen = {}
    for c in cards:
        key = f"{c['module']}::{c['id']}"
        seen[key] = c
    return list(seen.values())


def group_by_module(cards):
    grouped = {}
    for card in cards:
        grouped.setdefault(card["module"], []).append(card)
    return grouped


def topic_counts(cards):
    counts = {}
    for c in cards:
        counts[c["topic"]] = counts.get(c["topic"], 0) + 1
    return sorted(counts.items(), key=lambda x: (-x[1], x[0]))


def get_filtered_cards(cards, selected_module, search_text):
    module_cards = [c for c in cards if c["module"] == selected_module]
    q = search_text.strip().lower()
    if not q:
        return module_cards

    filtered = []
    for c in module_cards:
        if (
            q in c["topic"].lower()
            or q in c["question_cn"].lower()
            or q in c["answer_cn"].lower()
        ):
            filtered.append(c)
    return filtered


def ensure_state():
    if "cards" not in st.session_state:
        st.session_state.cards = load_default_cards()

    if "selected_module" not in st.session_state:
        modules = list(group_by_module(st.session_state.cards).keys())
        st.session_state.selected_module = modules[0] if modules else ""

    if "current_index" not in st.session_state:
        st.session_state.current_index = 0

    if "show_answer" not in st.session_state:
        st.session_state.show_answer = False

    if "search" not in st.session_state:
        st.session_state.search = ""

    if "progress_map" not in st.session_state:
        st.session_state.progress_map = {}

    if "completed_ids" not in st.session_state:
        st.session_state.completed_ids = []


def reset_learning_state():
    st.session_state.current_index = 0
    st.session_state.show_answer = False


def mark_card(card_id, level):
    st.session_state.progress_map[str(card_id)] = level
    if card_id not in st.session_state.completed_ids:
        st.session_state.completed_ids.append(card_id)


def module_progress(module_cards):
    if not module_cards:
        return 0
    done = sum(1 for c in module_cards if c["id"] in st.session_state.completed_ids)
    return int(done / len(module_cards) * 100)


def move_next(total):
    if total <= 0:
        return
    if st.session_state.current_index < total - 1:
        st.session_state.current_index += 1
    st.session_state.show_answer = False


def move_prev():
    if st.session_state.current_index > 0:
        st.session_state.current_index -= 1
    st.session_state.show_answer = False


# =========================
# Init
# =========================
ensure_state()

cards = st.session_state.cards
modules_dict = group_by_module(cards)
module_names = list(modules_dict.keys())

if st.session_state.selected_module not in module_names and module_names:
    st.session_state.selected_module = module_names[0]

selected_module = st.session_state.selected_module


# =========================
# Sidebar
# =========================
with st.sidebar:
    st.title("📘 TOGAF Study App")
    st.caption("MVP for Streamlit Cloud")

    st.subheader("导入更多卡片")
    uploaded_file = st.file_uploader("上传 JSON 文件", type=["json"])

    if uploaded_file is not None:
        try:
            raw = json.load(uploaded_file)
            new_cards = normalize_cards(raw)
            merged = dedupe_cards(st.session_state.cards + new_cards)
            st.session_state.cards = merged
            st.success(f"成功导入 {len(new_cards)} 张卡片")
            st.rerun()
        except Exception:
            st.error("JSON 读取失败。请检查格式是否为数组。")

    st.divider()
    st.subheader("模块")

    for name in module_names:
        total = len(modules_dict.get(name, []))
        done = sum(
            1 for c in modules_dict.get(name, []) if c["id"] in st.session_state.completed_ids
        )
        if st.button(f"{name} ({done}/{total})", use_container_width=True):
            st.session_state.selected_module = name
            reset_learning_state()
            st.rerun()

    st.divider()
    current_module_cards = modules_dict.get(selected_module, [])
    progress_value = module_progress(current_module_cards)
    st.subheader("当前模块进度")
    st.progress(progress_value / 100 if progress_value else 0)
    st.write(f"{progress_value}%")

    if st.button("重置学习进度", use_container_width=True):
        st.session_state.progress_map = {}
        st.session_state.completed_ids = []
        reset_learning_state()
        st.rerun()


# =========================
# Main layout
# =========================
st.title("TOGAF 学习系统")
st.caption("先把学习流程跑通，再继续扩充知识卡片和测试题库。")

tab1, tab2, tab3 = st.tabs(["学习", "概览", "复习"])

# =========================
# Tab 1: Study
# =========================
with tab1:
    st.subheader(selected_module if selected_module else "暂无模块")

    col1, col2 = st.columns([2, 1])
    with col1:
        search_text = st.text_input(
            "搜索 topic / question / answer",
            value=st.session_state.search,
            placeholder="例如：TOGAF / Architecture / Stakeholder",
        )
        st.session_state.search = search_text

    filtered_cards = get_filtered_cards(
        st.session_state.cards,
        st.session_state.selected_module,
        st.session_state.search,
    )

    total_cards = len(filtered_cards)

    if total_cards == 0:
        st.info("这个模块当前没有卡片，或者搜索条件下没有结果。")
    else:
        if st.session_state.current_index >= total_cards:
            st.session_state.current_index = total_cards - 1

        current_card = filtered_cards[st.session_state.current_index]

        st.write(
            f"第 **{st.session_state.current_index + 1}** / **{total_cards}** 张"
        )
        st.caption(f"Topic: {current_card['topic']}")

        with st.container(border=True):
            st.markdown("### Question")
            st.write(current_card["question_cn"])

            if st.session_state.show_answer:
                st.markdown("---")
                st.markdown("### Answer")
                st.write(current_card["answer_cn"])

        nav1, nav2, nav3 = st.columns([1, 1, 2])

        with nav1:
            if st.button("上一张", use_container_width=True):
                move_prev()
                st.rerun()

        with nav2:
            if st.button("下一张", use_container_width=True):
                move_next(total_cards)
                st.rerun()

        with nav3:
            if not st.session_state.show_answer:
                if st.button("显示答案", use_container_width=True, type="primary"):
                    st.session_state.show_answer = True
                    st.rerun()

        if st.session_state.show_answer:
            st.markdown("#### 你记住得怎么样？")
            r1, r2, r3, r4 = st.columns(4)

            with r1:
                if st.button("again", use_container_width=True):
                    mark_card(current_card["id"], "again")
                    move_next(total_cards)
                    st.rerun()

            with r2:
                if st.button("hard", use_container_width=True):
                    mark_card(current_card["id"], "hard")
                    move_next(total_cards)
                    st.rerun()

            with r3:
                if st.button("good", use_container_width=True):
                    mark_card(current_card["id"], "good")
                    move_next(total_cards)
                    st.rerun()

            with r4:
                if st.button("easy", use_container_width=True):
                    mark_card(current_card["id"], "easy")
                    move_next(total_cards)
                    st.rerun()


# =========================
# Tab 2: Overview
# =========================
with tab2:
    current_module_cards = modules_dict.get(selected_module, [])
    current_topic_counts = topic_counts(current_module_cards)
    completed_count = sum(
        1 for c in current_module_cards if c["id"] in st.session_state.completed_ids
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("总卡片数", len(current_module_cards))
    c2.metric("已学习", completed_count)
    c3.metric("Topic 数", len(current_topic_counts))

    st.markdown("### Topic 分布")
    if current_topic_counts:
        for topic, count in current_topic_counts:
            st.write(f"- **{topic}**：{count}")
    else:
        st.info("当前模块还没有 topic 数据。")


# =========================
# Tab 3: Review
# =========================
with tab3:
    st.markdown("### 复习清单")
    review_cards = [
        c
        for c in modules_dict.get(selected_module, [])
        if st.session_state.progress_map.get(str(c["id"])) in ["again", "hard"]
    ]

    if not review_cards:
        st.success("目前没有 again / hard 的卡片，挺好。")
    else:
        for idx, card in enumerate(review_cards, start=1):
            with st.expander(f"{idx}. {card['question_cn']}  |  {card['topic']}"):
                st.write(f"**Answer:** {card['answer_cn']}")
                st.write(
                    f"**记忆评级:** {st.session_state.progress_map.get(str(card['id']), '-')}"
                )
