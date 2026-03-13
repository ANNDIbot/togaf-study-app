import streamlit as st
import json
import random
from pathlib import Path

# --- 页面配置 ---
st.set_page_config(page_title="TOGAF 学习助手", layout="wide")

# 针对移动端和 UI 样式的深度优化
st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"] > div {
        min-width: 0px !important;
    }
    .stButton button {
        width: 100% !important;
        height: 3.5rem !important;
        font-size: 16px !important;
    }
    [data-testid="stCheckbox"] {
        margin-bottom: -15px !important;
        padding: 5px 0 !important;
    }
    .card-box {
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

# =========================
# 密码保护逻辑（整合 Secrets）
# =========================
def check_password():
    """如果密码正确则返回 True，否则显示输入框"""
    def password_entered():
        """从密钥库读取密码并验证"""
        # 优先读取名为 APP_PASSWORD 的 Secret，读不到则默认使用 0602aw
        correct_password = st.secrets.get("APP_PASSWORD")
        
        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # 安全起见，删除明文密码
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # 初始进入，显示输入界面
        st.title("🔒 TOGAF 学习系统")
        st.text_input(
            "请输入访问密码以继续", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # 密码错误，重新显示输入并提示
        st.title("🔒 TOGAF 学习系统")
        st.text_input(
            "请输入访问密码以继续", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.error("😕 密码错误，请重试")
        return False
    else:
        # 验证通过
        return True

# =========================
# 核心数据处理逻辑
# =========================
DATA_DIR = Path("data")

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
    if not DATA_DIR.exists():
        return hierarchy
    
    categories = sorted([d for d in DATA_DIR.iterdir() if d.is_dir()])
    for cat_path in categories:
        cat_display = cat_path.name.split('_', 1)[-1] if '_' in cat_path.name else cat_path.name
        hierarchy[cat_display] = {}
        all_jsons = list(cat_path.glob("*.json"))
        content_files = sorted([f for f in all_jsons if "_quiz" not in f.name])
        for cf in content_files:
            mod_display = cf.stem.replace('_', ' ').strip().title()
            potential_quiz = cat_path / f"{cf.stem}_quiz.json"
            hierarchy[cat_display][mod_display] = {
                "content": cf,
                "quiz": potential_quiz if potential_quiz.exists() else None
            }
    return hierarchy

# =========================
# 学习页面 UI
# =========================
def main_app():
    # 初始化状态
    if "card_idx" not in st.session_state: st.session_state.card_idx = 0
    if "quiz_idx" not in st.session_state: st.session_state.quiz_idx = 0
    if "show_answer" not in st.session_state: st.session_state.show_answer = False
    if "user_ans" not in st.session_state: st.session_state.user_ans = None
    if "last_mod" not in st.session_state: st.session_state.last_mod = ""

    # 加载目录
    hierarchy = get_hierarchy()

    with st.sidebar:
        st.title("TOGAF Study")
        if not hierarchy:
            st.error("未发现数据！")
            st.stop()
        
        sel_cat = st.selectbox("分类", list(hierarchy.keys()))
        mod_options = list(hierarchy[sel_cat].keys())
        sel_mod = st.radio("模块内容", mod_options)
        
        # 模块切换重置状态
        current_key = f"{sel_cat}_{sel_mod}"
        if current_key != st.session_state.last_mod:
            st.session_state.card_idx = 0
            st.session_state.quiz_idx = 0
            st.session_state.show_answer = False
            st.session_state.user_ans = None
            st.session_state.last_mod = current_key

        st.divider()
        mode = st.radio("模式", ["知识卡片", "模拟测试"], horizontal=True)
        
        if st.button("退出登录"):
            st.session_state.clear()
            st.rerun()

    paths = hierarchy[sel_cat][sel_mod]

    # --- 知识卡片模式 ---
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
                    if st.button("查看答案", type="primary", use_container_width=True):
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
                    st.session_state.card_idx = random.randint(0, total-1)
                    st.session_state.show_answer = False
                    st.rerun()
            with c3:
                if st.button("下一题"):
                    st.session_state.card_idx += 1
                    st.session_state.show_answer = False
                    st.rerun()
        else:
            st.info("暂无卡片数据")

    # --- 模拟测试模式 ---
    elif mode == "模拟测试":
        quiz_data = load_json(paths["quiz"])
        if quiz_data:
            total_q = len(quiz_data)
            st.session_state.quiz_idx %= total_q
            q = quiz_data[st.session_state.quiz_idx]
            st.caption(f"进度: {st.session_state.quiz_idx + 1} / {total_q}")
            
            with st.container(border=True):
                st.markdown(f"### {q['question']}")
                is_multi = q.get("type") == "multi" or len(q.get("answer", [])) > 1
                q_key = f"q_{st.session_state.last_mod}_{st.session_state.quiz_idx}"
                
                if is_multi:
                    selected = []
                    for i, opt in enumerate(q['options']):
                        if st.checkbox(opt, key=f"{q_key}_cb_{i}", disabled=st.session_state.show_answer):
                            selected.append(i)
                    if not st.session_state.show_answer:
                        if st.button("确认提交", type="primary", use_container_width=True):
                            st.session_state.user_ans = sorted(selected)
                            st.session_state.show_answer = True
                            st.rerun()
                else:
                    choice = st.radio("选项", q['options'], index=None, key=f"{q_key}_rad", disabled=st.session_state.show_answer)
                    if choice is not None and not st.session_state.show_answer:
                        st.session_state.user_ans = [q['options'].index(choice)]
                        st.session_state.show_answer = True
                        st.rerun()

                if st.session_state.show_answer:
                    is_correct = sorted(st.session_state.user_ans or []) == sorted(q['answer'])
                    if is_correct: st.success("回答正确")
                    else: st.error("回答错误")
                    
                    st.warning(f"**正确答案：** {', '.join([q['options'][i] for i in q['answer']])}")
                    st.write(f"**解析：** {q.get('explanation', '无')}")

            st.write("")
            q1, q2, q3 = st.columns(3)
            with q1:
                if st.button("上一题", key="q_prev"):
                    st.session_state.quiz_idx -= 1
                    st.session_state.show_answer = False
                    st.rerun()
            with q2:
                if st.button("随机", key="q_rand"):
                    st.session_state.quiz_idx = random.randint(0, total_q-1)
                    st.session_state.show_answer = False
                    st.rerun()
            with q3:
                if st.button("下一题", key="q_next"):
                    st.session_state.quiz_idx += 1
                    st.session_state.show_answer = False
                    st.rerun()
        else:
            st.warning("暂无测试题")

# =========================
# 启动程序
# =========================
if check_password():
    main_app()
