from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
from PIL import Image
import secrets  # Для генерации короткого идентификатора
import uuid  # Для генерации уникальных имён файлов

app = Flask(__name__)

# Настройки
UPLOAD_FOLDER = 'uploads'  # Папка uploads находится в корне проекта
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 МБ
MAX_FILES = 7
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'supersecretkey'  # Для работы flash-сообщений

# Создаем папку для загрузок, если её нет
def ensure_folder_exists(folder_path):
    """Создаёт папку, если её нет."""
    try:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Папка {folder_path} успешно создана.")
    except Exception as e:
        print(f"Ошибка при создании папки {folder_path}: {e}")
        flash('Ошибка при создании папки для файлов.')
        return False
    return True

# Проверка допустимых расширений файлов
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Удаление метаданных из изображения
def remove_metadata(image_path):
    try:
        img = Image.open(image_path)
        data = list(img.getdata())
        image_without_exif = Image.new(img.mode, img.size)
        image_without_exif.putdata(data)
        image_without_exif.save(image_path)
    except Exception as e:
        print(f"Ошибка при удалении метаданных: {e}")

# Генерация короткого уникального идентификатора (8 символов)
def generate_short_id():
    alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(secrets.choice(alphabet) for _ in range(8))

# Главная страница
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        files = request.files.getlist('photos')  # Получаем список файлов

        # Проверяем количество файлов
        if len(files) > MAX_FILES:
            flash('Можно загружать не более 7 файлов.')
            return redirect(request.url)

        # Генерируем короткий уникальный идентификатор
        short_id = generate_short_id()
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], short_id)

        # Создаем папку, если её нет
        if not ensure_folder_exists(folder_path):
            return redirect(request.url)

        uploaded_files = []

        for file in files:
            if file and allowed_file(file.filename):
                # Проверяем размер файла
                if len(file.read()) > MAX_FILE_SIZE:
                    flash('Размер файла превышает 5 МБ.')
                    return redirect(request.url)
                file.seek(0)  # Возвращаем указатель файла в начало

                # Генерируем уникальное имя для файла
                unique_filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
                file_path = os.path.join(folder_path, unique_filename)

                # Сохраняем файл
                try:
                    file.save(file_path)
                    print(f"Файл {unique_filename} успешно сохранён в {file_path}.")
                except Exception as e:
                    print(f"Ошибка при сохранении файла {unique_filename}: {e}")
                    flash('Ошибка при сохранении файла.')
                    return redirect(request.url)

                # Удаляем метаданные
                remove_metadata(file_path)

                # Добавляем файл в список загруженных
                uploaded_files.append(unique_filename)

        # Генерация короткой ссылки на папку
        short_link = f"http://localhost:5000/{short_id}"
        return f"""
        <div style="text-align: center; font-family: Arial, sans-serif;">
            <img src="/static/logo.jpeg" alt="Логотип" style="width: 300px; margin-bottom: 20px;">
            <h1>Ваши файлы загружены!</h1>
            <p>Ссылка для скачивания: 
                <a href='{short_link}'>{short_link}</a>
                <button onclick="copyToClipboard('{short_link}')">Скопировать</button>
            </p>
            <script>
                function copyToClipboard(text) {{
                    navigator.clipboard.writeText(text).then(() => {{
                        alert('Ссылка скопирована в буфер обмена!');
                    }});
                }}
            </script>
        </div>
        """

    return render_template('index.html')

# Страница для скачивания файлов
@app.route('/<short_id>')
def download(short_id):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], short_id)
    if not os.path.exists(folder_path):
        return "<h1>Папка не найдена</h1>", 404

    # Получаем список файлов в папке
    filenames = os.listdir(folder_path)
    return render_template('download.html', folder=short_id, filenames=filenames)

# Маршрут для обслуживания файлов из папки uploads
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)