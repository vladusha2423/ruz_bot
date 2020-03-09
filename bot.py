import zulip
import re
import ruz
import csv
import datetime

BOT_MAIL = "hse-bot@chat.miem.hse.ru"
HSE_API = "https://www.hse.ru/api/timetable/lessons?"
DaysOfWeek = {
    'Пн': 'Понедельник',
    'Вт': 'Вторник',
    'Ср': 'Среда',
    'Чт': 'Четверг',
    'Пт': 'Пятница',
    'Сб': 'Суббота',
    'Вс': 'Воскресенье'
}
HELLO_MESSAGE = '''
Доброго времени суток!

Я, HSE_bot, призван помочь узнавать расписание прямо здесь, в диалоге со мной :)

Есть один момент. Если Вы преподаватель, то для корректного вывода расписания вам надо дать мне понять об этом.
Для этого напишите мне какое-нибудь сообщение, содержащее ключевое слово "преподаватель".

Пример: "Я - преподаватель".

Перейдем к расписанию. 
Самый быстрый способ его узнать - написать мне сообщение с одним только ключевым словом "Расписание".

Пример: "Покажи мне расписание!" или просто "расписание"

Такой способ показывает положение дел на текущую неделю.
Если нужно конкретнее указать, на какой день или на какой период расписание необходимо, есть несколько способов:

"Расписание на сегодня"
"Расписание на завтра"
"Расписание на dd.MM.yyyy" - Будьте внимательны. Число всегда содержит две цифры (5 мая 2020 года = 05.05.2020).
"Расписание на dd.MM.yyyy-dd.MM.yyyy" - на период

Также, есть возможность узнать расписание приятеля или преподавателя. 
Нужно всего лишь знать его корпоративную почту и добавить в конец сообщения фразу "для xxx@edu.hse.ru".

Пример: "расписание на завтра для msmeladze@hse.ru"

Чтобы уточнить список команд, отправь мне сообщение с ключевым словом "Помощь".
  
'''
HELP_MESSAGE = '''
Доброго времени суток!

Я, HSE_bot, призван помочь узнавать расписание прямо здесь, в диалоге со мной :)

Самый быстрый способ - написать мне сообщение с одним только ключевым словом "Расписание".

Пример: "Покажи мне расписание!" или просто "расписание"

Такой способ показывает положение дел на текущую неделю.
Если нужно конкретнее указать, на какой день или на какой период расписание необходимо, есть несколько способов:

"Расписание на сегодня"
"Расписание на завтра"
"Расписание на dd.MM.yyyy" - Будьте внимательны. Число всегда содержит две цифры (5 мая 2020 года = 05.05.2020).
"Расписание на dd.MM.yyyy-dd.MM.yyyy" - на период

Также, есть возможность узнать расписание приятеля или преподавателя. 
Нужно всего лишь знать его корпоративную почту и добавить в конец сообщения фразу "для xxx@edu.hse.ru".

Пример: "расписание на завтра для msmeladze@hse.ru"

Если Вы преподаватель, то для корректного вывода расписания вам надо дать мне понять об этом.
Для этого напишите мне какое-нибудь сообщение, содержащее ключевое слово "преподаватель".

Пример: "Я - преподаватель".
  
'''

def check_csv(id):
    with open('teacher_id.csv', "r") as file:
        reader = csv.reader(file)
        for row in reader:
            if id == int(row[0]):
                return 'hse.ru'
    return 'edu.hse.ru'


class MyBotHandler(object):
    def __init__(self):
        self.client = zulip.Client(config_file="zuliprc")

    def get_msg(self, msg):
        if msg["sender_email"] != "hse-bot@chat.miem.hse.ru":
            for i in msg.keys():
                print(i, ':', msg[i])
            # self.send_msg(msg["sender_email"], msg["content"])
            self.check_msg(msg["sender_email"], msg["content"], msg["sender_id"], msg["type"])

    def send_msg(self, sender_email, content):
        request = {
            "type": "private",
            "to": sender_email,
            "content": content
        }
        self.client.send_message(request)

    def get_lessons(self, email, date_start='', date_end='', sender_id=0, other_email=''):
        if other_email != '':
            if date_start != '' and date_end != '':
                response = ruz.person_lessons(other_email, date_start, date_end)
            else:
                response = ruz.person_lessons(other_email)
        else:
            if date_start != '' and date_end != '':
                response = ruz.person_lessons(email.replace('miem.hse.ru', check_csv(sender_id)), date_start, date_end)
            else:
                response = ruz.person_lessons(email.replace('miem.hse.ru', check_csv(sender_id)))
        message = ''
        curr_date = ''
        print('LESSSSSSONS: \n', response)
        for lesson in response:
            if curr_date != lesson['date']:
                message += DaysOfWeek[lesson['dayOfWeekString']] + ':: ' + lesson['date'] + '\n'
                curr_date = lesson['date']
            message += str(lesson['lessonNumberStart']) + ' пара (' + \
                       lesson['beginLesson'] + '-' + lesson['endLesson'] + ')\n' +\
                       lesson['discipline'] + '\n' + \
                       lesson['kindOfWork'] + '\n' + \
                       lesson['auditorium'] + ' (' + lesson['building'] + ')' + '\n' +\
                       lesson['lecturer'] + '\n\n'
        self.send_msg(email, message)

    def check_msg(self, sender_email, content, sender_id, mtype):
        words = content.lower().split()
        if mtype == 'private' or '@**HSE_bot**' in words:
            if "расписание" in words:
                if 'сегодня' in words:
                    today = datetime.datetime.now().date().isoformat().replace('-', '.')
                    if 'для' in words:
                        self.get_lessons(sender_email, date_start=today, date_end=today, sender_id=sender_id,
                                         other_email=words[words.index('для') + 1])
                    else:
                        self.get_lessons(sender_email, date_start=today, date_end=today, sender_id=sender_id)
                elif 'завтра' in words:
                    tomorrow = (datetime.datetime.now() + datetime.timedelta(1)).date().isoformat().replace('-', '.')
                    if 'для' in words:
                        self.get_lessons(sender_email, date_start=tomorrow, date_end=tomorrow, sender_id=sender_id,
                                         other_email=words[words.index('для') + 1])
                    else:
                        self.get_lessons(sender_email, date_start=tomorrow, date_end=tomorrow, sender_id=sender_id)
                else:
                    date = re.search(r'\d\d.\d\d.\d{4}', content)
                    if date:
                        start = content.index(date.group())
                        date_end = re.search(r'\d\d.\d\d.\d{4}', content[start + 10:])
                        if date_end:
                            if 'для' in words:
                                self.get_lessons(sender_email, date_start=reverse_date(date.group()),
                                                 date_end=reverse_date(date_end.group()), sender_id=sender_id,
                                                 other_email=words[words.index('для') + 1])
                            else:
                                self.get_lessons(sender_email, date_start=reverse_date(date.group()),
                                                 date_end=reverse_date(date_end.group()), sender_id=sender_id)
                        else:
                            if 'для' in words:
                                self.get_lessons(sender_email, date_start=reverse_date(date.group()),
                                                 date_end=reverse_date(date.group()), sender_id=sender_id,
                                                 other_email=words[words.index('для') + 1])
                            else:
                                self.get_lessons(sender_email, date_start=reverse_date(date.group()), date_end=reverse_date(date.group()), sender_id=sender_id)
                    else:
                        if 'для' in words:
                            self.get_lessons(sender_email, sender_id=sender_id,
                                             other_email=words[words.index('для') + 1])
                        else:
                            self.get_lessons(sender_email, sender_id=sender_id)
            elif "преподаватель" in words:
                with open('teacher_id.csv', "w", newline='') as csv_file:
                    writer = csv.writer(csv_file, delimiter=',')
                    writer.writerow([sender_id])
            elif "привет" in words:
                self.send_msg(sender_email, HELLO_MESSAGE)
            elif "помощь" in words:
                self.send_msg(sender_email, HELP_MESSAGE)
            else:
                self.send_msg(sender_email, "Не знаю что и ответить :(. \n"
                                            "Чтобы узнать какие у меня есть команды, напиши 'Помощь'")


def reverse_date(date):
    list_date = list(map(str, date.split('.')))
    print(list_date)
    if len(list_date[0]) == 1:
        list_date[0] = '0' + list_date[0]
    res_date = '.'.join(list_date[::-1])
    return res_date


# Bot = MyBotHandler()
# Bot.client.call_on_each_message(Bot.get_msg)
handler_class = MyBotHandler


