import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Books Dashboard", layout="wide")

st.title("Amazon Books Dashboard")

# Load data
@st.cache_data
def load_scorecard():
    return pd.read_csv('./dataset/scorecard_data.csv')

@st.cache_data
def load_genre():
    return pd.read_csv('./dataset/genre_data.csv')

@st.cache_data
def load_top_books():
    return pd.read_csv('./dataset/top_books_data.csv')

@st.cache_data
def load_top_authors():
    return pd.read_csv('./dataset/top_authors_data.csv')

scorecard = load_scorecard()
genre_data = load_genre()
top_books_data = load_top_books()
top_authors_data = load_top_authors()

# Filters
filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    year_range = st.slider(
        "Published Year",
        min_value=int(scorecard['year'].min()),
        max_value=int(scorecard['year'].max()),
        value=(2000, int(scorecard['year'].max()))
    )

with filter_col2:
    measure = st.selectbox(
        "Measure for Top N Charts",
        options=["Sales", "Reviews"],
        index=0
    )

# Filter data by year range
filtered_data = scorecard[(scorecard['year'] >= year_range[0]) & (scorecard['year'] <= year_range[1])]

# Aggregate filtered data
total_books = filtered_data['total_books'].sum()
total_reviews = filtered_data['total_reviews'].sum()
total_sales = filtered_data['total_sales'].sum()

# Display scorecards
col1, col2, col3 = st.columns(3)

with col1:
    metric_col, chart_col = st.columns([1, 1])
    with metric_col:
        st.metric(
            label="Total Books",
            value=f"{total_books:,.0f}"
        )
    with chart_col:
        fig_books = px.line(filtered_data, x='year', y='total_books')
        fig_books.update_layout(
            showlegend=False,
            xaxis={'visible': False},
            yaxis={'visible': False},
            margin=dict(l=0, r=0, t=0, b=0),
            height=80
        )
        fig_books.update_xaxes(showgrid=False)
        fig_books.update_yaxes(showgrid=False)
        st.plotly_chart(fig_books, use_container_width=True)

with col2:
    metric_col, chart_col = st.columns([1, 1])
    with metric_col:
        st.metric(
            label="Total Reviews",
            value=f"{total_reviews:,.0f}"
        )
    with chart_col:
        fig_reviews = px.line(filtered_data, x='year', y='total_reviews')
        fig_reviews.update_layout(
            showlegend=False,
            xaxis={'visible': False},
            yaxis={'visible': False},
            margin=dict(l=0, r=0, t=0, b=0),
            height=80
        )
        fig_reviews.update_xaxes(showgrid=False)
        fig_reviews.update_yaxes(showgrid=False)
        st.plotly_chart(fig_reviews, use_container_width=True)

with col3:
    metric_col, chart_col = st.columns([1, 1])
    with metric_col:
        st.metric(
            label="Total Sales",
            value=f"${total_sales:,.2f}"
        )
    with chart_col:
        fig_sales = px.line(filtered_data, x='year', y='total_sales')
        fig_sales.update_layout(
            showlegend=False,
            xaxis={'visible': False},
            yaxis={'visible': False},
            margin=dict(l=0, r=0, t=0, b=0),
            height=80
        )
        fig_sales.update_xaxes(showgrid=False)
        fig_sales.update_yaxes(showgrid=False)
        st.plotly_chart(fig_sales, use_container_width=True)

# Top 10 Books and Authors by Sales with Genre Proportions
col_left, col_right = st.columns(2)

with col_left:
    # Filter genre data by year range
    filtered_genre = genre_data[(genre_data['year'] >= year_range[0]) & (genre_data['year'] <= year_range[1])]
    
    # Select measure column based on filter
    measure_col = 'total_sales' if measure == 'Sales' else 'review_count'
    measure_label = 'Sales' if measure == 'Sales' else 'Reviews'
    
    # Aggregate by genre
    genre_totals = filtered_genre.groupby('genre')[measure_col].sum().reset_index()
    genre_totals = genre_totals.sort_values(measure_col, ascending=False)
    
    # Keep top 5 and group the rest as 'Others'
    top_5 = genre_totals.head(5)
    others_count = genre_totals.iloc[5:][measure_col].sum()
    
    if others_count > 0:
        others_row = pd.DataFrame({'genre': ['Others'], measure_col: [others_count]})
        genre_totals_display = pd.concat([top_5, others_row], ignore_index=True)
    else:
        genre_totals_display = top_5
    
    # Display pie chart
    fig = px.pie(genre_totals_display, values=measure_col, names='genre', title=f'Top 5 Genres by {measure_label}')
    fig.update_layout(height=500, margin=dict(l=20, r=20, t=40, b=20),  title_font=dict(size=25))
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    # Select measure column based on filter
    measure_col = 'total_sales' if measure == 'Sales' else 'total_reviews'
    measure_label = 'Sales' if measure == 'Sales' else 'Reviews'
    x_axis_label = 'Sales ($)' if measure == 'Sales' else 'Reviews'
    
    # Filter and aggregate top authors
    filtered_authors = top_authors_data[(top_authors_data['year'] >= year_range[0]) & (top_authors_data['year'] <= year_range[1])]
    top_authors_agg = filtered_authors.groupby('author_name')[measure_col].sum().reset_index()
    top_authors_agg = top_authors_agg.sort_values(measure_col, ascending=False).head(10)
    
    # Create horizontal bar chart
    fig_authors = px.bar(top_authors_agg, x=measure_col, y='author_name', orientation='h',
                         labels={measure_col: x_axis_label, 'author_name': 'Author'},
                         title=f'Top 10 Authors by {measure_label}')
    fig_authors.update_layout(yaxis={'categoryorder':'total ascending'}, height=250, margin=dict(l=20, r=20, t=40, b=20), title_font=dict(size=25))
    st.plotly_chart(fig_authors, use_container_width=True)
    
    # Filter and aggregate top books
    filtered_books = top_books_data[(top_books_data['year'] >= year_range[0]) & (top_books_data['year'] <= year_range[1])]
    top_books_agg = filtered_books.groupby(['title', 'author_name'])[measure_col].sum().reset_index()
    top_books_agg = top_books_agg.sort_values(measure_col, ascending=False).head(10)
    
    # Create shortened title for display
    top_books_agg['title_short'] = top_books_agg['title'].apply(lambda x: x[:15] + '...' if len(x) > 15 else x)
    
    # Create horizontal bar chart
    fig_books = px.bar(top_books_agg, x=measure_col, y='title_short', orientation='h',
                       labels={measure_col: x_axis_label, 'title_short': 'Book Title'},
                       title=f'Top 10 Books by {measure_label}',
                       hover_data={'title': True, 'title_short': False, measure_col: True})
    fig_books.update_layout(yaxis={'categoryorder':'total ascending'}, height=250, margin=dict(l=20, r=20, t=40, b=20), title_font=dict(size=25))
    st.plotly_chart(fig_books, use_container_width=True)
    
