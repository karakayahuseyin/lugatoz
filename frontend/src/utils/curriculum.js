// Tarihöz müfredat yapısı: Sınıflar, Temalar ve Dünyanın Enleri

const COMMON_THEMES_5_6_7 = [
  { id: 'birlikte_yasamak', order: 1, name: 'Birlikte Yaşamak', full_name: '1. Birlikte Yaşamak', active_questions: 0, total_questions: 0 },
  { id: 'evimiz_dunya', order: 2, name: 'Evimiz Dünya', full_name: '2. Evimiz Dünya', active_questions: 0, total_questions: 0 },
  { id: 'ortak_mirasimiz', order: 3, name: 'Ortak Mirasımız', full_name: '3. Ortak Mirasımız', active_questions: 0, total_questions: 0 },
  { id: 'yasayan_demokrasimiz', order: 4, name: 'Yaşayan Demokrasimiz', full_name: '4. Yaşayan Demokrasimiz', active_questions: 0, total_questions: 0 },
  { id: 'hayatimizdaki_ekonomi', order: 5, name: 'Hayatımızdaki Ekonomi', full_name: '5. Hayatımızdaki Ekonomi', active_questions: 0, total_questions: 0 },
  { id: 'teknoloji_ve_sosyal_bilimler', order: 6, name: 'Teknoloji ve Sosyal Bilimler', full_name: '6. Teknoloji ve Sosyal Bilimler', active_questions: 0, total_questions: 0 },
];

const THEMES_8 = [
  { id: 'bir_kahraman_doguyor', order: 1, name: 'Bir Kahraman Doğuyor', full_name: '1. Bir Kahraman Doğuyor', active_questions: 0, total_questions: 0 },
  { id: 'milli_uyanis', order: 2, name: 'Millî Uyanış: Bağımsızlık Yolunda Atılan Adımlar', full_name: '2. Millî Uyanış: Bağımsızlık Yolunda Atılan Adımlar', active_questions: 0, total_questions: 0 },
  { id: 'milli_bir_destan', order: 3, name: 'Millî Bir Destan: Ya İstiklal Ya Ölüm!', full_name: '3. Millî Bir Destan: Ya İstiklal Ya Ölüm!', active_questions: 0, total_questions: 0 },
  { id: 'ataturkculuk_ve_cagdaslasan_turkiye', order: 4, name: 'Atatürkçülük ve Çağdaşlaşan Türkiye', full_name: '4. Atatürkçülük ve Çağdaşlaşan Türkiye', active_questions: 0, total_questions: 0 },
  { id: 'demokratiklesme_cabalari', order: 5, name: 'Demokratikleşme Çabaları', full_name: '5. Demokratikleşme Çabaları', active_questions: 0, total_questions: 0 },
  { id: 'ataturk_donemi_turk_dis_politikasi', order: 6, name: 'Atatürk Dönemi Türk Dış Politikası', full_name: '6. Atatürk Dönemi Türk Dış Politikası', active_questions: 0, total_questions: 0 },
  { id: 'ataturkun_olumu_ve_sonrasi', order: 7, name: "Atatürk'ün Ölümü ve Sonrası", full_name: "7. Atatürk'ün Ölümü ve Sonrası", active_questions: 0, total_questions: 0 },
];

export const DEFAULT_CURRICULUM = [
  {
    id: '5',
    name: '5. Sınıf',
    short_name: '5. Sınıf',
    has_themes: true,
    active_questions: 0,
    total_questions: 0,
    themes: COMMON_THEMES_5_6_7.map((t) => ({ ...t })),
  },
  {
    id: '6',
    name: '6. Sınıf',
    short_name: '6. Sınıf',
    has_themes: true,
    active_questions: 0,
    total_questions: 0,
    themes: COMMON_THEMES_5_6_7.map((t) => ({ ...t })),
  },
  {
    id: '7',
    name: '7. Sınıf',
    short_name: '7. Sınıf',
    has_themes: true,
    active_questions: 0,
    total_questions: 0,
    themes: COMMON_THEMES_5_6_7.map((t) => ({ ...t })),
  },
  {
    id: '8',
    name: '8. Sınıf',
    short_name: '8. Sınıf',
    has_themes: true,
    active_questions: 0,
    total_questions: 0,
    themes: THEMES_8.map((t) => ({ ...t })),
  },
  {
    id: 'dunyanin_enleri',
    name: 'Dünyanın Enleri',
    short_name: 'Dünyanın Enleri',
    has_themes: false,
    active_questions: 0,
    total_questions: 0,
    themes: [],
  },
];

export async function fetchCurriculum() {
  try {
    const response = await fetch('/api/curriculum');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return {
      sections: data.sections || DEFAULT_CURRICULUM,
      uncategorized_questions: data.uncategorized_questions || 0,
    };
  } catch (error) {
    console.error('Müfredat yüklenemedi:', error);
    return {
      sections: DEFAULT_CURRICULUM,
      uncategorized_questions: 0,
    };
  }
}

export function getSectionById(sections, gradeId) {
  const list = sections && sections.length ? sections : DEFAULT_CURRICULUM;
  return list.find((s) => s.id === gradeId) || null;
}

export function getThemeById(sections, gradeId, themeId) {
  const section = getSectionById(sections, gradeId);
  if (!section || !section.has_themes || !themeId) return null;
  return section.themes.find((t) => t.id === themeId) || null;
}

export function formatTopicLabel(sections, gradeId, themeId) {
  const section = getSectionById(sections, gradeId);
  if (!section) return '';
  if (!section.has_themes) return section.name;
  const theme = getThemeById(sections, gradeId, themeId);
  return theme ? `${section.name} • ${theme.full_name}` : section.name;
}
