# 1. Proje Tanıtımı

## 1.1 Projenin Adı

**ReqSense — Yapay Zekâ Destekli Yazılım Gereksinim Analizi Sistemi**

ReqSense; yazılım geliştirme projelerinin başlangıç aşamasında paydaşlardan, müşteri taleplerinden veya mülakat notlarından elde edilen serbest biçimli doğal dil metinlerini işleyerek yapılandırılmış yazılım gereksinimlerine, kullanıcı hikâyelerine, kabul kriterlerine ve önceliklendirme çıktılarına dönüştüren web tabanlı bir gereksinim mühendisliği uygulamasıdır.

---

## 1.2 Problem Tanımı

Yazılım mühendisliği süreçlerinde gereksinim mühendisliği (Requirements Engineering), bir ürünün doğru tanımlanması ve geliştirme maliyetlerinin kontrol altında tutulması açısından en kritik aşamadır. ISO/IEC/IEEE 29148 standardının da vurguladığı üzere, bir yazılım gereksiniminin açık, doğrulanabilir, tutarlı ve izlenebilir olması gerekir. Ancak pratikte gereksinim toplama ve analiz süreçleri çoğunlukla şu temel sorunlarla karşılaşmaktadır:

1. **Yüksek Zaman ve İş Gücü Maliyeti:** İş analistleri ve geliştirme ekipleri; mülakat kayıtları, e-postalar veya kısa proje fikirleri gibi yapılandırılmamış metinleri manuel olarak okuyup fonksiyonel (FR) ve fonksiyonel olmayan (NFR) gereksinimlere ayırmak, kullanıcı hikâyeleri (User Stories) yazmak ve her hikâye için test edilebilir kabul kriterleri (Given-When-Then) üretmek için önemli ölçüde zaman harcamaktadır.
2. **Doğal Dildeki Belirsizlik ve Muğlaklık Riski:** Müşteri veya paydaş ifadelerinde sıklıkla *"sistem hızlı olsun"*, *"arayüz kullanıcı dostu görünsün"*, *"veriler güvenli saklansın"* veya *"gerektiğinde rapor alınabilsin"* gibi ölçülebilir olmayan, öznel ve muğlak ifadeler yer alır. Bu ifadeler erken aşamada tespit edilip somut ölçütlere dönüştürülmediğinde, geliştirici ile paydaş arasında yorum farklarına yol açar.
3. **Eksik Kabul Kriterleri ve Önceliklendirme Karmaşası:** Başlangıç dokümanlarında gereksinimlerin hangi öncelikle (örneğin MoSCoW yöntemiyle) ele alınacağı ve hangi koşullarda "tamamlandı" sayılacağı çoğu zaman belirtilmez. Bu durum kapsam kaymasına (scope creep) ve sprint planlama hatalarına neden olur.
4. **Hataların Geç Aşamada Fark Edilmesinin Maliyeti:** Gereksinim aşamasında yapılan bir eksiklik veya yanlış anlama; tasarım, kodlama ve test aşamalarına taşındıkça düzeltme maliyeti katlanarak artmakta, yeniden çalışma (rework) ve teslim gecikmelerine sebebiyet vermektedir.

---

## 1.3 Projenin Amacı

ReqSense projesinin temel amacı; doğal dil işleme (NLP) ve Büyük Dil Modelleri (LLM) yeteneklerini yapılandırılmış şema zorunluluğu (Structured Output) ile birleştirerek manuel gereksinim analizi sürecini hızlandırmak, standartlaştırmak ve kalite denetimini otomatikleştirmektir.

Bu doğrultuda sistemin hedefleri şunlardır:

- **Yapılandırılmış Gereksinim Üretimi:** Serbest metin halindeki proje fikirlerini veya paydaş notlarını analiz ederek otomatik olarak kodlanmış Fonksiyonel Gereksinimler (`FR-xx`) ve Fonksiyonel Olmayan Gereksinimler (`NFR-xx`) üretmek.
- **Belirsizlik (Ambiguity) Tespiti:** Girdideki ölçülebilir olmayan muğlak ifadeleri tespit ederek her ilgili gereksinim için açıklayıcı belirsizlik uyarıları (`ambiguity_warning`) oluşturmak ve analisti netleştirmeye yönlendirmek.
- **Otomatik MoSCoW Önceliklendirmesi:** Üretilen gereksinimleri `Must`, `Should`, `Could` ve `Wont` kategorilerine ayırarak kapsam yönetimini kolaylaştırmak.
- **Çevik (Agile) Çıktı Dönüşümü:** Gereksinimlerle ilişkili kullanıcı hikâyelerini (*Rol – Hedef – Fayda*) ve BDD (Behavior-Driven Development) uyumlu *Given – When – Then* kabul kriterlerini tek adımda üretmek.
- **İnsan Denetimi ve Taşınabilir Dışa Aktarım:** Yapay zekâ çıktısını nihai karar verici yerine bir taslak yardımcı olarak sunmak; kullanıcının arayüz üzerinden tüm maddeleri düzenleyebilmesini, veritabanında saklayabilmesini ve onaylanan çıktıyı **Markdown (.md)**, **CSV (.csv)** ve **JSON (.json)** formatlarında dışa aktarabilmesini sağlamak.

---

## 1.4 Hedef Kullanıcılar

ReqSense, gereksinim dokümantasyonu üreten hem profesyonel ekipler hem de akademik/eğitim ortamındaki kullanıcılar için tasarlanmıştır.

| Hedef Kullanıcı Grubu | Kullanım Senaryosu ve Beklenen Fayda |
| :--- | :--- |
| **İş Analistleri (Business Analysts)** | Paydaş görüşme notlarından hızlıca ilk SRS (Software Requirements Specification) taslağını oluşturmak, muğlak müşteri taleplerini erken aşamada yakalamak. |
| **Proje Yöneticileri ve Ürün Sahipleri (PM / PO)** | Proje kapsamını MoSCoW etiketleriyle önceliklendirmek, Jira/Trello gibi iş takip araçlarına CSV ile aktarılabilir User Story listeleri hazırlamak. |
| **Yazılım Geliştiriciler ve Test Mühendisleri** | Belirsizlikten arındırılmış gereksinimlere ve doğrudan test senaryosuna dönüştürülebilen *Given-When-Then* kabul kriterlerine erişmek. |
| **Yazılım Mühendisliği Öğrencileri** | Ders ve bitirme projelerinde gereksinim mühendisliği standartlarını (FR/NFR ayrımı, MoSCoW, izlenebilirlik) uygulamalı olarak deneyimlemek ve proje dokümanlarını tutarlı hale getirmek. |

---

## 1.5 Projenin Kapsamı

Projenin teslim takvimi ve ders gereksinimleri doğrultusunda kapsam içi ve kapsam dışı özellikler net biçimde ayrılmıştır.

### Kapsam İçi (In-Scope)

- **Web Tabanlı MVP Arayüzü:** React + Tailwind CSS ile geliştirilmiş gereksinim giriş formu, sekmeli analiz sonuç görünümü, satır içi düzenleme ve geçmiş oturum listesi.
- **NLP/LLM Analiz Çekirdeği:** Google Gemini API (`google-genai`) ve Pydantic tabanlı Structured Output şemaları ile tutarlı JSON ayrıştırma; çevrimdışı veya sunum güvenliği için `DEMO_MODE=true` yerel fallback mekanizması.
- **5 Çekirdek Fonksiyonel Modül:** Doğal dil analizi (`FR-01`), belirsizlik uyarısı ve MoSCoW etiketleme (`FR-02`), etkileşimli düzenleme/ekleme/silme (`FR-03`), Markdown/CSV/JSON dışa aktarma (`FR-04`) ve analiz geçmişi yönetimi (`FR-05`).
- **İlişkisel Veri Kalıcılığı:** SQLite + SQLAlchemy üzerinde `AnalysisSession`, `Requirement`, `UserStory` ve `AcceptanceCriterion` tabloları.
- **Hata Yönetimi ve Otomatik Doğrulama:** 400/422 girdi doğrulama, 502/503 LLM/şema hata yakalama, 404 kayıt bulunamadı yönetimi ve `pytest` + `httpx` ile birim/mock-LLM entegrasyon testleri.

### Kapsam Dışı (Out-of-Scope — Gelecek Geliştirmeler)

- Çoklu kullanıcı kayıt/giriş sistemi, rol tabanlı erişim kontrolü (RBAC) ve ekip içi gerçek zamanlı ortak düzenleme.
- Jira, Trello veya GitHub Issues API'lerine doğrudan tek tıkla uzaktan kayıt gönderme (bu sürümde Jira/Trello uyumlu `.csv` dışa aktarma ile karşılanmaktadır).
- Ses kaydı (speech-to-text), `.pdf` veya `.docx` dosyalarından toplu metin çıkarımı (bu sürümde doğrudan metin girişi desteklenmektedir).
- Bulut tabanlı çoklu kiracı (multi-tenant) ölçeklendirme ve harici PostgreSQL küme yönetimi.
