import logging
import re
import paramiko
import os
import psycopg2

from psycopg2 import Error
from dotenv import load_dotenv

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

load_dotenv(dotenv_path='./.env')

TOKEN = os.getenv('TOKEN')


# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def ssh(cmd):

    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command(cmd)
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    return data

#МОНИТОРИНГ СИСТЕМЫ
def cmd_release(update: Update, context):
    update.message.reply_text(ssh('lsb_release -a'))
    
def cmd_uname(update: Update, context):
    update.message.reply_text(ssh('uname -a'))
    
def cmd_uptime(update: Update, context):
    update.message.reply_text(ssh('uptime'))
    
def cmd_df(update: Update, context):
    update.message.reply_text(ssh('df -h'))
    
def cmd_free(update: Update, context):
    update.message.reply_text(ssh('free -h'))
    
def cmd_mpstat(update: Update, context):
    update.message.reply_text(ssh('mpstat'))
    
def cmd_w(update: Update, context):
    update.message.reply_text(ssh('w'))
    
def cmd_auths(update: Update, context):
    update.message.reply_text(ssh('last -n 10'))
    
def cmd_critical(update: Update, context): #критических нет, вывожу последние 5
    update.message.reply_text(ssh('cat /var/log/syslog | tail -n 5'))
    
def cmd_ps(update: Update, context):
    ans=ssh('ps aux')
    parts = [ans[i:i + 4000] for i in range(0, len(ans), 4000)] # Отправляем каждую часть как отдельное сообщение
    for part in parts:
        update.message.reply_text(part)
        
def cmd_ss(update: Update, context):
    update.message.reply_text(ssh('ss -tulwn'))
    
def cmd_services(update: Update, context):
    ans=ssh('systemctl --type=service --state=active')
    parts = [ans[i:i + 4000] for i in range(0, len(ans), 4000)] # Отправляем каждую часть как отдельное сообщение
    for part in parts:
        update.message.reply_text(part)
        

#БАЗА    
def cmd_db_logs(update: Update, context):
    update.message.reply_text(ssh('docker ps -aqf "name=db_repl_1" | xargs docker logs'))


def cmd_db_emails(update: Update, context):
    connection = None
    try:
        connection = psycopg2.connect(user=os.getenv('DB_USER'),
                                    password=os.getenv('DB_PASSWORD'),
                                    host=os.getenv('DB_HOST'),
                                    port=os.getenv('DB_PORT'),
                                    database=os.getenv('DB_DATABASE'))

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM emails;")
        data = cursor.fetchall()
        for row in data:
            print(row)
            update.message.reply_text(row)
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
    
def cmd_db_phone_numbers (update: Update, context):
    connection = None
    try:
        connection = psycopg2.connect(user=os.getenv('DB_USER'),
                                    password=os.getenv('DB_PASSWORD'),
                                    host=os.getenv('DB_HOST'),
                                    port=os.getenv('DB_PORT'),
                                    database=os.getenv('DB_DATABASE'))

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM phone_numbers;")
        data = cursor.fetchall()
        for row in data:
            print(row)  
            update.message.reply_text(row)
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
                                      
def db_insert(qerry, table):
    
    logging.basicConfig(
        filename='app.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO, encoding="utf-8"
    )
    if table=="emails":
        arg="email"
    if table=="phone_numbers":
        arg="number"
    connection = None
    
    #sqli фильтр
    if "'" in qerry:
        update.message.reply_text('кавычку свою убрал!')
        return ConversationHandler.END
    if '"' in qerry:
        update.message.reply_text('кавычку свою убрал!')
        return ConversationHandler.END
        

    try:
        connection = psycopg2.connect(user=os.getenv('DB_USER'),
                                    password=os.getenv('DB_PASSWORD'),
                                    host=os.getenv('DB_HOST'),
                                    port=os.getenv('DB_PORT'),
                                    database=os.getenv('DB_DATABASE'))

        cursor = connection.cursor()
        cursor.execute("INSERT INTO "+table+" (ID, "+arg+") VALUES ((select max(ID) from "+table+")+1,'"+qerry+"');")
        connection.commit()
        logging.info("Запись успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
        return "Ошибка при работе с PostgreSQL: %s", error
    finally:
        if connection is not None:
            cursor.close()
            connection.close()    
            return "Запись успешно выполнена"
#ПРОЧЕЕ
def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def helpCommand(update: Update, context):
    update.message.reply_text('Help!')


def find_emailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска почтовых адресов: ')

    return 'find_email'

def find_phone_numberCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'find_phone_number'

def verify_passwordCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки, мы честно ничего не сохраняем :) ')

    return 'verify_password'

def verify_password (update: Update, context):
    user_input = update.message.text
    if len(user_input)<8:
        update.message.reply_text('Пароль должен содержать не менее восьми символов.')
        return ConversationHandler.END 

    re1 = re.compile(r'([A-Z]+)')
    check1 = re1.search(user_input)
    re2 = re.compile(r'([a-z]+)')
    check2 = re2.search(user_input)
    re3 = re.compile(r'([0-9]+)')
    check3 = re3.search(user_input)
    re4 = re.compile(r'([!@#$%^&*()])')
    check4 = re4.search(user_input)

    if check1==None:
        update.message.reply_text('Пароль должен включать как минимум одну заглавную букву (A–Z).')
        return ConversationHandler.END 
    if check2==None:
        update.message.reply_text('Пароль должен включать хотя бы одну строчную букву (a–z).')
        return ConversationHandler.END 
    if check3==None:
        update.message.reply_text('Пароль должен включать хотя бы одну цифру (0–9).')
        return ConversationHandler.END 
    if check4==None:
        update.message.reply_text('Пароль должен включать хотя бы один специальный символ, такой как !@#$%^&*().')
        return ConversationHandler.END 
    update.message.reply_text('Ништяк пароль')
    return ConversationHandler.END 

def get_apt_listCommand (update: Update, context):
    update.message.reply_text('Введите цифру 1 что бы получить все пакеты, либо введите название пакета: ')
    return 'get_apt_list'    

def get_apt_list (update: Update, context):
    user_input = update.message.text 
    if user_input=='1':
        ans = ssh('apt list --installed')
        parts = [ans[i:i + 4000] for i in range(0, len(ans), 4000)] # Отправляем каждую часть как отдельное сообщение
        for part in parts:
            update.message.reply_text(part)
    else:
        invalid_chars_pattern = re.compile(r"[^a-zA-Z0-9]")

        invalid_chars = re.findall(invalid_chars_pattern, user_input)

        if invalid_chars:
            update.message.reply_text("Ты мне тут еще похацкай давай, иди отсюда")
            return ConversationHandler.END
        update.message.reply_text(ssh('apt list '+user_input))
    return ConversationHandler.END 
    
def find_email (update: Update, context):
    user_input = update.message.text 
    mailRegex = re.compile(r'[\w\.\+\-]+@[\w\.\+\-]+')
    mailList = mailRegex.findall(user_input)

    if not mailList: 
        update.message.reply_text('Почты не найдены')
        return ConversationHandler.END 
    
    mails = '' 
    for i in range(len(mailList)):
        mails += f'{i+1}. {mailList[i]}\n'
        
    update.message.reply_text(mails) 
    
    update.message.reply_text('Добавить в базу? 1-да, 2-нет')
    context.user_data.update({'datalist': mailList})
    context.user_data.update({'table': 'emails'})

    return 'confirmation'
                                      
def confirmation (update: Update, context):
    user_input = update.message.text  
    table = context.user_data.get('table')
    datalist = context.user_data.get('datalist')
    if user_input=='1':
        for el in datalist:
            ans = db_insert(el, table)
            ans2="Запись: "+str(el)+" Результат: "+str(ans)
            update.message.reply_text(ans2)
        return ConversationHandler.END
    elif user_input=='2':
        return ConversationHandler.END
    else:
        update.message.reply_text('1 или 2!')
        return
                                      

def find_phone_number (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) номера телефонов
    phoneNumRegex = re.compile(r'[\+7|8][\s(-]{0,3}\d{3}[\s)-]{0,3}\d{3}[\s-]{0,3}\d{2}[\s-]{0,3}\d{2}')
    phoneNumberList = phoneNumRegex.findall(user_input) # Ищем номера телефонов

    if not phoneNumberList: # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END 
    
    phoneNumbers = '' # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n' # Записываем очередной номер
        
    update.message.reply_text(phoneNumbers) # Отправляем сообщение пользователю
    
    update.message.reply_text('Добавить в базу? 1-да, 2-нет')
    context.user_data.update({'datalist': phoneNumberList})
    context.user_data.update({'table': 'phone_numbers'})

    return 'confirmation'


def echo(update: Update, context):
    logging.info("Received message: %s", update.message.text)
    update.message.reply_text(update.message.text)
    
def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher
   
    
    #почта
    convHandlerfind_find_email = ConversationHandler(
        entry_points=[CommandHandler('find_email', find_emailCommand)],
        states={
            'find_email': [MessageHandler(Filters.text & ~Filters.command, find_email)],
            'confirmation': [MessageHandler(Filters.text & ~Filters.command, confirmation)],
        },
        fallbacks=[]
    )
    
    #номер
    convHandlerfind_phone_number = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', find_phone_numberCommand)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, find_phone_number)],
            'confirmation': [MessageHandler(Filters.text & ~Filters.command, confirmation)],
        },
        fallbacks=[]
    )
    
    #пароли
    convHandlerfind_verify_password = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verify_passwordCommand)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verify_password)],
        },
        fallbacks=[]
    )
    
    #вывод пакетов
    convHandlerfind_get_apt_list = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', get_apt_listCommand)],
        states={
            'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, get_apt_list)],
        },
        fallbacks=[]
    )
    

        # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerfind_phone_number) #номер
    dp.add_handler(convHandlerfind_find_email) #почта
    dp.add_handler(convHandlerfind_verify_password) #пароль
    
    #Обработчики под мониторинг 
    dp.add_handler(CommandHandler("get_release", cmd_release))
    dp.add_handler(CommandHandler("get_uname", cmd_uname))
    dp.add_handler(CommandHandler("get_uptime", cmd_uptime))
    dp.add_handler(CommandHandler("get_df", cmd_df))
    dp.add_handler(CommandHandler("get_free", cmd_free))
    dp.add_handler(CommandHandler("get_mpstat", cmd_mpstat))
    dp.add_handler(CommandHandler("get_w", cmd_w))
    dp.add_handler(CommandHandler("get_auths", cmd_auths))
    dp.add_handler(CommandHandler("get_critical", cmd_critical))
    dp.add_handler(CommandHandler("get_ps", cmd_ps))
    dp.add_handler(CommandHandler("get_ss", cmd_ss))
    dp.add_handler(CommandHandler("get_services", cmd_services))
    dp.add_handler(convHandlerfind_get_apt_list)
    
    #обработчики базы
    dp.add_handler(CommandHandler("get_repl_logs", cmd_db_logs)) #логи
    dp.add_handler(CommandHandler("get_emails", cmd_db_emails)) #почты
    dp.add_handler(CommandHandler("get_phone_numbers", cmd_db_phone_numbers)) #номера
    
        # Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))


        # Запускаем бота
    updater.start_polling()

        # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
