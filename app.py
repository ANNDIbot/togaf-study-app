import streamlit as st
import json
import os
from pathlib import Path

# --- 页面配置 ---
st.set_page_config(page_title="TOGAF 学习助手", layout="wide")

# --- 路径配置 ---
DATA_DIR = Path("data")

# --- 核心函数 ---

def load_json(path: Path):
    """通用 JSON 加载函数"""
    if not path or not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON 格式错误: {path.name} (行 {e.lineno})")
        return []
    except Exception as e:
        st.error(f"❌ 加载失败: {str(e)}")
        return []

def scan_data_hierarchy():
    """扫描目录并构建分类层级"""
    hierarchy = {}
    if not DATA_DIR.exists():
        return hierarchy

    # 扫描子文件夹作为类别 (如 01_Standard, 02_Guides)
    categories = sorted([d for d in DATA_DIR.iterdir() if d.is_dir()])
    
    for cat_path in categories:
        # 格式化 UI 显示名
        cat_display = cat_path.name.split('_', 1)[-1] if '_' in cat_path.name else cat_path.name
        hierarchy[cat_display] = {}
        
        # 查找内容文件 (非 _quiz 结尾)
        content_files = sorted([f for f in cat_path.glob("*.json") if "_quiz" not in f.name])
        
        for cf in content_files:
            module_name = cf.stem.replace('_', ' ').title()
            quiz_file = cat_path / f"{cf.stem}_quiz.json"
            
            hierarchy[cat_display][module_name] = {
                "content": cf,
                "quiz": quiz_file if quiz_file.exists() else None
            }
    return hierarchy

# --- UI 侧边栏 ---
hierarchy = scan_data_hierarchy()

with st.sidebar:
    st.title("📚 TOGAF 备考系统")
    if not hierarchy:
        st.warning("请在 data/ 目录下创建分类文件夹。")
        st.stop()

    selected_cat = st.selectbox("选择类别", list(hierarchy.keys()))
    selected_mod_name = st.radio("选择章节", list(hierarchy[selected_cat].keys()))
    
    current_paths = hierarchy[selected_cat][selected_mod_name]
    mode = st.segment_control("学习模式", options=["知识卡片", "模拟测试"], default="知识卡片")

# --- 主界面 ---

if mode == "知识卡片":
    st.header(f"📘 {selected_mod_name} 核心知识点")
    cards_data = load_json(current_paths["content"])
    
    if not cards_data:
        st.info("该模块暂无卡片数据。")
    else:
        for card in cards_data:
            # 适配你的 Schema: topic, question_cn, answer_cn
            with st.expander(f"📌 {card.get('topic', '知识点')} - {card.get('question_cn', '')}"):
                st.markdown(f"**回答：**\n{card.get('answer_cn', '暂无内容')}")
                if 'module' in card:
                    st.caption(f"来源: {card['module']}")

elif mode == "模拟测试":
    st.header(f"📝 {selected_mod_name} 章节自测")
    if not current_paths["quiz"]:
        st.error("未找到对应的测试题文件。")
    else:
        quiz_data = load_json(current_paths["quiz"])
        
        # 初始化答题状态
        session_key = f"quiz_state_{selected_mod_name}"
        if session_key not in st.session_state:
            st.session_state[session_key] = {}

        for idx, q in enumerate(quiz_data):
            st.write(f"**Q{idx+1}: {q['question']}**")
            
            # 判断单选/多选
            is_multi = q.get('type') == 'multi'
            q_id = f"{selected_mod_name}_{idx}"
            
            if is_multi:
                user_ans = st.multiselect("多选题 (请选择所有正确项)", q['options'], key=f"select_{q_id}")
                user_indices = sorted([q['options'].index(a) for a in user_ans])
                is_correct = user_indices == sorted(q['answer'])
            else:
                user_ans = st.radio("单选题", q['options'], index=None, key=f"radio_{q_id}")
                user_index = q['options'].index(user_ans) if user_ans else -1
                is_correct = [user_index] == q['answer']

            if user_ans:
                if is_correct:
                    st.success("✅ 正确！")
                else:
                    st.error(f"❌ 错误。正确答案是: {[q['options'][i] for i in q['answer']]}")
                    st.info(f"**解析:** {q.get('explanation', '无')}")
            st.divider()
