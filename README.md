# open-ymds
## Open source yandex money donation service
Прием платежей на Яндекс.Деньги физ. лица
- онлайн платежи с карты, яндекса, телефона
- добавление метки к платежу
- получение и проверка оповещений на свой сервер
- пример автоматизации подписки на Telegram бота

### Модули:
* **money.yandex.ru** - именной кошелек на который получаем деньги

* **httpsserver** - python сервер генерирующий страницы оплаты и принимающий оповещения от яндекса

* **billingservice** - remote процедура, вызываемая после получения оповещения о платеже, работает с базой

* **redis-server** - используется как сервер очередей для удаленного вызова процедур

* **example/telegrambot** - пример генерации ссылок для оплаты Telegram ботом

### money.yandex.ru:
![yandex](/image/ympic.png)
1. Регистрируемся, повышаем статус кошелька до именного
2. НАСТРОЙКИ->ВСЕ ОСТАЛЬНОЕ->HTTP УВЕДОМЛЕНИЯ
   * Добавляем свой домен и секрет
   * Включаем уведомления
3. Поднимаем redis-server, вносим параметры доступа в rq_access.py
4. Получаем SSL сертификат на домен, например через letsencrypt
5. Поднимаем https сервер со своими параметрами, не забываем про фаервол если сервер не доступен
6. Прописываем в httpsserver/.secret/ymsecret.py id кошелька и секрет для уведомлений из настроек
7. Правим httpserver-ympayment.service, запускаем сервер под супервизором
8. На машине с базой правим и запускаем billing.service - запустится rq worker
9. Проверяем удаленный запуск процедур через rq
10. Опираясь на example добавляем генерацию ссылки оплаты в вашу функцию бота

#### Пример работы

Нажимаем **/subscribe** :
- вызывается **generate_subscribe_link()** через **RedisQueue**
- удаленная процедура генерирует ссылку, защищенную от изменений хэшем на основе токена бота
- в базе данных создаются объекты invoce для каждого типа подписки
- через RQ возвращаются ссылки, которые вставляются в отправленное ботом сообщение

Переходим по ссылке:
- попадаем в обработчик GET запроса на httpsserver
- рассчитывается хэш, проверяется валидность ссылки, невалидная отклоняется
- в кнопки подставляются данные из ссылки, в т.ч. label - уникальный идентификатор инвойса
- к платежу прикрепляется label, при успешном платеже яндекс отправляет оповещение POST запросом
- чтобы проверить его валидность - рассчитываем хэш на основе общего с яндексом секрета
- из валидного запроса берем **label и operation_id**, вызываем удаленную процедуру **successful_payment_callback()**
- удаленная процедура проверяет - нет ли такого id в списке завершенных операций, если нет - \
выполняет подписку и вносит **operation_id** в список завершенных операций
- уведомляем пользователя, пишем лог

#### Это и многое другое вот здесь:

[@AudioTubeBot](t.me/AudioTubeBot) - лучший бот для работы с аудио (реально лучший)

[@VideoTubeBot](t.me/VideoTubeBot) - лучший бот для работы с видео (реально лучший)

[@MediaTube_stream](t.me/MediaTube_stream) - канал автора (не самый лучший, но  подписывайтесь)

[@MediaTube_chat](t.me/MediaTube_chat) - чат для вопросов и выражения благодарности

Призываю всех желающих внести посильный вклад и замечания в работу над сервисом
