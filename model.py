import csv
import requests
from bs4 import BeautifulSoup
import unicodedata
from pymongo import MongoClient

def scrape_hadith_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Mendapatkan bunyi hadits
    bunyi_hadits_element = soup.find('div', class_='col-md-6')
    bunyi_hadits = bunyi_hadits_element.find('p').text.strip()

    # Normalisasi Unicode pada bunyi hadits
    bunyi_hadits = unicodedata.normalize('NFKD', bunyi_hadits)

    # Mendapatkan perawi
    perawi_element = soup.find('span', class_='text-muted').find_next('a', href=lambda href: href and 'home?q=' in href)
    perawi = perawi_element.text

    # Mendapatkan ulama hadits
    ulama_hadits_element = soup.find('span', class_='text-muted', string='Ulama hadits:').find_next('a', href=lambda href: href and 'home?q=' in href)
    ulama_hadits = ulama_hadits_element.text

    # Mendapatkan nama kitab
    nama_kitab_element = soup.find('span', class_='text-muted', string='Nama kitab:').find_next('a', href=lambda href: href and 'home?q=' in href)
    nama_kitab = nama_kitab_element.text

    # Mendapatkan nomor hadits
    nomor_hadits_element = soup.find('span', class_='text-muted', string='Nomor:').find_next('strong')
    nomor_hadits = nomor_hadits_element.text

    return {
        'Bunyi Hadits': bunyi_hadits,
        'Perawi': perawi,
        'Ulama Hadits': ulama_hadits,
        'Nama Kitab': nama_kitab,
        'Nomor Hadits': nomor_hadits
    }

# Koneksi ke MongoDB
client = MongoClient('mongodb+srv://ainiwijoyo:admin@cluster0.cyddtya.mongodb.net/')
db = client['data_mining']
collection = db['model']

# Membuka file CSV yang berisi data perawi dan URL
with open('data_hadits.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)

    existing_data = set()

    # Melakukan scraping untuk setiap baris pada file CSV
    for row in reader:
        url = row['URL']
        data = scrape_hadith_data(url)
        
        # Mengecek apakah data sudah ada sebelumnya
        existing_data_key = (
            data['Bunyi Hadits'],
            data['Perawi'],
            data['Ulama Hadits'],
            data['Nama Kitab'],
            data['Nomor Hadits']
        )
        
        # Jika data belum ada, simpan data ke MongoDB dan tambahkan ke set existing_data
        if existing_data_key not in existing_data:
            collection.insert_one(data)
            existing_data.add(existing_data_key)

print("Selesai scraping dan data telah disimpan di MongoDB.")
