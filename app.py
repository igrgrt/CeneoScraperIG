from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import pandas as pd
import os
from scraper import extract_reviews, save_reviews_to_csv

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['GET', 'POST'])
def extract():
    if request.method == 'POST':
        product_id = request.form.get('product_id', '').strip()
        if product_id:
            try:
                reviews, product_name = extract_reviews(product_id)
                if reviews:
                    save_reviews_to_csv(reviews, product_id, product_name)
                    return redirect(url_for('product', product_id=product_id))
                else:
                    flash('No reviews found for this product.', 'warning')
            except Exception as e:
                flash(f'Error extracting reviews: {e}', 'danger')
        else:
            flash('Please enter a valid product ID.', 'warning')
    return render_template('extract.html')

@app.route('/product/<product_id>')
def product(product_id):
    data_dir = 'data'
    files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    file_path = None
    
    for file in files:
        if f'_{product_id}.csv' in file:
            file_path = os.path.join(data_dir, file)
            break
    
    if file_path and os.path.exists(file_path):
        df = pd.read_csv(file_path)
        reviews = df.to_dict('records')
        return render_template('product.html', reviews=reviews, product_id=product_id)
    else:
        flash('No reviews found for this product.', 'warning')
        return redirect(url_for('index'))

@app.route('/charts/<product_id>')
def charts(product_id):
    # Try to find the CSV file based on the product ID and product name
    data_dir = 'data'
    files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

    # Extract the file name that matches the pattern
    file_name = None
    for file in files:
        if f'_{product_id}.csv' in file:
            file_name = file
            break

    if not file_name:
        flash('No reviews found for this product.', 'warning')
        return redirect(url_for('index'))

    file_path = os.path.join(data_dir, file_name)
    
    try:
        df = pd.read_csv(file_path)

        # Generate chart data
        # Pie chart data: Share of recommendations
        recommendation_counts = df['recommendation'].value_counts()
        recommendations = [{"label": rec, "value": count} for rec, count in recommendation_counts.items()]

        # Bar chart data: Number of reviews with individual star ratings
        star_counts = df['stars'].value_counts().sort_index()
        star_ratings = [{"label": str(star), "value": count} for star, count in star_counts.items()]

        return render_template('charts.html',
                               product_id=product_id,
                               recommendations=recommendations,
                               star_ratings=star_ratings)
    except Exception as e:
        flash(f'Error generating charts: {e}', 'danger')
        return redirect(url_for('index'))

@app.route('/products')
def products():
    data_dir = 'data'
    files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    products = []
    
    for file in files:
        if file.startswith('reviews_') and file.endswith('.csv'):
            product_id = file.split('_')[-1].replace('.csv', '')
            product_name = file[len('reviews_'):-len(f'_{product_id}.csv')].replace('_', ' ')
            file_path = os.path.join(data_dir, file)
            df = pd.read_csv(file_path)
            
            # Compute statistics
            num_reviews = len(df)
            num_advantages = df['advantages'].apply(lambda x: len(eval(x)) if pd.notna(x) else 0).sum()
            num_disadvantages = df['disadvantages'].apply(lambda x: len(eval(x)) if pd.notna(x) else 0).sum()
            
            # Extract numeric part of stars and calculate mean
            def parse_stars(stars):
                try:
                    return float(stars.replace(',', '.').split('/')[0])
                except (ValueError, AttributeError):
                    return 0
            
            df['stars_numeric'] = df['stars'].apply(parse_stars)
            mean_stars = df['stars_numeric'].mean()
            
            products.append({
                'product_id': product_id,
                'product_name': product_name,
                'mean_reviews': num_reviews,
                'num_advantages': num_advantages,
                'num_disadvantages': num_disadvantages,
                'mean_stars': mean_stars,
                'csv_link': url_for('download_csv', filename=file)
            })
    
    if products:
        return render_template('products.html', products=products)
    else:
        flash('No products found.', 'warning')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_csv(filename):
    return send_from_directory('data', filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
