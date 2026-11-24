# 2. Gereksinim Analizi

Bu bölümde **ReqSense** sisteminin fonksiyonel gereksinimleri (FR), fonksiyonel olmayan gereksinimleri (NFR), kullanıcı hikâyeleri (User Stories), kabul kriterleri (*Given-When-Then*), MoSCoW önceliklendirme matrisi ve gereksinim izlenebilirlik matrisi sunulmaktadır.

---

## 2.1 Fonksiyonel Gereksinimler (FR)

Sistemin temel işlevlerini tanımlayan beş çekirdek fonksiyonel gereksinim ve hata/istisna yönetimi kuralları aşağıda listelenmiştir:

- **FR-01 (Doğal Dil Girdisi ve Yapay Zekâ Tabanlı Analiz):**  
  Kullanıcı, arayüz üzerinden proje başlığı (opsiyonel veya otomatik türetilebilir) ve doğal dilde proje açıklaması/mülakat notu girer. Sistem, girdiyi doğruladıktan sonra NLP/LLM analiz hattından geçirerek yapılandırılmış JSON formatında Fonksiyonel Gereksinimler (`FR`), Fonksiyonel Olmayan Gereksinimler (`NFR`), Kullanıcı Hikâyeleri (`UserStory`) ve Kabul Kriterleri (`AcceptanceCriterion`) üretir ve yeni bir analiz oturumu olarak veritabanına kaydeder.
  - *Girdi Doğrulama Kuralı:* Boş metin veya minimum uzunluk sınırının (20 karakter) altındaki girdiler işleme alınmaz; HTTP `422` (veya `400`) durum kodu ve açıklayıcı Türkçe doğrulama mesajı döndürülür.

- **FR-02 (Kalite, Belirsizlik Denetimi ve Otomatik MoSCoW Önceliklendirme):**  
  Sistem, analiz sırasında metindeki ölçülebilir olmayan, öznel veya muğlak ifadeleri (ör. *"hızlı olsun"*, *"kullanıcı dostu"*, *"modern tasarım"*, *"yeterince güvenli"*) tespit eder ve ilgili gereksinim kaydında açıklayıcı bir belirsizlik uyarısı (`ambiguity_warning`) alanı üretir. Ayrıca her gereksinime bağlama göre `Must`, `Should`, `Could` veya `Wont` değerlerinden birini içeren otomatik MoSCoW öncelik etiketi atar.

- **FR-03 (Etkileşimli Düzenleme ve Kalıcı Güncelleme):**  
  Kullanıcı, analiz sonucunda üretilen herhangi bir gereksinimi (açıklama, tür `functional`/`non_functional`, MoSCoW önceliği, belirsizlik uyarısı), kullanıcı hikâyesini (rol, hedef, fayda) veya kabul kriterini (*Given-When-Then*) arayüzdeki sekmeli tablo üzerinden düzenleyebilir, yeni satır ekleyebilir veya mevcut bir satırı silebilir. Yapılan değişiklikler backend API aracılığıyla SQLite veritabanında kalıcı olarak güncellenir.

- **FR-04 (Çoklu Formatta Dışa Aktarma):**  
  Kullanıcı, incelediği ve düzenlediği bir analiz oturumunun çıktılarını tek tıkla üç farklı formatta indirebilmelidir:
  1. **Markdown (`.md`):** SRS (Software Requirements Specification) taslağı yapısında okunabilir doküman.
  2. **CSV (`.csv`):** UTF-8 (Excel/Jira/Trello uyumlu, özel karakterleri düzgün kaçışlı) tablo çıktısı.
  3. **JSON (`.json`):** Sistem entegrasyonları için tam yapılandırılmış veri çıktısı.

- **FR-05 (Analiz Geçmişi Yönetimi):**  
  Kullanıcı, daha önce oluşturulmuş ve veritabanında saklanan analiz oturumlarını listeleyebilir, seçtiği bir oturumun tüm detaylarını tekrar görüntüleyebilir veya artık ihtiyaç duymadığı oturumları kalıcı olarak silebilir.

### Hata, İstisna Yönetimi ve Demo Güvenliği Kuralları

- **Girdi Doğrulama (HTTP 400 / 422):** Boş veya 20 karakterden kısa metin gönderildiğinde Pydantic doğrulaması devreye girer ve arayüzde kullanıcıya açıklayıcı uyarı gösterilir.
- **LLM API ve Ayrıştırma Hataları (HTTP 502 / 503):** Geçersiz API anahtarı, ağ zaman aşımı (timeout), API kota aşımı veya beklenmeyen LLM yanıtı durumlarında `try-except` blokları hatayı yakalar; uygulama çökmeden anlamlı bir JSON hata yanıtı döndürür ve arayüzde yeniden deneme seçeneği sunar.
- **Kayıt Bulunamadı (HTTP 404):** Mevcut olmayan bir oturum kimliği (`session_id`) ile görüntüleme, güncelleme, silme veya dışa aktarma istendiğinde standart HTTP `404` JSON hatası döndürülür.
- **Çevrimdışı Sunum Yedeği (`DEMO_MODE=true`):** Ortam değişkeni etkinleştirildiğinde sistem harici Gemini API çağrısı yapmadan önceden hazırlanmış gerçekçi örnek analiz yanıtı (fallback) üreterek demo sürekliliğini garanti eder.

---

## 2.2 Fonksiyonel Olmayan Gereksinimler (NFR)

| Kod | Kategori | Gereksinim Tanımı ve Ölçülebilir Kriter |
| :--- | :--- | :--- |
| **NFR-01** | **Performans** | Geçmiş oturumların listelenmesi, düzenlemelerin kaydedilmesi ve dışa aktarma işlemleri yerel ortamda en fazla **500 ms** içinde tamamlanmalıdır. LLM analiz isteği normal ağ koşullarında **15 saniye** içinde yanıt vermeli, aksi halde zaman aşımı koruması devreye girmelidir. |
| **NFR-02** | **Kullanılabilirlik** | İlk kez kullanan bir kullanıcı, harici bir kullanım kılavuzuna ihtiyaç duymadan **en fazla 3 adımda** (Metin Gir -> Analiz Et -> Düzenle/Dışa Aktar) ilk analizini tamamlayabilmelidir. Yükleme durumları (loading indicator), belirsizlik rozetleri ve hata mesajları açık Türkçe ifadelerle sunulmalıdır. |
| **NFR-03** | **Güvenilirlik ve Hata Toleransı** | Gemini Structured Output ve Pydantic şema doğrulaması sayesinde başarılı analiz yanıtlarının **%100'ü** geçerli veri modeline uygun olmalıdır. Dış API kesintilerinde backend süreci çökmemeli, HTTP `502`/`503` ile kontrollü hata dönmeli veya `DEMO_MODE=true` ile kesintisiz çalışabilmelidir. |
| **NFR-04** | **Taşınabilirlik ve Kurulum Kolaylığı** | Uygulama harici veritabanı sunucusu kurulumu gerektirmeden tek dosyalı SQLite veritabanıyla çalışabilmeli; Windows, macOS ve Linux ortamlarında `README.md` adımları izlenerek yerel olarak ayağa kaldırılabilmelidir. |
| **NFR-05** | **Güvenlik ve Yapılandırma Gizliliği** | `GEMINI_API_KEY` gibi hassas kimlik bilgileri kaynak koduna gömülmemeli, `.env` dosyası üzerinden okunmalı ve `.gitignore` ile sürüm kontrolü dışında tutulmalıdır. |

---

## 2.3 Kullanıcı Hikâyeleri ve Kabul Kriterleri (Given-When-Then)

### US-01: Doğal Dil Metninden Gereksinim Analizi Oluşturma (İlişkili: FR-01)
> **Bir** iş analisti veya yazılım öğrencisi **olarak**, müşteri talebini içeren serbest metni sisteme girip tek tıkla analiz ettirmek **istiyorum**; **böylece** manuel ayrıştırmaya saatler harcamadan yapılandırılmış gereksinim taslağı elde edebilirim.

- **AC-01.1 (Başarılı Analiz ve Kayıt):**
  - **Given** kullanıcı ana ekrandaki gereksinim giriş formundadır ve en az 20 karakterlik anlamlı bir proje açıklaması girmiştir,
  - **When** kullanıcı *"Analiz Et"* butonuna tıkladığında (`POST /api/analyze`),
  - **Then** sistem gereksinimleri (`FR`/`NFR`), kullanıcı hikâyelerini ve kabul kriterlerini üretir, oturumu SQLite veritabanına kaydeder ve sonuçları sekmeli görünümde listeler.
- **AC-01.2 (Geçersiz/Kısa Girdi Doğrulaması):**
  - **Given** kullanıcı metin alanını boş bırakmış veya 20 karakterden kısa bir ifade girmiştir,
  - **When** analiz isteği gönderildiğinde,
  - **Then** sistem HTTP `422` doğrulama hatası döndürür, LLM servisini gereksiz yere çağırmaz ve arayüzde kullanıcıya açıklayıcı uyarı mesajı gösterir.
- **AC-01.3 (Harici LLM Servis Hatası Yönetimi):**
  - **Given** `DEMO_MODE=false` iken Gemini API anahtarı geçersizdir veya zaman aşımı/kota hatası oluşmuştur,
  - **When** kullanıcı analiz başlattığında,
  - **Then** backend hatayı `try-except` ile yakalar, çökmeden HTTP `503` (veya `502`) JSON hatası döner ve arayüzde yeniden deneme bildirimi görüntülenir.

### US-02: Muğlak İfadelerin Tespiti ve MoSCoW Önceliklendirmesi (İlişkili: FR-02)
> **Bir** ürün sahibi **olarak**, girdi metnimdeki belirsiz ifadelerin işaretlenmesini ve her gereksinime otomatik MoSCoW etiketi atanmasını **istiyorum**; **böylece** geliştirme önceliklerini ve netleştirilmesi gereken noktaları hemen görebilirim.

- **AC-02.1 (Belirsizlik Uyarısı Üretimi):**
  - **Given** kullanıcı girdisinde *"Sistem çok hızlı çalışsın ve arayüzü kullanıcı dostu olsun"* gibi ölçülebilir olmayan ifadeler bulunmaktadır,
  - **When** analiz tamamlandığında,
  - **Then** ilgili gereksinim satırının `ambiguity_warning` alanında belirsizliğin nedenini ve nasıl somutlaştırılabileceğini belirten bir uyarı rozeti görüntülenir.
- **AC-02.2 (Geçerli MoSCoW Etiket Ataması):**
  - **Given** sistem analiz çıktısını üretmektedir,
  - **When** her gereksinim nesnesi şema doğrulamasından geçtiğinde,
  - **Then** `moscow_priority` alanı yalnızca `Must`, `Should`, `Could` veya `Wont` değerlerinden birini içerir ve arayüzde renkli etiket olarak gösterilir.

### US-03: Üretilen Gereksinim ve Kabul Kriterlerini Düzenleme (İlişkili: FR-03)
> **Bir** yazılım mühendisi **olarak**, yapay zekânın ürettiği gereksinimleri, öncelikleri ve kabul kriterlerini doğrudan tablo üzerinden düzenleyip yeni madde ekleyebilmek **istiyorum**; **böylece** alan bilgime göre çıktıyı son haline getirip saklayabilirim.

- **AC-03.1 (Satır İçi Güncelleme ve Kalıcılık):**
  - **Given** ekranda mevcut bir analiz oturumu açıktır,
  - **When** kullanıcı bir gereksinimin açıklamasını veya MoSCoW önceliğini değiştirip kaydettiğinde (`PUT /api/sessions/{id}`),
  - **Then** veritabanındaki kayıt güncellenir, başarı bildirimi gösterilir ve sayfa yenilendiğinde güncel değerler korunur.
- **AC-03.2 (Yeni Madde Ekleme ve Satır Silme):**
  - **Given** kullanıcı sonuç tablosunu incelemektedir,
  - **When** kullanıcı yeni bir gereksinim satırı eklediğinde veya istenmeyen bir satırı sildiğinde,
  - **Then** ilgili alt kayıt ilişkili oturum altında oluşturulur veya silinir ve güncel toplam sayı arayüze yansır.

### US-04: Onaylanan Çıktıyı Markdown, CSV veya JSON Olarak Dışa Aktarma (İlişkili: FR-04)
> **Bir** proje yöneticisi **olarak**, düzenlediğim gereksinim analizini tek tıkla `.md`, `.csv` veya `.json` formatında indirmek **istiyorum**; **böylece** proje dokümanımda veya Jira/Trello gibi araçlarda doğrudan kullanabilirim.

- **AC-04.1 (Markdown SRS Taslağı İndirme):**
  - **Given** veritabanında kayıtlı ve gereksinimler içeren bir oturum seçilidir,
  - **When** kullanıcı *"Markdown İndir"* seçeneğine tıkladığında (`GET /api/sessions/{id}/export?format=md`),
  - **Then** proje başlığını, FR/NFR tablosunu, belirsizlik notlarını, kullanıcı hikâyelerini ve *Given-When-Then* kriterlerini içeren geçerli bir `.md` dosyası indirilir.
- **AC-04.2 (Jira/Trello Uyumlu CSV İndirme):**
  - **Given** gereksinim açıklamalarında virgül, tırnak veya Türkçe karakterler yer almaktadır,
  - **When** kullanıcı *"CSV İndir"* seçeneğini tetiklediğinde (`GET /api/sessions/{id}/export?format=csv`),
  - **Then** CSV motoru özel karakterleri RFC 4180 kurallarına uygun biçimde kaçışlar (escaping) ve UTF-8 kodlamalı indirilebilir `.csv` dosyası sunar.

### US-05: Geçmiş Analiz Oturumlarını Görüntüleme ve Silme (İlişkili: FR-05)
> **Bir** kullanıcı **olarak**, önceki analiz oturumlarımı listeleyip tekrar açabilmek veya gereksiz olanları silebilmek **istiyorum**; **böylece** önceki çalışmalarıma kolayca geri dönebilirim.

- **AC-05.1 (Geçmiş Listeleme ve Tekrar Açma):**
  - **Given** veritabanında en az bir tamamlanmış analiz oturumu bulunmaktadır,
  - **When** kullanıcı geçmiş panelinden bir oturuma tıkladığında (`GET /api/sessions/{id}`),
  - **Then** oturuma ait ham girdi, gereksinimler, kullanıcı hikâyeleri ve kabul kriterleri ekrana yüklenir.
- **AC-05.2 (Oturum Silme ve 404 Kontrolü):**
  - **Given** kullanıcı geçmiş listesindeki bir oturumu siler (`DELETE /api/sessions/{id}`),
  - **When** silinen veya var olmayan bir ID tekrar sorgulandığında,
  - **Then** ilgili oturum ve bağlı alt kayıtlar (cascade) veritabanından kaldırılmış olur ve sonraki isteklerde HTTP `404` JSON hatası döndürülür.

---

## 2.4 Gereksinim Önceliklendirmesi (MoSCoW Matrisi)

| Kod | Başlık / Kapsam Maddesi | Tür | MoSCoW Önceliği | Gerekçe |
| :--- | :--- | :--- | :--- | :--- |
| **FR-01** | Doğal dil girdisinden yapılandırılmış analiz üretimi ve girdi doğrulama | FR | **Must Have** | Sistemin temel varoluş amacı ve MVP çekirdek akışıdır. |
| **FR-02** | Belirsizlik tespiti (`ambiguity_warning`) ve MoSCoW etiketleme | FR | **Must Have** | Müfredattaki gereksinim kalitesi odağını doğrudan karşılar. |
| **FR-03** | Etkileşimli satır içi düzenleme, ekleme/silme ve DB kaydı | FR | **Must Have** | MVP kapsamındaki "düzenleme" şartının zorunlu parçasıdır. |
| **FR-04** | Markdown (`.md`) ve CSV (`.csv`) dışa aktarma | FR | **Must Have** | MVP kapsamındaki "dışa aktarma" şartı için temel formatlardır. |
| **FR-04b** | JSON (`.json`) formatında dışa aktarma | FR | **Should Have** | Geliştirici ve API entegrasyon senaryolarını güçlendirir. |
| **FR-05** | Geçmiş analiz oturumlarını listeleme, görüntüleme ve silme | FR | **Should Have** | Veri kalıcılığı ve canlı demo B planı (hazır oturumlar) için kritiktir. |
| **NFR-01..05** | Performans, kullanılabilirlik, hata toleransı (`DEMO_MODE`), taşınabilirlik ve gizlilik | NFR | **Must Have** | Dersin hata yönetimi, test ve yerel çalıştırma şartlarını sağlar. |
| **EXT-01** | Toplu `.pdf`/`.docx` yükleme veya sesli girdi işleme | Kapsam Dışı | **Could Have** | Gelecek sürüm iyileştirmesi olarak planlanabilir, MVP için gerekli değildir. |
| **EXT-02** | Canlı Jira/Trello API yazma entegrasyonu ve çoklu kullanıcı RBAC | Kapsam Dışı | **Won't Have** | 20 günlük proje takvimi ve tek kullanıcılı yerel kapsam dışındadır. |

---

## 2.5 Gereksinim İzlenebilirlik Matrisi (Traceability Matrix)

| Gereksinim | Kullanıcı Hikâyesi | Planlanan API Uç Noktası | İlişkili Veritabanı Tabloları | Doğrulama Yöntemi (`pytest`) |
| :--- | :--- | :--- | :--- | :--- |
| **FR-01** | US-01 | `POST /api/analyze` | `AnalysisSession`, `Requirement`, `UserStory`, `AcceptanceCriterion` | Mock-LLM entegrasyon testi + 422/503 hata testi |
| **FR-02** | US-02 | `POST /api/analyze` | `Requirement` (`moscow_priority`, `ambiguity_warning`) | Pydantic şema ve mock-LLM yanıt doğrulaması |
| **FR-03** | US-03 | `PUT /api/sessions/{id}` | `Requirement`, `UserStory`, `AcceptanceCriterion` | Entegrasyon testi (güncelleme ve kalıcılık) |
| **FR-04** | US-04 | `GET /api/sessions/{id}/export` | `AnalysisSession` ve tüm ilişkili alt tablolar | Dışa aktarma motoru birim testleri (MD/CSV/JSON) |
| **FR-05** | US-05 | `GET /api/sessions`, `GET/DELETE /api/sessions/{id}` | `AnalysisSession` (cascade delete) | Listeleme, silme ve `404` hata senaryosu testi |
