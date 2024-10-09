import requests
import fitz  # PyMuPDF
from io import BytesIO
from telegram import Bot, Update
from telegram.ext import CommandHandler, ApplicationBuilder, ContextTypes
from datetime import datetime, timedelta
import asyncio
import os

TOKEN = '7342501772:AAEXlp7HdS4VbUBMw8hfQOBIC2onV_t-yzU'
CHAT_ID = '-1002279256667'

bot = Bot(token=TOKEN)
last_schedule_image_path = None  # Путь к последнему найденному изображению

async def check_schedule(day, month, year):
    # Формируем URL для трех вариантов
    urls = [
        f'http://ркэ.рф/assets/rasp/{day:02}{month:02}{year}.pdf',
        f'http://ркэ.рф/assets/rasp/{day:02}{month:02}{year}1.pdf',
        f'http://ркэ.рф/assets/rasp/{day:02}{month:02}{year}2.pdf'
    ]

    for url in urls:
        response = requests.get(url)
        # Проверяем, что полученный ответ - это PDF файл
        if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
            return response.content

    return None  # Файл не найден

async def send_schedule(file_content):
    global last_schedule_image_path  # Объявляем переменную глобальной

    # Открываем PDF файл с помощью PyMuPDF
    pdf_document = fitz.open(stream=file_content, filetype="pdf")
    
    if pdf_document.page_count >= 2:
        # Извлекаем вторую страницу
        page = pdf_document[1]  # Вторая страница имеет индекс 1
        pix = page.get_pixmap()  # Создаем изображение страницы
        
        # Определяем имя файла и путь для сохранения
        last_schedule_image_path = os.path.join(os.getcwd(), 'last_schedule.png')

        # Сохраняем изображение в файл
        pix.save(last_schedule_image_path)  # Сохраняем изображение как PNG
        
        # Отправляем изображение в указанный чат
        with open(last_schedule_image_path, 'rb') as img_file:
            await bot.send_photo(chat_id=CHAT_ID, photo=img_file)  # Используем await
        return True  # Успешная отправка

    return False  # Не удалось отправить

async def main():
    # Устанавливаем начальную дату на сегодняшний день
    current_date = datetime.now()

    while True:
        # Получаем день, месяц и год для поиска файла
        day = current_date.day
        month = current_date.month
        year = current_date.year

        # Проверяем наличие расписания на указанный день
        schedule_file = await check_schedule(day, month, year)
        if schedule_file:
            success = await send_schedule(schedule_file)
            if success:
                # Если файл успешно отправлен, обновляем дату на следующий день
                current_date += timedelta(days=1)  # Переходим к следующему дню
            continue  # Если файл найден и отправлен, продолжаем с новым днем
        
        await asyncio.sleep(10)  # Если не найдено, ждем 10 секунд перед следующей проверкой

async def send_last_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет последнее найденное расписание."""
    global last_schedule_image_path  # Получаем доступ к глобальной переменной

    if last_schedule_image_path and os.path.exists(last_schedule_image_path):
        # Отправляем последнее сохраненное изображение второй страницы
        with open(last_schedule_image_path, 'rb') as img_file:
            await bot.send_photo(chat_id=update.effective_chat.id, photo=img_file)
    else:
        await update.message.reply_text("Расписание еще не найдено.")

async def send_ribakova(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет сообщение о Рыбаковой."""
    await update.message.reply_text("Рыбакова сегодня не придет.")

if __name__ == '__main__':
    # Запускаем бота
    application = ApplicationBuilder().token(TOKEN).build()

    # Обработчик команд
    application.add_handler(CommandHandler("rasp", send_last_schedule))
    application.add_handler(CommandHandler("LEROKFRAEROK", send_ribakova))

    loop = asyncio.get_event_loop()  # Получаем текущий цикл событий
    asyncio.ensure_future(main())  # Запускаем асинхронную проверку расписания
    application.run_polling()  # Запускаем бота
