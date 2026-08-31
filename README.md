```markdown
<div align="center">

# 🧠 LifeOS
### *Autonomous Local Second Brain & Multi-Modal Semantic Engine*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Qt](https://img.shields.io/badge/PySide6-Tokyo_Night_GUI-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://pypi.org/project/PySide6/)
[![FAISS](https://img.shields.io/badge/Vector_DB-Meta_FAISS-008080?style=for-the-badge&logo=meta&logoColor=white)](https://github.com/facebookresearch/faiss)
[![LLM Support](https://img.shields.io/badge/AI_Engine-Gemini_%7C_OpenAI-7B2CBF?style=for-the-badge&logo=openai&logoColor=white)](https://github.com/Berkay-Dmr/LifeOs)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

<p align="center">
  <b>Yerel verilerinizi vektörleştirin, anlamsal ilişkiler kurun, AST tabanlı kod analizi yapın ve hibrit RAG ile masaüstünüzü dijital bir zihne dönüştürün.</b>
</p>

[✨ Özellikler](#-temel-özellikler) •
[⚡ Hızlı Başlangıç](#-hızlı-başlangıç) •
[🖥️ GUI & CLI](#-kullanım-paneli) •
[🏗️ Mimari](#-derinlemesine-sistem-mimarisi) •
[🛡️ Gizlilik & Güvenlik](#-güvenlik-ve-gizlilik)

---

</div>

## 🌌 Sisteme Bakış

**LifeOS**, dağınık durumdaki yerel belgelerinizi, kaynak kodlarınızı, taranmış dokümanlarınızı ve günlük notlarınızı birbirine bağlayan **yüksek performanslı, yerel bir RAG (Retrieval-Augmented Generation)** ekosistemidir.

Verileriniz diskinizde kalır; yerel embedding motorları (`sentence-transformers`) ve **Meta FAISS** vektör dizinlemesi ile tamamen makinenizde işlenir.


```

📁 Yerel Dosyalar ──► 🔍 Çoklu Parser / OCR ──► ✂️ Akıllı Chunker ──► 🧠 FAISS + SQLite
│
🖥️ PySide6 GUI / CLI ◄── 🤖 RAG Engine (Gemini / OpenAI) ◄──────────────────┘

```

---

## ✨ Temel Özellikler

### 🧬 Çok Boyutlu İndeksleme & Akıllı Ayrıştırma (Extractors)
* **Doküman Desteği:** `PDF`, `DOCX`, `Markdown`, `TXT`, `JSON`, `YAML`
* **Görsel & OCR:** Görüntü ön işleme filtresi destekli `EasyOCR` ile görseldeki metinleri yakalama
* **Kod Tabanı (AST Parser):** Dilden bağımsız salt metin bölmesi yerine fonksiyon ve sınıf hiyerarşisini koruyan özel `CodeChunker`
* **Git Repository Analizi:** Commit geçmişini ve repo metadata'sını taranabilir varlıklara dönüştürme

### ⚡ Hibrit Arama & Dinamik Sıralama (Hybrid Ranking)
* **Semantik Vektör Eşleme:** `all-MiniLM-L6-v2` embeddingleri ile FAISS L2/Cosine mesafe sorguları
* **Çok Faktörlü Skorlama:** `Score = Semantic + Keyword (BM25/TF-IDF) + Recency + Metadata Weights`

### 🧠 Bilişsel Bellek & Zaman Çizelgesi (Memory Engine)
* **Varlık (Entity) & İlişki (Relation) Çıkarımı:** Eklenen notlar arasında semantik bağ kurma
* **Zaman Çizelgesi (Timeline):** Dosya ve notların kronolojik akışını çıkarıp sorgulayabilme

### 🛡️ Gizlilik Kalkanı (Privacy Guard)
* Otomatik Regex tabanlı API Key, Token ve Secret filtreleme
* `.git`, `node_modules`, `venv`, `logs/`, `data/` dizinlerinin varsayılan izolasyonu

---

## 🛠️ Teknoloji Yığını

| Katman | Teknoloji | Açıklama |
|---|---|---|
| **Çekirdek Dil** | `Python 3.11+` | Tip güvenli dataclass mimarisi, modüler yapı |
| **Vektör Motoru** | `Meta FAISS` | Düşük gecikmeli vektör arama ve indeksleme |
| **Embedding** | `sentence-transformers` | `all-MiniLM-L6-v2` yerel vektörleştirme |
| **İlişkisel Veritabanı** | `SQLite3` | Repository pattern, otomatik migration katmanı |
| **Kullanıcı Arayüzü** | `PySide6 (Qt6)` | Özelleştirilmiş Tokyo Night karanlık tema |
| **Optik Karakter Tanıma**| `EasyOCR` | Çok dilli yerel metin okuma motoru |
| **Terminal & CLI** | `Click` + `Rich` | Renkli loglama ve terminal araç takımı |

---

## ⚡ Hızlı Başlangıç

### 1. Depoyu Klonlayın

```bash
git clone [https://github.com/Berkay-Dmr/LifeOs.git](https://github.com/Berkay-Dmr/LifeOs.git)
cd LifeOs

```

### 2. Sanal Ortam Kurulumu

```powershell
# Sanal ortamı oluşturun
python -m venv venv

# Aktif edin (Windows)
.\venv\Scripts\activate

# Aktif edin (Linux / macOS)
# source venv/bin/activate

```

### 3. Bağımlılıkları Yükleyin

```powershell
pip install -e .

```

### 4. Çevre Değişkenlerini Tanımlayın

Kök dizinde `.env` dosyanızı oluşturun:

```env
# Aktif AI Sağlayıcısı (gemini | openai)
LIFEOS_AI_PROVIDER=gemini

# API Anahtarları
GEMINI_API_KEY=AIzaSy...
OPENAI_API_KEY=sk-proj-...

# İsteğe Bağlı Kök Dizin
LIFEOS_ROOT=C:\Users\Kullanici\Belgeler

```

---

## 🖥️ Kullanım Paneli

### 🎨 Masaüstü Arayüzü (GUI)

Modern Qt6 tabanlı arayüzü başlatmak için:

```powershell
lifeos gui

```

> **Arayüz Sekmeleri:**
> * **🔍 Search:** Hibrit filtrelemeli hızlı semantik arama konsolu.
> * **🤖 Ask AI:** İndekslenen dokümanları bağlam olarak kullanan RAG sohbet ekranı.
> * **🧠 Memory & Timeline:** Not ekleme, varlık ilişkilendirme ve olay kronolojisi.
> * **⚙️ Settings:** Sağlayıcı ve sistem dizin konfigürasyonu.
> 
> 

---

### 💻 Komut Satırı Arayüzü (CLI)

```powershell
# 1. Veritabanını ve şemayı hazırla
lifeos init

# 2. Belgeleri tara ve indeksle (incremental)
lifeos index

# 3. İndekslenmiş içeriklerde semantik arama yap
lifeos search "veritabanı bağlantı havuzu ayarları"

# 4. RAG motoru üzerinden belgelerine soru sor
lifeos ask "Projedeki veritabanı mimarisi nasıl kurgulandı?" --provider gemini

# 5. Belleğe yeni bir bilgi kaydet
lifeos memory add "Sistem mimarisi mikroservis yapısına geçirilecek" --tags mimari,plan

# 6. Bellekten bağlamsal geri çağırma yap
lifeos memory recall "mikroservis"

```

---

## 🏗️ Derinlemesine Sistem Mimarisi

```text
lifeos/
├── 📂 app/
│   ├── 🤖 ai/             # LLM Entegrasyonları (Gemini & OpenAI), Context Builder, Promptlar
│   ├── 🔄 background/     # File Watcher, Otomatik Indexer, System Tray Modülü
│   ├── 🧩 chunking/       # Semantik Metin ve AST Tabanlı Kod Parçalayıcılar
│   ├── 💻 cli/            # Click & Rich Tabanlı Terminal Komutları
│   ├── ⚙️ config/         # Pydantic Settings, Ortam Değişkeni Yönetimi
│   ├── 🗄️ database/       # SQLite Bağlantısı, Tablo Şemaları & Repository Katmanı
│   ├── 🔢 embeddings/     # Yerel Embedding Caching ve Model Entegrasyonu
│   ├── 📄 extractors/     # PDF, DOCX, Markdown, Kod, JSON/YAML Parserları
│   ├── 🌿 git/            # Yerel Git Repo Tespiti ve Commit İndeksleyici
│   ├── 🖥️ gui/            # PySide6 Pencereleri, Widget'lar ve Tokyo Night Teması
│   ├── 📥 ingestion/      # Incremental File Scanner ve Registry
│   ├── 🧠 memory/         # Entity, Relation ve Timeline Bellek Motoru
│   ├── 📦 models/         # Tip Güvenli Veri Modelleri (Dataclasses)
│   ├── 👁️ ocr/            # EasyOCR Entegrasyonu ve Görsel Ön İşleme
│   ├── 🛡️ privacy/        # Regex Tabanlı Secret/API Key Filtresi ve Dizin İzolasyonu
│   ├── 🔎 search/         # Hibrit Sıralama, Semantik ve TF-IDF Arama Algoritmaları
│   ├── 🛠️ utils/          # Hashing, Logging, Metin ve Dosya Yardımcıları
│   └── 🗃️ vectorstore/    # Meta FAISS Vektör İndeksi ve Metadata Yönetimi
├── 📄 .env.example        # Örnek Konfigürasyon Şablonu
├── ⚙️ pyproject.toml      # Paket ve Proje Yapılandırması
└── 📋 requirements.txt    # Bağımlılık Listesi

```

---

## 🛡️ Güvenlik ve Gizlilik

* **%100 Yerel Veri Saklama:** İndekslenen tüm metinler, FAISS vektörleri ve SQLite verileri cihazınızda şifrelenmeden veya buluta yüklenmeden yerel diskte saklanır.
* **Secret Redaction:** İndeksleme sırasında kaynak kod veya dokümanlarda tespit edilen hassas API anahtarları otomatik olarak maskelenir.
* **Dışarı Kapalı Mimari:** Yapay zekâ sorguları haricinde hiçbir veriniz üçüncü taraf sunuculara iletilmez.

---

## 📜 Lisans

Bu proje **MIT Lisansı** kapsamında sunulmaktadır. Ayrıntılar için [`LICENSE`](https://www.google.com/search?q=LICENSE) dosyasına göz atabilirsiniz.

---

⭐ **Projeyi beğendiyseniz yıldız vermeyi unutmayın!** ⭐
