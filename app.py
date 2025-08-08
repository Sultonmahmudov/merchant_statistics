import dash
from dash import dcc, html, Output, Input
import pandas as pd
import plotly.graph_objs as go

# Ma'lumotlarni yuklash
cash = pd.read_excel("To'lovlar_Naqt to'lov amaliyoti.xlsx")
click = pd.read_excel("To'lovlar_Click to'lov amaliyoti.xlsx")

click_cash = pd.concat([click, cash], ignore_index=True) # adding 2 dataset using concatanate function
click_cash.head()

# UTC vaqtni Asia/Tashkent vaqt zonasiga o'zgartirish
click_cash['Tashkent_time'] = pd.to_datetime(click_cash['created_at']) \
    .dt.tz_localize('UTC') \
    .dt.tz_convert('Asia/Tashkent') \
    .dt.tz_localize(None)

# Yangi faylga yozish
click_cash.to_excel('iyun_iyul_stat.xlsx', index=False)


df = pd.read_excel("iyun_iyul_stat.xlsx")
df['date'] = pd.to_datetime(df['Tashkent_time']).dt.date
df['month'] = pd.to_datetime(df['Tashkent_time']).dt.month
df['year'] = pd.to_datetime(df['Tashkent_time']).dt.year

# Qurilmalar ro'yxati
devices = df['device_obj__name'].unique()

# App
app = dash.Dash(__name__)
app.title = "Tushumlar Paneli"

app.layout = html.Div([
    html.Div([
        html.H2("📊 Filtrlar", style={'textAlign': 'center'}),
        html.Label("Qurilmani tanlang:"),
        dcc.Dropdown(
            options=[{'label': d, 'value': d} for d in devices],
            id='device-dropdown',
            multi=True,
            value=[devices[0]]
        ),
        html.Br(),
        html.Label("Yilni tanlang:"),
        dcc.Dropdown(
            options=[{'label': str(y), 'value': y} for y in sorted(df['year'].unique())],
            id='year-dropdown',
            value=2025
        ),
        html.Br(),
        html.Label("Oyni tanlang:"),
        dcc.Dropdown(
            options=[{'label': f"{m}-oy", 'value': m} for m in sorted(df['month'].unique())],
            id='month-dropdown',
            value=7
        ),
    ], style={'width': '20%', 'float': 'left', 'padding': '20px'}),

    html.Div([
        html.H2("📈 Har kunlik tushum grafigi", style={'textAlign': 'center'}),
        dcc.Graph(id='line-chart'),
        html.H2("📊 Qurilma bo‘yicha umumiy tushum (bar chart)", style={'textAlign': 'center'}),
        dcc.Graph(id='bar-chart'),
    ], style={'width': '75%', 'float': 'right', 'padding': '20px'})
])

@app.callback(
    [Output('line-chart', 'figure'),
     Output('bar-chart', 'figure')],
    [Input('device-dropdown', 'value'),
     Input('month-dropdown', 'value'),
     Input('year-dropdown', 'value')]
)
def update_charts(selected_devices, selected_month, selected_year):
    filtered = df[(df['device_obj__name'].isin(selected_devices)) &
                  (df['month'] == selected_month) &
                  (df['year'] == selected_year)]

    # Har kunlik tushum line chart
    line_fig = go.Figure()
    for device in selected_devices:
        device_df = filtered[filtered['device_obj__name'] == device]
        daily_sum = device_df.groupby('date')['amount'].sum()
        line_fig.add_trace(go.Scatter(
            x=daily_sum.index,
            y=daily_sum.values,
            mode='lines+markers',
            name=device
        ))
    line_fig.update_layout(
        xaxis_title='Sana',
        yaxis_title="Tushum (so'm)",
        hovermode='x',
        template='plotly_white'
    )

    # Bar chart – Jami va o‘rtacha tushum
    summary = filtered.groupby('device_obj__name').agg(
        total_amount=('amount', 'sum'),
        avg_daily_amount=('amount', lambda x: round(x.sum() / 31, 2))
    ).reset_index()

    bar_fig = go.Figure(data=[
        go.Bar(name='Jami tushum', x=summary['device_obj__name'], y=summary['total_amount']),
        go.Bar(name='O‘rtacha kunlik', x=summary['device_obj__name'], y=summary['avg_daily_amount'])
    ])
    bar_fig.update_layout(
        barmode='group',
        xaxis_title='Qurilma',
        yaxis_title="So'm",
        template='plotly_white'
    )

    return line_fig, bar_fig

if __name__ == '__main__':
    app.run(debug=True)
