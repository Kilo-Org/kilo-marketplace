<p align="center"><a href="https://once-email.com"><img src="../assets/unpack-flow-banner.png" alt="UnpackFlow by Once Email" width="100%"></a></p>

# UnpackFlow — вложенные архивы без дежурства

[English](../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [हिन्दी](README.hi.md) · [العربية](README.ar.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [日本語](README.ja.md) · [Русский](README.ru.md)

В режиме `-r`, если имя результата уже занято, UnpackFlow добавляет имя исходной папки, например `sample-backup-legacy-set-unpacked`, а при следующих конфликтах — `-2`, `-3`, не перезаписывая и не пропуская результаты.

Небольшой набор `unpack-flow-minimal-testcases-v1.zip` проверяет ZIP, TAR.GZ, Unicode, вложенность, многотомный `part01.exe` и ожидаемый сбой при отсутствии тома; крупных приложений нет, SFX не запускается.

Нативная приёмка использует синтетические данные в `/data/unpack-flow-testcases`; путь можно изменить через `UNPACK_FLOW_TEST_ROOT`. Большие наборы необязательны и применяются только для производительности или дополнительной совместимости форматов.

UnpackFlow обрабатывает дистрибутивы программ, наборы данных, резервные копии, медиаматериалы и другие крупные архивы. Он находит первый том, раскрывает вложенные слои по очереди и показывает пакет, этап, уровень и время.

## Использование и установка

Команды: `unpack-flow list 'Archive*'`, `plan`, `unpack-flow 'Archive*'`, `status`. Linux требует Bash, Windows — PowerShell и 7-Zip, macOS — PowerShell 7+ и `7zz`. `scripts/build-release.sh` создаёт три пакета и SHA-256.

Python не нужен для запуска `unpack-flow` или распаковки архивов. Python 3 требуется только для автоматической установки Skill в Linux/macOS через `install_local.py` или `install_local.sh` и для Python-аудита. В Windows `install_local.ps1` работает только с PowerShell; ручное копирование Skill также не требует Python.

## Поддерживаемые сценарии распаковки

UnpackFlow пакетно обрабатывает каталоги и шаблоны, раскрывает вложенные архивы слой за слоем и определяет первый том многотомного RAR. Самораспаковывающиеся RAR исследуются без запуска неизвестных EXE. Подходит для дистрибутивов, наборов данных, резервных копий, медиаматериалов, журналов и образов ISO или WIM.

По умолчанию обрабатывается до 10 внутренних уровней. Повреждённый или неполный внутренний архив сохраняется, регистрируется и пропускается, а остальные продолжают обрабатываться; `-StopOnError` останавливает работу при первой ошибке.

## Учебные примеры

Используйте `list`, `plan`, `start`, `status`, `log` и `wait` для резервных копий, данных, журналов, программ и многотомных архивов. Игры — лишь один пример, а не граница продукта.

Во всех трёх системах `run` работает на переднем плане и показывает ход выполнения, а `start` запускает фоновое задание и возвращает его ID.

При длительной работе 7-Zip или UnRAR время обновляется каждую секунду, а каждые 30 секунд в журнал записывается сигнал активности.

В macOS и Windows команда `start` полностью отсоединяет интерактивные потоки; прогресс записывается только в журнал без ANSI-кодов и звуков терминала.

Параметр `-r` или `-Recursive` находит все архивы в подпапках и распаковывает внутренние уровни; при совпадении имени результат сохраняется как `имя-unpacked`.

Поддерживается и `unpack-flow run *`. Даже после раскрытия `*` оболочкой сканирование оставляет только одиночные архивы и первые тома, например `part1.exe`, `part1.rar`, `.7z.001` или `.zip.001`, отбрасывая `.sha256`, посторонние файлы и последующие тома.

`unpack-flow help` выводит объединённую справку на английском и упрощённом китайском языках.

## Фоновые задания и журналы

`unpack-flow start "архив" -Output "каталог"` запускает распаковку в фоне и возвращает ID задания. Используйте `unpack-flow status [ID]`, `unpack-flow log [ID]` и `unpack-flow wait [ID]`; без ID выбирается последнее задание. Журналы хранятся в `%LOCALAPPDATA%\unpack-flow\state` в Windows и `~/.local/state/unpack-flow` в macOS/Linux.

Поддерживаются TAR, TAR.GZ/TGZ и отдельный GZ. После 7-Zip программа по формату пробует UnRAR, системный `tar`, GZip или встроенный ZIP, очищая результат неудачной попытки. Если все подходящие средства не сработали, исходный архив сохраняется, ошибка записывается и обработка продолжается без бесконечных повторов.

В Linux x64 включён официальный UnRAR 7.23. В Windows x64/ARM64 включён полный официальный 7-Zip 26.02, а в x64 также UnRAR. Исходные официальные пакеты и лицензии сохранены.

## Полный быстрый старт

```bash
unpack-flow list '/data/archives/*'
unpack-flow plan '/data/archives/backup.part1.rar'
unpack-flow run '/data/archives/*' -Output '/data/extracted'
```

Для фонового запуска:

```bash
unpack-flow start '/data/archives/*' -Output '/data/extracted'
unpack-flow status
unpack-flow log
unpack-flow wait
```

`run` остаётся в текущем терминале до завершения, а `start` сразу возвращает ID задания. В обоих режимах исходные архивы сохраняются.

## Установка инструмента командной строки

### Linux

```bash
./install-linux.sh --check
./install-linux.sh
unpack-flow version
```

### macOS

```bash
./install-macos.sh --check
./install-macos.sh
unpack-flow version
```

### Windows

```bat
install.bat -Check
install.bat
unpack-flow version
```

Команды проверки сообщают об отсутствующих зависимостях, но не устанавливают системные программы автоматически.

## Рекурсия, журналы и ошибки

Параметры `-r` и `-Recursive` включают поиск в подпапках и распаковку внутренних уровней. По умолчанию разрешено до 10 внутренних уровней.

| Платформа | Каталог состояния по умолчанию |
|---|---|
| Windows | `%LOCALAPPDATA%\unpack-flow\state` |
| Linux/macOS | `${XDG_STATE_HOME:-$HOME/.local/state}/unpack-flow` |

UnpackFlow использует ограниченную цепочку: 7-Zip, UnRAR для RAR и подходящие системные средства для TAR, GZ или ZIP. Неполный результат каждой попытки удаляется. Если все варианты не сработали, исходный архив сохраняется, ошибка записывается и обработка продолжается. Используйте `-StopOnError` только для остановки при первой ошибке.

## Тесты и установка Agent Skill

```bash
bash tests/generate-minimal-public-suite.sh
bash tests/test-minimal-public-suite.sh
pwsh -NoProfile -File tests/test-minimal-public-suite.ps1
scripts/install_local.sh .
```

В Windows Skill устанавливается через `scripts/install_local.ps1`. Python не нужен для распаковки; он используется только автоматическим установщиком Skill для Linux/macOS и Python-аудитом.

## Безопасность, проект и поддержка

UnpackFlow сохраняет исходные файлы, не перезаписывает каталоги назначения и не запускает неизвестные EXE-файлы.

- Официальный сайт: [once-email.com](https://once-email.com)
- Автор и разработчик: helen.jar
- Проект GitHub: [pangxin12345/unpack-flow](https://github.com/pangxin12345/unpack-flow)
- Электронная почта поддержки: [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com)

По любым вопросам пишите на [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com) или [создайте обращение в GitHub Issues](https://github.com/pangxin12345/unpack-flow/issues).

Лицензия MIT, версия 2.1.4.
