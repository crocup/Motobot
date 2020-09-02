# Motobot

Простой Bot в Telegram для поиска и проверки новых объявлений на moto.av.by.

Внимание! Motobot находится в разработке и поиск обьявлений пока ограничен моделями Honda CB, VFR, VF. 
Если данный простой проект будет интересн, в дальнейшем планируется добавить поиск и автомобилей. 

## Настройка

1. Создаем нового бота в telegram с помощью `@BotFather` и получаем токен.
2. `git clone https://github.com/crocup/Motobot.git`
3. `cd Motobot/src`
4. Открываем файл `config.ini` и вставляем полученный токен
5. Сохраняем файл и возращаемся в директорию Motobot

## Установка
С помощью `docker`
1. docker build -t motobot .
2. docker run motobot

## Запуск

В telegram находим своего созданного бота (Пример: @mybot) и запускаем `/start`
