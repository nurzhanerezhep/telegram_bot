import telebot
from telebot import types
from requests import get
from pandas import DataFrame, concat
from bs4 import BeautifulSoup
from re import sub
import sys

# Telegram
token = '6650583648:AAF9n4X_bUOCwVmA3DQ7cFbFnPos6E0g4gM'
bot = telebot.TeleBot(token)
# NCSTE
n_summary = 240
n_formal = 71
my_quantity = ['BR21881930', 'BR21881941']
# my_quantity = ['BR20381077']
# ur = 'https://is.ncste.kz/object/current-state?ov_type_id=203'
ur = 'https://is.ncste.kz/object/current-state?ov_type_id=203'


def read_total_quantity(url):
    page = get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    table = soup.find('table', class_='table table-striped jambo_table')
    columns = table.tfoot.find_all('tr')[0].find_all('td')
    if columns[1].text == '':
        total_quantity = sub('[^0-9]', '', columns[0].text.strip())
        print(f'Total qunatity -{total_quantity}- notes in -1- page')
        return read_data(url), total_quantity
    else:
        total_quantity = sub('[^0-9]', '', columns[0].text.strip())
        n_page = int([i.text for i in columns[1].find_all('a')][-2])
        print(f'Total qunatity -{total_quantity}- notes in -{n_page}- page')
        df = DataFrame(columns=['N', 'IRN', 'Total_score'])
        for page_id in range(1, n_page+1):
            page_url = url + '&page=' + str(page_id)
            __ = read_data(page_url)
            # print(f"{page_url}:\n{__}\n\n")
            df = concat([df, __], axis=0, ignore_index=True)
        # print(df, "\n", len(df.N))
        return df, total_quantity


def read_data(url):
    page = get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    table = soup.find('table', class_='table table-striped jambo_table')
    _ = DataFrame(columns=['N', 'IRN', 'Total_score'])
    for row in table.tbody.find_all('tr'):
        columns = row.find_all('td')
        if columns:
            n = columns[0].text.strip()
            irn = columns[1].text.strip()
            total_score = columns[5].text.strip('&0.')
            data = {'N': n, 'IRN': irn, 'Total_score': total_score}
            _ = concat([_, DataFrame([data])], ignore_index=True)
    return _


def find_quantity(irn):
    frame_all, n_expert = read_total_quantity(ur)
    _ = DataFrame(columns=['-N-', '-----IRN----', '-Total_score-'])
    number_of_find = 0
    for irn_id in irn:
        for i in range(len(frame_all)):
            if irn_id == frame_all.IRN[i]:
                number_of_find += 1
                data = {'-N-': frame_all.N[i], '-----IRN----': frame_all.IRN[i],
                        '-Total_score-': frame_all.Total_score[i]}
                _ = concat([_, DataFrame([data])], ignore_index=True)
    return _, number_of_find, n_expert


def get_info():
    frame_find, n_find, n_expert = find_quantity(my_quantity)
    if n_find == 0:
        print(f"Didn't find same Notes")
        return n_expert, 0, []
    else:
        print(f'Find {n_find} Notes\n{frame_find}')
        return n_expert, n_find, frame_find


@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_1 = types.KeyboardButton("/search")
    button_2 = types.KeyboardButton("/info")
    markup.add(button_1, button_2)
    bot.send_message(message.chat.id,
                     "Привет, {0.first_name}! "
                     "Добро пожаловать в бот для поиска ИРН "
                     "в списке результатов обьектов ГНТЭ (https://is.ncste.kz/object/current-state)".format(message.from_user),
                     reply_markup=markup)


@bot.message_handler(commands=['search'])
def search_handler(message):
    try:
        n_expert, n_find, frame_find = get_info()
        if n_find == 0:
            text = f'Наши ИРН отсутсвуют в списке из {n_expert} заявок'
            bot.send_message(message.chat.id, text)
        else:
            text = f'Найдено {n_find} из {n_expert}\nЗаписи:\n{frame_find}' \
                   f'\n\n**1930-Тимур Кадыржанович,\n**1941-Нуржан Орынбасарович'
            bot.send_message(message.chat.id, text)
    except Exception as error_message:
        print(error_message)
        text = 'Непредвиденная ошибка,\n' \
               'проверьте НЦГНТЭ https://is.ncste.kz/object/current-state' \
               '({error_message})'
        bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['info'])
def info_handler(message):
    try:
        n_expert, n_find, frame_find = get_info()
        text = f'Всего  {n_summary}  конкурсных заявок\n' \
               f'Не прошли:\n' \
               f'-{n_formal}- заявок по Формальной\n' \
               f'-{n_expert}- заявок по Экпертизе \n' \
               f'На рассмотрении:\n-{n_summary - n_formal - int(n_expert)}-\n' \
               f'\n(https://is.ncste.kz/object/current-state)'
        bot.send_message(message.chat.id, text)
    except Exception as error_message:
        print(error_message)
        text = 'Непредвиденная ошибка,\n'\
               'проверьте НЦГНТЭ https://is.ncste.kz/object/current-state' \
               '({error_message})'
        bot.send_message(message.chat.id, text)


if __name__ == '__main__':
    @bot.message_handler(commands=['stop'])
    def stop(message):
        bot.send_message(message.chat.id, 'бот остановлен')
        bot.stop_polling()
    bot.polling()

