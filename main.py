from flask import Flask, render_template, request, redirect
from pymongo import MongoClient
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

app = Flask(__name__)

# Koneksi ke MongoDB
client = MongoClient('mongodb+srv://ainiwijoyo:admin@cluster0.cyddtya.mongodb.net/')
db = client['data_mining']
collection = db['model']

factory = StemmerFactory()
stemmer = factory.create_stemmer()

def preprocess_text(text):
    # Case folding
    text = text.lower()
    
    # Tokenizing
    tokens = re.findall(r'\b\w+\b', text)
    
    # Filtering hapus stopword
    stopword_factory = StopWordRemoverFactory()
    stopword_list = stopword_factory.get_stop_words()
    filtered_tokens = [token for token in tokens if token not in stopword_list]
    
    # Stemming
    stemmer_factory = StemmerFactory()
    stemmer = stemmer_factory.create_stemmer()
    stemmed_tokens = [stemmer.stem(token) for token in filtered_tokens]
    
    # gabungkan stemmed
    processed_text = ' '.join(stemmed_tokens)
    
    return processed_text

def calculate_cosine_similarity(keyword, documents):
    tfidf_vectorizer = TfidfVectorizer(preprocessor=preprocess_text)
    tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
    keyword_tfidf_vector = tfidf_vectorizer.transform([preprocess_text(keyword)])
    similarity_scores = cosine_similarity(keyword_tfidf_vector, tfidf_matrix)
    return similarity_scores[0]

def index_documents():
    documents = collection.find({})
    indexed_documents = []
    
    for document in documents:
        text = preprocess_text(document['Bunyi Hadits'])
        indexed_documents.append({'_id': document['_id'], 'text': text})
    
    # Hapus indeks sebelumnya jika ada
    existing_indexes = collection.index_information()
    if 'text_index' in existing_indexes:
        collection.drop_index('text_index')
    
    # Buat indeks baru
    collection.create_index([('text', 'text')], name='text_index')
    
    return indexed_documents

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    keyword = request.form['keyword']
    
    stemmed_keyword = preprocess_text(keyword)
    query = {'Bunyi Hadits': {'$regex': stemmed_keyword, '$options': 'i'}}
    
    search_results = collection.find(query)
    documents = [result['Bunyi Hadits'] for result in search_results]
    
    if len(documents) == 0:
        return redirect('/none')
    
    similarity_scores = calculate_cosine_similarity(stemmed_keyword, documents)
    
    search_results.rewind()
    search_results = list(search_results)
    
    filtered_results = [result for result, similarity in zip(search_results, similarity_scores) if similarity > 0]
    
    sorted_results = sorted(filtered_results, key=lambda x: similarity_scores[search_results.index(x)], reverse=True)
    
    for i, result in enumerate(sorted_results):
        result['Cosine Similarity'] = '{:.2%}'.format(similarity_scores[search_results.index(result)])
    
    return render_template('search_results.html', search_results=sorted_results)

@app.route('/none')
def none():
    return render_template('none.html')

if __name__ == '__main__':
    indexed_documents = index_documents()
    app.run(debug=True)
