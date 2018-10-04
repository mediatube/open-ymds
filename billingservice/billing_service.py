import hashlib
import imp

# invoices - коллекция/таблица с объектами инвойсов для каждого пользователя
# один инвойс может быть использован сколько угодно раз - например ежемесячная подписка
# operations - коллекция/таблица с завершенными платежами, может быть несколько уведомлений на один платеж

# Секрет на ваше усмотрение, используется для создания хэша, подписывающего ссылку, токен бота - удобно
# Если изменится какой либо параметр ссылке - сервер может это проверить зная секрет и вычислив хэш
with open('.secret/botsecret.py', 'rb') as fp:
    bottoken = imp.load_module('botsecret', fp, '.secret/botsecret.py', ('.py', 'rb', imp.PY_SOURCE)).bottoken


# Функция, вызываемая через redis удаленно - возвращает ссылку для каждого пользователя, создавая инвойс в базе
def get_invoice_link(user_id: str, months:str, price: str):
    # Генерируем ссылку на инвойс
    param_str = '&{0}&{1}&{2}&{3}'.format(str(user_id), str(months), str(price), bottoken)

    # Хэш с токеном бота в качестве секрета
    hash_sha1 = hashlib.sha1()
    hash_sha1.update(param_str.encode('utf-8'))
    invoice_hash = str(hash_sha1.hexdigest())

    # Конечная ссылка на страницу оплаты
    link = 'https://yourdomain.xyz/generate?page=subscribe' \
           '&uid={0}&months={1}&sum={2}&hash={3}'.format(user_id, months, price, invoice_hash)

    # ID пользователя гарантированно уникален, хэш - нет -> объединяем в метку платежа label
    # По полю label строим индекс в СУБД
    invoice = {'label': f'{user_id}:{invoice_hash}',
               'user_id': f'{user_id}',
               'months': f'{months}',
               'price': f'{price}',
               'link': f'{link}'}
    # Ищем существующий инвойс, если нет - создаем новый
    invoice_id = 'id'  # invoices.find_one({'label': f'{user_id}:{invoice_hash}'})
    if not invoice_id:
        invoice_id = 'id'  # invoices.insert_one(invoice).inserted_id

    # Возвращаем ссылку
    return link


# Эту функцию удаленно вызывает сервер, после получения оповещения и проверки его валидности
def successful_payment_callback(invoice_label: str, operation_id: str, datetime: str):
    # Проверяем - нет ли в базе завершенной операции с таким id - если есть - выходим
    completed = False  # db.operations.find_one({'id': f'{operation_id}'})
    if not completed:
        # Достаем из базы инвойс по уникальной метке
        invoice = {}  # db.invoices.find_one({'label': invoice_label})
        # Вызываем целевую функцию, которая, например подписывает на оплаченный срок
        subscribe_user(int(invoice['user_id']), int(invoice['months']))
        # Добавляем операцию в список завершенных
        operation = {'id': f'{operation_id}', 'datetime': f'{datetime}'}
        completed_id = 'id'  # db.operations.insert_one(operation).inserted_id
        return completed_id
    return


def subscribe_user(user_id: int, months: int):
    # Ваша функция подписки
    return
