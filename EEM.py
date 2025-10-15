import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="光谱数据管理系统", layout="wide")
st.title("三维荧光指纹谱图库")

# ================== 初始化 ==================
columns_order = [
    "日期", "AQI", "PM2.5浓度", "O3浓度", "NOx", "VOCs", "CO",
    "Ex(nm)", "Em(nm)", "光谱峰值", "EEM谱图"
]

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=columns_order)
if "files" not in st.session_state:
    st.session_state.files = {}  # 保存上传文件对象


# ================== 表单输入区域 ==================
st.markdown("## ➕ 新增数据")  # ✅ 与“数据表”层级一致，字体更大
with st.expander("点击展开以录入新样品", expanded=True):
    with st.form("add_form", clear_on_submit=True):

        # 一级分支：基础参数
        st.markdown("#### 🧾 基础参数")  # 字体略小，用 ####
        base_cols = st.columns(7)
        with base_cols[0]:
            date = st.date_input("📅 日期")
        with base_cols[1]:
            AQI = st.number_input("AQI", min_value=0, step=1)
        with base_cols[2]:
            pm25 = st.number_input("PM₂.₅ (μg/m³)", min_value=0.0, step=0.1)
        with base_cols[3]:
            o3 = st.number_input("O₃ (μg/m³)", min_value=0.0, step=0.1)
        with base_cols[4]:
            NOx = st.number_input("NOx (ppb)", min_value=0.0, step=0.1)
        with base_cols[5]:
            VOCs = st.number_input("VOCs (ppb)", min_value=0.0, step=0.1)
        with base_cols[6]:
            CO = st.number_input("CO (ppm)", min_value=0.0, step=0.01)

        st.markdown("---")

        # 二级分支：光谱参数
        st.markdown("#### 💡 光谱参数")
        spec_cols = st.columns(4)
        with spec_cols[0]:
            ex = st.number_input("激发波长 Ex (nm)", min_value=200, max_value=600, step=1)
        with spec_cols[1]:
            em = st.number_input("发射波长 Em (nm)", min_value=250, max_value=700, step=1)
        with spec_cols[2]:
            peak = st.number_input("光谱峰值", min_value=0.0, step=0.1)
        with spec_cols[3]:
            uploaded_spectrum = st.file_uploader(
                "📎 上传光谱文件", 
                type=["csv", "txt", "xlsx"]
            )

        st.markdown("---")
        submitted = st.form_submit_button("✅ 确认提交")

        if submitted:
            if uploaded_spectrum is not None:
                # 保存文件对象
                st.session_state.files[uploaded_spectrum.name] = uploaded_spectrum

                new_entry = {
                    "日期": date,
                    "AQI": AQI,
                    "PM2.5浓度": pm25,
                    "O3浓度": o3,
                    "NOx": NOx,
                    "VOCs": VOCs,
                    "CO": CO,
                    "Ex(nm)": ex,
                    "Em(nm)": em,
                    "光谱峰值": peak,
                    "EEM谱图": uploaded_spectrum.name
                }

                st.session_state.data = pd.concat(
                    [st.session_state.data, pd.DataFrame([new_entry])],
                    ignore_index=True
                )

                st.success(f"✅ 数据已成功添加：{uploaded_spectrum.name}")
            else:
                st.warning("⚠️ 请上传光谱文件后再提交。")


# ================== 数据展示 + 删除功能 ==================
st.markdown("## 📋 数据表")  # ✅ 与“新增数据”同级标题
data_df = st.session_state.data.copy()

if not data_df.empty:
    action_col = []
    for i, row in data_df.iterrows():
        delete_button = st.button("🗑 删除", key=f"delete_{i}")
        if delete_button:
            file_name = row['EEM谱图']
            if 'files' in st.session_state and file_name in st.session_state.files:
                del st.session_state.files[file_name]
            st.session_state.data.drop(index=i, inplace=True)
            st.session_state.data.reset_index(drop=True, inplace=True)
            st.success(f"✅ 已删除样品：{file_name}")
            st.experimental_rerun()
        action_col.append("🗑 删除")

    data_df["操作"] = action_col
    st.dataframe(data_df, use_container_width=True, hide_index=True)
else:
    st.info("暂无数据，请在上方添加样品。")


# ================== 光谱图展示 ==================
if not st.session_state.data.empty:
    st.markdown("## 🔬 光谱图查看")
    selected = st.selectbox(
        "选择样品日期查看光谱", 
        st.session_state.data["日期"].astype(str).unique()
    )

    selected_row = st.session_state.data[
        st.session_state.data["日期"].astype(str) == selected
    ].iloc[0]
    spectrum_file = selected_row["EEM谱图"]

    intensity = None
    if spectrum_file in st.session_state.files:
        uploaded_file = st.session_state.files[spectrum_file]
        try:
            if spectrum_file.endswith((".csv", ".txt")):
                df = pd.read_csv(uploaded_file, header=None)
            elif spectrum_file.endswith(".xlsx"):
                df = pd.read_excel(uploaded_file, header=None)
            intensity = df.values
            ex_vals = np.linspace(200, 400, intensity.shape[1])
            em_vals = np.linspace(300, 600, intensity.shape[0])
        except Exception as e:
            st.error(f"读取光谱文件出错: {e}")
    else:
        st.info(f"请重新上传 {spectrum_file} 文件以显示光谱")

    if intensity is not None:
        fig = go.Figure(data=[go.Surface(z=intensity, x=ex_vals, y=em_vals)])
        fig.update_layout(
            scene=dict(
                xaxis_title='Ex (nm)',
                yaxis_title='Em (nm)',
                zaxis_title='强度'
            ),
            title=f"{selected} 的三维荧光光谱"
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("尚未添加任何样品数据，请在上方填写后提交。")
