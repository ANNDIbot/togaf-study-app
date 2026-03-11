import streamlit as st
import json
import random
from pathlib import Path

# --- 页面配置 ---
st.set_page_config(page_title="TOGAF 学习助手", layout="wide")

# 针对移动端和深浅色模式的适配
st.markdown("""
    <style>
    /* 强制按钮在移动端横向平分宽度 */
    div[data-testid="stHorizontalBlock"] > div {
        min-width: 0px !important;
    }
    .stButton button {
        width: 100% !important;
        height: 3.5rem !important;
        font-size: 16px !important;
    }
    /* 卡片样式：支持深浅模式自适应 */
    .card-container {
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        margin-bottom: 1rem;
        min-height: 150px;
    }
    </style>
""", unsafe_allow_html=True)

DATA_DIR = Path("data")

# =========================
# 数据加载与层级扫描
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
    # 扫描子文件夹作为类别
    cats = sorted([d for d in DATA_DIR.iterdir() if d.is_dir()])
    for c_path in cats:
        cat_name = c_path.name.split('_', 1)[-1] if '_' in c_path.name else c_path.name
        hierarchy[cat_name] = {}
        # 匹配内容文件
        files = sorted([f for f in c_path.glob("*.json") if "_quiz" not in f.name])
        for f in files:
            mod_display = f.stem.replace('_', ' ').title()
            hierarchy[cat_name][mod_display] = {
                "content": f, "quiz": c_path / f"{f.stem}_quiz.json"
            }
    return hierarchy

# =========================
# 状态初始化
# =========================
if "idx" not in st.session_state: st.session_state.idx = 0
if "show_ans" not in st.session_state: st.session_state.show_ans = False
if "current_key" not in st.session_state: st.session_state.current_key = ""

# =========================
# 侧边栏
# =========================
h = get_hierarchy()
with st.sidebar:
    st.title("TOGAF Study App")
    if not h: st.stop()
    sel_cat = st.selectbox("选择类别", list(h.keys()))
    sel_mod = st.radio("选择章节", list(h[sel_cat].keys()))
    
    # 切换模块时重置状态
    this_key = f"{sel_cat}_{sel_mod}"
    if st.session_state.current_key != this_key:
        st.session_state.idx = 0
        st.session_state.show_ans = False
        st.session_state.current_key = this_key

    mode = st.radio("学习模式", ["知识卡片", "模拟测试"], horizontal=True)

paths = h[sel_cat][sel_mod]

# =========================
# 知识卡片模式（点击翻面）
# =========================
if mode == "知识卡片":
    data = load_json(paths["content"])
    if data:
        total = len(data)
        st.session_state.idx %= total
        item = data[st.session_state.idx]
        
        st.caption(f"进度: {st.session_state.idx + 1} / {total}")
        
        # 1. 题目显示（卡片形式）
        with st.container(border=True):
            st.write(f"**Topic: {item.get('topic', '')}**")
            st.markdown(f"### {item.get('question_cn', '')}")
            
            st.divider()
            
            # 2. 答案遮罩逻辑
            if st.session_state.show_ans:
                st.info(f"**回答：**\n\n{item.get('answer_cn', '')}")
                if st.button("隐藏答案", use_container_width=True):
                    st.session_state.show_ans = False
                    st.rerun()
            else:
                if st.button("查看答案", type="primary", use_container_width=True):
                    st.session_state.show_ans = True
                    st.rerun()

        # 3. 三按钮并列一行
        st.write("")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("上一题"):
                st.session_state.idx -= 1
                st.session_state.show_ans = False
                st.rerun()
        with c2:
            if st.button("随机"):
                st.session_state.idx = random.randint(0, total - 1)
                st.session_state.show_ans = False
                st.rerun()
        with c3:
            if st.button("下一题"):
                st.session_state.idx += 1
                st.session_state.show_ans = False
                st.rerun()
    else:
        st.info("该模块暂无卡片数据")

# =========================
# 模拟测试模式（多选识别修复）
# =========================
elif mode == "模拟测试":
    q_data = load_json(paths["quiz"])
    if q_data:
        total_q = len(q_data)
        st.session_state.idx %= total_q
        q = q_data[st.session_state.idx]
        
        st.caption(f"题目: {st.session_state.idx + 1} / {total_q}")
        
        with st.container(border=True):
            st.markdown(f"### {q['question']}")
            
            is_multi = q.get("type") == "multi"
            q_key = f"quiz_{st.session_state.idx}"
            
            if is_multi:
                selected = st.multiselect("多项选择（选择所有正确项）", q['options'], key=q_key)
                # 修复多选识别逻辑：先将选中的文字转为索引，再排序后对比
                user_indices = sorted([q['options'].index(s) for s in selected])
                correct_indices = sorted(q['answer'])
                is_correct = (user_indices == correct_indices)
                
                if st.button("提交回答", use_container_width=True):
                    st.session_state.show_ans = True
            else:
                selected = st.radio("单项选择", q['options'], index=None, key=q_key)
                user_idx = [q['options'].index(selected)] if selected else []
                is_correct = (user_idx == q['answer'])
                if selected: st.session_state.show_ans = True

            if st.session_state.show_ans:
                if is_correct:
                    st.success("回答正确")
                else:
                    st.error(f"回答错误。正确答案索引: {q['answer']}")
                
                with st.expander("查看解析", expanded=True):
                    st.write(q.get("explanation", "暂无解析"))

        # 底部控制栏
        st.write("")
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("上一题", key="q_p"):
                st.session_state.idx -= 1
                st.session_state.show_ans = False
                st.rerun()
        with b2:
            if st.button("随机", key="q_r"):
                st.session_state.idx = random.randint(0, total_q - 1)
                st.session_state.show_ans = False
                st.rerun()
        with b3:
            if st.button("下一题", key="q_n"):
                st.session_state.idx += 1
                st.session_state.show_ans = False
                st.rerun()
    else:
        st.warning("暂无自测题数据")
