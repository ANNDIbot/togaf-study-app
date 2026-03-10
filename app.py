import streamlit as st
import json

# --- 1. 视觉配置：极简黑白灰 ---
st.set_page_config(page_title="TOGAF 学习助手", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    /* 卡片容器样式 */
    .flashcard {
        padding: 40px;
        border: 2px solid #1a1a1a;
        background-color: #f9f9f9;
        min-height: 250px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        margin-bottom: 20px;
    }
    .topic-tag { font-size: 0.8rem; color: #666; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px; }
    .stButton>button { width: 100%; border-radius: 0px; background-color: #1a1a1a; color: white; border: none; height: 3em; }
    .stButton>button:hover { background-color: #444; color: white; }
    /* 进度条颜色 */
    .stProgress > div > div > div > div { background-color: #1a1a1a; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 数据加载 ---
@st.cache_data
def load_cards():
    try:
        with open('cards.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"加载 cards.json 失败: {e}")
        return []

all_data = load_cards()

# --- 3. 核心逻辑 ---
def main():
    st.title("⚪ TOGAF Card Study")
    
    if not all_data:
        st.info("请确保 cards.json 已上传至 GitHub 仓库根目录。")
        return

    # 侧边栏：筛选模块
    modules = sorted(list(set(card['module'] for card in all_data)))
    selected_mod = st.sidebar.selectbox("选择学习模块", ["全部"] + modules)
    
    # 过滤数据
    cards = all_data if selected_mod == "全部" else [c for c in all_data if c['module'] == selected_mod]
    
    # 初始化状态
    if 'idx' not in st.session_state: st.session_state.idx = 0
    if 'flipped' not in st.session_state: st.session_state.flipped = False

    if cards:
        # 防止越界
        st.session_state.idx %= len(cards)
        current = cards[st.session_state.idx]

        # 进度指示
        st.caption(f"模块: {current['module']} | 卡片: {st.session_state.idx + 1} / {len(cards)}")
        st.progress((st.session_state.idx + 1) / len(cards))

        # --- 卡片渲染 ---
        with st.container():
            st.markdown(f'<div class="topic-tag">{current["topic"]}</div>', unsafe_allow_html=True)
            if not st.session_state.flipped:
                # 正面：问题
                st.markdown(f'<div class="flashcard"><h3>{current["question"]}</h3><p style="color:#aaa; font-size:0.9rem;">点击“翻转”查看答案</p></div>', unsafe_allow_html=True)
            else:
                # 反面：答案
                st.markdown(f'<div class="flashcard"><h4 style="font-weight:normal;">{current["answer"]}</h4></div>', unsafe_allow_html=True)

        # --- 交互按钮 ---
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("⬅️"):
                st.session_state.idx -= 1
                st.session_state.flipped = False
                st.rerun()
        with c2:
            label = "查看答案" if not st.session_state.flipped else "显示问题"
            if st.button(label):
                st.session_state.flipped = not st.session_state.flipped
                st.rerun()
        with c3:
            if st.button("➡️"):
                st.session_state.idx += 1
                st.session_state.flipped = False
                st.rerun()
                
        # 快捷键提示
        st.sidebar.markdown("---")
        st.sidebar.caption("提示：在手机上可直接点击“查看答案”快速切换。")
    
if __name__ == "__main__":
    main()
