// Misafir oyuncular için görülen soruların tarayıcıda (localStorage) takibi

const STORAGE_KEY = 'tarihtoz_seen_questions';

export function getGuestSeenQuestions() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : {};
  } catch (e) {
    return {};
  }
}

export function setGuestSeenForTopic(topicKey, questionIds) {
  if (!topicKey) return;
  try {
    const current = getGuestSeenQuestions();
    if (!Array.isArray(questionIds) || questionIds.length === 0) {
      delete current[topicKey];
    } else {
      current[topicKey] = questionIds;
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(current));
  } catch (e) {
    // Ignore storage quota / privacy mode errors
  }
}
