[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/nalivayev/florentine_abbot/blob/master/README.md)
[![ru](https://img.shields.io/badge/lang-ru-yellow.svg)](https://github.com/nalivayev/florentine_abbot/blob/master/README.ru.md)
[![by](https://img.shields.io/badge/lang-by-green.svg)](https://github.com/nalivayev/florentine_abbot/blob/master/README.by.md)

# Florentine Abbot

Florentine Abbot — гэта праект, прысвечаны сканаванню і лічбавай арганізацыі хатніх фотаархіваў.

## Архітэктура і стандарты

Праект у некаторай ступені рэалізуе падыходы эталоннай мадэлі **OAIS (Open Archival Information System)**, распрацаванай **[Consultative Committee for Space Data Systems (CCSDS)](https://public.ccsds.org/)** — стандарту для доўгатэрміновага захоўвання даных, які выкарыстоўваецца архівамі і бібліятэкамі.

OAIS апублікаваны як:
- **[CCSDS 650.0-M-3](https://public.ccsds.org/Pubs/650x0m3.pdf)** (Pink Book, 2019) — актуальная версія, свабодна даступная
- **[ISO 14721:2025](https://www.iso.org/standard/87471.html)** — фармальны міжнародны стандарт (ідэнтычны CCSDS 650.0-M-3 па змеце)

Праект рэалізуе тры функцыянальныя блокі OAIS:

- **Ingest (Прыём даных)** рэалізаваны ў `scan-batcher` і `file-organizer` — аўтаматызацыя сканавання, разбор структураваных імёнаў файлаў і валідацыя метаданых
- **Archival Storage (Архіўнае захоўванне)** рэалізавана ў `file-organizer` і `archive-keeper` — раскладка файлаў, прысваенне UUID-ідэнтыфікатараў, запіс метаданых у XMP/EXIF, кантроль цэласнасці праз SHA-256
- **Access (Доступ)** рэалізаваны ў `preview-maker` — генерацыя палегчаных JPEG-выяў з майстар-файлаў

Для аблічбоўкі выяў праект таксама абапіраецца на рэкамендацыі **[Federal Agencies Digital Guidelines Initiative (FADGI)](https://www.digitizationguidelines.gov/)**:
- **[Technical Guidelines for Digitizing Cultural Heritage Materials, 3rd Edition](https://www.digitizationguidelines.gov/guidelines/FADGITechnicalGuidelinesforDigitizingCulturalHeritageMaterials_ThirdEdition_05092023.pdf)** (май 2023)

Для кадавання і захавання метаданых выкарыстоўваецца **[XMP (Extensible Metadata Platform)](https://www.adobe.com/devnet/xmp.html)**:
- **[ISO 16684-1:2019](https://www.iso.org/standard/75163.html)** — Extensible metadata platform (XMP) — Частка 1: Мадэль даных, серыялізацыя і асноўныя ўласцівасці
- **[XMP Specification Part 2: Additional Properties](https://github.com/adobe/xmp-docs/tree/master/XMPSpecifications)** (Adobe) — пашыраныя прасторы імёнаў, уключаючы XMP Media Management (xmpMM) для адсочвання гісторыі файлаў

## Сканаванне (Scan Batcher)

Утыліта для аўтаматызацыі працэсу сканавання з дапамогай знешняга ПЗ для сканавання (напрыклад, [VueScan](https://www.hamrick.com) ад Ed Hamrick).

### Навошта гэта трэба?

Сучасныя праграмы сканавання — магутныя і гнуткія, але пры патокавай працы мноства налад лёгка ператвараецца ў праблему: параметры раскіданыя па розных укладках, іх проста забыць скарэктаваць ці выпадкова скінуць.

Florentine Abbot вырашае гэта за кошт эталонных профіляў і аўтаматызаванага працэсу, што дае:
- **Прадказальнасць** — аднолькавыя налады для кожнага скана
- **Узнаўляльнасць** — дакладны паўтор працэсу нават праз час
- **Стандартызацыю** — адзіны працоўны працэс для каманды
- **Аўтаматызацыю** — менш ручных дзеянняў і ніжэйшая рызыка памылак

### Магчымасці

- **Аўтаматычны разлік аптымальнага DPI сканавання** на аснове параметраў фотаздымка і патрабаванняў да выніку.
- **Пакетная апрацоўка**: інтэрактыўны рэжым, адзіночны разлік або апрацоўка папкі.
- **Гнуткая сістэма шаблонаў** для імёнаў файлаў і метаданых, уключаючы выманне EXIF.
- **Аўтаматызацыя працоўнага працэсу**: запуск VueScan са згенераванымі наладамі, перамяшчэнне і перайменаванне файлаў, выманне EXIF-метаданых.
- **Падрабязнае лагіраванне** ўсіх этапаў працы.
- **Камандны радок** з валідацыяй аргументаў і даведкай.
- **Плагінная сістэма**: лёгка пашырайце працоўныя працэсы, дадаючы новыя плагіны.

### Патрабаванні

- Python 3.10+
- [ExifTool](https://exiftool.org/) павінен быць усталяваны і даступны ў PATH.

### Выкарыстанне

Запуск асноўнага працоўнага працэсу:

```sh
scan-batcher --workflow <шлях_да_ini> --engine vuescan --batch scan --min-dpi 300 --max-dpi 4800 --dpis 600 1200 2400 4800
```

Праграма **інтэрактыўна запытае** ў вас памеры фотаздымка і выявы падчас выканання.

У Windows PowerShell сінтаксіс той жа. Калі значэнні ўтрымліваюць прабелы — выкарыстоўвайце двукоссі:

```powershell
scan-batcher --workflow .\examples\workflow.ini --batch scan --dpis 300 600 1200 2400 --templates author="John Doe" project="Family Archive"
```

Для атрымання поўнага спісу аргументаў і опцый выкарыстоўвайце:

```sh
scan-batcher --help
```

#### Аргументы каманднага радка

- `-b, --batch` - Рэжым пакетнай апрацоўкі: scan (інтэрактыўны), calculate (адзіночны разлік), або process (апрацоўка папкі). Па змаўчанні: scan
- `-w, --workflow` - Шлях да файла канфігурацыі працоўнага працэсу (фармат INI) для пакетнай апрацоўкі
- `-t, --templates` - Спіс пар ключ-значэнне для шаблонаў імёнаў файлаў або метаданых, напрыклад `-t year=2024 author=Smith`
- `-e, --engine` - Рухавік (engine) сканавання для апрацоўкі (па змаўчанні: vuescan)
- `-mnd, --min-dpi` - Мінімальна дапушчальнае значэнне DPI для сканавання (неабавязкова)
- `-mxd, --max-dpi` - Максімальна дапушчальнае значэнне DPI для сканавання (неабавязкова)
- `-d, --dpis` - Спіс падтрымоўваных сканерам дазволаў DPI, падзеленых прабелам, напрыклад `100 300 1200`
- `-r, --rounding` - Стратэгія акруглення: `mx` (максімальнае), `mn` (мінімальнае), `nr` (бліжэйшае). Па змаўчанні: nr. Унутры выкарыстоўвае enum `RoundingStrategy`

#### Прыклады выкарыстання

**Інтэрактыўны разлік DPI (рэжым scan)**
```sh
scan-batcher --workflow examples/workflow.ini --batch scan --dpis 300 600 1200 2400
```
*Праграма запытае ў вас памеры фотаздымка ў інтэрактыўным рэжыме.*

**Адзіночны разлік DPI (рэжым calculate)**
```sh
scan-batcher --workflow examples/workflow.ini --batch calculate --min-dpi 300 --max-dpi 4800 --dpis 600 1200 2400 4800 --rounding nr
```
*Праграма запытае памеры фотаздымка і выявы, затым завершыцца пасля аднаго разліку.*

**Апрацоўка файлаў з папкі**
```sh
scan-batcher --workflow examples/workflow.ini --batch process /path/to/scanned/files --templates author="John Doe" project="Family Archive"
```
*Апрацоўка існуючых файлаў без інтэрактыўнага ўводу.*

### Сістэма шаблонаў

Шаблоны выкарыстоўваюцца ў наладах і імёнах файлаў для падстаноўкі дынамічных значэнняў.

**Фармат шаблона:**

```
{<name>[:length[:align[:pad]]]}
```

- `name` — імя пераменнай шаблона  
- `length` — выніковая даўжыня (неабавязкова)  
- `align` — выраўноўванне (`<`, `>`, `^`; неабавязкова)  
- `pad` — сімвал запаўнення (неабавязкова)  

#### Падтрымоўваныя пераменныя шаблонаў

- `user_name` — імя карыстальніка аперацыйнай сістэмы  
- `digitization_year` — год аблічбоўкі (з EXIF або часу змены файла)  
- `digitization_month` — месяц аблічбоўкі  
- `digitization_day` — дзень аблічбоўкі  
- `digitization_hour` — гадзіна аблічбоўкі  
- `digitization_minute` — хвіліна аблічбоўкі  
- `digitization_second` — секунда аблічбоўкі  
- `scan_dpi` — значэнне DPI, выбранае ці разлічанае падчас пакетнай або інтэрактыўнай апрацоўкі  
- ...а таксама любыя дадатковыя пераменныя, перададзеныя праз камандны радок (`--templates ключ=значэнне`) ці batch-шаблоны

**Заўвага:**  
Калі EXIF-метаданыя адсутнічаюць, пераменныя даты і часу запаўняюцца часам змены файла.

**Прыклад:**
```
{digitization_year:8:>:0}
```

### Ключавыя модулі

- `scan_batcher/cli.py` — кропка ўваходу CLI (каманда `scan-batcher`).
- `scan_batcher/batch.py` — логіка пакетных і інтэрактыўных разлікаў DPI.
- `scan_batcher/calculator.py` — алгарытмы разліку DPI.
- `scan_batcher/parser.py` — парсінг і валідацыя аргументаў камандной радка.
- `scan_batcher/constants.py` — цэнтралізаваныя канстанты і пералічэнні (напрыклад, `RoundingStrategy`).
- `scan_batcher/workflow.py` — базавы клас для ўсіх workflow-плагінаў.
- `scan_batcher/workflows/__init__.py` — рэгістрацыя і выяўленне плагінаў.
- `scan_batcher/workflows/vuescan/workflow.py` — аўтаматызацыя працоўнага працэсу VueScan.

## Аўтаматычная арганізацыя (File Organizer)

> **⚠️ Статус**: У распрацоўцы. Пакуль не цалкам пратэсціравана або дакументавана.

Інструмент для аўтаматычнай арганізацыі адсканаваных файлаў на аснове іх імёнаў. Ён выцягвае метаданыя з імя файла (дата, мадыфікатары, роля па суфіксе) і перамяшчае кожны файл у дапаможнае дрэва `processed/` з наступнай структурай па змаўчанні:

- `processed/{year}/{year}.{month}.{day}/` — папка канкрэтнай даты (наладжваецца праз `formats.json`)
- `processed/{year}/{year}.{month}.{day}/SOURCES/` — RAW, майстар‑копіі (`MSR`) і звязаныя з імі службовыя файлы
- `processed/{year}/{year}.{month}.{day}/DERIVATIVES/` — вытворныя файлы (WEB, PRT і іншыя выходныя фарматы)
- `processed/{year}/{year}.{month}.{day}/` — файлы `*.PRV.jpg` для хуткага прагляду (праглядавыя копіі), якія ляжаць прама ў папцы даты

Структура архіва цалкам наладжваецца праз `formats.json` (гл. [Налада фарматаў шляхоў і імёнаў файлаў](#налада-фарматаў-шляхоў-і-імёнаў-файлаў-formatsjson) ніжэй).

Тая ж інфармацыя пра дату запісваецца ў тэгі EXIF/XMP файла. Падрабязныя правілы і прыклады глядзіце ў `docs/by/naming.md` (Часткі 2 і 3).

### Выкарыстанне

**Пакетны рэжым (апрацоўка існуючых файлаў):**
```sh
file-organizer "D:\Scans\Inbox"
```

**Рэжым дэмана (бесперапынны маніторынг):**
```sh
file-organizer "D:\Scans\Inbox" --daemon
```

**З метаданымі (праз JSON-канфіг):**
1. Адзін раз запусціце `file-organizer` без `--config`, каб ён стварыў файл канфігурацыі на аснове `config.template.json`.
2. Адкрыйце створаны JSON‑файл (звычайна ў карыстальніцкім канфіг‑каталогу) і адрэдагуйце секцыю `metadata.languages`. Кожны ключ у `languages` — гэта моўны код у фармаце BCP‑47 (напрыклад, `"ru-RU"`, `"en-US"`, `"be-BY"`), унутры — блок палёў, чытэльных для чалавека:

	 ```jsonc
	 "metadata": {
		 "languages": {
			 "be-BY": {
				 "default": true,
				 "creator": ["Імя Прозвішча", "Суаўтар"],
				 "credit": "Назва архіва або калекцыі",
				 "description": [
					 "Кароткае апісанне серыі або набору здымкаў.",
					 "Можна ў некалькі радкоў."
				 ],
				 "rights": "Тэкст пра правы і абмежаванні.",
				 "terms": "Умовы выкарыстання (калі патрэбныя).",
				 "source": "Фізічная крыніца: скрынка, альбом і г.д."
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

	 У аднаго моўнага блока павінна стаяць `"default": true` — яго значэнні дадаткова запісваюцца ў «звычайныя» XMP‑палі (x‑default). Поле `creator` бярэцца з блока мовы па змаўчанні і пішацца адзін раз як спіс імёнаў; астатнія тэкставыя палі (`description`, `credit`, `rights`, `terms`, `source`) пішуцца па мовах.

3. Пры неабходнасці яўна пакажыце шлях да канфіга праз `--config`:

```sh
file-organizer "D:\Scans\Inbox" --config "D:\Configs\file-organizer.json"
```

### Пашыраная канфігурацыя

**Налада палёў метаданых (`tags.json`):**

Па змаўчанні File Organizer выкарыстоўвае стандартны набор XMP-тэгаў для метаданых (`description`, `credit`, `rights`, `terms`, `source`). Вы можаце перавызначыць гэтыя адпаведнасці, стварыўшы файл `tags.json` у канфігурацыйнай папцы:

```json
{
  "description": "XMP-dc:Description",
  "credit": "XMP-photoshop:Credit",
  "rights": "XMP-dc:Rights",
  "terms": "XMP-xmpRights:UsageTerms",
  "source": "XMP-dc:Source"
}
```

Вы можаце дадаць уласныя палі, паказаўшы новую пару `"імя_поля": "XMP-namespace:TagName"`. Затым дадайце гэта поле ў моўныя блокі канфігурацыі, і яно аўтаматычна будзе запісвацца ў файлы з моўнымі варыянтамі.

**Налада раскладкі файлаў (`routes.json`):**

Правілы маршрутызацыі файлаў выкарыстоўваюцца сумесна інструментамі `file-organizer` і `preview-maker`. Файлы канфігурацыі размешчаны ў:
- Windows: `%APPDATA%\florentine-abbot\routes.json`, `tags.json` і `formats.json`
- Linux/macOS: `~/.config/florentine-abbot/routes.json`, `tags.json` і `formats.json`

Па змаўчанні файлы раскладваюцца так:
- `RAW`, `MSR` → `SOURCES/`
- `PRV` → корань папкі даты (`.`)
- усе астатнія → `DERIVATIVES/`

Вы можаце перавызначыць гэтую логіку, стварыўшы файл `routes.json`:

```json
{
  "RAW": "SOURCES",
  "MSR": "SOURCES",
  "PRV": ".",
  "COR": "MASTERS",
  "EDT": "EXPORTS"
}
```

Значэнні:
- `"SOURCES"`, `"DERIVATIVES"` ці любое імя папкі — стварыць падпапку ў папцы даты (напрыклад, `{year}/{year}.{month}.{day}/SOURCES/`)
- `"."` — пакласці файл прама ў корань папкі даты

**Налада шаблонаў (`formats.json`):**

Вы можаце наладзіць, як парсяцца імёны ўваходных файлаў і як фарматуюцца шляхі/імёны файлаў у архіве. Стварыце файл `formats.json` у папцы канфігурацыі:

```json
{
  "source_filename_template": "{year}.{month}.{day}.{hour}.{minute}.{second}.{modifier}.{group}.{subgroup}.{sequence}.{side}.{suffix}.{extension}",
  "archive_path_template": "{year:04d}/{year:04d}.{month:02d}.{day:02d}",
  "archive_filename_template": "{year:04d}.{month:02d}.{day:02d}.{hour:02d}.{minute:02d}.{second:02d}.{modifier}.{group}.{subgroup}.{sequence:04d}.{side}.{suffix}"
}
```

- `source_filename_template` — вызначае чаканую структуру імёнаў уваходных файлаў. Кожны `{field}` ператвараецца ў групу захопу regex для парсінгу. Палі, адсутныя ў шаблоне, атрымліваюць значэнні па змаўчанні і не валідуюцца.
- `archive_path_template` — структура папак у архіўным сховішчы.
- `archive_filename_template` — нармалізаванае імя файла (без пашырэння) у архіве.

Даступныя палі:
- Дата/час: `{year}`, `{month}`, `{day}`, `{hour}`, `{minute}`, `{second}`
- Кампаненты: `{modifier}`, `{group}`, `{subgroup}`, `{sequence}`, `{side}`, `{suffix}`, `{extension}`

Спецыфікатары фармату (стандартнае фарматаванне Python, для архіўных шаблонаў):
- `{year:04d}` — 4 лічбы з вядучымі нулямі (0000, 2024)
- `{month:02d}` — 2 лічбы з вядучым нулём (01, 12)
- `{sequence:04d}` — 4 лічбы з вядучымі нулямі (0001, 0042)

Прыклады шаблонаў імёнаў уваходных файлаў:
- Па змаўчанні: `"{year}.{month}.{day}.{hour}.{minute}.{second}.{modifier}.{group}.{subgroup}.{sequence}.{side}.{suffix}.{extension}"`
- Без часу: `"{year}.{month}.{day}.{modifier}.{group}.{subgroup}.{sequence}.{side}.{suffix}.{extension}"`
- Праз падкрэсліванне: `"{year}_{month}_{day}_{modifier}_{group}_{sequence}.{extension}"`

Прыклады архіўных шаблонаў:
- Плоская структура: `"archive_path_template": "{year:04d}.{month:02d}.{day:02d}"`
- Па месяцах: `"archive_path_template": "{year:04d}/{year:04d}.{month:02d}"`
- Па групах: `"archive_path_template": "{group}/{year:04d}/{year:04d}.{month:02d}.{day:02d}"`
- Кампактнае імя: `"archive_filename_template": "{year:04d}{month:02d}{day:02d}_{hour:02d}{minute:02d}{second:02d}_{group}_{suffix}"`
- ISO-стыль: `"archive_filename_template": "{year:04d}-{month:02d}-{day:02d}_{hour:02d}-{minute:02d}-{second:02d}_{modifier}_{group}_{subgroup}_{sequence:04d}_{side}_{suffix}"`

Усе файлы канфігурацыі апцыянальныя. Пры іх адсутнасці выкарыстоўваюцца ўбудаваныя значэнні па змаўчанні. Гэтыя налады ўплываюць як на арганізацыю файлаў (`file-organizer`), так і на генерацыю прэв'ю (`preview-maker`).

### Ключавыя модулі

- `file_organizer/cli.py` — CLI (падкаманды `batch`, `watch`).
- `file_organizer/organizer.py` — ядро пакетнай апрацоўкі і пафайлавай аркестрацыі.
- `file_organizer/processor.py` — парсінг імёнаў файлаў, валідацыя і запіс метаданых.
- `file_organizer/watcher.py` — рэжым дэмана праз watchdog, дэлегуе `FileOrganizer`.
- `file_organizer/metadata.py` — `ArchiveMetadata`: шматмоўнае разрашэнне XMP-палёў.
- `file_organizer/constants.py` — канфігурацыя метаданых па змаўчанні (`DEFAULT_METADATA`).
- `file_organizer/config.py` — загрузка канфіга з `file-organizer/config.json`.

## Preview Maker (генератар PRV)

> **⚠️ Статус**: У распрацоўцы. Пакуль не цалкам пратэсціравана або дакументавана.

Preview Maker выкарыстоўвае тыя ж правілы маршрутызацыі (`routes.json`), што і File Organizer, для пошуку майстар-файлаў і вызначэння месца размяшчэння прэв'ю-выяв.

Для ўжо структураванага архіва ёсць дапаможны інструмент, які можа генераваць праглядавыя JPEG‑копіі `PRV` з крыніц `RAW`/`MSR`.

- пры наяўнасці пары RAW+MSR робіць PRV **толькі з MSR**;
- запісвае прэв'ю `*.PRV.jpg` у папку даты (бацька `SOURCES/`).
- па змаўчанні існуючыя PRV захоўваюцца, калі не паказаны `--overwrite`.

Метаданыя для прэв'ю наследуюцца ад адпаведных майстар‑файлаў:
- кантэкстныя EXIF/XMP‑палі (апісанне, аўтар, правы, крыніца і г.д.) капіруюцца з `RAW`/`MSR`‑майстра;
- кожны `PRV` атрымлівае ўласны ідэнтыфікатар;
- у метаданых фіксуецца яўная сувязь (relation) паміж `PRV` і яго майстрам.

Параметры выявы (памер, фармат, якасць) задаюцца ў канфігурацыйным файле (`config.json`), а не ў камандным радку. Падтрымліваецца шматфарматны вывад: JPEG, PNG, WebP, TIFF.

Preview Maker падае тры падкаманды: `batch` (аднаразовая апрацоўка), `watch` (дэман) і `convert` (адзінкавы файл).

**Пакетны рэжым (генерацыя прэв'ю для архіва):**
```sh
preview-maker batch --path "D:\Archive\PHOTO_ARCHIVES"
```

**З перазапісам існуючых PRV:**
```sh
preview-maker batch --path "D:\Archive\PHOTO_ARCHIVES" --overwrite
```

**Рэжым дэмана (адсочванне новых майстар-файлаў):**
```sh
preview-maker watch --path "D:\Archive\PHOTO_ARCHIVES"
```

**Канвертацыя адзінкавага файла (без пайплайна, без метаданых):**
```sh
preview-maker convert --file "D:\photo.jpg" --size 2000 --format jpeg --quality 80
```

Логі пішуцца па тых жа правілах, што і ў іншых утыліт:
- па змаўчанні: `~/.florentine-abbot/logs/preview_maker.log`;
- каталог можна перавызначыць праз `--log-path` або пераменную асяроддзя `FLORENTINE_LOG_DIR`.

### Ключавыя модулі

- `preview_maker/cli.py` — CLI (падкаманды `batch`, `watch`, `convert`).
- `preview_maker/maker.py` — ядро логікі генерацыі PRV.
- `preview_maker/converter.py` — чыстая канвертацыя выяў (рэсайз + фармат); выкарыстоўваецца і пайплайнам, і падкамандай `convert`.
- `preview_maker/constants.py` — карты фарматаў, памеры па змаўчанні, аліасы фарматаў.
- `preview_maker/watcher.py` — рэжым дэмана праз watchdog, дэлегуе `PreviewMaker`.

## Цэласнасць архіва (Archive Keeper)

> **⚠️ Статус**: У распрацоўцы. Пакуль не цалкам пратэсціраваны або дакументаваны. Не ўваходзіць ва ўсталяваны пакет; запускаць з зыходнікаў.

Інструмент для забеспячэння доўгатэрміновай цэласнасці вашага лічбавага архіва. Ён сканіруе папку архіва, вылічае хэшы SHA-256 усіх файлаў і захоўвае іх у базе даных SQLite. Пры наступных запусках ён выяўляе:
- **Новыя файлы** (Added)
- **Зменены файлы** (Content changed)
- **Перамешчаныя файлы** (Same content, different path)
- **Адсутныя файлы** (Deleted or moved outside)
- **Пашкоджаныя файлы** (Bit rot detection)

### Выкарыстанне

Запускайце ўтыліту наўпрост з зыходнікаў праз модульную кропку ўваходу:

```sh
python -m archive_keeper.cli "D:\Archive\Photos"
```

Гэта створыць файл `archive.db` і запоўніць яго бягучым станам архіва. Наступныя запускі будуць параўноўваць файлавую сістэму з гэтай базай даных.

### Ключавыя модулі

- `archive_keeper/cli.py` — кропка ўваходу CLI (каманда `archive-keeper`).
- `archive_keeper/engine.py` — логіка сканавання, хэшавання і параўнання.
- `archive_keeper/scanner.py` — абход файлавай сістэмы і вылічэнне SHA-256.

## Распазнаванне твараў (Face Detector)

> **⚠️ Статус**: У распрацоўцы. Пакуль не цалкам пратэсціраваны або дакументаваны. Не ўваходзіць ва ўсталяваны пакет; запускаць з зыходнікаў.

Інструмент для аўтаматычнага выяўлення твараў і кластарызацыі ідэнтычнасцяў у фотаархіве. Рэкурсіўна сканіруе дрэва каталогаў, выяўляе твары з дапамогай падключаемых дэтэктараў, захоўвае эмбедынгі ў базе даных SQLite і кластарызуе іх у дамены ідэнтычнасцяў з дапамогай DBSCAN.

- **Падключаемыя дэтэктары** — убудаваная падтрымка InsightFace; дадатковыя дэтэктары можна рэгіставаць праз entry points.
- **Інкрэментальная апрацоўка** — ужо апрацаваныя файлы прапускаюцца, калі не паказаны `--overwrite`.
- **Кластарызацыя ідэнтычнасцяў** — DBSCAN групуе эмбедынгі твараў з розных выяў у дамены ідэнтычнасцяў.
- **Візуалізацыя** — адмалёўвае bounding box'ы на JPEG-прэв'ю для ручной праверкі.

### Патрабаванні

Патрабуюцца дадатковыя залежнасці. Усталюйце з опцыяй `face-insightface` з зыходнікаў:

```sh
pip install -e .[face-insightface]
```

### Выкарыстанне

Запускайце з зыходнікаў праз модульную кропку ўваходу:

**Сканаванне і кластарызацыя:**
```sh
python -m face_detector.cli batch --path "D:\Archive\PHOTO_ARCHIVES"
```

**Без кластарызацыі:**
```sh
python -m face_detector.cli batch --path "D:\Archive\PHOTO_ARCHIVES" --no-cluster
```

**Паўторная апрацоўка ўжо праіндэксаваных файлаў:**
```sh
python -m face_detector.cli batch --path "D:\Archive\PHOTO_ARCHIVES" --overwrite
```

**Прэв'ю выяўленых твараў:**
```sh
python -m face_detector.cli preview --file "D:\Archive\2024\photo.jpg"
```

Поўны спіс аргументаў:

```sh
python -m face_detector.cli --help
```

### Ключавыя модулі

- `face_detector/cli.py` — CLI (падкаманды `batch`, `preview`).
- `face_detector/engine.py` — аркестрацыя пакетнага выяўлення па дрэве каталогаў.
- `face_detector/detector.py` — абстрактны базавы клас для дэтэктар-плагінаў.
- `face_detector/store.py` — SQLite-сховішча для эмбедынгаў твараў.
- `face_detector/clusterer.py` — кластарызацыя ідэнтычнасцяў на аснове DBSCAN.
- `face_detector/visualizer.py` — візуалізацыя выяўленых твараў на прэв'ю выяў.

## Налада (Setup Runner)

Інтэрактыўны інструмент першапачатковай налады. Запусціце адзін раз пасля ўсталёўкі, каб задаць шляхі і стварыць файлы канфігурацыі для ўсіх дэманаў.

### Што ён робіць

- **Правярае ExifTool** — правярае наяўнасць залежнасці; прапануе аўтаматычную ўсталёўку праз winget (Windows) або Homebrew (macOS) або выводзіць інструкцыі для ручной усталёўкі.
- **Наладжвае шляхі** — запытвае папку ўваходных файлаў (inbox) і корань архіва, стварае іх пры неабходнасці.
- **Стварае канфігі дэманаў** — генеруе `config.json` для `file-organizer`, `preview-maker` і `face-detector`.
- **Стварае ярлык на працоўным стале** — ярлык для вэб-дашборда (`http://127.0.0.1:8000/`) на працоўным стале (Windows, macOS, Linux).
- **Апцыянальна запускае вэб-дашборд** — адразу пасля налады можа запусціць `florentine-web`.

### Выкарыстанне

```sh
setup-runner
```

Файлы канфігурацыі запісваюцца ў:
- Windows: `%APPDATA%\florentine-abbot\`
- Linux/macOS: `~/.config/florentine-abbot/`

### Ключавыя модулі

- `setup_runner/cli.py` — кропка ўваходу CLI (каманда `setup-runner`).
- `setup_runner/runner.py` — логіка інтэрактыўнай налады; платформенныя падкласы для Windows, macOS, Linux.

## Тэхнічныя дэталі

### Агульныя модулі

Выкарыстоўваюцца ўсімі ўтылітамі:

- `common/logger.py` — адзіная падсістэма лагіравання.
- `common/naming.py` — агульны парсер і валідатар імёнаў файлаў.
- `common/router.py` — наладжвальная маршрутызацыя файлаў (шаблон імя → папка).
- `common/formatter.py` — наладжвальнае фарматаванне шляхоў і імёнаў файлаў архіва.
- `common/tagger.py` — абстракцыя пакетнага XMP/EXIF чытання/запісу паверх exiftool.
- `common/exifer.py` — выманне і апрацоўка EXIF-метаданых.
- `common/constants.py` — імёны тэгаў, канстанты дзеянняў і канфігурацыя па змаўчанні.

### Усталяванне

#### Патрабаванні
- Python 3.10 ці вышэй
- Праграма VueScan (для аперацый сканавання)

#### Усталяванне з зыходнага кода

Для лакальнай усталёўкі пакета з зыходнага каталога выкарыстоўвайце:

```sh
pip install .
```

Гэта ўсталюе ўсе неабходныя залежнасці і зробіць асноўныя CLI-каманды даступнымі ў вашай сістэме:

- `scan-batcher`
- `file-organizer`
- `preview-maker`
- `florentine-web`
- `setup-runner`

> **Заўвага:**  
> Рэкамендуецца выкарыстоўваць [віртуальнае асяроддзе](https://docs.python.org/3/library/venv.html) для ўсталёўкі і распрацоўкі.

#### Усталяванне для распрацоўкі

Для распрацоўкі з рэдагаванай усталёўкай:

```sh
pip install -e .
```

Для абнаўлення ўжо ўсталяванага пакета выкарыстоўвайце:

```sh
pip install --upgrade .
```

### Лагіраванне

Усе ўтыліты запісваюць логі ў цэнтралізаванае месца:

**Размяшчэнне па змаўчанні:**
- Linux/macOS: `~/.florentine-abbot/logs/`
- Windows: `C:\Users\<імя_карыстальніка>\.florentine-abbot\logs\`

**Файлы логаў:**
- `scan_batcher.log` — актыўнасць Scan Batcher
- `file_organizer.log` — актыўнасць File Organizer (`file-organizer`)
- `archive_keeper.log` — актыўнасць Archive Keeper
- `preview_maker.log` — актыўнасць Preview Maker (`preview-maker`)
- `face_detector.log` — актыўнасць Face Detector

**Карыстальніцкае размяшчэнне логаў:**

Можна перавызначыць размяшчэнне двума спосабамі:

**1. Параметр камандной радка (найвышэйшы прыярытэт):**
```sh
scan-batcher --log-path /custom/logs --workflow examples/workflow.ini
file-organizer --log-path /custom/logs /path/to/scans
archive-keeper --log-path /custom/logs /path/to/archive
```

**2. Пераменная асяроддзя:**
```sh
# Linux/macOS
export FLORENTINE_LOG_DIR=/var/log/florentine-abbot
scan-batcher --workflow examples/workflow.ini

# Windows PowerShell
$env:FLORENTINE_LOG_DIR = "D:\Logs\florentine-abbot"
scan-batcher --workflow examples\workflow.ini
```

**Парадак прыярытэту:**
1. Параметр `--log-path` (перавызначэнне для адной каманды)
2. Пераменная асяроддзя `FLORENTINE_LOG_DIR` (для сесіі/сістэмы)
3. Па змаўчанні: `~/.florentine-abbot/logs/`

Гэта карысна для:
- **Распрацоўкі**: хуткае перавызначэнне праз `--log-path /tmp/debug`
- **Daemon-рэжыму**: усталёўка праз ENV у systemd unit файлах
- **Docker**: налада праз `ENV` у Dockerfile
- **Цэнтралізаванага лагіравання**: накіраванне ўсіх утыліт у адно месца

**Магчымасці лагіравання:**
- Адзіны фармат часавых адбіткаў: `YYYY.MM.DD HH:MM:SS.mmm`
- Аўтаматычная ратацыя (10 МБ на файл, 5 рэзервовых копій)
- Вывад у кансоль + запіс у файл
- Імя модуля і ўзровень лагіравання ў кожным запісе

## Дакументацыя

- Індэкс дакументацыі: [docs/README.ru.md](docs/README.ru.md)
- Кіраўніцтва па імянаванні (BY): [docs/by/naming.md](docs/by/naming.md)

---

Для падрабязнасцяў гл. [README.ru.md](README.ru.md) (па-руску).
