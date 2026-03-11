import streamlit as st
import json
import random
from pathlib import Path

# --- 页面配置 ---
st.set_page_config(page_title="TOGAF Pocket", layout="wide")

# 自定义 CSS：优化移动端按钮布局和卡片样式
st.markdown("""
    <style>
    /* 强制按钮在同一行平分宽度，并增加高度方便手指点击 */
    div[data-testid="stHorizontalBlock"] > div {
        min-width: 0px !important;
    }
    button {
        width: 100% !important;
        height: 3.5rem !important;
        padding: 0px !important;
        font-size: 16px !important;
    }
    /* 卡片显示区域样式 */
    .card-container {
        background-color: #ffffff;
        border: 2px solid #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        min-height: 180px;
    }
    /* 移动端顶部留白微调 */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    </style>
""", unsafe_allow_html=True)

DATA_DIR = Path("data")

# =========================
# 数据逻辑
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
# 状态管理
# =========================
if "idx" not in st.session_state: st.session_state.idx = 0
if "show_ans" not in st.session_state: st.session_state.show_ans = False
if "current_mod" not in st.session_state: st.session_state.current_mod = ""

# =========================
# 侧边栏导航
# =========================
h = get_hierarchy()
with st.sidebar:
    st.title("TOGAF Study")
    if not h: st.stop()
    sel_cat = st.selectbox("分类", list(h.keys()))
    sel_mod = st.radio("模块内容", list(h[sel_cat].keys()))
    
    # 模块切换重置
    if st.session_state.current_mod != f"{sel_cat}_{sel_mod}":
        st.session_state.idx = 0
        st.session_state.show_ans = False
        st.session_state.current_mod = f"{sel_cat}_{sel_mod}"

    mode = st.radio("学习模式", ["知识卡片", "模拟测试"], horizontal=True)

paths = h[sel_cat][sel_mod]

# =========================
# 模式渲染
# =========================
if mode == "知识卡片":
    data = load_json(paths["content"])
    if data:
        total = len(data)
        st.session_state.idx %= total
        item = data[st.session_state.idx]
        
        st.caption(f"进度: {st.session_state.idx + 1} / {total}")
        
        # 卡片正面：题目
        st.markdown(f"""
            <div class="card-container">
                <small style="color:gray;">{item.get('topic', 'Topic')}</small>
                <h3 style="margin-top:10px;">{item.get('question_cn', '无内容')}</h3>
            </div>
        """, unsafe_allow_html=True)

        # 答案遮盖逻辑
        if st.session_state.show_ans:
            st.info(f"**答案：**\n\n{item.get('answer_cn', '')}")
            if st.button("隐藏答案", use_container_width=True):
                st.session_state.show_ans = False
                st.rerun()
        else:
            if st.button("查看答案", type="primary", use_container_width=True):
                st.session_state.show_ans = True
                st.rerun()

        st.write("") # 间距
        
        # 三个按钮并列一行 (控制栏)
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            if st.button("上一题"):
                st.session_state.idx -= 1
                st.session_state.show_ans = False
                st.rerun()
        with btn_col2:
            if st.button("随机"):
                st.session_state.idx = random.randint(0, total - 1)
                st.session_state.show_ans = False
                st.rerun()
        with btn_col3:
            if st.button("下一题"):
                st.session_state.idx += 1
                st.session_state.show_ans = False
                st.rerun()
    else:
        st.info("该模块暂无卡片数据")

elif mode == "模拟测试":
    quiz_data = load_json(paths["quiz"])
    if quiz_data:
        total_q = len(quiz_data)
        st.session_state.idx %= total_q
        q = quiz_data[st.session_state.idx]
        
        st.caption(f"题目: {st.session_state.idx + 1} / {total_q}")
        st.markdown(f"#### {q['question']}")
        
        is_multi = q.get("type") == "multi"
        q_key = f"q_{st.session_state.idx}"
        
        if is_multi:
            ans = st.multiselect("多选", q['options'], key=q_key)
            if st.button("提交回答", use_container_width=True):
                st.session_state.show_ans = True
        else:
            ans = st.radio("单选", q['options'], index=None, key=q_key)
            if ans: st.session_state.show_ans = True

        if st.session_state.show_ans:
            st.warning(f"**正确索引：** {q['answer']}\n\n**解析：** {q.get('explanation','')}")

        st.write("")
        
        # 三个按钮并列一行 (控制栏)
        q_btn1, q_btn2, q_btn3 = st.columns(3)
        with q_btn1:
            if st.button("上一题", key="prev_q"):
                st.session_state.idx -= 1
                st.session_state.show_ans = False
                st.rerun()
        with q_btn2:
            if st.button("随机", key="rand_q"):
                st.session_state.idx = random.randint(0, total_q - 1)
                st.session_state.show_ans = False
                st.rerun()
        with q_btn3:
            if st.button("下一题", key="next_q"):
                st.session_state.idx += 1
                st.session_state.show_ans = False
                st.rerun()
    else:
        st.error("未找到测试题文件")
