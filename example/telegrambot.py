from . import billing_service
from redis import Redis
from rq import Queue
import imp

with open('.secret/rq_access.py', 'rb') as fp:
    rq_access = imp.load_module('rq_access', fp, '.secret/rq_access.py', ('.py', 'rb', imp.PY_SOURCE))
# Подключаемся к соответствующей очереди redis через которую вызываем удаленные процедуры
redis_conn = Redis(host=rq_access.host, port=rq_access.port, password=rq_access.password)
q_billing = Queue(connection=redis_conn, name='billing', default_timeout=3600)

# Пример функции генерирукщей ссылки из шаблона
def show_pay_subscribe_message(message):
    # Читаем текстовый файл с шаблонами для ссылок
    # ...
    # <b>Подписка 1200 мес</b>
    # 👉<a href="%SUBSCRIBELINK1200%">Yandex Money 600р</a>
    # 👉<a href="%SUBSCRIBELINK1200%">Картой 600р</a>
    # 👉<a href="%SUBSCRIBELINK1200%">С мобильного 600р</a>
    # ...
    # #Генерируем соответствующую ссылку и заменяем в тексте
    # message_to_send = message_to_send.replace('%SUBSCRIBELINK1200%', generate_subscribe_link(user_id, 1200, 600))
    # bot.send_message(chat_id, parse_mode='HTML', text=message_to_send, disable_web_page_preview=True,
    #                  disable_notification=True)
    return


def generate_subscribe_link(user_id, months, price):
    job_dl = q_billing.enqueue(billing_service.get_invoice_link, str(user_id), str(months), str(price))
    while job_dl.result is None:
        job_dl.refresh()
        if job_dl.is_failed:
            raise Exception
    return job_dl.result
