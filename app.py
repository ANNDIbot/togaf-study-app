import streamlit as st
import json
import random
from pathlib import Path

# --- 页面配置 ---
st.set_page_config(page_title="TOGAF 学习助手", layout="wide")

DATA_DIR = Path("data")

# =========================
# 核心数据加载函数
# =========================
def load_json(path: Path):
    if not path or not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"解析文件 {path.name} 失败，请检查 JSON 格式（逗号或括号）。")
        return []

def get_hierarchy():
    hierarchy = {}
    if not DATA_DIR.exists(): return hierarchy
    categories = sorted([d for d in DATA_DIR.iterdir() if d.is_dir()])
    for cat_path in categories:
        cat_display = cat_path.name.split('_', 1)[-1] if '_' in cat_path.name else cat_path.name
        hierarchy[cat_display] = {}
        content_files = sorted([f for f in cat_path.glob("*.json") if "_quiz" not in f.name])
        for cf in content_files:
            mod_display = cf.stem.replace('_', ' ').title()
            hierarchy[cat_display][mod_display] = {
                "content": cf,
                "quiz": cat_path / f"{cf.stem}_quiz.json"
            }
    return hierarchy

# =========================
# 初始化 Session State
# =========================
if "card_idx" not in st.session_state: st.session_state.card_idx = 0
if "quiz_idx" not in st.session_state: st.session_state.quiz_idx = 0
if "last_mod" not in st.session_state: st.session_state.last_mod = ""

# =========================
# 侧边栏
# =========================
hierarchy = get_hierarchy()
with st.sidebar:
    st.title("📘 TOGAF 备考助手")
    if not hierarchy:
        st.stop()
    
    sel_cat = st.selectbox("选择类别", list(hierarchy.keys()))
    sel_mod = st.radio("选择章节", list(hierarchy[sel_cat].keys()))
    
    # 如果切换了章节，重置索引
    if sel_mod != st.session_state.last_mod:
        st.session_state.card_idx = 0
        st.session_state.quiz_idx = 0
        st.session_state.last_mod = sel_mod

    st.divider()
    mode = st.radio("切换模式", ["知识卡片", "模拟测试"], horizontal=True)

paths = hierarchy[sel_cat][sel_mod]

# =========================
# 模式 1：知识卡片（单张模式）
# =========================
if mode == "知识卡片":
    data = load_json(paths["content"])
    if data:
        total = len(data)
        # 防止越界
        st.session_state.card_idx = max(0, min(st.session_state.card_idx, total - 1))
        
        item = data[st.session_state.card_idx]
        
        st.header(f"🗂️ 知识点学习 ({st.session_state.card_idx + 1} / {total})")
        
        # 卡片展示区
        with st.container(border=True):
            st.subheader(item.get("topic", "核心概念"))
            st.markdown(f"#### **问：{item.get('question_cn', '')}**")
            st.divider()
            st.markdown(f"**答：**\n{item.get('answer_cn', '')}")
            st.caption(f"ID: {item.get('id')} | Module: {item.get('module')}")

        # 控制按钮
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("⬅️ 上一张"):
                st.session_state.card_idx = (st.session_state.card_idx - 1) % total
                st.rerun()
        with col2:
            if st.button("下一张 ➡️"):
                st.session_state.card_idx = (st.session_state.card_idx + 1) % total
                st.rerun()
        with col3:
            if st.button("🎲 随机抽一张"):
                st.session_state.card_idx = random.randint(0, total - 1)
                st.rerun()
    else:
        st.info("暂无卡片数据。")

# =========================
# 模式 2：模拟测试（单题模式）
# =========================
elif mode == "模拟测试":
    quiz_data = load_json(paths["quiz"])
    if quiz_data:
        total_q = len(quiz_data)
        st.session_state.quiz_idx = max(0, min(st.session_state.quiz_idx, total_q - 1))
        
        q = quiz_data[st.session_state.quiz_idx]
        
        st.header(f"📝 章节自测 ({st.session_state.quiz_idx + 1} / {total_q})")
        
        with st.container(border=True):
            st.markdown(f"### {q['question']}")
            
            is_multi = q.get("type") == "multi"
            if is_multi:
                ans = st.multiselect("多项选择", q['options'], key=f"q_{sel_mod}_{st.session_state.quiz_idx}")
                user_res = sorted([q['options'].index(a) for a in ans])
                correct = user_res == sorted(q['answer'])
            else:
                ans = st.radio("单项选择", q['options'], index=None, key=f"q_{sel_mod}_{st.session_state.quiz_idx}")
                user_res = [q['options'].index(ans)] if ans else []
                correct = user_res == q['answer']

            if ans:
                if correct:
                    st.success("🎯 回答正确！")
                else:
                    st.error(f"❌ 回答错误。正确答案索引：{q['answer']}")
                
                with st.expander("查看解析", expanded=True):
                    st.write(q.get("explanation", "暂无解析。"))

        # 控制按钮
        st.write("")
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            if st.button("上一步"):
                st.session_state.quiz_idx = (st.session_state.quiz_idx - 1) % total_q
                st.rerun()
        with c2:
            if st.button("下一题"):
                st.session_state.quiz_idx = (st.session_state.quiz_idx + 1) % total_q
                st.rerun()
        with c3:
            if st.button("🔀 随机测试"):
                st.session_state.quiz_idx = random.randint(0, total_q - 1)
                st.rerun()
    else:
        st.warning("未找到测试题文件。")
