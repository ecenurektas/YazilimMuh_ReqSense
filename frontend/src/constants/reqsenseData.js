export const MIN_INPUT_LENGTH = 20;
export const MAX_TITLE_LENGTH = 255;

export const MOSCOW_OPTIONS = [
  {
    value: "Must",
    label: "Must Have",
    shortLabel: "Must",
    badgeClass: "bg-rose-50 text-rose-700 ring-rose-200",
    selectClass: "border-rose-200 bg-rose-50/70 text-rose-800",
  },
  {
    value: "Should",
    label: "Should Have",
    shortLabel: "Should",
    badgeClass: "bg-amber-50 text-amber-800 ring-amber-200",
    selectClass: "border-amber-200 bg-amber-50/70 text-amber-900",
  },
  {
    value: "Could",
    label: "Could Have",
    shortLabel: "Could",
    badgeClass: "bg-sky-50 text-sky-700 ring-sky-200",
    selectClass: "border-sky-200 bg-sky-50/70 text-sky-800",
  },
  {
    value: "Wont",
    label: "Won't Have",
    shortLabel: "Won't",
    badgeClass: "bg-slate-100 text-slate-700 ring-slate-200",
    selectClass: "border-slate-200 bg-slate-100 text-slate-700",
  },
];

export const MOSCOW_MAP = Object.fromEntries(
  MOSCOW_OPTIONS.map((item) => [item.value, item])
);

export const REQ_TYPE_OPTIONS = [
  {
    value: "functional",
    label: "FR — Fonksiyonel",
    shortLabel: "FR",
    badgeClass: "bg-indigo-50 text-indigo-700 ring-indigo-200",
  },
  {
    value: "non_functional",
    label: "NFR — Fonksiyonel Olmayan",
    shortLabel: "NFR",
    badgeClass: "bg-violet-50 text-violet-700 ring-violet-200",
  },
];

export const REQ_TYPE_MAP = Object.fromEntries(
  REQ_TYPE_OPTIONS.map((item) => [item.value, item])
);

export const SAMPLE_SCENARIOS = [
  {
    id: "staj",
    label: "Üniversite Staj Takip Sistemi",
    title: "Üniversite Staj Başvuru ve Onay Portalı",
    rawInput:
      "Öğrenciler staj başvurularını çevrimiçi doldurabilmeli ve şirket kabul belgesini PDF olarak yükleyebilmelidir. Bölüm danışmanları başvuruları onaylayabilmeli veya eksiklik varsa öğrenciye geri bildirim gönderebilmelidir. Sistem çok hızlı çalışsın, arayüz kullanıcı dostu olsun ve öğrenci verileri güvenli saklansın. Dönem sonunda staj koordinatörü onaylanan başvuruları CSV veya Markdown olarak dışa aktarabilmelidir.",
  },
  {
    id: "kutuphane",
    label: "Kütüphane Çalışma Odası Rezervasyonu",
    title: "Akıllı Kütüphane Oda Rezervasyon Sistemi",
    rawInput:
      "Üniversite öğrencileri kampüs kütüphanesindeki bireysel ve grup çalışma odalarının doluluk durumunu canlı görebilmeli, uygun saat dilimini seçip en fazla 2 saatlik rezervasyon oluşturabilmelidir. Giriş yaparken öğrenci numarası doğrulanmalı ve rezervasyon saatinden 15 dakika önce hatırlatma gönderilmelidir. Mobil cihazlarda da kolay ve modern bir kullanım sunmalı, yoğun sınav haftalarında hızlı yanıt vermelidir.",
  },
  {
    id: "klinik",
    label: "Klinik Randevu ve Hasta Takibi",
    title: "Diş Kliniği Randevu Yönetim Uygulaması",
    rawInput:
      "Hastalar doktor uzmanlık alanına göre müsait randevu saatlerini listeleyebilmeli ve tek tıkla randevu oluşturabilmelidir. Sekreterler gerektiğinde randevuyu erteleyebilmeli veya iptal edebilmeli, hastalara otomatik bilgilendirme iletilmelidir. Hasta geçmişi ve muayene notları yalnızca yetkili hekimler tarafından görülebilmeli ve sistem yeterince güvenli olmalıdır.",
  },
];
