import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Tushumlar Paneli", layout="wide")

# Ma'lumotlarni yuklash
cash = pd.read_excel("To'lovlar_Click to'lov amaliyoti (3).xlsx")
click = pd.read_excel("To'lovlar_Click to'lov amaliyoti.xlsx")

click_cash = pd.concat([click, cash], ignore_index=True) # adding 2 dataset using concatanate function
click_cash.head()

# UTC vaqtni Asia/Tashkent vaqt zonasiga o'zgartirish
click_cash['Tashkent_time'] = pd.to_datetime(click_cash['created_at']) \
    .dt.tz_localize('UTC') \
    .dt.tz_convert('Asia/Tashkent') \
    .dt.tz_localize(None)
# Yangi faylga yozish
click_cash.to_excel('avgusto_7.xlsx', index=False)

df = pd.read_excel("avgusto_7.xlsx")
df['date'] = pd.to_datetime(df['Tashkent_time']).dt.date
df['month'] = pd.to_datetime(df['Tashkent_time']).dt.month
df['year'] = pd.to_datetime(df['Tashkent_time']).dt.year

# Sarlavha
st.title("📊 Qurilma bo‘yicha tushumlar paneli")

# Sidebar
st.sidebar.header("🔍 Filtrlar")

devices = df['device_obj__name'].unique()
selected_devices = st.sidebar.multiselect("Qurilmani tanlang:", devices, default=devices[:1])

years = sorted(df['year'].unique())
selected_year = st.sidebar.selectbox("Yilni tanlang:", years, index=years.index(2025))

months = sorted(df['month'].unique())
selected_month = st.sidebar.selectbox("Oyni tanlang:", months, index=months.index(7))

# Filtrlash
filtered = df[
    (df['device_obj__name'].isin(selected_devices)) &
    (df['year'] == selected_year) &
    (df['month'] == selected_month)
]

# 1. Line Chart – Har kunlik tushum
st.subheader("📈 Har kunlik tushum grafigi")

if filtered.empty:
    st.warning("Tanlangan qurilmalar uchun ma'lumot topilmadi.")
else:
    line_df = filtered.groupby(['date', 'device_obj__name'])['amount'].sum().reset_index()
    line_fig = px.line(
        line_df,
        x='date',
        y='amount',
        color='device_obj__name',
        markers=True,
        labels={"amount": "Tushum (so'm)", "date": "Sana"},
        title="Tanlangan qurilmalar bo‘yicha tushumlar"
    )
    st.plotly_chart(line_fig, use_container_width=True)

# 2. Bar Chart – Jami va o‘rtacha tushum
st.subheader("📊 Qurilma bo‘yicha umumiy va o‘rtacha tushum")

if not filtered.empty:
    summary = filtered.groupby('device_obj__name').agg(
        jami_tushum=('amount', 'sum'),
        ortacha_kunlik=('amount', lambda x: round(x.sum() / 31, 2))
    ).reset_index()

    bar_fig = px.bar(
        summary.melt(id_vars='device_obj__name', var_name='Ko‘rsatkich', value_name='So‘m'),
        x='device_obj__name',
        y='So‘m',
        color='Ko‘rsatkich',
        barmode='group',
        labels={"device_obj__name": "Qurilma"},
        title="Jami va o‘rtacha tushumlar"
    )
    st.plotly_chart(bar_fig, use_container_width=True)

    # 3. Jadval
    st.subheader("📋 Statistika jadvali")
    st.dataframe(summary)

    # 4. Yuklab olish
    csv = summary.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Statistika faylini yuklab olish (CSV)",
        data=csv,
        file_name='qurilma_tushum_statistika.csv',
        mime='text/csv',
    )
