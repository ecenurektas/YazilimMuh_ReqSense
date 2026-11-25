# ReqSense — Yapay Zekâ Destekli Yazılım Gereksinim Analizi Sistemi

**ReqSense**, serbest metin (mülakat notları, proje fikri, müşteri talebi) halindeki doğal dil girdilerini işleyerek yapılandırılmış **fonksiyonel / fonksiyonel olmayan gereksinimler (FR/NFR)**, **belirsizlik uyarıları**, **MoSCoW öncelikleri**, **kullanıcı hikâyeleri (User Stories)** ve **kabul kriterleri (Given-When-Then)** üreten; üretilen çıktıları etkileşimli olarak düzenleyip **Markdown (.md)**, **CSV (.csv)** ve **JSON (.json)** formatlarında dışa aktarmayı sağlayan web tabanlı bir gereksinim mühendisliği uygulamasıdır.

---

## Teknoloji Yığını

| Katman | Teknoloji | Kullanım Amacı |
| :--- | :--- | :--- |
| **Backend & API** | Python 3.12 + FastAPI | Yüksek performanslı REST API, Pydantic veri doğrulama ve otomatik Swagger/OpenAPI dokümantasyonu |
| **NLP / Yapay Zekâ** | Google Gemini API (`google-genai`) | Structured Output (JSON şeması zorunluluğu) ile deterministik ayrıştırılabilir gereksinim üretimi |
| **Ön Yüz (Frontend)** | React (Vite) + Tailwind CSS | Bileşen tabanlı gereksinim giriş formu, sekmeli düzenleme tablosu ve dışa aktarma arayüzü |
| **Veritabanı** | SQLite + SQLAlchemy (ORM) | Sunucusuz, tek dosyalı ve taşınabilir ilişkisel veri kalıcılığı |
| **Otomatik Test** | `pytest` + `httpx` (`TestClient`) | Birim testleri, mock-LLM entegrasyon testleri ve hata senaryosu doğrulamaları |
| **Sürüm Kontrolü** | Git + GitHub | `main`, `dev` ve `feature/...` dalları ile yapılandırılmış geliştirme süreci |

---

## Klasör Yapısı

```text
YazılımMuh/
├── backend/
│   ├── app/
│   │   ├── models/        # SQLAlchemy ORM modelleri (AnalysisSession, Requirement, UserStory, AcceptanceCriterion)
│   │   ├── schemas/       # Pydantic istek/yanıt ve Gemini Structured Output şemaları
│   │   ├── services/      # NLP/Gemini servisi, DEMO_MODE fallback ve dışa aktarma motoru
│   │   ├── routers/       # FastAPI uç noktaları (/api/health, /api/analyze, /api/sessions, /api/export)
│   │   ├── config.py      # Ortam değişkenleri ve uygulama ayarları
│   │   └── main.py        # FastAPI uygulama giriş noktası ve CORS ayarları
│   ├── tests/             # pytest birim ve entegrasyon testleri
│   ├── .env.example       # Örnek ortam değişkenleri şablonu
│   ├── pytest.ini         # pytest yapılandırması
│   └── requirements.txt   # Python bağımlılıkları
├── frontend/
│   ├── src/
│   │   ├── components/    # Arayüz bileşenleri
│   │   ├── services/      # Backend API istemcisi
│   │   ├── App.jsx        # Ana uygulama kabuğu
│   │   ├── index.css      # Tailwind CSS v4 girişi
│   │   └── main.jsx       # React giriş noktası
│   ├── .env.example       # Frontend ortam değişkenleri şablonu
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── docs/
│   ├── 01-proje-tanitimi.md       # Bölüm 1: Proje Tanıtımı taslağı
│   └── 02-gereksinim-analizi.md   # Bölüm 2: Gereksinim Analizi taslağı
├── .gitignore
└── README.md
```

---

## Kurulum ve Çalıştırma

### 1. Backend Kurulumu (Python 3.12 + `uv`)

```powershell
# Sanal ortamı oluştur (Python 3.12 önerilir)
uv venv --python 3.12 backend/.venv

# Bağımlılıkları yükle
uv pip install --python backend/.venv/Scripts/python.exe -r backend/requirements.txt

# Ortam değişkenleri dosyasını oluştur
Copy-Item backend/.env.example backend/.env
```

`backend/.env` dosyasını açıp `GEMINI_API_KEY` değerini tanımlayın. Sunum veya çevrimdışı demo sırasında API bağlantısı olmadan yerel örnek yanıt kullanmak için `DEMO_MODE=true` ayarlanabilir:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-4-hydrogen
GEMINI_TIMEOUT_SECONDS=15
DATABASE_URL=sqlite:///./reqsense.db
DEMO_MODE=false
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

**Backend sunucusunu başlatma:**

```powershell
cd backend
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

API dokümantasyonu (Swagger UI): `http://127.0.0.1:8000/docs`  
Sağlık kontrolü: `http://127.0.0.1:8000/api/health`

**Otomatik testleri çalıştırma:**

```powershell
cd backend
.\.venv\Scripts\pytest.exe -v
```

### 2. Frontend Kurulumu (Node.js LTS + Vite)

> **Ön koşul:** Sistemde Node.js LTS kurulu olmalıdır (`winget install OpenJS.NodeJS.LTS`).

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Ön yüz geliştirme sunucusu varsayılan olarak `http://localhost:5173` adresinde çalışır ve `/api` isteklerini otomatik olarak `http://127.0.0.1:8000` adresindeki FastAPI sunucusuna yönlendirir.

---

## Sürüm Kontrolü ve Dal (Branch) Stratejisi

- `main`: Kararlı, testleri geçmiş ve sunuma/teslime hazır sürüm dalı.
- `dev`: Günlük geliştirme ve entegrasyon dalı.
- `feature/<ozellik-adi>`: Yeni modül veya görevler için açılan özellik dalları (`dev` dalına birleştirilir).

---

## 20 Günlük Yol Haritası Durumu (24 Kasım – 14 Aralık 2026)

| Tarih Aralığı | Aşama | Durum |
| :--- | :--- | :--- |
| **24–25 Kasım** | Planlama, Kurulum, Klasör Yapısı ve Doküman Bölüm 1–2 | Tamamlandı |
| **26–28 Kasım** | Veri Modeli (SQLite/SQLAlchemy) ve NLP Çekirdeği (Gemini Structured Output) | Tamamlandı |
| **29 Kasım – 1 Aralık** | Backend REST API Uç Noktaları, Dışa Aktarma ve Hata Yönetimi | Tamamlandı |
| **2–4 Aralık** | Frontend MVP Arayüzü (Form, Sekmeli Tablo, Düzenleme, Dışa Aktarma) | Tamamlandı |
| **5–6 Aralık** | Frontend–Backend Entegrasyonu ve Geçmiş Oturum Yönetimi | Tamamlandı |
| **7–8 Aralık** | Otomatik Testler (`pytest`), Hata Düzeltme ve `dev -> main` Birleştirmesi | Tamamlandı |
| **9–10 Aralık** | UML Diyagramları ve Tasarım/Geliştirme Dokümanı (Bölüm 3–4) | Planlandı |
| **11–12 Aralık** | Test Raporu, Sonuç ve Kaynakça (Bölüm 5–7) + PDF Çıktısı | Planlandı |
| **13–14 Aralık** | Sunum Hazırlığı, Canlı Demo Provası ve Teslim | Planlandı |
