[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/nalivayev/florentine_abbot/blob/master/README.md)
[![ru](https://img.shields.io/badge/lang-ru-yellow.svg)](https://github.com/nalivayev/florentine_abbot/blob/master/README.ru.md)

# Florentine Abbot

Florentine Abbot — это проект, посвященный сканированию и цифровой организации домашних фотоархивов.

## Архитектура и стандарты

Проект в некоторой степени реализует подходы эталонной модели **OAIS (Open Archival Information System)**, разработанной **[Consultative Committee for Space Data Systems (CCSDS)](https://public.ccsds.org/)** — стандарта для долгосрочного хранения данных, используемого архивами и библиотеками.

OAIS опубликован как:
- **[CCSDS 650.0-M-3](https://public.ccsds.org/Pubs/650x0m3.pdf)** (Pink Book, 2019) — актуальная версия, свободно доступна
- **[ISO 14721:2025](https://www.iso.org/standard/87471.html)** — формальный международный стандарт (идентичен CCSDS 650.0-M-3 по содержанию)

Для оцифровки изображений проект опирается на рекомендации **[Federal Agencies Digital Guidelines Initiative (FADGI)](https://www.digitizationguidelines.gov/)**:
- **[Technical Guidelines for Digitizing Cultural Heritage Materials, 3rd Edition](https://www.digitizationguidelines.gov/guidelines/FADGITechnicalGuidelinesforDigitizingCulturalHeritageMaterials_ThirdEdition_05092023.pdf)** (Май 2023)

Проект реализует три функциональных блока OAIS:

- **Ingest (Прием данных)** реализован в `scan-batcher` и `file-organizer` — автоматизация сканирования, разбор структурированных имен файлов и валидация метаданных
- **Archival Storage (Архивное хранение)** реализовано в `file-organizer` и `archive-keeper` — раскладка файлов, присвоение UUID-идентификаторов, запись метаданных в XMP/EXIF, контроль целостности через SHA-256
- **Access (Доступ)** реализован в `preview-maker` — генерация облегченных JPEG-изображений из мастер-файлов

## Сканирование (Scan Batcher)

Утилита для автоматизации процесса сканирования с помощью [VueScan](https://www.hamrick.com) от Ed Hamrick.

### Зачем это нужно?

VueScan — мощный инструмент, но при потоковом сканировании его гибкость превращается в проблему: сотни настроек на разных вкладках легко случайно изменить или забыть выставить.

Florentine Abbot решает это за счёт эталонных INI‑профилей и автоматизированного процесса, что даёт:
- **Предсказуемость** — одинаковые настройки для каждого скана
- **Воспроизводимость** — точный повтор процесса даже спустя время
- **Стандартизацию** — единый рабочий процесс для команды
- **Автоматизацию** — меньше ручных действий и ниже риск ошибок

### Возможности

- **Автоматический расчёт оптимального DPI сканирования** на основе параметров фотографии и требований к результату.
- **Пакетная обработка**: интерактивный режим, одиночный расчёт или обработка папки.
- **Гибкая система шаблонов** для имён файлов и метаданных, включая извлечение EXIF.
- **Автоматизация рабочего процесса**: запуск VueScan с сгенерированными настройками, перемещение и переименование файлов, извлечение EXIF-метаданных.
- **Подробное логирование** всех этапов работы.
- **Командная строка** с валидацией аргументов и справкой.
- **Плагинная система**: легко расширяйте рабочие процессы, добавляя новые плагины.

### Требования

- Python 3.10+
- [ExifTool](https://exiftool.org/) должен быть установлен и доступен в PATH.

### Использование

Запуск основного рабочего процесса:

```sh
scan-batcher --workflow <путь_к_ini> --engine vuescan --batch scan --min-dpi 300 --max-dpi 4800 --dpis 600 1200 2400 4800
```

Программа **интерактивно запросит** у вас размеры фотографии и изображения во время выполнения.

В Windows PowerShell синтаксис тот же. Если значения содержат пробелы — используйте кавычки:

```powershell
scan-batcher --workflow .\examples\workflow.ini --batch scan --dpis 300 600 1200 2400 --templates author="John Doe" project="Family Archive"
```

Для получения полного списка аргументов и опций используйте:

```sh
scan-batcher --help
```

#### Аргументы командной строки

- `-b, --batch` - Режим пакетной обработки: scan (интерактивный), calculate (одиночный расчёт), или process (обработка папки). По умолчанию: scan
- `-w, --workflow` - Путь к файлу конфигурации рабочего процесса (формат INI) для пакетной обработки
- `-t, --templates` - Список пар ключ-значение для шаблонов имён файлов или метаданных, например `-t year=2024 author=Smith`
- `-e, --engine` - Движок сканирования для обработки (по умолчанию: vuescan)
- `-mnd, --min-dpi` - Минимально допустимое значение DPI для сканирования (необязательно)
- `-mxd, --max-dpi` - Максимально допустимое значение DPI для сканирования (необязательно)
- `-d, --dpis` - Список поддерживаемых сканером разрешений DPI, разделённых пробелом, например `100 300 1200`
- `-r, --rounding` - Стратегия округления: `mx` (максимальное), `mn` (минимальное), `nr` (ближайшее). По умолчанию: nr. Внутри использует enum `RoundingStrategy`

#### Примеры использования

**Интерактивный расчёт DPI (режим scan)**
```sh
scan-batcher --workflow examples/workflow.ini --batch scan --dpis 300 600 1200 2400
```
*Программа запросит у вас размеры фотографии в интерактивном режиме.*

**Одиночный расчёт DPI (режим calculate)**
```sh
scan-batcher --workflow examples/workflow.ini --batch calculate --min-dpi 300 --max-dpi 4800 --dpis 600 1200 2400 4800 --rounding nr
```
*Программа запросит размеры фотографии и изображения, затем завершится после одного расчёта.*

**Обработка файлов из папки**
```sh
scan-batcher --workflow examples/workflow.ini --batch process /path/to/scanned/files --templates author="John Doe" project="Family Archive"
```
*Обработка существующих файлов без интерактивного ввода.*

### Система шаблонов

Шаблоны используются в настройках и именах файлов для подстановки динамических значений.

**Формат шаблона:**

```
{<name>[:length[:align[:pad]]]}
```

- `name` — имя переменной шаблона  
- `length` — итоговая длина (необязательно)  
- `align` — выравнивание (`<`, `>`, `^`; необязательно)  
- `pad` — символ заполнения (необязательно)  

#### Поддерживаемые переменные шаблонов

- `user_name` — имя пользователя операционной системы  
- `digitization_year` — год оцифровки (из EXIF или времени изменения файла)  
- `digitization_month` — месяц оцифровки  
- `digitization_day` — день оцифровки  
- `digitization_hour` — час оцифровки  
- `digitization_minute` — минута оцифровки  
- `digitization_second` — секунда оцифровки  
- `scan_dpi` — значение DPI, выбранное или рассчитанное в ходе пакетной или интерактивной обработки  
- ...а также любые дополнительные переменные, переданные через командную строку (`--templates ключ=значение`) или batch-шаблоны

**Примечание:**  
Если EXIF-метаданные отсутствуют, переменные даты и времени заполняются временем изменения файла.

**Пример:**
```
{digitization_year:8:>:0}
```

## Автоматическая организация (File Organizer)

> **⚠️ Статус**: В разработке. Пока не полностью протестирована или документирована.

Инструмент для автоматической организации отсканированных файлов на основе их имён. Он извлекает метаданные из имени файла (дата, модификаторы, роль по суффиксу) и перемещает каждый файл во вспомогательное дерево `processed/` со следующей структурой:

- `processed/YYYY/YYYY.MM.DD/` — папка конкретной даты (корень дерева для этой даты)
- `processed/YYYY/YYYY.MM.DD/SOURCES/` — RAW, мастер‑копии (`MSR`) и связанные с ними служебные файлы
- `processed/YYYY/YYYY.MM.DD/DERIVATIVES/` — производные файлы (WEB, PRT и другие выходные форматы)
- `processed/YYYY/YYYY.MM.DD/` — файлы `*.PRV.jpg` для быстрого просмотра (просмотровые копии), лежащие прямо в папке даты

Та же информация о дате записывается в теги EXIF/XMP файла. Подробные правила и примеры смотрите в `docs/ru/naming.md` (Части 2 и 3).

### Использование

**Пакетный режим (обработка существующих файлов):**
```sh
file-organizer "D:\Scans\Inbox"
```

**Режим демона (непрерывный мониторинг):**
```sh
file-organizer "D:\Scans\Inbox" --daemon
```

**С метаданными (через JSON-конфиг):**
1. Один раз запустите `file-organizer` без `--config`, чтобы он создал файл конфигурации на основе `config.template.json`.
2. Откройте созданный JSON‑файл (обычно в пользовательском конфиг‑каталоге) и отредактируйте секцию `metadata.languages`. Каждый ключ в `languages` — это языковой код в формате BCP‑47 (например, `"ru-RU"`, `"en-US"`), внутри — блок человекочитаемых полей:

	 ```jsonc
	 "metadata": {
		 "languages": {
			 "ru-RU": {
				 "default": true,
				 "creator": ["Имя Фамилия", "Соавтор"],
				 "credit": "Название архива или коллекции",
				 "description": [
					 "Краткое описание серии или набора снимков.",
					 "Можно в несколько строк."
				 ],
				 "rights": "Текст про права и ограничения.",
				 "terms": "Условия использования (если нужны).",
				 "source": "Физический источник: коробка, альбом и т.п."
			 },
			 "en-US": {
				 "default": false,
				 "creator": ["Name Surname", "Co-author"],
				 "credit": "Archive or collection name",
				 "description": [
					 "Short description of the series or image set.",
					 "Can span multiple lines."
				 ],
				 "rights": "Rights and restrictions text.",
				 "terms": "Usage terms (if needed).",
				 "source": "Physical source: box, album, etc."
			 }
		 }
	 }
	 ```

	 У одного языкового блока должно стоять `"default": true` — его значения дополнительно записываются в «обычные» XMP‑поля (x‑default). Поле `creator` берётся из блока языка по умолчанию и пишется один раз как список имён; остальные текстовые поля (`description`, `credit`, `rights`, `terms`, `source`) пишутся по языкам.

3. При необходимости явно укажите путь к конфигу через `--config`:

```sh
file-organizer "D:\Scans\Inbox" --config "D:\Configs\file-organizer.json"
```

## Preview Maker (генератор PRV)

> **⚠️ Статус**: В разработке. Пока не полностью протестирована или документирована.

Для уже структурированного архива есть вспомогательный инструмент, который может генерировать просмотровые JPEG‑копии `PRV` из источников `RAW`/`MSR`.

- при наличии пары RAW+MSR делает PRV **только из MSR**;
- записывает превью `*.PRV.jpg` в папку даты (родитель `SOURCES/`).
- по умолчанию существующие PRV сохраняются, если не указан `--overwrite`.

Метаданные для превью наследуются от соответствующих мастер‑файлов:
- контекстные EXIF/XMP‑поля (описание, автор, права, источник и т.п.) копируются с `RAW`/`MSR`‑мастера;
- каждый `PRV` получает собственный идентификатор;
- в метаданных фиксируется явная связь (relation) между `PRV` и его мастером.

**Пакетный режим (генерация превью для архива):**
```sh
preview-maker --path "D:\Archive\PHOTO_ARCHIVES" --max-size 2000 --quality 80
```

**С перезаписью существующих PRV:**
```sh
preview-maker --path "D:\Archive\PHOTO_ARCHIVES" --max-size 2400 --quality 85 --overwrite
```

Логи пишутся по тем же правилам, что и у других утилит:
- по умолчанию: `~/.florentine-abbot/logs/preview_maker.log`;
- каталог можно переопределить через `--log-path` или переменную окружения `FLORENTINE_LOG_DIR`.

## Целостность архива (Archive Keeper)

> **⚠️ Статус**: В разработке. Пока не полностью протестирован или документирован. Не входит в устанавливаемый пакет; запускать из исходников.

Инструмент для обеспечения долгосрочной целостности вашего цифрового архива. Он сканирует папку архива, вычисляет хеши SHA-256 всех файлов и сохраняет их в базе данных SQLite. При последующих запусках он обнаруживает:
- **Новые файлы** (Added)
- **Измененные файлы** (Content changed)
- **Перемещенные файлы** (Same content, different path)
- **Пропавшие файлы** (Deleted or moved outside)
- **Поврежденные файлы** (Bit rot detection)

### Использование

Запускайте утилиту напрямую из исходников через модульную точку входа:

```sh
python -m archive_keeper.cli "D:\Archive\Photos"
```

Это создаст файл `archive.db` и заполнит его текущим состоянием архива. Последующие запуски будут сравнивать файловую систему с этой базой данных.

## Технические детали

### Основные модули

- `scan_batcher/cli.py` — основной CLI-модуль (используется для команды `scan-batcher`).
- `archive_keeper/cli.py` — CLI для утилиты `archive-keeper`.
- `file_organizer/cli.py` — CLI для утилиты `file-organizer`.
- `preview_maker/cli.py` — CLI для утилиты `preview-maker`.
- `preview_maker/maker.py` — ядро Preview Maker (логика генерации PRV-превью).
- `scan_batcher/batch.py` — логика пакетных и интерактивных расчётов DPI.
- `scan_batcher/calculator.py` — алгоритмы расчёта DPI.
- `scan_batcher/parser.py` — парсинг и валидация аргументов командной строки.
- `common/logger.py` — единая подсистема логирования для всех утилит.
- `scan_batcher/constants.py` — централизованные константы и перечисления (например, `RoundingStrategy`).
- `scan_batcher/workflow.py` — базовый класс для всех workflow-плагинов.
- `scan_batcher/workflows/__init__.py` — регистрация и обнаружение плагинов.
- `scan_batcher/workflows/vuescan/workflow.py` — автоматизация рабочего процесса VueScan.
- `common/exifer.py` — извлечение и обработка EXIF-метаданных, общая для всех утилит.
 - `common/archive_metadata.py` — централизованная политика архивных метаданных для мастер‑ и производных файлов.

### Установка

#### Требования
- Python 3.10 или выше
- Программа VueScan (для операций сканирования)

#### Установка из исходного кода

Для локальной установки пакета из исходного каталога используйте:

```sh
pip install .
```

Это установит все необходимые зависимости и сделает основные CLI-команды доступными в вашей системе:

- `scan-batcher`
- `file-organizer`
- `preview-maker`

> **Примечание:**  
> Рекомендуется использовать [виртуальное окружение](https://docs.python.org/3/library/venv.html) для установки и разработки.

#### Установка для разработки

Для разработки с редактируемой установкой:

```sh
pip install -e .
```

Для обновления уже установленного пакета используйте:

```sh
pip install --upgrade .
```

### Логирование

Все утилиты записывают логи в централизованное место:

**Расположение по умолчанию:**
- Linux/macOS: `~/.florentine-abbot/logs/`
- Windows: `C:\Users\<имя_пользователя>\.florentine-abbot\logs\`

**Файлы логов:**
- `scan_batcher.log` — активность Scan Batcher
- `file_organizer.log` — активность File Organizer (`file-organizer`)
- `archive_keeper.log` — активность Archive Keeper
 - `preview_maker.log` — активность Preview Maker (`preview-maker`)

**Пользовательское расположение логов:**

Можно переопределить расположение двумя способами:

**1. Параметр командной строки (наивысший приоритет):**
```sh
scan-batcher --log-path /custom/logs --workflow examples/workflow.ini
file-organizer --log-path /custom/logs /path/to/scans
archive-keeper --log-path /custom/logs /path/to/archive
```

**2. Переменная окружения:**
```sh
# Linux/macOS
export FLORENTINE_LOG_DIR=/var/log/florentine-abbot
scan-batcher --workflow examples/workflow.ini

# Windows PowerShell
$env:FLORENTINE_LOG_DIR = "D:\Logs\florentine-abbot"
scan-batcher --workflow examples\workflow.ini
```

**Порядок приоритета:**
1. Параметр `--log-path` (переопределение для одной команды)
2. Переменная окружения `FLORENTINE_LOG_DIR` (для сессии/системы)
3. По умолчанию: `~/.florentine-abbot/logs/`

Это полезно для:
- **Разработки**: быстрое переопределение через `--log-path /tmp/debug`
- **Daemon-режима**: установка через ENV в systemd unit файлах
- **Docker**: настройка через `ENV` в Dockerfile
- **Централизованного логирования**: направление всех утилит в одно место

**Возможности логирования:**
- Единый формат временных меток: `YYYY.MM.DD HH:MM:SS.mmm`
- Автоматическая ротация (10 МБ на файл, 5 резервных копий)
- Вывод в консоль + запись в файл
- Имя модуля и уровень логирования в каждой записи

## Документация

- Индекс документации: [docs/README.ru.md](docs/README.ru.md)
- Руководство по именованию (RU): [docs/ru/naming.md](docs/ru/naming.md)
- Процесс сканирования (RU): [docs/ru/scanning.md](docs/ru/scanning.md)
- Цифровой workflow для born-digital фото (RU): [docs/ru/digital_workflow.md](docs/ru/digital_workflow.md)

---

Для подробностей см. [README.md](README.md) (на английском).
