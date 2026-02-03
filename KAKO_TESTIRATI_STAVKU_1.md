# 🎬 TESTIRANJE STAVKE 1 - Background Runner

## Koraci za testiranje:

### 1️⃣ POKRENI SERVER

Otvori **NOVI PowerShell terminal** (ne ovaj u VS Code) i pokreni:

```bash
cd "C:\Users\Adi\Desktop\Personal Movie Recommender"
python -m uvicorn src.interface.api:app --host 0.0.0.0 --port 8001
```

Ili duplim klikom na: **start_server.bat**

Videćeš:
```
INFO:src.application.runner:Background runner started (tick interval: 5.0s)
INFO:     Uvicorn running on http://0.0.0.0:8001
```

✅ To znači da **background runner radi autonomno**!

---

### 2️⃣ OTVORI WEB INTERFEJS

U browseru idi na: **http://localhost:8001/static/index.html**

---

### 3️⃣ TESTIRAJ NORMALNO

1. **Unesi ime** (npr. "Adi")
2. **Izaberi mood** (npr. "Happy")
3. **Klikni "Get Recommendations"**
4. Videćeš preporuke filmova ✅

Ovo radi normalno kao i ranije.

---

### 4️⃣ TESTIRAJ BACKGROUND RUNNER (KLJUČNO!)

#### Opcija A - Kroz Browser (novi tab):

Otvori **novi tab** i idi na:

**http://localhost:8001/runner/stats**

Videćeš JSON:
```json
{
  "running": true,
  "total_processed": 0,
  "total_no_work": 12,
  "tick_interval": 5.0
}
```

- `running: true` → Runner je aktivan! ✅
- `total_no_work` → Broj puta kad nije bilo posla (broj raste svake 5s!)
- `total_processed` → Broj procesiranih event-a

**Refršuj stranicu posle 10 sekundi** - `total_no_work` će rasti! To dokazuje da runner **AUTONOMNO radi u pozadini**! 🎉

---

#### Opcija B - Dodaj event i vidi processing:

**1. Dodaj event u queue:**

Idi na: **http://localhost:8001/runner/events**

Videćeš:
```json
{"pending": 0, "processed": 0, "total": 0}
```

**2. U drugom PowerShell-u pokreni:**
```bash
cd "C:\Users\Adi\Desktop\Personal Movie Recommender"
python test_stavka1.py
```

Videćeš:
```
✅ SUCCESS! Runner je autonomno procesirao 3 event-a
✅ Background loop radi!
✅ NoWork izlaz implementiran
```

**3. Refršuj http://localhost:8001/runner/events**

Sada će biti:
```json
{"pending": 0, "processed": 3, "total": 3}
```

**Background runner ih je SAM procesirao** dok si ti čekao! 🤖

---

### 5️⃣ ŠTA DOKAZUJE DA RUNNER RADI?

1. **Vidiš log** u terminalu: `Background runner started`
2. **NoWork ticks rastu** - runner radi konstantno
3. **Eventi se procesiraju sami** - dodaš u queue, sačekaš, oni se obrade
4. **Ne moraš kliknuti ništa** - agent radi autonomno!

---

## 🎯 RAZLIKA SA PRETHODNOM VERZIJOM:

| **RANIJE** | **SADA** |
|------------|----------|
| Klikneš dugme → Procesira | Klikneš dugme → Dodaje u queue |
| Čekaš da se završi | Odmah dobiješ odgovor |
| Nema autonomnog rada | **Runner radi 24/7 u pozadini** |
| Reaktivna aplikacija | **Pravi autonomni agent** ✅ |

---

## 📝 BRZI TEST (za profesora):

```bash
# Terminal 1: Pokreni server
python -m uvicorn src.interface.api:app --host 0.0.0.0 --port 8001

# Terminal 2: Pokreni test
python test_stavka1.py
```

Output će biti:
```
✅ SUCCESS! Runner je autonomno procesirao 3 event-a
✅ Background loop radi!
✅ NoWork izlaz implementiran (vidi NoWork ticks)
✅ Event queue sistem funkcioniše!
```

**TO JE TO! STAVKA 1 DONE!** 🎉
