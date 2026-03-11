import streamlit as st
import json
import os
import random
from pathlib import Path

# --- 页面配置 ---
st.set_page_config(
    page_title="TOGAF 学习助手",
    page_icon="📘",
    layout="wide"
)

DATA_DIR = Path("data")

# =========================
# 工具函数
# =========================
def load_json(path: Path):
    """通用的 JSON 加载函数，带有格式错误提示"""
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON 格式错误: {path.name} (第 {e.lineno} 行附近有误，通常是漏掉逗号)")
        return []
    except Exception as e:
        st.error(f"❌ 加载失败: {str(e)}")
        return []

def get_data_hierarchy():
    """扫描 data 目录构建分类层级"""
    hierarchy = {}
    if not DATA_DIR.exists():
        os.makedirs(DATA_DIR)
        return hierarchy

    # 扫描子文件夹并排序
    categories = sorted([d for d in DATA_DIR.iterdir() if d.is_dir()])
    
    for cat_path in categories:
        # 格式化 UI 显示名: 去掉 01_ 这种前缀
        cat_display = cat_path.name.split('_', 1)[-1] if '_' in cat_path.name else cat_path.name
        hierarchy[cat_display] = {}
        
        # 寻找内容文件
        content_files = sorted([f for f in cat_path.glob("*.json") if "_quiz" not in f.name])
        
        for cf in content_files:
            # 模块显示名
            mod_display = cf.stem.replace('_', ' ').title()
            quiz_path = cat_path / f"{cf.stem}_quiz.json"
            
            hierarchy[cat_display][mod_display] = {
                "content": cf,
                "quiz": quiz_path if quiz_path.exists() else None
            }
    return hierarchy

# =========================
# 侧边栏导航
# =========================
hierarchy = get_data_hierarchy()

with st.sidebar:
    st.title("📚 TOGAF 备考系统")
    
    if not hierarchy:
        st.info("请在 data/ 目录下创建分类文件夹（如 01_Standard）。")
        st.stop()

    # 第一级：类别选择
    selected_cat = st.selectbox("1️⃣ 选择知识类别", list(hierarchy.keys()))
    
    # 第二级：章节选择
    modules = hierarchy[selected_cat]
    selected_mod_name = st.radio("2️⃣ 选择学习章节", list(modules.keys()))
    
    current_paths = modules[selected_mod_name]
    
    st.divider()
    
    # 模式选择 (方案 A：使用 radio 替代 segment_control)
    mode = st.radio("🛠️ 模式切换", ["知识卡片", "模拟测试"], horizontal=True)

# =========================
# 主界面逻辑
# =========================

if mode == "知识卡片":
    st.header(f"📘 {selected_mod_name} - 核心知识点")
    cards = load_json(current_paths["content"])
    
    if not cards:
        st.warning("该模块暂无卡片数据。")
    else:
        st.info(f"共加载 {len(cards)} 个知识点")
        for card in cards:
            # 适配 Schema: topic, question_cn, answer_cn
            topic = card.get("topic", "未命名知识点")
            q_cn = card.get("question_cn", "")
            a_cn = card.get("answer_cn", "暂无内容")
            
            with st.expander(f"📌 {topic}：{q_cn}"):
                st.markdown(f"**知识解析：**\n\n{a_cn}")
                if "module" in card:
                    st.caption(f"来源：{card['module']}")

elif mode == "模拟测试":
    st.header(f"📝 {selected_mod_name} - 章节自测")
    
    if not current_paths["quiz"]:
        st.error("⚠️ 未找到该模块的测试题文件 (_quiz.json)")
    else:
        quiz_data = load_json(current_paths["quiz"])
        
        if not quiz_data:
            st.warning("测试题内容为空。")
        else:
            # 答题逻辑：逐题显示并立即反馈
            for idx, q in enumerate(quiz_data):
                st.subheader(f"Q{idx+1}: {q['question']}")
                
                # 判定单选/多选
                is_multi = q.get("type") == "multi"
                q_key = f"q_{selected_mod_name}_{idx}" # 唯一标识符防止串题
                
                if is_multi:
                    user_ans = st.multiselect("请选择所有正确答案 (多选)", q['options'], key=f"sel_{q_key}")
                    # 将用户选择的内容转为索引列表进行对比
                    user_indices = sorted([q['options'].index(a) for a in user_ans])
                    is_correct = user_indices == sorted(q['answer'])
                else:
                    user_ans = st.radio("请选择正确答案 (单选)", q['options'], index=None, key=f"rad_{q_key}")
                    user_index = q['options'].index(user_ans) if user_ans else -1
                    is_correct = [user_index] == q['answer']

                # 如果用户已经做了选择，则显示反馈
                if user_ans:
                    if is_correct:
                        st.success("✅ 正确")
                    else:
                        # 转换答案索引为文字显示
                        correct_text = [q['options'][i] for i in q['answer']]
                        st.error(f"❌ 错误。正确答案是: {', '.join(correct_text)}")
                        if q.get("explanation"):
                            st.info(f"**解析:** {q['explanation']}")
                st.divider()

            # 底部进度提示
            st.caption(f"到底啦！本次测试共 {len(quiz_data)} 道题。")
