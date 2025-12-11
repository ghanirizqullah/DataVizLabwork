import pandas as pd
import duckdb
import os
import kagglehub
from kagglehub import KaggleDatasetAdapter
import pandas as pd

def query(s):
    return duckdb.sql(s).df()

outdir = './dataset'
if not os.path.exists(outdir):
    os.mkdir(outdir)

metadata_path = './dataset/metadata.csv'
reviews_path = './dataset/reviews.csv'
clean_reviews_path = './dataset/books_reviews_clean.csv'

if not os.path.exists(metadata_path) or not os.path.exists(reviews_path):
    # Download and save the files locally
    books_metadata = kagglehub.dataset_load(
        "hadifariborzi/amazon-books-dataset-20k-books-727k-reviews",
        "amazon_books_metadata_sample_20k.csv",
    )
    
    books_reviews = kagglehub.dataset_load(
        "hadifariborzi/amazon-books-dataset-20k-books-727k-reviews",
        "amazon_books_reviews_sample_20k.csv",
    )
    
    books_metadata.to_csv(metadata_path)
    books_reviews.to_csv(reviews_path)

if not os.path.exists(clean_reviews_path):
    clean_reviews_dir = kagglehub.dataset_download("tobypu/book-reviews-clean")
    import shutil
    shutil.copy(os.path.join(clean_reviews_dir, "books_reviews_clean.csv"), clean_reviews_path)

# Load raw data
books_metadata = pd.read_csv(metadata_path, index_col=0)
books_reviews = pd.read_csv(reviews_path, index_col=0)
books_reviews_clean = pd.read_csv(clean_reviews_path, index_col=0)

processed_metadata = query("""
    with p1 as (
      select 
        * exclude(publisher_date),
        case 
          when try_cast(right(substr(publisher_date, strpos(publisher_date, '(')),4) as integer) is not null 
          then split(publisher_date,'(')[-1]
          else null
        end as date_str,
      from books_metadata 
    )
    select 
      *,
      case when length(date_str) > 8 then strptime(date_str, '%B %-d, %Y') else null end as published_date
    from p1
""")

processed_metadata.to_csv('./dataset/processed_metadata.csv', index=False)

scorecard_data = query("""
    select 
        year(m.published_date) as year,
        count(distinct m.parent_asin) as total_books,
        count(r.asin) as total_reviews,
        sum(r.rating * m.price) as total_sales
    from processed_metadata m
    left join books_reviews r using(parent_asin)
    where m.published_date is not null
    group by year(m.published_date)
    order by year
""")

scorecard_data.to_csv('./dataset/scorecard_data.csv', index=False)

genre_data = query("""
    select 
        year(m.published_date) as year,
        m.category_level_3_detail as genre,
        count(distinct m.parent_asin) as book_count,
        count(r.asin) as review_count,
        sum(r.rating * m.price) as total_sales
    from processed_metadata m
    left join books_reviews r using(parent_asin)
    where m.published_date is not null and m.category_level_3_detail is not null
    group by year(m.published_date), m.category_level_3_detail
    order by year, book_count desc
""")

genre_data.to_csv('./dataset/genre_data.csv', index=False)

top_books_data = query("""
    select 
        year(m.published_date) as year,
        m.title,
        m.author_name,
        m.category_level_3_detail as genre,
        count(r.asin) as total_reviews,
        sum(r.rating * m.price) as total_sales
    from processed_metadata m
    left join books_reviews r using(parent_asin)
    where m.published_date is not null
    group by year(m.published_date), m.title, m.author_name, m.category_level_3_detail
    order by year, total_sales desc
""")

top_books_data.to_csv('./dataset/top_books_data.csv', index=False)

top_authors_data = query("""
    select 
        year(m.published_date) as year,
        m.author_name,
        count(r.asin) as total_reviews,
        sum(r.rating * m.price) as total_sales
    from processed_metadata m
    left join books_reviews r using(parent_asin)
    where m.published_date is not null and m.author_name is not null
    group by year(m.published_date), m.author_name
    order by year, total_sales desc
""")

top_authors_data.to_csv('./dataset/top_authors_data.csv', index=False)

format_data = query("""
    select 
        year(m.published_date) as year,
        coalesce(m.format, 'Kindle') as book_format,
        m.category_level_3_detail as genre,
        avg(m.price_numeric) as avg_price,
        avg(m.page_count) as avg_page_count,
        count(distinct m.parent_asin) as book_count,
        count(r.asin) as total_reviews,
        sum(r.rating * m.price_numeric) as total_sales
    from processed_metadata m
    left join books_reviews r using(parent_asin)
    where m.published_date is not null and m.price_numeric is not null and m.category_level_3_detail is not null
    group by year(m.published_date), coalesce(m.format, 'Kindle'), m.category_level_3_detail
    order by year, book_format
""")

all_formats = query("""
    select 
        year(m.published_date) as year,
        'All Formats' as book_format,
        avg(m.price_numeric) as avg_price,
        avg(m.page_count) as avg_page_count,
        count(distinct m.parent_asin) as book_count,
        count(r.asin) as total_reviews,
        sum(r.rating * m.price_numeric) as total_sales
    from processed_metadata m
    left join books_reviews r using(parent_asin)
    where m.published_date is not null and m.price_numeric is not null
    group by year(m.published_date)
    order by year
""")

format_data = pd.concat([format_data, all_formats], ignore_index=True)
format_data.to_csv('./dataset/format_data.csv', index=False)

top_publishers_data = query("""
    select 
        year(m.published_date) as year,
        m.publisher as publisher_name,
        m.category_level_3_detail as genre,
        count(distinct m.parent_asin) as book_count,
        count(r.asin) as total_reviews,
        sum(r.rating * m.price) as total_sales,
        avg(r.rating) as avg_rating
    from processed_metadata m
    left join books_reviews r using(parent_asin)
    where m.published_date is not null and m.publisher is not null and m.category_level_3_detail is not null
    group by year(m.published_date), m.publisher, m.category_level_3_detail
    order by year, total_sales desc
""")

top_publishers_data.to_csv('./dataset/top_publishers_data.csv', index=False)

print("Data processing complete!")
print(f"Processed metadata: {len(processed_metadata)} rows")
print(f"Scorecard data saved")
print(f"Genre data saved")
print(f"Top books data saved")
print(f"Top authors data saved")
print(f"Top publishers data saved")
print(scorecard_data)