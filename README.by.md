[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/nalivayev/florentine-abbot/blob/master/README.md)
[![ru](https://img.shields.io/badge/lang-ru-yellow.svg)](https://github.com/nalivayev/florentine-abbot/blob/master/README.ru.md)
[![by](https://img.shields.io/badge/lang-by-green.svg)](https://github.com/nalivayev/florentine-abbot/blob/master/README.by.md)

# Scan Batcher

Scan Batcher — гэта праект, прысвечаны сканаванню і лічбавай арганізацыі хатніх фотаархіваў.

## Архітэктура і стандарты

Праект у некаторай ступені рэалізуе падыходы эталоннай мадэлі **OAIS (Open Archival Information System)**, распрацаванай **[Consultative Committee for Space Data Systems (CCSDS)](https://public.ccsds.org/)** — стандарту для доўгатэрміновага захоўвання даных, які выкарыстоўваецца архівамі і бібліятэкамі.

OAIS апублікаваны як:
- **[CCSDS 650.0-M-3](https://public.ccsds.org/Pubs/650x0m3.pdf)** (Pink Book, 2019) — актуальная версія, свабодна даступная
- **[ISO 14721:2025](https://www.iso.org/standard/87471.html)** — фармальны міжнародны стандарт (ідэнтычны CCSDS 650.0-M-3 па змеце)

Праект рэалізуе функцыянальны блок OAIS **Ingest (Прыём даных)**: аўтаматызацыю сканавання, разбор структураваных імёнаў файлаў і запіс метаданых (XMP/EXIF).

Для аблічбоўкі выяў праект таксама абапіраецца на рэкамендацыі **[Federal Agencies Digital Guidelines Initiative (FADGI)](https://www.digitizationguidelines.gov/)**:
- **[Technical Guidelines for Digitizing Cultural Heritage Materials, 3rd Edition](https://www.digitizationguidelines.gov/guidelines/FADGITechnicalGuidelinesforDigitizingCulturalHeritageMaterials_ThirdEdition_05092023.pdf)** (май 2023)

Для кадавання і захавання метаданых выкарыстоўваецца **[XMP (Extensible Metadata Platform)](https://www.adobe.com/devnet/xmp.html)**:
- **[ISO 16684-1:2019](https://www.iso.org/standard/75163.html)** — Extensible metadata platform (XMP) — Частка 1: Мадэль даных, серыялізацыя і асноўныя ўласцівасці
- **[XMP Specification Part 2: Additional Properties](https://github.com/adobe/xmp-docs/tree/master/XMPSpecifications)** (Adobe) — пашыраныя прасторы імёнаў, уключаючы XMP Media Management (xmpMM) для адсочвання гісторыі файлаў

## Сканаванне

Утыліта для аўтаматызацыі працэсу сканавання з дапамогай знешняга ПЗ для сканавання (напрыклад, [VueScan](https://www.hamrick.com) ад Ed Hamrick).

### Навошта гэта трэба?

Сучасныя праграмы сканавання — магутныя і гнуткія, але пры патокавай працы мноства налад лёгка ператвараецца ў праблему: параметры раскіданыя па розных укладках, іх проста забыць скарэктаваць ці выпадкова скінуць.

Scan Batcher вырашае гэта за кошт эталонных профіляў і аўтаматызаванага працэсу, што дае:
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
