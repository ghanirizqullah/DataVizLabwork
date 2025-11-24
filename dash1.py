import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Books Dashboard", layout="wide")
st.title("Amazon Books Dashboard")

# Load data
@st.cache_data
def load_data():
    return {
        'scorecard': pd.read_csv('./dataset/scorecard_data.csv'),
        'genre': pd.read_csv('./dataset/genre_data.csv'),
        'books': pd.read_csv('./dataset/top_books_data.csv'),
        'authors': pd.read_csv('./dataset/top_authors_data.csv')
    }

data = load_data()
scorecard, genre_data, top_books_data, top_authors_data = data['scorecard'], data['genre'], data['books'], data['authors']

# Initialize session state
if 'selected_genre' not in st.session_state:
    st.session_state.selected_genre = "All Genres"

# Helper functions
def get_measure_cols(measure):
    return {
        'genre_col': 'total_sales' if measure == 'Sales' else 'review_count',
        'books_col': 'total_sales' if measure == 'Sales' else 'total_reviews',
        'label': 'Sales',
        'axis_label': 'Sales ($)' if measure == 'Sales' else 'Reviews'
    }

def truncate_text(text, max_len=15):
    return (text[:max_len] + '...')[:max_len].ljust(max_len) if len(text) > max_len else text.ljust(max_len)

def create_sparkline_chart(data, y_col):
    fig = px.line(data, x='year', y=y_col)
    fig.update_layout(showlegend=False, xaxis={'visible': False}, yaxis={'visible': False},
                      margin=dict(l=0, r=0, t=0, b=0), height=80)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    return fig

def filter_by_year(df, year_range):
    return (df['year'] >= year_range[0]) & (df['year'] <= year_range[1])

# Filters
filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    year_range = st.slider("Published Year", int(scorecard['year'].min()), int(scorecard['year'].max()), 
                           (2000, int(scorecard['year'].max())))

with filter_col2:
    measure = st.selectbox("Measure for Top N Charts", ["Sales", "Reviews"], index=0)

with filter_col3:
    filtered_genre_for_options = genre_data[filter_by_year(genre_data, year_range)]
    all_genres = sorted([g for g in filtered_genre_for_options['genre'].unique() if pd.notna(g)])
    genre_options = ["All Genres"] + all_genres
    current_idx = genre_options.index(st.session_state.selected_genre) if st.session_state.selected_genre in genre_options else 0
    st.selectbox("Filter by Genre", genre_options, index=current_idx, key="genre_filter", 
                 on_change=lambda: st.session_state.update({'selected_genre': st.session_state.genre_filter}))
    st.session_state.selected_genre = st.session_state.get('genre_filter', "All Genres")

# Display key metrics
filtered_scorecard = scorecard[filter_by_year(scorecard, year_range)]
col1, col2, col3 = st.columns(3)

for idx, (col, label, value_col, fmt) in enumerate([(col1, "Total Books", "total_books", "{:,.0f}"),
                                                      (col2, "Total Reviews", "total_reviews", "{:,.0f}"),
                                                      (col3, "Total Sales", "total_sales", "${:,.2f}")]):
    with col:
        m_col, c_col = st.columns([1, 1])
        with m_col:
            val = filtered_scorecard[value_col].sum()
            st.metric(label, fmt.format(val))
        with c_col:
            st.plotly_chart(create_sparkline_chart(filtered_scorecard, value_col), config={'responsive': True})

# Genre overview
st.subheader("Genre Analysis")
filtered_genre = genre_data[filter_by_year(genre_data, year_range)]
cols = get_measure_cols(measure)
genre_sums = filtered_genre.groupby('genre')[cols['genre_col']].sum().reset_index()
top_genres = genre_sums.nlargest(5, cols['genre_col'])['genre'].tolist()
color_palette = px.colors.qualitative.Plotly

col_treemap = st.columns(1)[0]

with col_treemap:
    genre_treemap = top_books_data[filter_by_year(top_books_data, year_range)].groupby('genre')[cols['books_col']].sum().reset_index().dropna(subset=['genre'])
    fig = px.treemap(genre_treemap, path=['genre'], values=cols['books_col'], 
                     title=f"All Genres by {cols['label']}", color_discrete_sequence=color_palette)
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20), title_font=dict(size=25), showlegend=False)
    fig.update_traces(textinfo='label', textfont=dict(size=12), 
                      hovertemplate='<b>%{label}</b><br>' + cols['label'] + ': %{value}<extra></extra>')
    st.plotly_chart(fig, config={'responsive': True})

# Genre trends and top genres
col_pie, col_stacked = st.columns([0.3, 0.7])

with col_pie:
    genre_agg = filtered_genre.groupby('genre')[cols['genre_col']].sum().reset_index().nlargest(5, cols['genre_col'])
    pct = (genre_agg[cols['genre_col']].sum() / filtered_genre[cols['genre_col']].sum()) * 100
    fig = px.pie(genre_agg, values=cols['genre_col'], names='genre', 
                 title=f'Top 5 Genres by {cols["label"]}', hole=0.4, color_discrete_sequence=color_palette)
    fig.update_layout(height=500, margin=dict(l=20, r=20, t=40, b=20), title_font=dict(size=25), showlegend=True)
    fig.add_annotation(text=f"Top 5 Share(%):<br>{pct:.1f}%", x=0.5, y=0.5, showarrow=False, font=dict(size=16, color='white'))
    fig.update_traces(hovertemplate='<b>%{label}</b><br>' + cols['label'] + ': %{value}<extra></extra>')
    st.plotly_chart(fig, config={'responsive': True})

with col_stacked:
    genre_year = filtered_genre.groupby(['year', 'genre'])[cols['genre_col']].sum().reset_index()
    genre_year = genre_year[genre_year['genre'].isin(top_genres)]
    fig = px.bar(genre_year, x='year', y=cols['genre_col'], color='genre', 
                 labels={'year': 'Year', cols['genre_col']: cols['axis_label'], 'genre': 'Genre'},
                 title=f'Top 5 Genres Trends', color_discrete_sequence=color_palette, category_orders={'genre': top_genres})
    fig.update_layout(height=500, margin=dict(l=20, r=20, t=40, b=20), title_font=dict(size=25), showlegend=False)
    fig.update_traces(hovertemplate='<b>%{fullData.name}</b><br>Year: %{x}<br>' + cols['axis_label'] + ': %{y}<extra></extra>')
    st.plotly_chart(fig, config={'responsive': True})

# Top 10 Books and Authors
def create_top_chart(data, group_cols, name_col, title):
    agg = data.groupby(group_cols)[cols['books_col']].sum().reset_index().nlargest(10, cols['books_col'])
    agg['short_name'] = agg[name_col].apply(truncate_text)
    fig = px.bar(agg, x=cols['books_col'], y='short_name', orientation='h',
                 labels={cols['books_col']: cols['axis_label'], 'short_name': name_col.title()},
                 title=f'{title} by {cols["label"]}')
    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=250, margin=dict(l=20, r=20, t=40, b=20),
                      title_font=dict(size=25), yaxis_tickfont=dict(family='monospace'))
    return fig

selected_genre = st.session_state.selected_genre
filtered_books = top_books_data[filter_by_year(top_books_data, year_range)]
if selected_genre != "All Genres":
    filtered_books = filtered_books[filtered_books['genre'] == selected_genre]

st.plotly_chart(create_top_chart(filtered_books, ['title', 'author_name'], 'title', 'Top 10 Books'), config={'responsive': True})

filtered_authors = top_authors_data[filter_by_year(top_authors_data, year_range)]
if selected_genre != "All Genres":
    genre_authors = top_books_data[filter_by_year(top_books_data, year_range) & (top_books_data['genre'] == selected_genre)]['author_name'].unique()
    filtered_authors = filtered_authors[filtered_authors['author_name'].isin(genre_authors)]

st.plotly_chart(create_top_chart(filtered_authors, ['author_name'], 'author_name', 'Top 10 Authors'), config={'responsive': True})


