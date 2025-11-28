import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from google.colab import files
import os

def find_html_file():
    """Находит HTML файл в текущей директории"""
    for file in os.listdir('.'):
        if file.endswith('.html'):
            print(f"📁 Найден файл: {file}")
            return file
    return None

def parse_parties():
    """Парсит политические партии из HTML файла"""
    
    # Ищем HTML файл
    html_file = find_html_file()
    
    if not html_file:
        print("HTML файл не найден!")
        print("Загрузите HTML файл:")
        uploaded = files.upload()
        for filename in uploaded.keys():
            if filename.endswith('.html'):
                html_file = filename
                break
    
    if not html_file:
        print("Не удалось найти HTML файл")
        return []
    
    try:
        # Читаем HTML файл
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        print(f"Файл '{html_file}' успешно загружен")
    except Exception as e:
        print(f"Ошибка чтения файла: {e}")
        return []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    parties = []
    
    print("🔍 Анализирую структуру страницы...")
    
    # СПОСОБ 1: Ищем по таблицам
    tables = soup.find_all('table')
    print(f"Найдено таблиц: {len(tables)}")
    
    for table in tables:
        rows = table.find_all('tr')[1:]  # Пропускаем заголовок
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                name = cells[0].get_text(strip=True)
                if name and len(name) > 10:
                    # Ищем ссылку на документ
                    doc_url = None
                    for cell in cells:
                        links = cell.find_all('a', href=True)
                        for link in links:
                            href = link.get('href')
                            if href and ('.pdf' in href.lower() or '/documents/' in href):
                                doc_url = normalize_url(href)
                                break
                        if doc_url:
                            break
                    
                    parties.append({
                        'name': clean_party_name(name),
                        'doc_url': doc_url
                    })
    
    # СПОСОБ 2: Ищем по ссылкам на документы
    if not parties:
        print("Ищу ссылки на документы...")
        doc_links = soup.find_all('a', href=lambda x: x and '/documents/' in x)
        print(f"Найдено ссылок на документы: {len(doc_links)}")
        
        for link in doc_links:
            name = link.get_text(strip=True)
            if name and len(name) > 10:
                doc_url = normalize_url(link.get('href'))
                parties.append({
                    'name': clean_party_name(name),
                    'doc_url': doc_url
                })
    
    # СПОСОБ 3: Ищем по спискам
    if not parties:
        print("Ищу в списках...")
        lists = soup.find_all(['ul', 'ol'])
        for list_elem in lists:
            items = list_elem.find_all('li')
            for item in items:
                name = item.get_text(strip=True)
                if name and len(name) > 10 and is_party_name(name):
                    doc_url = extract_document_url(item)
                    parties.append({
                        'name': clean_party_name(name),
                        'doc_url': doc_url
                    })
    
    # СПОСОБ 4: Ищем по дивам с классами
    if not parties:
        print("Ищу по классам...")
        divs = soup.find_all('div', class_=True)
        for div in divs:
            classes = ' '.join(div.get('class', []))
            if any(word in classes.lower() for word in ['party', 'item', 'document']):
                name = div.get_text(strip=True)
                if name and len(name) > 10 and is_party_name(name):
                    doc_url = extract_document_url(div)
                    parties.append({
                        'name': clean_party_name(name),
                        'doc_url': doc_url
                    })
    
    # Убираем дубликаты
    unique_parties = []
    seen_names = set()
    
    for party in parties:
        if party['name'] not in seen_names:
            seen_names.add(party['name'])
            unique_parties.append(party)
    
    # Сортируем по алфавиту
    unique_parties.sort(key=lambda x: x['name'])
    
    return unique_parties

def clean_party_name(name):
    """Очищает название партии"""
    if not name:
        return name
    
    # Убираем лишние префиксы
    prefixes = [
        'Политическая партия',
        'Политическая Партия', 
        'Партия',
        'Название:',
        'Свидетельство о государственной регистрации'
    ]
    
    for prefix in prefixes:
        if name.startswith(prefix):
            name = name.replace(prefix, '').strip()
    
    # Убираем кавычки и лишние пробелы
    name = name.replace('"', '').strip()
    name = ' '.join(name.split())
    
    return name

def extract_document_url(element):
    """Извлекает ссылку на документ из элемента"""
    if not element:
        return None
    
    # Ищем PDF ссылки
    pdf_links = element.find_all('a', href=lambda x: x and '.pdf' in x.lower())
    if pdf_links:
        return normalize_url(pdf_links[0].get('href'))
    
    # Ищем любые ссылки
    links = element.find_all('a', href=True)
    for link in links:
        href = link.get('href')
        if href and ('/documents/' in href or 'download' in href.lower()):
            return normalize_url(href)
    
    return None

def normalize_url(url):
    """Нормализует URL"""
    if not url:
        return None
    
    # Делаем абсолютный URL
    if url.startswith('/'):
        url = urljoin('https://minjust.gov.ru', url)
    
    # Исправляем протокол
    if url.startswith('http://'):
        url = url.replace('http://', 'https://')
    
    return url

def is_party_name(text):
    """Проверяет, является ли текст названием партии"""
    if not text or len(text) < 10 or len(text) > 200:
        return False
    
    keywords = ['партия', 'росси', 'демократ', 'союз', 'движение', 'объединение']
    return any(keyword in text.lower() for keyword in keywords)

def main():
    print("=" * 60)
    print("ПАРСИНГ ПОЛИТИЧЕСКИХ ПАРТИЙ")
    print("=" * 60)
    
    # Парсим данные
    parties = parse_parties()
    
    if parties:
        # Сохраняем в JSON
        with open('parties.json', 'w', encoding='utf-8') as f:
            json.dump(parties, f, ensure_ascii=False, indent=2)
        
        print(f"Найдено партий: {len(parties)}")
        print("Результат сохранен в parties.json")
        
        # Выводим результаты
        print("СПИСОК ПАРТИЙ:")
        for i, party in enumerate(parties, 1):
            doc_status = party['doc_url'] if party['doc_url'] else "Документ не найден"
            print(f"{i:2d}. {party['name']}")
            if party['doc_url']:
                print(f"     {party['doc_url']}")
            print()
        
        # Скачиваем результат
        print("Скачиваю файл с результатом...")
        files.download('parties.json')
        
    else:
        print("Не удалось найти партии")
     

if __name__ == "__main__":
    main()
