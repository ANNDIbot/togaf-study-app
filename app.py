import streamlit as st
import json
import os
from pathlib import Path

# --- 页面配置 ---
st.set_page_config(page_title="TOGAF 学习助手专业版", layout="wide", initial_sidebar_state="expanded")

# --- 路径配置 ---
DATA_DIR = Path("data")

# --- 核心函数 ---

def load_json(path: Path):
    """通用 JSON 加载函数，带有详细报错提示"""
    if not path or not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON 格式错误: {path.name} (行 {e.lineno}, 列 {e.colno})")
        return []
    except Exception as e:
        st.error(f"❌ 无法读取文件 {path.name}: {str(e)}")
        return []

def scan_data_hierarchy():
    """
    扫描 data 目录构建层级结构：
    { "分类名称": { "模块名称": {"content": Path, "quiz": Path} } }
    """
    hierarchy = {}
    if not DATA_DIR.exists():
        os.makedirs(DATA_DIR)
        return hierarchy

    # 获取所有子文件夹并排序（支持 01_xxx 格式排序）
    categories = sorted([d for d in DATA_DIR.iterdir() if d.is_dir()])
    
    for cat_path in categories:
        # 格式化分类显示名：去掉数字前缀，如下划线后的部分
        cat_display_name = cat_path.name.split('_', 1)[-1] if '_' in cat_path.name else cat_path.name
        hierarchy[cat_display_name] = {}
        
        # 查找该目录下所有的内容文件 (排除带 _quiz 的)
        content_files = sorted(list(cat_path.glob("*.json")))
        modules = [f for f in content_files if "_quiz" not in f.name]
        
        for cf in modules:
            module_key = cf.stem  # 文件名去掉后缀
            display_name = module_key.replace('_', ' ').title()
            
            # 自动匹配对应的测试题文件
            quiz_file = cat_path / f"{module_key}_quiz.json"
            
            hierarchy[cat_display_name][display_name] = {
                "content": cf,
                "quiz": quiz_file if quiz_file.exists() else None
            }
    return hierarchy

# --- 初始化数据结构 ---
hierarchy = scan_data_hierarchy()

# --- 侧边栏导航 ---
with st.sidebar:
    st.title("🚀 TOGAF 备考系统")
    
    if not hierarchy:
        st.info("请在 data/ 目录下创建子文件夹并放入 JSON 文件。")
        st.stop()

    # 1. 选择大类 (例如：Standard ADM 或 Series Guides)
    all_categories = list(hierarchy.keys())
    selected_cat = st.selectbox("📚 选择知识类别", all_categories)

    # 2. 选择具体模块 (例如：Module 1 或 Guide 1)
    modules_in_cat = hierarchy[selected_cat]
    selected_mod_name = st.radio("📖 选择学习章节", list(modules_in_cat.keys()))
    
    current_paths = modules_in_cat[selected_mod_name]

    st.divider()
    
    # 3. 学习模式切换
    mode = st.radio("🛠️ 学习模式", ["知识卡片 (Cards)", "模拟测试 (Quiz)"])

# --- 主界面内容 ---

if mode == "知识卡片 (Cards)":
    st.header(f"📘 {selected_mod_name} 核心要点")
    cards_data = load_json(current_paths["content"])
    
    if not cards_data:
        st.warning("该模块暂无知识卡片。")
    else:
        st.info(f"本章节共包含 {len(cards_data)} 个关键知识点")
        for i, card in enumerate(cards_data):
            with st.expander(f"要点 {i+1}: {card.get('title', card.get('question', '未命名知识点'))}"):
                # 兼容不同格式的 JSON 字段
                content = card.get('content') or card.get('explanation')
                st.markdown(content)
                if 'example' in card:
                    st.caption(f"**案例/补充:** {card['example']}")

elif mode == "模拟测试 (Quiz)":
    st.header(f"📝 {selected_mod_name} 章节自测")
    
    if not current_paths["quiz"]:
        st.error("⚠️ 未找到该模块对应的测试题文件 (_quiz.json)。")
    else:
        quiz_data = load_json(current_paths["quiz"])
        
        if not quiz_data:
            st.warning("测试题内容为空。")
        else:
            # 答题逻辑初始化
            if f"quiz_{selected_mod_name}" not in st.session_state:
                st.session_state[f"quiz_{selected_mod_name}"] = [None] * len(quiz_data)

            # 渲染题目
            correct_count = 0
            for idx, item in enumerate(quiz_data):
                st.subheader(f"Q{idx+1}: {item['question']}")
                
                # 判定单选还是多选
                is_multi = item.get('type') == 'multi'
                
                if is_multi:
                    ans = st.multiselect(f"选择正确答案 (多选) - ID: {item['id']}", 
                                         item['options'], key=f"q_{selected_mod_name}_{idx}")
                    # 将选择的索引转为列表与 answer 对比
                    user_indices = sorted([item['options'].index(a) for a in ans])
                    is_correct = user_indices == sorted(item['answer'])
                else:
                    ans = st.radio(f"选择正确答案 (单选) - ID: {item['id']}", 
                                   item['options'], index=None, key=f"q_{selected_mod_name}_{idx}")
                    user_index = item['options'].index(ans) if ans else -1
                    is_correct = [user_index] == item['answer']

                # 显示反馈
                if ans:
                    if is_correct:
                        st.success("✅ 正确")
                        correct_count += 1
                    else:
                        st.error(f"❌ 错误。正确答案索引为: {item['answer']}")
                        st.info(f"**解析:** {item.get('explanation', '无')}")
                st.divider()

            # 计分板
            st.sidebar.metric("当前得分", f"{correct_count}/{len(quiz_data)}")
            if correct_count == len(quiz_data) and len(quiz_data) > 0:
                st.balloons()
