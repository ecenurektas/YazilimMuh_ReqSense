"""DEMO_MODE=true için çevrimdışı gereksinim analizi fallback motoru."""

import re

from app.schemas.analysis import (
    LLMAcceptanceCriterion,
    LLMAnalysisOutput,
    LLMRequirement,
    LLMUserStory,
)

AMBIGUOUS_PHRASE_HINTS: dict[str, str] = {
    "hızlı": (
        "Muğlak ifade tespit edildi ('hızlı'): Yanıt süresi için ölçülebilir hedef "
        "(ör. isteklerin %95'i 500 ms altında) tanımlanmalıdır."
    ),
    "kullanıcı dostu": (
        "Muğlak ifade tespit edildi ('kullanıcı dostu'): Kullanılabilirlik için somut ölçüt "
        "(ör. ilk kez kullanan birinin en fazla 3 adımda işlemi tamamlaması) eklenmelidir."
    ),
    "güvenli": (
        "Muğlak ifade tespit edildi ('güvenli'): Güvenlik beklentisi somutlaştırılmalıdır "
        "(ör. TLS 1.3 şifreleme, rol tabanlı erişim ve şifre karma standardı)."
    ),
    "modern": (
        "Muğlak ifade tespit edildi ('modern'): Arayüz tasarım kriterleri WCAG erişilebilirlik "
        "düzeyi ve duyarlı (responsive) kırılım noktalarıyla netleştirilmelidir."
    ),
    "kolay": (
        "Muğlak ifade tespit edildi ('kolay'): İşlem adımı sayısı veya maksimum tamamlanma "
        "süresi gibi doğrulanabilir bir ölçüt belirtilmelidir."
    ),
    "esnek": (
        "Muğlak ifade tespit edildi ('esnek'): Desteklenecek yapılandırma, eklenti veya "
        "veri formatı sınırları açıkça listelenmelidir."
    ),
    "ölçeklenebilir": (
        "Muğlak ifade tespit edildi ('ölçeklenebilir'): Eşzamanlı kullanıcı ve saniye başına "
        "işlem (RPS) hedefleri sayısal olarak verilmelidir."
    ),
    "gerektiğinde": (
        "Muğlak ifade tespit edildi ('gerektiğinde'): İşlemin hangi koşul, rol veya olayla "
        "tetikleneceği kesin olarak tanımlanmalıdır."
    ),
    "yeterince": (
        "Muğlak ifade tespit edildi ('yeterince'): Öznel yeterlilik ifadesi yerine alt/üst "
        "sınır değerleri (SLA/SLO) belirlenmelidir."
    ),
    "fast": (
        "Muğlak ifade tespit edildi ('fast'): Maksimum gecikme süresi (ör. p95 <= 500 ms) "
        "sayısal olarak belirtilmelidir."
    ),
    "user-friendly": (
        "Muğlak ifade tespit edildi ('user-friendly'): Görev tamamlama süresi veya adım sayısı "
        "gibi ölçülebilir UX kriterleri tanımlanmalıdır."
    ),
    "secure": (
        "Muğlak ifade tespit edildi ('secure'): Kimlik doğrulama, yetkilendirme ve şifreleme "
        "standartları açıkça belirtilmelidir."
    ),
    "easy": (
        "Muğlak ifade tespit edildi ('easy'): Kullanım kolaylığı hedefi somut etkileşim "
        "kriterlerine dönüştürülmelidir."
    ),
}

_DEFAULT_PERFORMANCE_AMBIGUITY = (
    "Performans ve yanıt süresi beklentileri için somut eşik değer (ör. normal yükte "
    "en fazla 500 ms yanıt süresi) doğrulanmalıdır."
)
_DEFAULT_UX_AMBIGUITY = (
    "Arayüz ve kullanılabilirlik beklentileri için ölçülebilir kabul ölçütleri "
    "(ör. adım sayısı ve erişilebilirlik seviyesi) netleştirilmelidir."
)


def detect_ambiguities(raw_input: str) -> list[tuple[str, str]]:
    """Ham metindeki ölçülebilir olmayan muğlak ifadeleri ve önerileri döndürür."""
    normalized = raw_input.casefold()
    matches: list[tuple[str, str]] = []
    for phrase, hint in AMBIGUOUS_PHRASE_HINTS.items():
        if re.search(rf"(?<!\w){re.escape(phrase)}", normalized):
            matches.append((phrase, hint))
    return matches


def _derive_project_title(raw_input: str, title: str | None) -> str:
    """Kullanıcı başlık vermediyse ham metinden kısa ve okunabilir bir proje başlığı türetir."""
    if title and title.strip():
        return title.strip()[:255]

    first_line = next((line.strip() for line in raw_input.splitlines() if line.strip()), "")
    cleaned = re.sub(r"\s+", " ", first_line).strip(" .,:;-")
    if not cleaned:
        return "Demo Gereksinim Analizi Projesi"

    words = cleaned.split()
    snippet = " ".join(words[:6])
    if len(words) > 6:
        snippet = f"{snippet}..."
    return snippet[:255]


def _pick_warning(
    detected: list[tuple[str, str]],
    preferred_phrases: set[str],
    fallback: str | None = None,
) -> str | None:
    """Tespit edilen uyarılar arasından kategoriye en uygun olanını seçer."""
    matching_hints = [hint for phrase, hint in detected if phrase in preferred_phrases]
    if matching_hints:
        return " ".join(matching_hints)
    return fallback


def generate_demo_analysis(raw_input: str, title: str | None = None) -> LLMAnalysisOutput:
    """Harici LLM çağrısı olmadan gerçekçi, şemaya %100 uyumlu demo analiz çıktısı üretir."""
    project_title = _derive_project_title(raw_input, title)
    detected = detect_ambiguities(raw_input)

    perf_warning = _pick_warning(
        detected,
        {"hızlı", "fast", "ölçeklenebilir", "yeterince"},
        fallback=_DEFAULT_PERFORMANCE_AMBIGUITY if not detected else None,
    )
    ux_warning = _pick_warning(
        detected,
        {"kullanıcı dostu", "user-friendly", "modern", "kolay", "easy"},
        fallback=_DEFAULT_UX_AMBIGUITY if not detected else None,
    )
    security_warning = _pick_warning(
        detected,
        {"güvenli", "secure", "esnek", "gerektiğinde"},
    )

    requirements = [
        LLMRequirement(
            code="FR-01",
            req_type="functional",
            category="Veri Girişi ve Doğrulama",
            title="Yapılandırılmış Talep ve İşlem Kaydı",
            description=(
                "Sistem, kullanıcının girdiği temel alanları doğrulamalı ve geçerli kayıtları "
                "kalıcı veri deposunda saklamalıdır."
            ),
            moscow_priority="Must",
            ambiguity_warning=None,
        ),
        LLMRequirement(
            code="FR-02",
            req_type="functional",
            category="Yetkilendirme ve Güvenlik",
            title="Kimlik Doğrulama ve Rol Tabanlı Erişim",
            description=(
                "Sistem, oturum açan kullanıcıların rolüne göre görüntüleme ve düzenleme "
                "yetkilerini denetlemelidir."
            ),
            moscow_priority="Must",
            ambiguity_warning=security_warning,
        ),
        LLMRequirement(
            code="FR-03",
            req_type="functional",
            category="Raporlama ve Dışa Aktarma",
            title="Filtrelenebilir Liste ve Dışa Aktarma",
            description=(
                "Kullanıcılar kayıtlı öğeleri durum veya önceliğe göre filtreleyebilmeli ve "
                "standart dosya formatlarında dışa aktarabilmelidir."
            ),
            moscow_priority="Should",
            ambiguity_warning=None,
        ),
        LLMRequirement(
            code="FR-04",
            req_type="functional",
            category="Bildirim ve Entegrasyon",
            title="Otomatik Özet Bildirimi ve Harici Senkronizasyon",
            description=(
                "Önemli durum değişikliklerinde ilgili paydaşlara özet bilgilendirme iletilmeli "
                "ve isteğe bağlı dış sistem aktarımları desteklenmelidir."
            ),
            moscow_priority="Could",
            ambiguity_warning=None,
        ),
        LLMRequirement(
            code="NFR-01",
            req_type="non_functional",
            category="Performans",
            title="Yanıt Süresi ve İşlem Kapasitesi",
            description=(
                "Standart sorgu ve kayıt güncelleme işlemleri normal çalışma yükü altında "
                "500 ms içinde yanıt vermelidir."
            ),
            moscow_priority="Must",
            ambiguity_warning=perf_warning,
        ),
        LLMRequirement(
            code="NFR-02",
            req_type="non_functional",
            category="Kullanılabilirlik",
            title="Sezgisel Arayüz ve Çoklu Cihaz Desteği",
            description=(
                "Ana iş akışı ilk kez kullanan bir kullanıcı tarafından en fazla 3 adımda "
                "tamamlanabilmeli ve arayüz net Türkçe geri bildirimler sunmalıdır."
            ),
            moscow_priority="Wont",
            ambiguity_warning=ux_warning,
        ),
    ]

    user_stories = [
        LLMUserStory(
            code="US-01",
            related_requirement_code="FR-01",
            role="Son Kullanıcı",
            goal="sisteme geçerli talep bilgilerini girip kaydedebilmek",
            benefit="tüm süreç verilerini tek merkezden eksiksiz takip edebilirim",
            acceptance_criteria=[
                LLMAcceptanceCriterion(
                    code="AC-01.1",
                    given_clause="Kullanıcı veri giriş formundadır ve zorunlu alanları doldurmuştur",
                    when_clause="Kaydet butonuna tıklandığında",
                    then_clause="Kayıt veritabanına kaydedilir ve kullanıcıya başarı bildirimi gösterilir",
                ),
                LLMAcceptanceCriterion(
                    code="AC-01.2",
                    given_clause="Zorunlu bir alan boş bırakılmıştır veya geçersiz format girilmiştir",
                    when_clause="Form gönderilmeye çalışıldığında",
                    then_clause="İşlem engellenir ve ilgili alan için açıklayıcı doğrulama uyarısı gösterilir",
                ),
            ],
        ),
        LLMUserStory(
            code="US-02",
            related_requirement_code="FR-02",
            role="Sistem Yöneticisi",
            goal="kullanıcı erişimlerini rol ve güvenlik politikalarına göre sınırlandırmak",
            benefit="yetkisiz veri erişimlerinin ve güvenlik ihlallerinin önüne geçebilirim",
            acceptance_criteria=[
                LLMAcceptanceCriterion(
                    code="AC-02.1",
                    given_clause="Kullanıcı geçerli kimlik bilgileriyle oturum açmıştır",
                    when_clause="Yetkili olduğu bir modüle erişmek istediğinde",
                    then_clause="Sistem talebi onaylar ve ilgili ekranı yükler",
                ),
                LLMAcceptanceCriterion(
                    code="AC-02.2",
                    given_clause="Yetkisiz veya oturumu kapalı bir kullanıcı korunan bir işleme erişmeye çalışır",
                    when_clause="İstek sunucuya ulaştığında",
                    then_clause="Erişim reddedilir ve güvenli hata mesajı döndürülür",
                ),
            ],
        ),
        LLMUserStory(
            code="US-03",
            related_requirement_code="FR-03",
            role="Proje Yöneticisi",
            goal="kayıtları önceliklendirip rapor formatında dışa aktarabilmek",
            benefit="paydaş değerlendirme ve planlama toplantılarını hızlandırabilirim",
            acceptance_criteria=[
                LLMAcceptanceCriterion(
                    code="AC-03.1",
                    given_clause="Sistemde en az bir analiz edilmiş kayıt bulunmaktadır",
                    when_clause="Kullanıcı dışa aktarma seçeneğini seçtiğinde",
                    then_clause="Seçilen formatta eksiksiz ve okunabilir bir çıktı dosyası oluşturulur",
                ),
            ],
        ),
    ]

    ambiguity_count = sum(1 for req in requirements if req.ambiguity_warning)
    summary = (
        f"'{project_title}' girdisi demo analiz motoru ile değerlendirildi; "
        f"4 fonksiyonel, 2 fonksiyonel olmayan gereksinim, 3 kullanıcı hikâyesi ve "
        f"{ambiguity_count} belirsizlik uyarısı üretildi."
    )

    return LLMAnalysisOutput(
        project_title=project_title,
        summary=summary,
        requirements=requirements,
        user_stories=user_stories,
    )
