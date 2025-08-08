import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz

# ---- PAGE CONFIG ----
st.set_page_config(page_title="Merchant Statistic", layout="wide")

# ---- HEADER ----
col1, col2 = st.columns([1, 6])
with col1:
    st.image("download.jpeg", width=50)
with col2:
    st.markdown("<h1 style='text-align: left; font-weight:bold;'>Merchant Statistic</h1>", unsafe_allow_html=True)

# ---- SIDEBAR ----
st.sidebar.header("📂 Ma'lumot yuklash")
uploaded_files = st.sidebar.file_uploader("Excel fayllarni yuklang", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    dfs = []
    for file in uploaded_files:
        df_temp = pd.read_excel(file)
        dfs.append(df_temp)
    df = pd.concat(dfs, ignore_index=True)

    # ---- UTC -> Tashkent ----
    df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
    df['created_at'] = df['created_at'].dt.tz_convert('Asia/Tashkent').dt.tz_localize(None)

    # Extract date parts
    df['date'] = df['created_at'].dt.date

    # ---- FILTERS ----
    filial_list = df['device_obj__company__name'].dropna().unique()
    filial_selected = st.sidebar.multiselect("Filialni tanlang:", filial_list, default=filial_list)

    # 📦 Box filter
    box_list = df['device_obj__name'].dropna().unique()
    box_selected = st.sidebar.multiselect("Boxni tanlang:", box_list, default=box_list)

    start_date = st.sidebar.date_input("Boshlanish sanasi", df['date'].min())
    end_date = st.sidebar.date_input("Tugash sanasi", df['date'].max())

    # ---- DATA FILTER ----
    filtered_df = df[
        (df['device_obj__company__name'].isin(filial_selected)) &
        (df['device_obj__name'].isin(box_selected)) &
        (df['date'] >= start_date) & (df['date'] <= end_date)
    ]

    st.markdown("## 📊 Filial bo‘yicha tahlillar")

    # --- 1. BAR CHART: Filial bo‘yicha jami tushum ---
    filial_summary = filtered_df.groupby('device_obj__company__name')['amount'].sum().reset_index()
    bar_fig = px.bar(filial_summary, x='device_obj__company__name', y='amount',
                     title="Jami tushum (Filial bo‘yicha)", color='device_obj__company__name')
    st.plotly_chart(bar_fig, use_container_width=True)

    # --- 2. LINE CHART: Kunlik tushum ---
    daily_filial = filtered_df.groupby(['date', 'device_obj__company__name'])['amount'].sum().reset_index()
    line_fig = px.line(daily_filial, x='date', y='amount', color='device_obj__company__name',
                       title="Kunlik tushum (Filial bo‘yicha)", markers=True)
    st.plotly_chart(line_fig, use_container_width=True)

    # --- 3. PIE CHART: Filial ulushi ---
    filial_pie = filial_summary.copy()
    filial_pie['box_soni'] = filtered_df.groupby('device_obj__company__name')['device_obj__name'].nunique().values
    pie_fig = px.pie(filial_pie, names='device_obj__company__name', values='amount',
                     title="Filial ulushi", hole=0.4)
    st.plotly_chart(pie_fig, use_container_width=True)

    # ---- BOX BO‘YICHA TAHLIL ----
    st.markdown("## 📦 Box bo‘yicha tahlillar")

    # KPI - jami tushum va o‘rtacha box tushumi
    total_amount = filtered_df['amount'].sum()
    avg_amount = filtered_df.groupby('device_obj__name')['amount'].mean().mean()

    st.metric("Jami tushum", f"{total_amount:,.0f} so'm")
    st.metric("O‘rtacha box tushumi", f"{avg_amount:,.0f} so'm")

    # --- BOX Bar Chart ---
    box_summary = filtered_df.groupby('device_obj__name')['amount'].sum().reset_index()
    box_bar = px.bar(box_summary, x='device_obj__name', y='amount',
                     title="Box bo‘yicha jami tushum", color='device_obj__name')
    st.plotly_chart(box_bar, use_container_width=True)

    # --- BOX Line Chart ---
    daily_box = filtered_df.groupby(['date', 'device_obj__name'])['amount'].sum().reset_index()
    box_line = px.line(daily_box, x='date', y='amount', color='device_obj__name',
                       title="Box bo‘yicha kunlik tushum", markers=True)
    st.plotly_chart(box_line, use_container_width=True)

    # --- BOX Pie Chart ---
    box_pie = px.pie(box_summary, names='device_obj__name', values='amount',
                     title="Box ulushi", hole=0.4)
    st.plotly_chart(box_pie, use_container_width=True)

    # ---- CSV YUKLASH ----
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Natijalarni yuklab olish (CSV)", csv, "statistika.csv", "text/csv")
else:
    st.warning("Iltimos, kamida bitta Excel fayl yuklang.")
