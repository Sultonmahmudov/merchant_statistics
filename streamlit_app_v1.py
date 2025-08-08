import streamlit as st
import pandas as pd
import plotly.express as px
import calendar

st.set_page_config(page_title="Tushumlar Paneli", layout="wide")

st.title("📊 Qurilma bo‘yicha tushumlar paneli")

# Excel fayl yuklash
uploaded_files = st.sidebar.file_uploader(
    "📤 Excel fayllarni yuklang (bir nechta tanlash mumkin)", 
    type=["xlsx"], 
    accept_multiple_files=True
)

if uploaded_files:
    # Barcha fayllarni o‘qish va birlashtirish
    dfs = [pd.read_excel(file) for file in uploaded_files]
    click_cash = pd.concat(dfs, ignore_index=True)

    # UTC → Tashkent
    click_cash['Tashkent_time'] = pd.to_datetime(click_cash['created_at']) \
        .dt.tz_localize('UTC') \
        .dt.tz_convert('Asia/Tashkent') \
        .dt.tz_localize(None)

    # Sana ustunlari
    click_cash['date'] = click_cash['Tashkent_time'].dt.date
    click_cash['month'] = click_cash['Tashkent_time'].dt.month
    click_cash['year'] = click_cash['Tashkent_time'].dt.year

    # Sidebar filtrlari
    st.sidebar.header("🔍 Filtrlar")
    devices = click_cash['device_obj__name'].unique()
    selected_devices = st.sidebar.multiselect("Qurilmani tanlang:", devices, default=devices[:1])

    years = sorted(click_cash['year'].unique())
    selected_year = st.sidebar.selectbox("Yilni tanlang:", years)

    months = sorted(click_cash['month'].unique())
    selected_month = st.sidebar.selectbox("Oyni tanlang:", months)

    # Filtrlash
    filtered = click_cash[
        (click_cash['device_obj__name'].isin(selected_devices)) &
        (click_cash['year'] == selected_year) &
        (click_cash['month'] == selected_month)
    ]

    if filtered.empty:
        st.warning("Tanlangan qurilmalar uchun ma'lumot topilmadi.")
    else:
        # Kunlar soni
        days_in_month = calendar.monthrange(selected_year, selected_month)[1]

        # 📈 Har kunlik tushum
        st.subheader("📈 Har kunlik tushum grafigi")
        line_df = filtered.groupby(['date', 'device_obj__name'])['amount'].sum().reset_index()
        line_fig = px.line(
            line_df,
            x='date', y='amount', color='device_obj__name',
            markers=True,
            labels={"amount": "Tushum (so'm)", "date": "Sana"},
            title="Tanlangan qurilmalar bo‘yicha tushumlar"
        )
        st.plotly_chart(line_fig, use_container_width=True)

        # 📊 Jami va o‘rtacha tushum
        st.subheader("📊 Qurilma bo‘yicha umumiy va o‘rtacha tushum")
        summary = filtered.groupby('device_obj__name').agg(
            jami_tushum=('amount', 'sum'),
            ortacha_kunlik=('amount', lambda x: round(x.sum() / days_in_month, 2))
        ).reset_index()

        bar_fig = px.bar(
            summary.melt(id_vars='device_obj__name', var_name='Ko‘rsatkich', value_name='So‘m'),
            x='device_obj__name', y='So‘m',
            color='Ko‘rsatkich', barmode='group',
            labels={"device_obj__name": "Qurilma"},
            title="Jami va o‘rtacha tushumlar"
        )
        st.plotly_chart(bar_fig, use_container_width=True)

        # 🥧 Pie chart — ulushlar
        st.subheader("🥧 Qurilma bo‘yicha tushum ulushi")
        pie_fig = px.pie(
            summary,
            values='jami_tushum',
            names='device_obj__name',
            title="Qurilma bo‘yicha tushum foizi"
        )
        st.plotly_chart(pie_fig, use_container_width=True)

        # 📋 Statistika jadvali
        st.subheader("📋 Statistika jadvali")
        st.dataframe(summary)

        # 📥 CSV yuklab olish
        csv = summary.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Statistika faylini yuklab olish (CSV)",
            data=csv,
            file_name='qurilma_tushum_statistika.csv',
            mime='text/csv',
        )
else:
    st.info("Iltimos, chap tomondan Excel fayllarni yuklang.")
