import logging
import requests

from telegram.ext import Updater, MessageHandler, Filters, CommandHandler


TOKEN = "654743514:AAG4oRRVYuOaWrnzKS3d0lJdDj3_naRVbIg"
SEARCH_URL = 'https://booking.uz.gov.ua/ru/train_search/'
SUCCESS_STATUS_CODE = 200

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

updater = Updater(token=TOKEN)
dispatcher = updater.dispatcher


def get_payload():
    return {
        'from': '2218000',
        'to': '2200001',
        'date': '2018-09-16',
        'time': '00:00',
        'get_tpl': '1'
    }


def to_string(fn):
    def inner(*args, **kwargs):
        train = fn(*args, **kwargs)
        try:
            num = train.pop('num')
        except (KeyError, ValueError, TypeError):
            return train
        str_train = 'Train: {}\n'.format(num)
        for k, v in train.items():
            str_train += '{}: {}\n'.format(k, v)

        return str_train
    return inner


@to_string
def get_response_format(train):
    types = train.get('types', [])
    types = [{
        'id': _type.get('id'),
        'places': _type.get('places'),
        'title': _type.get('title')
    } for _type in types]

    return {
        'allowBooking': train.get('allowBooking'),
        'num': train.get('num'),
        'from': {
            'date': train.get('from', {}).get('date'),
            'time': train.get('from', {}).get('time')
        },
        'to': {
            'date': train.get('to', {}).get('date'),
            'time': train.get('to', {}).get('time')
        },
        'types': types
    }


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")


def echo(bot, update):
    train_number = update.message.text
    logger.info('Train number: {}'.format(train_number))
    response = requests.post(SEARCH_URL, data=get_payload())
    if response.status_code != SUCCESS_STATUS_CODE:
        bot.send_message(chat_id=update.message.chat_id,
                         text='Error response. code: {}; body: {}'
                         .format(response.status_code, response.json()))

    body = response.json()
    try:
        trains = body['data']['list']
    except (KeyError, ValueError, TypeError) as exc:
        logger.error(exc, exc_info=True)
        bot.send_message(chat_id=update.message.chat_id,
                         text='Error format: {}'.format(body))
        return
    count = 0
    for train in trains:
        if train.get('num') == train_number:
            bot.send_message(chat_id=update.message.chat_id, text=get_response_format(train))
            count += 1
    if not count:
        bot.send_message(chat_id=update.message.chat_id, text='Not Found')


start_handler = CommandHandler('start', start)
echo_handler = MessageHandler(Filters.text, echo)

dispatcher.add_handler(echo_handler)
dispatcher.add_handler(start_handler)


def main():
    updater.start_polling()


if __name__ == '__main__':
    main()
