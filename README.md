```markdown
# LifeOS - Personal Second Brain

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Database-SQLite3-003B57?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/Vector%20Store-FAISS-008080?style=flat-square" alt="FAISS">
  <img src="https://img.shields.io/badge/AI%20Providers-Gemini%20%7C%20OpenAI-8E75B2?style=flat-square&logo=openai&logoColor=white" alt="AI">
  <img src="https://img.shields.io/badge/GUI-PySide6%20(Qt6)-41CD52?style=flat-square&logo=qt&logoColor=white" alt="GUI">
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" alt="License">
</p>

<p align="center">
  <b>Yerel dosyalarınızı indeksleyin, içerik çıkarın, semantik arama yapın ve yapay zekâ destekli RAG motoruyla belgelerinizle etkileşime geçin.</b>
</p>

<p align="center">
  <a href="#genel-bakış">Genel Bakış</a> •
  <a href="#temel-özellikler">Özellikler</a> •
  <a href="#teknoloji-yığını">Teknolojiler</a> •
  <a href="#kurulum">Kurulum</a> •
  <a href="#kullanım">Kullanım</a> •
  <a href="#proje-mimarisi">Mimari</a> •
  <a href="#güvenlik-ve-gizlilik">Güvenlik</a>
</p>

---

## Genel Bakış

**LifeOS**, kişisel bilgisayarınızdaki tüm veri akışını (kodlar, belgeler, notlar, görsel içerikler) anlamlandırıp birbirine bağlayan yerel bir **İkinci Beyin (Second Brain)** sistemidir.

Verilerinizi güvenli şekilde yerelde işler, vektör veritabanına aktarır ve hem **CLI** hem de modern **PySide6 Masaüstü Arayüzü** üzerinden semantik/hibrit aramalar yapmanıza, RAG (Retrieval-Augmented Generation) altyapısıyla belgeleriniz üzerinden sorular sormanıza olanak tanır.

---

## Temel Özellikler

### 1. Çok Formatlı Doküman Çıkarımı & OCR
- **Belgeler & Notlar:** `PDF`, `DOCX`, `TXT`, `MD`, `JSON`, `YAML`
- **Görsel & Taramalar:** `EasyOCR` entegrasyonu ve görüntü ön işleme ile görseldeki metinleri çıkarma
- **Kod Tabanı:** Dili tanıyan ve AST/kod mantığına göre bloklayan özel `CodeChunker`

### 2. Hibrit Arama & Sıralama (Hybrid Search & Ranking)
- **Semantik Arama:** `sentence-transformers` (`all-MiniLM-L6-v2`) ve `FAISS` indeksleme
- **Hibrit Skorlama:** Anlamsal benzerlik + anahtar kelime eşleşmesi + dosya güncelliği (recency) + meta veri ağırlıklandırması

### 3. Çoklu LLM / RAG Desteği
- **Google Gemini** ve **OpenAI** API entegrasyonu
- Bağlam birleştirici (`ContextBuilder`) ve yanıt doğrulayıcı (`AnswerValidator`) mimarisi

### 4. Bellek & Zaman Çizelgesi (Memory Engine)
- Anlık notlar, varlık (entity) ve ilişki (relation) çıkarımı
- Kronolojik olay takibi ve geçmiş sorgulama (`Timeline`)

### 5. Arka Plan Senkronizasyonu & Güvenlik
- Dosya değişikliklerini izleyen `Watcher` ve arka plan `Indexer` servisi
- Sistem tepsisi (`System Tray`) entegrasyonu
- Otomatik hassas veri (API Key, Secrets) ve gizli dizin (`.git`, `node_modules`, `data/`) filtreleme

---

## Teknoloji Yığını

| Katman | Teknoloji / Kütüphane |
|---|---|
| **Programlama Dili** | Python 3.11+ |
| **Vektör Depolama** | Meta FAISS |
| **Metin Gömme (Embedding)** | `sentence-transformers` (`all-MiniLM-L6-v2`) |
| **İlişkisel Veritabanı** | SQLite3 (Repository Pattern, Migrations) |
| **Masaüstü Arayüzü** | PySide6 (Qt6) — Tokyo Night Koyu Tema |
| **Görsel İşleme / OCR** | EasyOCR + Preprocessor |
| **CLI / Terminal** | Click + Rich |
| **Konfigürasyon** | Pydantic Settings + `.env` |

---

## Kurulum

### 1. Repoyu Klonlayın
```bash
git clone [https://github.com/Berkay-Dmr/LifeOs.git](https://github.com/Berkay-Dmr/LifeOs.git)
cd LifeOs

```

### 2. Sanal Ortamı Oluşturun ve Aktif Edin

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\activate

```

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate

```

### 3. Bağımlılıkları Yükleyin

```bash
pip install -e .

```

### 4. Ortam Değişkenlerini Tanımlayın

Kök dizindeki `.env.example` dosyasını `.env` olarak kopyalayın ve anahtarlarınızı girin:

```env
# AI Sağlayıcı Seçimi (gemini veya openai)
LIFEOS_AI_PROVIDER=gemini

# API Anahtarları
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# İsteğe Bağlı Dizin Yapılandırması
LIFEOS_ROOT=C:\Users\Kullanici\Belgeler

```

---

## Kullanım

### Masaüstü Arayüzü (GUI)

Modern ve karanlık temalı masaüstü kontrol panelini başlatmak için:

```powershell
lifeos gui

```

Arayüz modülleri:

* **Search:** Çok parametreli hibrit ve semantik belge arama
* **Ask AI:** RAG destekli akıllı doküman asistanı
* **Memory & Timeline:** Not ekleme, ilişki görselleştirme ve olay zaman çizelgesi
* **Settings:** Model sağlayıcı ve dizin yapılandırma paneli

---

### Komut Satırı Arayüzü (CLI)

#### Veritabanı & İndeksleme

```powershell
# Veritabanını ve tabloları başlat
lifeos init

# Belgeleri tara ve vektörleştir
lifeos index

# Tüm belgeleri sıfırdan zorla indeksle
lifeos index --force

```

#### Arama & AI Sorgulama

```powershell
# Hibrit arama yap
lifeos search "veritabanı bağlantı havuzu ayarları"

# RAG motoru ile belgeler üzerinden soru sor
lifeos ask "Projedeki veritabanı mimarisi nasıl kurgulandı?" --provider gemini

```

#### Bellek Yönetimi

```powershell
# Belleğe yeni bir bilgi/not ekle
lifeos memory add "Sistem mimarisi mikroservis yapısına geçirilecek" --tags mimari,plan

# Bellekten ara ve getir
lifeos memory recall "mikroservis"

# Kayıtlı tüm bellek girdilerini listele
lifeos memory list

```

---

## Proje Mimarisi

```text
lifeos/
├── app/
│   ├── ai/             # Gemini & OpenAI Provider, Context Builder, RAG Prompts
│   ├── background/     # File Watcher, Auto Indexer, System Tray
│   ├── chunking/       # Text & AST Tabanlı Code Chunker
│   ├── cli/            # Click & Rich Tabanlı Komut Seti
│   ├── config/         # Pydantic Tabanlı Ayar ve .env Yönetimi
│   ├── database/       # SQLite Bağlantısı, Migrations, Repository Katmanı
│   ├── embeddings/     # Yerel Caching ve Sentence-Transformers Altyapısı
│   ├── extractors/     # PDF, DOCX, Markdown, Kod, JSON/YAML Parserları
│   ├── git/            # Yerel Git Repository ve Commit İndeksleyici
│   ├── gui/            # PySide6 Qt Pencereleri ve Tokyo Night Stilleri
│   ├── ingestion/      # Incremental File Scanner ve Metadata Registry
│   ├── memory/         # Entity, Relation, Timeline ve Memory Motoru
│   ├── models/         # Tip Güvenli Veri Modelleri (Dataclasses)
│   ├── ocr/            # EasyOCR Entegrasyonu ve Görsel Ön İşleme
│   ├── privacy/        # Secret & API Key Tespiti, Hariç Tutma Filtreleri
│   ├── search/         # Hibrit Sıralama, Semantik ve TF-IDF Tabanlı Arama
│   ├── utils/          # Hashing, Logging, Metin ve Dosya Araçları
│   └── vectorstore/    # FAISS Vektör İndeksi ve Metadata Yönetimi
├── .env.example        # Şablon Ortam Değişkenleri
├── pyproject.toml      # Paket ve Proje Yapılandırması
└── requirements.txt    # Python Bağımlılık Listesi

```

---

## Güvenlik ve Gizlilik

* **Yerel Veri Saklama:** Vektör indeksleri (`faiss.index`) ve ilişkisel veriler (`sqlite.db`) tamamen yerel diskinizde tutulur.
* **Hassas Veri Filtreleme:** İndeksleme sırasında kaynak kodlar veya metinlerdeki API anahtarları, şifreler ve gizli değerler taranarak vektör tabanına aktarılmaz.
* **Dizin İzolasyonu:** `.git`, `node_modules`, `venv`, derleme çıktıları ve loglar tarama dışı bırakılır.

---

## Lisans

Bu proje **MIT Lisansı** altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakabilirsiniz.

```

```
