# Chess Arena

Django asosidagi shaxmat platformasi: bot bilan o'yin (3 daraja), ikki kishilik (bitta qurilmada), do'st bilan link orqali onlayn o'yin, va link orqali taklif qilinadigan single-elimination musobaqalar.

## O'rnatish va ishga tushirish

### CMD (Command Prompt)

```cmd
cd chess_arena
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### PowerShell

```powershell
cd chess_arena
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Keyin brauzerda oching: **http://127.0.0.1:8000/**

## Musobaqa/do'st bilan o'ynash haqida eslatma

Hozirgi versiya `runserver` bilan faqat sizning kompyuteringizda ishlaydi (127.0.0.1). Do'stlaringiz boshqa qurilmadan link orqali qo'shilishi uchun:
- Ikkalangiz bir xil Wi-Fi tarmog'ida bo'lsangiz: `python manage.py runserver 0.0.0.0:8000` bilan ishga tushiring, keyin do'stingizga kompyuteringizning mahalliy IP manzilini bering (masalan `http://192.168.1.5:8000/`)
- Internet orqali istalgan joydan ulanish uchun loyihani biror hosting xizmatiga (Render, Railway, PythonAnywhere va h.k.) joylashtirish kerak bo'ladi — buni xohlasangiz, keyingi bosqichda yordam bera olaman.

## Struktura

- `game/models.py` — Game, Tournament, TournamentPlayer, TournamentMatch
- `game/engine.py` — bot AI (minimax + alpha-beta, pozitsion baholash jadvallari)
- `game/bracket.py` — musobaqa bracket generatsiyasi va g'olibni keyingi bosqichga o'tkazish
- `game/views.py` — barcha rejimlar uchun view'lar
- `game/static/game/` — CSS va original SVG shaxmat donalari
