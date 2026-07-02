import os
import json
import time
import random
import re
import requests

# 1. AYARLAR
BASE_DIR = os.getcwd()
DATA_FILE = os.path.join(BASE_DIR, "urunler.json")

# Ortam değişkenleri
SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY", "")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# 2. URL LİSTESİ (Senin verdiğin linkler)
url_listesi = [
    "https://www.amazon.com.tr/s?k=tv&rh=p_6%3AA1UNQM1SR2CHM%2Cp_123%3A15808732%257C1744057%257C195698%257C249374%257C338933%257C46655%257C746331&dc&__mk_tr_TR=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=3SKKHDSUJH9T&qid=1782978103&rnid=91049075031&sprefix=tv%2Caps%2C146&xpid=eHxwq6Wq5sRQ0&ref=sr_nr_p_123_8&ds=v1%3AOohTPxksfF1Ys20Lj72ctsZy24vTuAeFrL%2BswqBL6jM",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A13709898031%2Cp_6%3AA1UNQM1SR2CHM%2Cp_123%3A110955%257C222211%257C32374%257C338933&dc&qid=1782978403&rnid=91049075031&xpid=fXX5lWxtbEpkJ&ref=sr_pg_1",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A13709898031%2Cp_6%3AA1UNQM1SR2CHM%2Cp_123%3A110955%257C222211%257C32374%257C338933&dc&page=2&qid=1782978407&rnid=91049075031&xpid=fXX5lWxtbEpkJ&ref=sr_pg_2",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A13709880031%2Cp_6%3AA1UNQM1SR2CHM%2Cp_123%3A110955%257C32374%257C338933%257C339703%257C46655&dc&qid=1782978499&rnid=91049075031&xpid=MKBm5kVKAvR9d&ref=sr_pg_1",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A13709880031%2Cp_6%3AA1UNQM1SR2CHM%2Cp_123%3A110955%257C32374%257C338933%257C339703%257C46655&dc&page=2&qid=1782978505&rnid=91049075031&xpid=MKBm5kVKAvR9d&ref=sr_pg_2",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A13709880031%2Cp_6%3AA1UNQM1SR2CHM%2Cp_123%3A110955%257C32374%257C338933%257C339703%257C46655&dc&page=3&qid=1782978520&rnid=91049075031&xpid=MKBm5kVKAvR9d&ref=sr_pg_3",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A13709880031%2Cp_6%3AA1UNQM1SR2CHM%2Cp_123%3A110955%257C32374%257C338933%257C339703%257C46655&dc&page=4&qid=1782978531&rnid=91049075031&xpid=MKBm5kVKAvR9d&ref=sr_pg_4",
    "https://www.amazon.com.tr/s?i=computers&rh=n%3A12601907031%2Cp_6%3AA1UNQM1SR2CHM%2Cp_123%3A110955%257C32374%257C338933%257C339703%257C391242%257C46655&s=popularity-rank&dc&fs=true&qid=1782978588&rnid=91049075031&ref=sr_nr_p_123_6&ds=v1%3A7%2BoRgvwyekQZ5vnBZVU2l8tYlAg6575v9c0w8VcGPGY",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A13709883031%2Cp_6%3AA1UNQM1SR2CHM%2Cp_123%3A237204%257C250644%257C255891%257C28133%257C2979630%257C338933%257C359121&s=popularity-rank&dc&fs=true&qid=1782978646&rnid=91049075031&ref=sr_nr_p_123_9&ds=v1%3ABnNjZBrL6tnPIGquOg4lTH9TlLYPSe6ER4DoM4%2F%2B%2FAI",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A13709883031%2Cp_6%3AA1UNQM1SR2CHM%2Cp_123%3A237204%257C250644%257C255891%257C28133%257C2979630%257C338933%257C359121&s=popularity-rank&dc&fs=true&page=2&xpid=dYHkaO_aO0WrS&qid=1782978650&rnid=91049075031&ref=sr_pg_2",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A13709883031%2Cp_6%3AA1UNQM1SR2CHM%2Cp_123%3A237204%257C250644%257C255891%257C28133%257C2979630%257C338933%257C359121&s=popularity-rank&dc&fs=true&page=3&qid=1782978652&rnid=91049075031&xpid=dYHkaO_aO0WrS&ref=sr_pg_3",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A13709883031%2Cp_6%3AA1UNQM1SR2CHM%2Cp_123%3A237204%257C250644%257C255891%257C28133%257C2979630%257C338933%257C359121&s=popularity-rank&dc&fs=true&page=4&qid=1782978683&rnid=91049075031&xpid=dYHkaO_aO0WrS&ref=sr_pg_4",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A13709883031%2Cp_6%3AA1UNQM1SR2CHM%2Cp_123%3A237204%257C250644%257C255891%257C28133%257C2979630%257C338933%257C359121&s=popularity-rank&dc&fs=true&page=5&qid=1782978698&rnid=91049075031&xpid=dYHkaO_aO0WrS&ref=sr_pg_5",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A13710018031%2Cp_6%3AA1UNQM1SR2CHM%2Cp_123%3A110955%257C233043%257C237204%257C256864%257C32374%257C338933%257C46655&s=popularity-rank&dc&fs=true&page=4&xpid=wX53UQADtN2-U&qid=1782978766&rnid=91049075031&ref=sr_pg_4",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A13710018031%2Cp_6%3AA1UNQM1SR2CHM%2Cp_123%3A110955%257C233043%257C237204%257C256864%257C32374%257C338933%257C46655&s=popularity-rank&dc&fs=true&page=3&qid=1782978770&rnid=91049075031&xpid=wX53UQADtN2-U&ref=sr_pg_3",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A13710018031%2Cp_6%3AA1UNQM1SR2CHM%2Cp_123%3A110955%257C233043%257C237204%257C256864%257C32374%257C338933%257C46655&s=popularity-rank&dc&fs=true&page=2&qid=1782978783&rnid=91049075031&xpid=wX53UQADtN2-U&ref=sr_pg_2",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A13710018031%2Cp_6%3AA1UNQM1SR2CHM%2Cp_123%3A110955%257C233043%257C237204%257C256864%257C32374%257C338933%257C46655&s=popularity-rank&dc&fs=true&qid=1782978769&rnid=91049075031&xpid=wX53UQADtN2-U&ref=sr_pg_1",
    "https://www.amazon.com.tr/s?bbn=14630942031&rh=n%3A14630942031%2Cp_6%3AA1UNQM1SR2CHM&dc&qid=1782978841&rnid=15358539031&ref=sr_nr_p_6_1",
    "https://www.amazon.com.tr/s?i=kitchen&bbn=14630942031&rh=n%3A14630942031%2Cp_6%3AA1UNQM1SR2CHM&dc&page=2&qid=1782978844&rnid=15358539031&xpid=lPoOU0uSNGQ9g&ref=sr_pg_2",
    "https://www.amazon.com.tr/s?i=kitchen&bbn=14630942031&rh=n%3A14630942031%2Cp_6%3AA1UNQM1SR2CHM&dc&page=3&qid=1782978877&rnid=15358539031&xpid=lPoOU0uSNGQ9g&ref=sr_pg_3",
    "https://www.amazon.com.tr/s?i=kitchen&bbn=14630942031%2Cp_6%3AA1UNQM1SR2CHM&dc&page=4&qid=1782978887&rnid=15358539031&xpid=lPoOU0uSNGQ9g&ref=sr_pg_4",
    "https://www.amazon.com.tr/s?i=kitchen&bbn=14630942031%2Cp_6%3AA1UNQM1SR2CHM&dc&page=5&qid=1782978890&rnid=15358539031&xpid=lPoOU0uSNGQ9g&ref=sr_pg_5",
    "https://www.amazon.com.tr/s?i=kitchen&bbn=14630942031%2Cp_6%3AA1UNQM1SR2CHM&dc&page=6&qid=1782978903&rnid=15358539031&xpid=lPoOU0uSNGQ9g&ref=sr_pg_6",
    "https://www.amazon.com.tr/s?i=kitchen&bbn=14630942031%2Cp_6%3AA1UNQM1SR2CHM&dc&page=7&qid=1782978920&rnid=15358539031&xpid=lPoOU0uSNGQ9g&ref=sr_pg_7",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&qid=178297980&rnid=15358539031&ref=sr_nr_p_6_1&ds=v1%3AwDr7Mz4deCaFvH%2BCGbIHB3MKYaRMmJmb68Ib%2B9aRABI",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=2&xpid=3D0oEmMlA80pq&qid=1782978985&rnid=15358539031&ref=sr_pg_2",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=3&qid=1782978989&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_3",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=4&qid=1782979015&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_4",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=5&qid=1782979022&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_5",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=6&qid=1782979028&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_6",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=7&qid=1782979039&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_7",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=8&qid=1782979091&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_8",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=9&qid=1782979102&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_9",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=10&qid=1782979117&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_10",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=11&qid=1782979127&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_11",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=12&qid=1782979135&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_12",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=13&qid=1782979145&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_13",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=14&qid=1782979160&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_14",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=15&qid=1782979169&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_15",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=16&qid=1782979176&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_16",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=17&qid=1782979184&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_17",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=18&qid=1782979199&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_18",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=19&qid=1782979209&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_19",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=20&qid=1782979217&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_20",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=21&qid=1782979223&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_21",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=22&qid=1782979291&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_22",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=23&qid=1782979311&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_23",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=24&qid=1782979321&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_24",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=25&qid=1782979330&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_25",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=26&qid=1782979340&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_26",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=27&qid=1782979349&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_27",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=28&qid=1782979356&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_28",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=29&qid=1782979438&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_29",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=30&qid=1782979448&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_30",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=31&qid=1782979456&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_31",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=32&qid=1782979466&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_32",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=33&qid=1782979475&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_33",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=34&qid=1782979481&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_34",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=35&qid=1782979489&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_35",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=36&qid=1782979501&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_36",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=37&qid=1782979511&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_37",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=38&qid=1782979518&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_38",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=39&qid=1782979527&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_39",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=40&qid=1782979535&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_40",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=41&qid=1782979546&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_41",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=42&qid=1782979554&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_42",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=43&qid=1782979563&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_43",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=44&qid=1782979569&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_44",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=45&qid=1782979590&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_45",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=46&qid=1782979595&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_46",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=47&qid=1782979611&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_47",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=48&qid=1782979619&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_48",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=49&qid=1782979626&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_49",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=50&qid=1782979632&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_50",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=51&qid=1782979645&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_51",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=52&qid=1782979654&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_52",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=53&qid=1782979669&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_53",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=54&qid=1782979676&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_54",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=55&qid=1782979684&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_55",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=56&qid=1782979690&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_56",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=57&qid=1782979720&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_57",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=58&qid=1782979728&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_58",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=59&qid=1782979961&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_59",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=60&qid=1782979973&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_60",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=61&qid=1782979981&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_61",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=62&qid=1782980018&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_62",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=63&qid=1782980020&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_63",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=64&qid=1782980017&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_64",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=65&qid=1782980038&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_65",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=66&qid=1782980048&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_66",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=67&qid=1782980054&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_67",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=68&qid=1782980064&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_68",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=69&qid=1782980071&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_69",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=70&qid=1782980091&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_70",
    "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cp_6%3AA1UNQM1SR2CHM&s=popularity-rank&dc&fs=true&page=71&qid=1782980097&rnid=15358539031&xpid=3D0oEmMlA80pq&ref=sr_pg_71",
    "https://www.amazon.com.tr/s?i=warehouse-deals&srs=44219324031&bbn=44219324031&rh=n%3A44219324031%2Cn%3A12466496031&s=date-desc-rank&dc&fs=true&ds=v1%3AN8qg0Wfmh%2BC%2FqcuYbBRla46EqbeKHdRWDxAJnsIICss&qid=1782980139&rnid=44219324031&ref=sr_nr_n_4",
    "https://www.amazon.com.tr/s?i=electronics&srs=44219324031&bbn=44219324031&rh=n%3A44219324031%2Cn%3A12466496031&s=date-desc-rank&dc&fs=true&page=2&qid=1782980150&rnid=44219324031&xpid=x1Qkzzm2n180s&ref=sr_pg_2",
    "https://www.amazon.com.tr/s?i=electronics&srs=44219324031&bbn=44219324031&rh=n%3A44219324031%2Cn%3A12466496031&s=date-desc-rank&dc&fs=true&page=3&qid=1782980164&rnid=44219324031&xpid=x1Qkzzm2n180s&ref=sr_pg_3",
    "https://www.amazon.com.tr/s?i=electronics&srs=44219324031&bbn=44219324031&rh=n%3A44219324031%2Cn%3A12466496031&s=date-desc-rank&dc&fs=true&page=4&qid=1782980170&rnid=44219324031&xpid=x1Qkzzm2n180s&ref=sr_pg_4",
    "https://www.amazon.com.tr/s?i=electronics&srs=44219324031&bbn=44219324031&rh=n%3A44219324031%2Cn%3A12466496031&s=date-desc-rank&dc&fs=true&page=5&qid=1782980178&rnid=44219324031&xpid=x1Qkzzm2n180s&ref=sr_pg_5",
    "https://www.amazon.com.tr/s?i=electronics&srs=44219324031&bbn=44219324031&rh=n%3A44219324031%2Cn%3A12466496031&s=date-desc-rank&dc&fs=true&page=6&qid=1782980187&rnid=44219324031&xpid=x1Qkzzm2n180s&ref=sr_pg_6"
]

# 3. VERİTABANI YÜKLEME
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            veritabanı = json.load(f)
    except:
        veritabanı = {}
else:
    veritabanı = {}

def telegram_mesaj_gonder(mesaj):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def amazon_sayfa_tara(url):
    scraper_url = "https://api.scraperapi.com/"
    params = {"api_key": SCRAPER_API_KEY, "url": url, "country_code": "tr"}
    try:
        response = requests.get(scraper_url, params=params, timeout=60)
        return response.text if response.status_code == 200 else None
    except:
        return None

def veriyi_isle(html_icerik):
    bulunan_urunler = []
    # Amazon arama sonuçları için geliştirilmiş regex
    pattern = r'data-asin="([A-Z0-9]{10})".*?<h2.*?>(.*?)</h2>.*?<span class="a-price-whole">(.*?)</span>'
    matches = re.findall(pattern, html_icerik, re.DOTALL)
    
    for asin, baslik_html, fiyat_str in matches:
        try:
            temiz_baslik = re.sub('<[^<]+?>', '', baslik_html).strip()[:60]
            temiz_fiyat_str = re.sub(r'[^\d]', '', fiyat_str)
            fiyat = float(temiz_fiyat_str)
            bulunan_urunler.append({"asin": asin, "baslik": temiz_baslik, "fiyat": fiyat})
        except:
            continue
    return bulunan_urunler

def ana_program():
    global veritabanı
    print(f"Tarama başlatılıyor. Toplam {len(url_listesi)} sayfa kontrol edilecek.")
    
    for hedef_url in url_listesi:
        html = amazon_sayfa_tara(hedef_url)
        if not html: continue
            
        urunler = veriyi_isle(html)
        
        for urun in urunler:
            asin = urun["asin"]
            fiyat = urun["fiyat"]
            baslik = urun["baslik"]
            
            if asin not in veritabanı:
                veritabanı[asin] = {"baslik": baslik, "fiyat": fiyat}
                telegram_mesaj_gonder(f"🚨 *YENİ ÜRÜN*\n📦 {baslik}\n💰 {fiyat} TL")
            elif fiyat < veritabanı[asin]["fiyat"]:
                telegram_mesaj_gonder(f"📉 *İNDİRİM*\n📦 {baslik}\n✅ Yeni: {fiyat} TL")
                veritabanı[asin]["fiyat"] = fiyat
        
        # API'yi patlatmamak ve bloklanmamak için her sayfadan sonra bekleme
        time.sleep(random.uniform(3, 7))

    # Tüm tarama bitince dosyayı tek seferde güncelle
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(veritabanı, f, ensure_ascii=False, indent=4)
    print("İşlem tamamlandı.")

if __name__ == "__main__":
    ana_program()
