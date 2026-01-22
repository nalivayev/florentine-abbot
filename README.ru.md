[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/nalivayev/florentine-abbot/blob/master/README.md)
[![ru](https://img.shields.io/badge/lang-ru-yellow.svg)](https://github.com/nalivayev/florentine-abbot/blob/master/README.ru.md)

# Scan Batcher

Scan Batcher — это проект, посвященный сканированию и цифровой организации домашних фотоархивов.

## Архитектура и стандарты

Проект в некоторой степени реализует подходы эталонной модели **OAIS (Open Archival Information System)**, разработанной **[Consultative Committee for Space Data Systems (CCSDS)](https://public.ccsds.org/)** — стандарта для долгосрочного хранения данных, используемого архивами и библиотеками.

OAIS опубликован как:
- **[CCSDS 650.0-M-3](https://public.ccsds.org/Pubs/650x0m3.pdf)** (Pink Book, 2019) — актуальная версия, свободно доступна
- **[ISO 14721:2025](https://www.iso.org/standard/87471.html)** — формальный международный стандарт (идентичен CCSDS 650.0-M-3 по содержанию)

Проект реализует функциональный блок OAIS **Ingest (Приём данных)**: автоматизацию сканирования, разбор структурированных имён файлов и запись метаданных (XMP/EXIF).

Для оцифровки изображений проект также опирается на рекомендации **[Federal Agencies Digital Guidelines Initiative (FADGI)](https://www.digitizationguidelines.gov/)**:
- **[Technical Guidelines for Digitizing Cultural Heritage Materials, 3rd Edition](https://www.digitizationguidelines.gov/guidelines/FADGITechnicalGuidelinesforDigitizingCulturalHeritageMaterials_ThirdEdition_05092023.pdf)** (май 2023)

Для кодирования и сохранения метаданных используется **[XMP (Extensible Metadata Platform)](https://www.adobe.com/devnet/xmp.html)**:
- **[ISO 16684-1:2019](https://www.iso.org/standard/75163.html)** — Extensible metadata platform (XMP) — Часть 1: Модель данных, сериализация и основные свойства
- **[XMP Specification Part 2: Additional Properties](https://github.com/adobe/xmp-docs/tree/master/XMPSpecifications)** (Adobe) — расширенные пространства имён, включая XMP Media Management (xmpMM) для отслеживания истории файлов

## Сканирование

Утилита для автоматизации процесса сканирования с помощью внешнего сканирующего ПО (например, [VueScan](https://www.hamrick.com) от Ed Hamrick).

### Зачем это нужно?

Современные программы сканирования — мощные и гибкие, но при потоковой работе их множество настроек легко превращается в проблему: параметры разбросаны по разным вкладкам, их просто забыть скорректировать или случайно сбросить.

Scan Batcher решает это за счёт эталонных профилей и автоматизированного процесса, что даёт:
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

## Технические детали

### Основные модули

- `scan_batcher/cli.py` — основной CLI-модуль (используется для команды `scan-batcher`).
- `scan_batcher/batch.py` — логика пакетных и интерактивных расчётов DPI.
- `scan_batcher/calculator.py` — алгоритмы расчёта DPI.
- `scan_batcher/parser.py` — парсинг и валидация аргументов командной строки.
- `common/logger.py` — единая подсистема логирования.
- `scan_batcher/constants.py` — централизованные константы и перечисления (например, `RoundingStrategy`).
- `scan_batcher/workflow.py` — базовый класс для всех workflow-плагинов.
- `scan_batcher/workflows/__init__.py` — регистрация и обнаружение плагинов.
- `scan_batcher/workflows/vuescan/workflow.py` — автоматизация рабочего процесса VueScan.
- `common/exifer.py` — извлечение и обработка EXIF-метаданных.

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

Логи записываются в централизованное место:

**Расположение по умолчанию:**
- Linux/macOS: `~/.scan-batcher/logs/`
- Windows: `C:\Users\<имя_пользователя>\.scan-batcher\logs\`

**Файл лога:**
- `scan_batcher.log` — активность Scan Batcher

**Пользовательское расположение логов:**

Можно переопределить расположение двумя способами:

**1. Параметр командной строки (наивысший приоритет):**
```sh
scan-batcher --log-path /custom/logs --workflow examples/workflow.ini
```

**2. Переменная окружения:**
```sh
# Linux/macOS
export SCAN_BATCHER_LOG_DIR=/var/log/scan-batcher
scan-batcher --workflow examples/workflow.ini

# Windows PowerShell
$env:SCAN_BATCHER_LOG_DIR = "D:\Logs\scan-batcher"
scan-batcher --workflow examples\workflow.ini
```

**Порядок приоритета:**
1. Параметр `--log-path` (переопределение для одной команды)
2. Переменная окружения `SCAN_BATCHER_LOG_DIR` (для сессии/системы)
3. По умолчанию: `~/.scan-batcher/logs/`

Это полезно для:
- **Разработки**: быстрое переопределение через `--log-path /tmp/debug`
- **Docker**: настройка через `ENV` в Dockerfile

**Возможности логирования:**
- Единый формат временных меток: `YYYY.MM.DD HH:MM:SS.mmm`
- Автоматическая ротация (10 МБ на файл, 5 резервных копий)
- Вывод в консоль + запись в файл
- Имя модуля и уровень логирования в каждой записи

## Документация

- Индекс документации: [docs/README.ru.md](docs/README.ru.md)
- Руководство по именованию (RU): [docs/ru/naming.md](docs/ru/naming.md)
- Процесс сканирования (RU): [docs/ru/scanning.md](docs/ru/scanning.md)

---

Для подробностей см. [README.md](README.md) (на английском).
