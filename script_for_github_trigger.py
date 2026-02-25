import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime

# --- НАСТРОЙКИ TELEGRAM ---
TELEGRAM_TOKEN = "8512162352:AAEOdKxFMSD644yR7VAYdRr8lUzojJ8vLr8"
TELEGRAM_CHAT_ID = "-1003561345068"

# --- КОНСТАНТЫ ---
BASE_URL = "https://pass.rw.by/ru/route/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",  # Пытаемся запросить JSON/AJAX для стабильности
    "Referer": "https://pass.rw.by",
}

STATIONS = {
    "Минск": {"exp": "2100000", "esr": "140210"},
    "Гомель": {"exp": "2100100", "esr": "150000"},
    "Брест": {"exp": "2100250", "esr": "130006"},
    "Витебск": {"exp": "2100005", "esr": "160002"},
    "Могилев": {"exp": "2100150", "esr": "156609"},
    "Гродно": {"exp": "2100110", "esr": "136005"}
}

def send_telegram(message):
    """Отправка сообщения в Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
        time.sleep(2)
    except Exception as e:
        print(f"Ошибка отправки в TG: {e}")

def get_user_params():
    print("--- Настройка авто-мониторинга билетов (2026) ---")
    #f_city = input("Откуда (напр. Гомель): ").strip().capitalize()
    #t_city = input("Куда (напр. Минск): ").strip().capitalize()
    #date_val = input("Дата (ГГГГ-ММ-ДД, напр. 2026-03-08): ").strip()
    #target_time_input = input("На какие времена ищем поезд? (пример: 07:00, 12:30 или 'все'): ").strip()
    f_city = "Гомель"
    t_city = "Минск"
    date_val = "2026-03-08"
    target_time_input = "07:00, 19:08"
    f_info = STATIONS.get(f_city, {"exp": "", "esr": ""})
    t_info = STATIONS.get(t_city, {"exp": "", "esr": ""})

    # Поддержка нескольких времен:
    # - если введено 'все' (без учёта регистра), ищем все поезда
    # - иначе разбиваем по запятой и trimming
    raw = target_time_input.lower()
    if raw == "все":
        target_times = ["все"]
    else:
        target_times = [t.strip() for t in target_time_input.split(",") if t.strip()]

    return {
        "params": {
            "from": f_city, "from_exp": f_info["exp"], "to": t_city, "to_exp": t_info["exp"], "date": date_val
        },
        "target_times": target_times
    }


def check_tickets(params, target_times):
    """Один цикл проверки билетов. Поддерживает несколько целевых времен."""
    try:
        with requests.Session() as session:
            # БЖД часто требует сначала зайти на страницу поиска для установки куки
            init_url = f"{BASE_URL}?from={params['from']}&to={params['to']}&date={params['date']}"
            session.get(init_url, headers=HEADERS, timeout=15)

            # Затем делаем запрос к поисковому API
            response = session.get(BASE_URL, params=params, headers=HEADERS, timeout=15)

            if "application/json" in response.headers.get("Content-Type", ""):
                html_content = response.json().get('html', '')
            else:
                html_content = response.text

            soup = BeautifulSoup(html_content, 'html.parser')
            train_rows = soup.find_all(class_='sch-table__row-wrap')

            now = datetime.now().strftime("%H:%M:%S")
            found_total = 0
            messages_to_send = []

            for row in train_rows:
                time_tag = row.find(class_='train-from-time')
                dep_time = time_tag.get_text(strip=True) if time_tag else ""

                # Разрешаем поиск либо по конкретному времени, либо по всем
                if "все" not in target_times:
                    if dep_time not in target_times:
                        continue

                ticket_items = row.find_all(class_='sch-table__t-item')
                current_type = ""

                found_now = []
                last_found_count = 0

                for item in ticket_items:
                    name_tag = item.find(class_='sch-table__t-name')
                    if name_tag and name_tag.get_text(strip=True):
                        current_type = name_tag.get_text(strip=True)

                    price_tag = item.find(class_='ticket-cost')
                    if price_tag:
                        try:
                            price = float(price_tag.get_text(strip=True).replace(',', '.'))
                        except ValueError:
                            continue

                        if "Сидячий" in current_type and 20.0 <= price <= 26.0:
                            q_tag = item.find(class_='sch-table__t-quant')
                            count = int(q_tag.find('span').get_text(strip=True)) if q_tag else 0

                            if count > 0:
                                print(f"[{now}] 🔥 НАЙДЕНО! Поезд {dep_time}: {count} мест по {price} BYN")
                                found_total += count
                                found_now.append(f"🚆 {dep_time}: {count} мест по {price} BYN")

                if found_now:
                    message = f"<b>🔥 НАЙДЕНЫ БИЛЕТЫ!</b>\n" + "\n".join(found_now)
                    # Подготовим сообщения на основе времени (плюс можно объединять все в одно)
                    messages_to_send.append(message)
                    # Считаем кол-во найденных мест для общего контроля
                    current_total = len(found_now)
                    if current_total != last_found_count:
                        last_found_count = current_total
                    print(f"[{now}] ✅ Билеты найдены для времени {dep_time}.")

            if messages_to_send:
                # Объединяем все найденные блоки в одно сообщение
                full_message = "\n\n".join(messages_to_send)
                send_telegram(full_message)
                print(f"[{now}] 🔔 Отправлено уведомление в Telegram.")
                return True
            else:
                print(f"[{now}] Мест нет.")
                return False

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка связи: {e}")
        return False


def main():
    config = get_user_params()
    #print(f"\nЗапущен мониторинг. Проверка каждую минуту...")

    success = check_tickets(config['params'], config['target_times'])

    #while True:
        #success = check_tickets(config['params'], config['target_times'])

        # Если билеты найдены, можно либо остановить цикл, либо продолжать
        # if success: break

        #time.sleep(60)  # Интервал в секундах


if __name__ == "__main__":
    main()
