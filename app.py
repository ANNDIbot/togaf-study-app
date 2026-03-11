import streamlit as st
import json
import random
from pathlib import Path

# --- 页面配置 ---
st.set_page_config(page_title="TOGAF 学习助手", layout="wide")

# 针对移动端的样式优化
st.markdown("""
    <style>
    /* 适配手机端按钮布局 */
    div[data-testid="stHorizontalBlock"] > div {
        min-width: 0px !important;
    }
    .stButton button {
        width: 100% !important;
        height: 3.5rem !important;
        font-size: 16px !important;
    }
    /* 卡片容器 */
    .card-box {
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

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
    except Exception:
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
if "show_answer" not in st.session_state: st.session_state.show_answer = False
if "last_mod" not in st.session_state: st.session_state.last_mod = ""

# =========================
# 侧边栏
# =========================
hierarchy = get_hierarchy()
with st.sidebar:
    st.title("TOGAF Study")
    if not hierarchy:
        st.stop()
    
    sel_cat = st.selectbox("分类", list(hierarchy.keys()))
    sel_mod = st.radio("模块", list(hierarchy[sel_cat].keys()))
    
    # 切换模块重置所有状态
    if sel_mod != st.session_state.last_mod:
        st.session_state.card_idx = 0
        st.session_state.quiz_idx = 0
        st.session_state.show_answer = False
        st.session_state.last_mod = f"{sel_cat}_{sel_mod}"

    st.divider()
    mode = st.radio("模式", ["知识卡片", "模拟测试"], horizontal=True)

paths = hierarchy[sel_cat][sel_mod]

# =========================
# 模式 1：知识卡片
# =========================
if mode == "知识卡片":
    data = load_json(paths["content"])
    if data:
        total = len(data)
        st.session_state.card_idx %= total
        item = data[st.session_state.card_idx]
        
        st.caption(f"进度: {st.session_state.card_idx + 1} / {total}")
        
        with st.container(border=True):
            st.write(f"**{item.get('topic', '核心概念')}**")
            st.markdown(f"### {item.get('question_cn', '')}")
            st.divider()
            
            if st.session_state.show_answer:
                st.info(f"**答案：**\n\n{item.get('answer_cn', '')}")
                if st.button("隐藏答案", use_container_width=True):
                    st.session_state.show_answer = False
                    st.rerun()
            else:
                if st.button("点击查看答案", type="primary", use_container_width=True):
                    st.session_state.show_answer = True
                    st.rerun()

        st.write("")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("上一题"):
                st.session_state.card_idx -= 1
                st.session_state.show_answer = False
                st.rerun()
        with c2:
            if st.button("随机"):
                st.session_state.card_idx = random.randint(0, total - 1)
                st.session_state.show_answer = False
                st.rerun()
        with c3:
            if st.button("下一题"):
                st.session_state.card_idx += 1
                st.session_state.show_answer = False
                st.rerun()
    else:
        st.info("暂无卡片数据")

# =========================
# 模式 2：模拟测试（修复多选识别逻辑）
# =========================
elif mode == "模拟测试":
    quiz_data = load_json(paths["quiz"])
    if quiz_data:
        total_q = len(quiz_data)
        st.session_state.quiz_idx %= total_q
        q = quiz_data[st.session_state.quiz_idx]
        
        st.caption(f"题目: {st.session_state.quiz_idx + 1} / {total_q}")
        
        with st.container(border=True):
            st.markdown(f"### {q['question']}")
            
            # 兼容不同数据格式的类型判断
            is_multi = q.get("type") == "multi" or len(q.get("answer", [])) > 1
            q_key = f"q_{st.session_state.last_mod}_{st.session_state.quiz_idx}"
            
            if is_multi:
                ans = st.multiselect("多项选择", q['options'], key=q_key)
                if not st.session_state.show_answer:
                    if st.button("确认提交", use_container_width=True):
                        st.session_state.show_answer = True
                        st.rerun()
            else:
                ans = st.radio("单项选择", q['options'], index=None, key=q_key)
                if ans and not st.session_state.show_answer:
                    st.session_state.show_answer = True
                    st.rerun()

            if st.session_state.show_answer:
                # 转换索引为具体选项文字以便阅读
                correct_text = [q['options'][i] for i in q['answer']]
                st.warning(f"**正确答案：** {', '.join(correct_text)}")
                with st.expander("查看解析", expanded=True):
                    st.write(q.get("explanation", "暂无解析"))

        st.write("")
        q1, q2, q3 = st.columns(3)
        with q1:
            if st.button("上一题", key="q_prev"):
                st.session_state.quiz_idx -= 1
                st.session_state.show_answer = False
                st.rerun()
        with q2:
            if st.button("随机", key="q_rand"):
                st.session_state.quiz_idx = random.randint(0, total_q - 1)
                st.session_state.show_answer = False
                st.rerun()
        with q3:
            if st.button("下一题", key="q_next"):
                st.session_state.quiz_idx += 1
                st.session_state.show_answer = False
                st.rerun()
    else:
        st.warning("暂无测试题数据")
