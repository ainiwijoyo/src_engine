import csv
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

base_url = 'https://hadits.site/shahih'

def get_total_pages():
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    pagination = soup.find('ul', class_='pagination')
    page_links = pagination.find_all('a', href=True)
    last_page_link = page_links[-2]
    last_page_number = int(last_page_link.text)
    return last_page_number

def scrape_hadith_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Mendapatkan data perawi
    perawi_elements = soup.find_all('a', href=lambda href: href and 'home?q=' in href)
    perawis = [element.text for element in perawi_elements]

    # Mendapatkan data URL
    url_elements = soup.find_all('a', href=lambda href: href and '/hadits/' in href)
    urls = [f"https://hadits.site{element['href']}" for element in url_elements]

    return list(zip(perawis, urls))

# Koneksi ke MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['data_mining']
collection = db['scrp']

# Membuka file CSV yang berisi data perawi dan URL
with open('data_hadits.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Perawi', 'URL']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    hadith_data = []

    # Mengambil total jumlah halaman secara otomatis
    total_pages = get_total_pages()

    # Melakukan scraping dan menyimpan data ke MongoDB
    for page in range(1, total_pages+1):
        url = f'{base_url}?page={page}'
        data = scrape_hadith_data(url)
        hadith_data.extend({'Perawi': perawi, 'URL': url} for perawi, url in data)

        # Menyimpan data perawi dan URL ke dalam file CSV
        for perawi, url in data:
            writer.writerow({'Perawi': perawi, 'URL': url})

        print(f"Selesai scraping halaman {page}")

# Menyimpan data hasil scraping ke MongoDB
collection.insert_many(hadith_data)

print("Selesai scraping semua halaman. Data telah disimpan di MongoDB.")
