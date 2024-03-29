<h1 align="center">

![Logo](icons/icon.ico)  
Spotify-downloader  
[![en](https://img.shields.io/badge/README-en-red.svg)](README.md)

</h1>


<div align="center">

![Platform](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white "Не кликабельно")

[![Last release](https://img.shields.io/github/v/release/LuTiFlekSSer/Spotify-downloader)](https://github.com/LuTiFlekSSer/Spotify-downloader/releases/latest "Скачать")
![Downloads](https://img.shields.io/github/downloads/LuTiFlekSSer/Spotify-downloader/total "Не кликабельно")

Spotify-downloader - это приложение, которое позволяет скачивать музыку с сервиса Spotify,
а также синхронизировать локальную папку с треками с любимыми треками в Spotify.

</div>

## Возможности :sparkles:

* Синхронизация локальных и любимых треков
    * Можно загружать только отсутствующие треки на диске
    * Можно проверять, какие треки были случайно удалены из любимых
    * Можно добавлять треки в игнор листы, чтобы пропускать их при синхронизации
* Загрузка треков из плейлистов
* Загрузка отдельных треков по ссылке
* Настраиваемое кол-во потоков для загрузки
* Автоматическое переименование треков при синхронизации, если они были переименованы в Spotify
* Автоматическое обновление

## Скриншоты :camera:

| ![Main](res/main_ru.png) | ![Settings](res/settings_ru.png) |
|:------------------------:|:--------------------------------:|
| ![Sync](res/sync_ru.png) |    ![Sync](res/sync_1_ru.png)    |

## Установка :wrench:

1. Необходимо загрузить программу из раздела с [релизами](https://github.com/LuTiFlekSSer/Spotify-downloader/releases/latest)
2. Запустить скачанный файл
3. Чтобы работала синхронизация с аккаунтом, необходимо ввести `clinet id`, `client secret` и `redirect uri`, которые можно получить на [странице разработчика](https://developer.spotify.com/) Spotify:
    1. Необходимо залогиниться на сайте со своего аккаунта Spotify
    2. Перейти в раздел [Dashboard](https://developer.spotify.com/dashboard/)
    3. [Создать](https://developer.spotify.com/dashboard/create) новое приложение и заполнить поля
    4. Перейти на страничку созданного приложения и нажать **settings**, откуда можно скопировать необходимые данные
4. В программе перейти в `Синхронизацию треков` или `Проверку треков`
5. Следовать дальнейшим инструкциям программы для завершения входа в аккаунт

P.S. Если не сделать действия из 3 и дальнейших пунктов, то будут работать только загрузка плейлистов и отдельных треков

## Обратная связь :mailbox:

* В случае обнаружения проблем с программой, можно создать [issue](https://github.com/LuTiFlekSSer/Spotify-downloader/issues/) с соответствующим описанием ошибки и меткой `bug`
* Предлагать улучшения можно в [issue](https://github.com/LuTiFlekSSer/Spotify-downloader/issues/) с меткой `enhancement`

___

<div align="center">

![Thanks](res/md_thanks.jpg)

</div>