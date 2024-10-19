RU_ru = {
    '/start': """{}, добро пожаловать, для того чтобы получить полный доступ, необходимо зарегистрироваться

Введите /register чтобы запустить процесс регистрации

Если я завис при выполнении чего-либо, напишите /start, либо /menu или вызовите соответствующие команды из бокового меню.""",
    '/start_unsuccessful': """Приветствую, к сожалению не узнал Вас.
Если Вы являетесь членом команды, 
попросите добавить вас в белый список, 
чтобы начать пользоваться моими функциями
    """,

    'not_admin': """Вы не можете пользоваться этой функцией.

Если вы считаете, что это ошибка, то обратитесь к администратору

<i>Ваш ID: <code>{}</code></i>""",

    'not_employee': """Для начала вам необходимо зарегистрироваться

Введите /register чтобы запустить процесс регистрации""",

    'empty': 'Пусто',

    'admin': 'Админ панель',

    'white_list': 'Белый список',

    'navigation': {
        'location': 'Отправить геолокацию',
        'open': 'Открыть смену',
        'close': 'Закрыть смену',
        'stats': 'Статистика',
        'name': 'Имя',
        'phone': 'Номер телефона',
        'job_title': 'Должность',
        'share': 'Поделиться',
        'done': 'Готово',
        'settings': 'Настройки',
        'menu': 'Главное меню',
        'yes': 'Да',
        'no': 'Нет',
        'back': 'Назад',
        'receive_upd': 'Обновление смен',
        'receive_time': 'Отработанное время',
        'receive_messages': 'Иные уведомления',
        'white_list': 'Белый список',
    },

    'settings': """<b>Настройки</b>

Имя: {}
Номер телефона: {}

Получать уведомления об открытых/закрытых сменах: {}
Получать уведомления об отработанных часах: {}
Получать иные уведомления: {}
""",

    'error': """{}, что-то пошло не так, попробуйте снова через 5 минут.
Если ошибка повториться, пожалуйста, обратитесь к разработчику""",

    'shift': {
        'sure_close': "{}, Вы уверены, что хотите закрыть личную смену?",
        'sure_open': "{}, Вы уверены, что хотите открыть личную смену?",
        'close_success': """{}, Ваша смена успешно закрыта!
Часов отработано: ~~~""",
        'open_success': 'Готово! Ваша смена была открыта в {}',
        'open': {
            'location': '{}, пожалуйста, отправьте вашу геолокацию, чтобы я мог удостовериться, что вы находитесь на рабочем месте',
            'location_success': 'Отлично, выберите, где желаете открыть смену:',
            'location_fail': """К сожалению, я не могу открыть вам смену, так как вы находитесь далеко.

Если вы считаете, что это ошибка - попробуйте снова
Если ошибка повториться, откройте смену вручную и сообщите об этом администратору""",
        }
    },
    'server': {
        'shift_open': """{}, ваша смена была успешно открыта
<b>Время открытия: {}</b>""",
        'shift_close': """{}, ваша смена была успешно закрыта
<b>Время закрытия: {}
Отработано: {}</b>""",
        'stop_list_update': """<b>Новые позиции в стоп-листе:</b>
        
    {}

<b>Стоп-лист на данный момент:</b>

{}
        """
    },

    'unknown': 'Неизвестно',

    'register': {
        'start': """{}, для успешной регистрации необходимо предоставить ваши данные

Нажимая на соответсвующую кнопку, вы можете добавлять или изменять данные""",
        'name': """<b>Регистрация</b>

Для корректной работы отправьте вашу фамилию и имя в формате:
<b>Иванов Александр</b>""",
        'phone': """<b>Регистрация</b>
        
Для того, чтобы сохранить ваш номер телефона - нажмите на кнопку внизу экрана""",

        'info': """<b>Регистрация</b>

Имя - <b>{}</b>
Номер телефона - <b>{}</b>""",

        'save': """Регистрация завершена, теперь вы можете пользоваться всеми моими функциями"""
    }

}

commands = [
    {'command': '/menu', 'description': 'Главное меню'},
    {'command': '/help', 'description': 'Помощь'},
    {'command': '/start', 'description': 'Возврат к началу или обновить бота'},
    ]