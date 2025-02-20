import requests
import sqlite3
from bs4 import BeautifulSoup
import telebot
from telebot import types
import string

API_TOKEN = 'your_token'
bot = telebot.TeleBot(API_TOKEN)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# Хранение состояния пользователя
user_state = {}


@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Я студент")
    btn2 = types.KeyboardButton("Я преподаватель")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, f"Здравствуйте {message.from_user.first_name}! Вы студент или преподаватель?", reply_markup=markup)
    user_state[message.chat.id] = 'waiting_for_role'


@bot.message_handler(commands=['set_group_or_name'])
def set_gru_or_prep_command(message):
    bot.send_message(message.chat.id, f"Введите группу или ФИО:", reply_markup=telebot.types.ReplyKeyboardRemove())
    user_state[message.chat.id] = 'waiting_for_gru_or_prep'


@bot.message_handler(commands=['set_timeline'])
def set_timeline(message):
    bot.send_message(message.chat.id, f"Введите Ваш логин:", reply_markup=telebot.types.ReplyKeyboardRemove())
    user_state[message.chat.id] = "waiting_for_login"


@bot.message_handler(commands=['help'])
def help_command(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Расписание")
    btn2 = types.KeyboardButton("Частые вопросы")
    btn3 = types.KeyboardButton("Ресурсы РГППУ")
    btn4 = types.KeyboardButton("Проверка таймлайна")
    btn5 = types.KeyboardButton("Связь с преподавателем")
    markup.add(btn1, btn2, btn3)
    markup.row(btn4)
    markup.row(btn5)
    bot.send_message(message.chat.id, f"В случае, если чат-бот Вам не овтечает, проверьте правильность написания группы/ФИО", reply_markup=markup)


@bot.message_handler(commands=['delete'])
def delete_command(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Да")
    btn2 = types.KeyboardButton("Нет")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, f"Вы действительно хотите безвозвратно удалить свои данные?", reply_markup=markup)
    user_state[message.chat.id] = 'waiting_for_confirmation'


@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'waiting_for_gru_or_prep')
def set_gru_or_prep(message):
    gru_or_prep = message.text.strip().lower()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Расписание")
    markup.add(btn1)

    try:
        connect = sqlite3.connect("assistant.db")
        cursor = connect.cursor()
        cursor.execute(f"UPDATE people SET gru_or_prep=? WHERE chat_id=?", (gru_or_prep, message.chat.id))
        connect.commit()
        connect.close()

        bot.send_message(message.chat.id, f"Изменения сохранены!", reply_markup=markup)

    except Exception as ex:
        bot.send_message(message.chat.id, f"Ошибка!", reply_markup=markup)

    del user_state[message.chat.id]


@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'waiting_for_login')
def set_timeline_login(message):
    login = message.text.strip()

    try:
        connect = sqlite3.connect("assistant.db")
        cursor = connect.cursor()
        cursor.execute(f"UPDATE people SET login=? WHERE chat_id=?", (login, message.chat.id))
        connect.commit()
        connect.close()

    except Exception as ex:
        bot.send_message(message.chat.id, f"Ошибка!")
        print(ex)
        del user_state[message.chat.id]

    bot.send_message(message.chat.id, "Введите пароль:")
    user_state[message.chat.id] = "waiting_for_passwd"


@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'waiting_for_passwd')
def set_timeline_passwd(message):
    passwd = message.text.strip()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Расписание")
    btn2 = types.KeyboardButton("Посмотреть баллы")
    btn3 = types.KeyboardButton("Получить ресурсы")
    markup.add(btn1, btn2, btn3)

    try:
        connect = sqlite3.connect("assistant.db")
        cursor = connect.cursor()
        cursor.execute(f"UPDATE people SET passwd=? WHERE chat_id=?", (passwd, message.chat.id))
        connect.commit()
        connect.close()

        bot.send_message(message.chat.id, f"Данные сохранены!", reply_markup=markup)

    except:
        bot.send_message(message.chat.id, f"Ошибка")

    del user_state[message.chat.id]


@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'waiting_for_confirmation')
def delete_user(message):
    user_confirm = message.text.strip().lower()

    if user_confirm == "да":
        try:
            connect = sqlite3.connect("assistant.db")
            cursor = connect.cursor()
            cursor.execute(f"DELETE FROM people WHERE chat_id={message.chat.id}")
            connect.commit()
            connect.close()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("/start")
            markup.add(btn1)
            bot.send_message(message.chat.id, f"Удаление данных успешно завершено!\nЧтобы снова получить доступ к функциям, "
                                              f"требуется перезапуск бота по команде /start", reply_markup=markup)

        except:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("Расписание")
            markup.add(btn1)
            bot.send_message(message.chat.id, f"Ошибка! Возможно вы не указывали группу")

        del user_state[message.chat.id]

    elif user_confirm == "нет":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Расписание")
        markup.add(btn1)
        bot.send_message(message.chat.id, f"Хорошо!", reply_markup=markup)
        del user_state[message.chat.id]

    else:
        bot.send_message(message.chat.id, f"Пожалуйста, используйте кнопки для ответа")
        del user_state[message.chat.id]


@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'waiting_for_role')
def role_response(message):
    user_response = message.text.strip().lower()

    if user_response == "я студент":
        bot.send_message(message.chat.id, "Введите вашу группу:", reply_markup=telebot.types.ReplyKeyboardRemove())
        user_state[message.chat.id] = 'waiting_for_group'
    elif user_response == "я преподаватель":
        bot.send_message(message.chat.id, "Введите ваше ФИО(полностью):", reply_markup=telebot.types.ReplyKeyboardRemove())
        user_state[message.chat.id] = 'waiting_for_name'
    else:
        bot.send_message(message.chat.id, "Пожалуйста, ответьте 'Я студент' или 'Я преподаватель'.")


@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'waiting_for_group')
def group_response(message):
    group = message.text.strip().lower()


    try:
        connect = sqlite3.connect("assistant.db")
        cursor = connect.cursor()
        cursor.execute("INSERT INTO people(chat_id, gru_or_prep) VALUES (?, ?)", (message.chat.id, group))
        connect.commit()
        connect.close()
    except:
        pass

    with open("gru.txt", "r", encoding="utf-8") as kab_file:
        for index, line in enumerate(kab_file):
            if group in line.lower():
                data = line.strip().split()[-1]

                try:
                    response = requests.get(url=f"https://rsvpu.ru/mobile/?v_gru={data}", verify=False)

                    if response.status_code != 200:
                        bot.send_message(message.chat.id, "Группа не найдена")

                    soup = BeautifulSoup(response.text, "lxml")
                    today = soup.find("div", class_="dateBlock")

                    date = today.find("div", class_="dateToday").text  # Дата сегодняшнего дня
                    bot.send_message(message.chat.id, f"Расписание на ближайший день: {date}")

                    lessons_block = today.find("div", class_="tableRasp")
                    lessons = lessons_block.find_all("table", class_="disciplina_cont")

                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    btn1 = types.KeyboardButton("Расписание")
                    btn2 = types.KeyboardButton("Посмотреть баллы")
                    btn3 = types.KeyboardButton("Получить ресурсы")
                    markup.add(btn1, btn2, btn3)

                    for lesson in lessons:
                        start_time = lesson.find("p").text  # Начало пары
                        end_time = lesson.find("div", class_="end-time").text  # Конец пары

                        info = lesson.find("td", class_="disciplina_info")
                        less_type = info.find("div").text  # Тип пары
                        less_name = info.find("p").text  # Название дисциплины
                        less_teacher = info.find("div", class_="prepod view-link").text  # Преподаватель
                        less_place = info.find("div", class_="auditioria view-link").text  # Аудитория

                        bot.send_message(message.chat.id,
                                         f" {start_time}-{end_time} {less_type} \n"
                                         f"{less_name} \n"
                                         f"{less_teacher} {less_place}", reply_markup=markup)

                    del user_state[message.chat.id]  # Удаляем состояние пользователя

                    break

                except Exception as ex:
                    print(f"exeprion: \n {ex}")
                    bot.send_message(message.chat.id, "Неверный ввод")
                break


@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'waiting_for_name')
def name_response(message):
    teacher_name = message.text.strip().lower()

    with open("prep.txt", "r", encoding="utf-8") as prep_file:
        for index, line in enumerate(prep_file):
            if teacher_name in line.lower():
                data = line.strip().split()[3]

                try:
                    response = requests.get(url=f"https://rsvpu.ru/mobile/?v_prep={data}", verify=False)
                    soup = BeautifulSoup(response.text, "lxml")
                    today = soup.find("div", class_="dateBlock")

                    date = today.find("div", class_="dateToday").text  # Дата сегодняшнего дня
                    bot.send_message(message.chat.id, f"Расписание на ближайший день: {date}")

                    lessons_block = today.find("div", class_="tableRasp")
                    lessons = lessons_block.find_all("table", class_="disciplina_cont")

                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    btn1 = types.KeyboardButton("Расписание")
                    markup.add(btn1)

                    for lesson in lessons:
                        start_time = lesson.find("p").text  # Начало пары
                        end_time = lesson.find("div", class_="end-time").text  # Конец пары

                        info = lesson.find("td", class_="disciplina_info")
                        less_type = info.find("div").text  # Тип пары
                        less_name = info.find("p").text  # Название дисциплины
                        less_group = info.find("div", class_="allgroup").text  # Преподаватель
                        less_place = info.find("div", class_="auditioria view-link").text  # Аудитория

                        bot.send_message(message.chat.id,
                                         f" {start_time}-{end_time} {less_type} \n"
                                         f"{less_name} \n"
                                         f"{less_group} {less_place}", reply_markup=markup)

                    del user_state[message.chat.id]  # Удаляем состояние пользователя

                    break

                except Exception as ex:
                    print(f"exeprion: \n {ex}")
                    bot.send_message(message.chat.id, "Неверный ввод")
                break


@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'waiting_for_FIO')
def name_response(message):
    teacher_name = message.text.strip().lower()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Расписание")
    btn2 = types.KeyboardButton("Посмотреть баллы")
    btn3 = types.KeyboardButton("Получить ресурсы")
    markup.add(btn1, btn2, btn3)

    with open("mails.txt", "r", encoding="utf-8") as mails:
        for index, line in enumerate(mails):
            if teacher_name in line.lower():
                mail = line.strip().split()[-1]
                bot.send_message(message.chat.id, f"{string.capwords(teacher_name)}:\n{mail}", reply_markup=markup)
                break


@bot.message_handler(content_types=['text'])
def get_request(message):
    if message.text == "Расписание":

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Расписание")
        btn2 = types.KeyboardButton("Посмотреть баллы")
        btn3 = types.KeyboardButton("Получить ресурсы")
        markup.add(btn1, btn2, btn3)

        connect = sqlite3.connect("assistant.db")
        cursor = connect.cursor()

        sql_req = cursor.execute(f"SELECT gru_or_prep FROM people WHERE chat_id={message.chat.id}")
        group_or_prep = str(sql_req.fetchone()).replace("('", "").replace("',)", "").lower()

        connect.commit()
        connect.close()

        with open("gru.txt", "r", encoding="utf-8") as group_file:
            for index, line in enumerate(group_file):
                if group_or_prep in line.lower():
                    data = line.strip().split()[-1]

                    try:
                        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                        btn1 = types.KeyboardButton("Расписание")
                        btn2 = types.KeyboardButton("Посмотреть баллы")
                        markup.add(btn1, btn2)

                        response = requests.get(url=f"https://rsvpu.ru/mobile/?v_gru={data}", verify=False)

                        if response.status_code != 200:
                            bot.send_message(message.chat.id, "Группа не найдена")

                        soup = BeautifulSoup(response.text, "lxml")
                        today = soup.find("div", class_="dateBlock")

                        date = today.find("div", class_="dateToday").text  # Дата сегодняшнего дня
                        bot.send_message(message.chat.id, f"Расписание на ближайший день: {date}")

                        lessons_block = today.find("div", class_="tableRasp")
                        lessons = lessons_block.find_all("table", class_="disciplina_cont")

                        for lesson in lessons:
                            start_time = lesson.find("p").text  # Начало пары
                            end_time = lesson.find("div", class_="end-time").text  # Конец пары

                            info = lesson.find("td", class_="disciplina_info")
                            less_type = info.find("div").text  # Тип пары
                            less_name = info.find("p").text  # Название дисциплины
                            less_teacher = info.find("div", class_="prepod view-link").text  # Преподаватель
                            less_place = info.find("div", class_="auditioria view-link").text  # Аудитория

                            bot.send_message(message.chat.id,
                                             f" {start_time}-{end_time} {less_type} \n"
                                             f"{less_name} \n"
                                             f"{less_teacher} {less_place}", reply_markup=markup)

                        break

                    except:
                        break

        with open("prep.txt", "r", encoding="utf-8") as prep_file:
            for index, line in enumerate(prep_file):
                if group_or_prep in line.lower():
                    data = line.strip().split()[-1]

                    try:
                        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                        btn1 = types.KeyboardButton("Расписание")
                        btn2 = types.KeyboardButton("Посмотреть баллы")
                        markup.add(btn1, btn2)

                        response = requests.get(url=f"https://rsvpu.ru/mobile/?v_prep={data}", verify=False)
                        soup = BeautifulSoup(response.text, "lxml")
                        today = soup.find("div", class_="dateBlock")

                        date = today.find("div", class_="dateToday").text  # Дата сегодняшнего дня
                        bot.send_message(message.chat.id, f"Расписание на ближайший день: {date}")

                        lessons_block = today.find("div", class_="tableRasp")
                        lessons = lessons_block.find_all("table", class_="disciplina_cont")

                        for lesson in lessons:
                            start_time = lesson.find("p").text  # Начало пары
                            end_time = lesson.find("div", class_="end-time").text  # Конец пары

                            info = lesson.find("td", class_="disciplina_info")
                            less_type = info.find("div").text  # Тип пары
                            less_name = info.find("p").text  # Название дисциплины
                            less_group = info.find("div", class_="allgroup").text  # Группа
                            less_place = info.find("div", class_="auditioria view-link").text  # Аудитория

                            bot.send_message(message.chat.id,
                                             f" {start_time}-{end_time} {less_type} \n"
                                             f"{less_name} \n"
                                             f"{less_group} {less_place}", reply_markup=markup)

                        del user_state[message.chat.id]  # Удаляем состояние пользователя

                        break

                    except Exception as ex:
                        print(f"Exeption: {ex}")
                        break

    if message.text == "Посмотреть баллы":

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Расписание")
        btn2 = types.KeyboardButton("Посмотреть баллы")
        btn3 = types.KeyboardButton("Получить ресурсы")
        markup.add(btn1, btn2, btn3)

        connect = sqlite3.connect("assistant.db")
        cursor = connect.cursor()

        sql_req1 = cursor.execute(f"SELECT login FROM people WHERE chat_id={message.chat.id}")
        login = str(sql_req1.fetchone()).replace("('", "").replace("',)", "")

        sql_req2 = cursor.execute(f"SELECT passwd FROM people WHERE chat_id={message.chat.id}")
        passwd = str(sql_req2.fetchone()).replace("('", "").replace("',)", "")

        connect.commit()
        connect.close()

        if login == "(None,)":
            bot.send_message(message.chat.id, f"Вы ещё не зарегистрировались в системе!")


        elif login != "(None,)":

            data = {
                "Login": login,
                "Password": passwd
            }

            try:
                session = requests.Session()
                response_timeline_form = session.post("https://timeline.rsvpu.ru/Account/OAuthLogin?returnUrl=%2FOAuth20%2FAuth%3Fresponse_type%3Dcode%26client_id%3Deios%26redirect_uri%3Dhttps%253A%252F%252Feios.rsvpu.ru%252Fsignin-timeline%26scope%3DReadUserInfo%26state%3DB9V2XWG2ncN-ue244332BcZXtVbIxV2TS69r5GP15oTwG-FH9NRgc0XDfCI8sTfA1tsz6X3pNIn7jSYYHoKBGXKu3KfOQcS8Ngo8k4pfrHRsK_Abjl5zj_kZoASkDN8H5AG0PP1jaDWW_GpPP2azFxK5e153hUpPYu9dNp3HdFyYW2PGS6jV32b1F7vRSAS7iA4LLQaRyprBIbEGUqRJfn1OHe6BEcLYh9Havy3HqP4", verify=False, data=data)
                if response_timeline_form.status_code != 200:
                    bot.send_message(message.chat.id, "Таймлайн не отвечает!")
                response_timeline = session.get("https://timeline.rsvpu.ru/Timeline", verify=False)
                tl_soup = BeautifulSoup(response_timeline.text, "lxml")
                objects = tl_soup.find_all("tr", class_="moduleRow")

                for object in objects:
                    disciplina = object.find("div", class_="tl-moduleNameCell-moduleName").text.strip()
                    points = object.find("span", class_="timelineTotalPoints").text.strip()
                    possible_points = object.find("span", class_="timelineTotalPossiblePoints").text.strip()

                    bot.send_message(message.chat.id, f"{disciplina}: {points}/{possible_points}", reply_markup=markup)

                session.close()
            except Exception as ex:
                print(ex)
                bot.send_message(message.chat.id, f"Ошибка!", reply_markup=markup)

    if message.text == "Получить ресурсы":

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Расписание")
        btn2 = types.KeyboardButton("Посмотреть баллы")
        btn3 = types.KeyboardButton("Получить ресурсы")
        markup.add(btn1, btn2, btn3)

        connect = sqlite3.connect("assistant.db")
        cursor = connect.cursor()

        sql_req1 = cursor.execute(f"SELECT login FROM people WHERE chat_id={message.chat.id}")
        login = str(sql_req1.fetchone()).replace("('", "").replace("',)", "")

        sql_req2 = cursor.execute(f"SELECT passwd FROM people WHERE chat_id={message.chat.id}")
        passwd = str(sql_req2.fetchone()).replace("('", "").replace("',)", "")

        connect.commit()
        connect.close()

        if login == "(None,)":
            bot.send_message(message.chat.id, f"Вы ещё не зарегистрировались в системе!")


        elif login != "(None,)":

            data = {
                "Login": login,
                "Password": passwd
            }

            try:
                session = requests.Session()
                response_timeline_form = session.post("https://timeline.rsvpu.ru/Account/OAuthLogin?returnUrl=%2FOAuth20%2FAuth%3Fresponse_type%3Dcode%26client_id%3Deios%26redirect_uri%3Dhttps%253A%252F%252Feios.rsvpu.ru%252Fsignin-timeline%26scope%3DReadUserInfo%26state%3DB9V2XWG2ncN-ue244332BcZXtVbIxV2TS69r5GP15oTwG-FH9NRgc0XDfCI8sTfA1tsz6X3pNIn7jSYYHoKBGXKu3KfOQcS8Ngo8k4pfrHRsK_Abjl5zj_kZoASkDN8H5AG0PP1jaDWW_GpPP2azFxK5e153hUpPYu9dNp3HdFyYW2PGS6jV32b1F7vRSAS7iA4LLQaRyprBIbEGUqRJfn1OHe6BEcLYh9Havy3HqP4", verify=False, data=data)
                if response_timeline_form.status_code != 200:
                    bot.send_message(message.chat.id, "Таймлайн не отвечает!")
                response_timeline = session.get("https://timeline.rsvpu.ru/Timeline", verify=False)
                tl_soup = BeautifulSoup(response_timeline.text, "lxml")
                objects = tl_soup.find_all("tr", class_="moduleRow")

                for object in objects:
                    try:
                        disciplina = object.find("div", class_="tl-moduleNameCell-moduleName").text.strip()
                        resource_raw_link = object.find("a", class_="jsLink tl-moduleNameCell-bottomLink")

                        resource_link = resource_raw_link.attrs["href"]
                        source_response = session.get(f"https://timeline.rsvpu.ru{resource_link}", verify=False).text
                        soup_edu = BeautifulSoup(source_response, "lxml")

                        try:
                            edu_res = soup_edu.find_all("li", class_="eduResource")
                            bot.send_message(message.chat.id, f"{disciplina}:", reply_markup=markup)
                            for elem in edu_res:
                                link_res = elem.find("a").attrs["href"]
                                name = elem.find_next("a")
                                new_name = name.find_next("a").text.strip()
                                bot.send_message(message.chat.id, f"{new_name}:\n{link_res}")

                        except:
                            pass

                    except:
                        continue

                session.close()
            except Exception as ex:
                print(ex)
                bot.send_message(message.chat.id, f"Ошибка!", reply_markup=markup)

    if message.text.lower() == "частые вопросы":
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton("Что делать, если был утерян или забыт пароль для входа в ЭИОС РГППУ?",
                                          callback_data="btn1")
        btn2 = types.InlineKeyboardButton("Как обучающемуся зарегистрироваться в ЭИОС РГППУ?",
                                          callback_data="btn2")
        btn3 = types.InlineKeyboardButton("Для чего нужен компонент «Электронное портфолио»?",
                                          callback_data="btn3")
        btn4 = types.InlineKeyboardButton("Что такое личный кабинет в ЭИОС РГППУ?",
                                          callback_data="btn4")
        btn5 = types.InlineKeyboardButton("Для чего нужен компонент «Таймлайн»?",
                                          callback_data="btn5")
        btn6 = types.InlineKeyboardButton("Почему у меня нет ни одной дисциплины?",
                                          callback_data="btn6")
        btn7 = types.InlineKeyboardButton("Где я могу найти тест по дисциплине?",
                                          callback_data="btn7")
        btn8 = types.InlineKeyboardButton("Как добавить результат в своё портфолио?",
                                          callback_data="btn8")
        btn9 = types.InlineKeyboardButton("Для чего нужен компонент «Достижения»?",
                                          callback_data="btn9")
        btn10 = types.InlineKeyboardButton("Почему некоторые прямоугольные блоки окрашены в зеленый и красный цвет, а другие в серый?",
                                          callback_data="btn10")

        markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8, btn9, btn10)

        bot.send_message(message.chat.id, "Список часто задаваемых вопросов:", reply_markup=markup)


    if message.text.lower() == "ресурсы ргппу":
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton("Официальный сайт", url='https://rsvpu.ru')
        btn2 = types.InlineKeyboardButton("Группа ВКонтакте", url='https://m.vk.com/rsvpu_official')
        btn3 = types.InlineKeyboardButton("Контактная информация", url='https://rsvpu.ru/kontakty')
        btn4 = types.InlineKeyboardButton("Медиа-центр", url='https://rsvpu.ru/media-center')
        btn5 = types.InlineKeyboardButton("Подготовительные курсы", url='https://rsvpu.ru/podgotovitelnye-kursy')
        btn6 = types.InlineKeyboardButton("Профессии будущего", url='https://rsvpu.ru/professii-buduschego-v-rgppu')
        btn7 = types.InlineKeyboardButton("ВК Абитуриенту РГППУ", url='https://m.vk.com/abiturientrsvpu')
        btn8 = types.InlineKeyboardButton("Библиотека РГППУ", url='https://rsvpu.ru/informacionno-bibliotechnoe-obsluzhivanie-biblioteka')
        btn9 = types.InlineKeyboardButton("План мероприятий в РГППУ", url='https://rsvpu.ru/deyatelnost')
        btn10 = types.InlineKeyboardButton("Таймлайн РГППУ", url='https://timeline.rsvpu.ru')
        btn11 = types.InlineKeyboardButton("Официальное расписание занятий", url='https://old.rsvpu.ru/raspisanie-zanyatij-ochnoe-otdelenie/')
        btn12 = types.InlineKeyboardButton("Ректорат РГППУ", url='https://rsvpu.ru/rektorat')
        btn13 = types.InlineKeyboardButton("Ютуб канал РГППУ", url='https://www.youtube.com/user/RsvpuVideo')
        btn14 = types.InlineKeyboardButton("Антиплагиат", url='https://rsvpu.antiplagiat.ru')

        markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8, btn9, btn10, btn11, btn12, btn13, btn14)

        bot.send_message(message.chat.id, "Список ресурсов РГППУ:", reply_markup=markup)


    if message.text.lower() == "проверка таймлайна":
        try:
            try_response = requests.get(url="https://timeline.rsvpu.ru", verify=False)
            if try_response.status_code != 200:
                bot.send_message(message.chat.id, f"Таймлайн не работает!")
            elif try_response.status_code == 200:
                bot.send_message(message.chat.id, f"Таймлайн работает!")
        except Exception as exepts:
            bot.send_message(message.chat.id, "Ошибка!")
            print(exepts)


    if message.text.lower() == "связь с преподавателем":
        rm_btn = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "Введите ФИО преподавателя", reply_markup=rm_btn)
        user_state[message.chat.id] = 'waiting_for_FIO'


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        with open("ask_me.txt", "r", encoding="utf-8") as ask_file:
            if call.data == "btn1":
                bot.send_message(call.message.chat.id, f"Что делать, если был утерян или забыт пароль для входа в ЭИОС РГППУ?\n\nПерейдите на страницу входа в ЭИОС РГППУ, нажмите кнопку «Получить пароль». Введите адрес Вашей электронной почты, который был указан при регистрации и нажмите кнопку «Восстановить». На данный адрес придет повторное письмо со ссылкой для получения данных для входа в ЭИОС РГППУ.")
            if call.data == "btn2":
                bot.send_message(call.message.chat.id, "Как обучающемуся зарегистрироваться в ЭИОС РГППУ?\n\nВ срок до 15 сентября текущего учебного года все обучающиеся, поступившие на первый курс, получают данные для входа (логин и пароль) в ЭИОС РГППУ на адрес электронной почты, предоставленный в дирекцию института. Далее, необходимо подтвердить получение данных для входа своей личной подписью в центре «Мои документы» (каб. 0-101). Если письмо с данными для входа не было получено, то необходимо обратиться в дирекцию Вашего института.")
            if call.data == "btn3":
                bot.send_message(call.message.chat.id, "Для чего нужен компонент «Электронное портфолио»?\n\nВ «Электронном портфолио» происходит накопление и обобщение наиболее значимых результатов профессионального и личностного становления будущего специалиста, идентификация собственных достижений в образовательной и внеучебной деятельности.")
            if call.data == "btn4":
                bot.send_message(call.message.chat.id, "Что такое личный кабинет в ЭИОС РГППУ?\n\nЛичный кабинет — это место, где хранятся Ваши данные. Попасть в это пространство Вы можете, используя для входа свой логин и пароль. Личный кабинет в ЭИОС РГППУ предусматривает наличие таких кнопок как «Расписание», «Обучение», «Портфолио», «Мои документы», «Библиотека», «Диалоги», которые позволяют получить доступ к компонентам ЭИОС РГППУ.")
            if call.data == "btn5":
                bot.send_message(call.message.chat.id, "Для чего нужен компонент «Таймлайн»?\n\nКомпонент «Таймлайн» предоставляет доступ обучающимся к учебным материалам, заданиям и текущим баллам читаемых учебных дисциплин. «Таймлайн» построен в формате графика, который предусматривает оптимальное распределение времени при изучении учебных дисциплин.")
            if call.data == "btn6":
                bot.send_message(call.message.chat.id, "Почему у меня нет ни одной дисциплины?\n\nЕсли во вкладке «График» не отображается ни одной дисциплины, скорее всего в текущем семестре данная дисциплина еще не заполнена. Если нужно просмотреть дисциплины за другой семестр, то необходимо в выпадающем списке «Семестр» выбрать интересующий.")
            if call.data == "btn7":
                bot.send_message(call.message.chat.id, "Где я могу найти тест по дисциплине?\n\nВыберите необходимую дисциплину во вкладке «График» компонента «Таймлайн» и откройте блок с изображением галочки в нижнем левом углу. В открывшемся окне нажмите кнопку «Перейти к тесту».")
            if call.data == "btn8":
                bot.send_message(call.message.chat.id, "Как добавить результат в своё портфолио?\n\nДля добавления результата выберите соответствующий раздел в портфолио и нажмите кнопку «Добавить». В соответствующем поле напишите название результата и прикрепите подтверждающие файлы при помощи кнопки «Добавить файл». После чего нажмите кнопку «Сохранить».")
            if call.data == "btn9":
                bot.send_message(call.message.chat.id, "Для чего нужен компонент «Достижения»?\n\nВ компоненте «Достижения» осуществляется фиксация и накопление достижений по направлениям деятельности обучающихся вуза.")
            if call.data == "btn10":
                bot.send_message(call.message.chat.id, "Почему некоторые прямоугольные блоки окрашены в зеленый и красный цвет, а другие в серый?\n\nЗеленый цвет блока означает, что контрольная точка зачтена. Красный – точка требует внимания (либо задание не сдано, либо получен отрицательный результат). Серым цветом выделяются блоки, которые по календарю еще не наступили, они же становятся цветными после прохождения текущей недели. Текущая неделя выделена оранжевым цветом.")


if __name__ == '__main__':
    bot.polling(none_stop=True)