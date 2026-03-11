import streamlit as st
import json
import random
from pathlib import Path

# --- 页面配置：手机端建议 wide 模式但控制内容宽度 ---
st.set_page_config(page_title="TOGAF Pocket", layout="wide")

# 强制手机端样式微调
st.markdown("""
    <style>
    .stButton button { width: 100%; height: 3rem; font-size: 1.1rem; }
    .stExpander { border: 1px solid #e0e0e0; border-radius: 10px; }
    .card-box { 
        background-color: #f8f9fa; 
        padding: 20px; 
        border-radius: 15px; 
        border: 2px solid #007bff;
        margin-bottom: 20px;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    </style>
""", unsafe_allow_html=True)

DATA_DIR = Path("data")

# =========================
# 数据处理
# =========================
def load_json(path: Path):
    if not path.exists(): return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return []

def get_hierarchy():
    hierarchy = {}
    if not DATA_DIR.exists(): return hierarchy
    cats = sorted([d for d in DATA_DIR.iterdir() if d.is_dir()])
    for c in cats:
        cat_name = c.name.split('_', 1)[-1] if '_' in c.name else c.name
        hierarchy[cat_name] = {}
        files = sorted([f for f in c.glob("*.json") if "_quiz" not in f.name])
        for f in files:
            hierarchy[cat_name][f.stem.replace('_',' ').title()] = {
                "content": f, "quiz": c / f"{f.stem}_quiz.json"
            }
    return hierarchy

# =========================
# 状态初始化
# =========================
if "idx" not in st.session_state: st.session_state.idx = 0
if "show_answer" not in st.session_state: st.session_state.show_answer = False
if "last_key" not in st.session_state: st.session_state.last_key = ""

# =========================
# 导航栏
# =========================
h = get_hierarchy()
with st.sidebar:
    st.title("📱 TOGAF Pocket")
    if not h: st.stop()
    sel_cat = st.selectbox("分类", list(h.keys()))
    sel_mod = st.radio("模块", list(h[sel_cat].keys()))
    
    # 切换模块重置
    current_key = f"{sel_cat}_{sel_mod}"
    if st.session_state.last_key != current_key:
        st.session_state.idx = 0
        st.session_state.show_answer = False
        st.session_state.last_key = current_key

    mode = st.radio("模式", ["知识卡片", "模拟测试"], horizontal=True)

paths = h[sel_cat][sel_mod]

# =========================
# 模式 1：知识卡片（点击翻面）
# =========================
if mode == "知识卡片":
    data = load_json(paths["content"])
    if data:
        item = data[st.session_state.idx % len(data)]
        st.caption(f"进度: {st.session_state.idx + 1} / {len(data)} | {sel_mod}")

        # 卡片正面：问题
        st.markdown(f"""
            <div class="card-box">
                <h4 style='color: #555;'>{item.get('topic', 'Topic')}</h4>
                <h2 style='text-align: center; margin-top: 20px;'>{item.get('question_cn', '无问题内容')}</h2>
            </div>
        """, unsafe_allow_html=True)

        # 答案区
        if st.session_state.show_answer:
            st.success(f"**答案：**\n\n{item.get('answer_cn', '暂无答案')}")
            if st.button("🙈 隐藏答案"):
                st.session_state.show_answer = False
                st.rerun()
        else:
            if st.button("💡 点击查看答案", type="primary"):
                st.session_state.show_answer = True
                st.rerun()

        st.write("---")
        # 手机端底控制栏
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️"):
                st.session_state.idx -= 1
                st.session_state.show_answer = False
                st.rerun()
        with col2:
            if st.button("🎲"):
                st.session_state.idx = random.randint(0, len(data)-1)
                st.session_state.show_answer = False
                st.rerun()
        with col3:
            if st.button("➡️"):
                st.session_state.idx += 1
                st.session_state.show_answer = False
                st.rerun()

# =========================
# 模式 2：模拟测试
# =========================
elif mode == "模拟测试":
    quiz_data = load_json(paths["quiz"])
    if quiz_data:
        q = quiz_data[st.session_state.idx % len(quiz_data)]
        st.caption(f"题目: {st.session_state.idx + 1} / {len(quiz_data)}")
        
        st.markdown(f"### {q['question']}")
        
        # 手机端为了防误触，单选也建议使用较宽的间距
        is_multi = q.get("type") == "multi"
        q_key = f"quiz_{st.session_state.idx}"
        
        if is_multi:
            ans = st.multiselect("多选", q['options'], key=q_key)
            if st.button("提交回答"):
                st.session_state.show_answer = True
        else:
            ans = st.radio("单选", q['options'], index=None, key=q_key)
            if ans: st.session_state.show_answer = True

        if st.session_state.show_answer:
            correct = q['answer']
            st.info(f"**正确答案索引：** {correct}\n\n**解析：** {q.get('explanation','')}")
            
        st.write("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("上题"):
                st.session_state.idx -= 1
                st.session_state.show_answer = False
                st.rerun()
        with col2:
             if st.button("随机"):
                st.session_state.idx = random.randint(0, len(quiz_data)-1)
                st.session_state.show_answer = False
                st.rerun()
        with c3:
            if st.button("下题"):
                st.session_state.idx += 1
                st.session_state.show_answer = False
                st.rerun()
