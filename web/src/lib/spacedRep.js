// SM-2 spaced repetition algorithm adapted for quiz items
// Each quiz item is identified by {lessonSlug, questionIndex}

// Initialize with default values if not present
function initItem(item) {
  if (!item.reps) item.reps = 0;
  if (!item.easiness) item.easiness = 2.5; // EF
  if (!item.interval) item.interval = 0; // days
  if (!item.nextReview) item.nextReview = Date.now(); // immediately
  return item;
}

function updateItem(item, quality) {
  // quality: 0..5 (but we only have binary correct/incorrect for now)
  // Map: correct -> 5, incorrect -> 1
  if (quality === undefined) {
    quality = item.lastResultCorrect ? 5 : 1;
  }
  item = initItem(item);
  if (quality >= 3) {
    // correct response
    if (item.reps === 0) {
      item.interval = 1;
    } else if (item.reps === 1) {
      item.interval = 6;
    } else {
      item.interval = Math.round(item.interval * item.easiness);
    }
    item.easiness += 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02);
    if (item.easiness < 1.3) item.easiness = 1.3;
  } else {
    // incorrect response
    item.interval = 1;
    item.easiness -= 0.2;
    if (item.easiness < 1.3) item.easiness = 1.3;
  }
  item.reps += 1;
  // next review in milliseconds
  item.nextReview = Date.now() + item.interval * 24 * 60 * 60 * 1000;
  item.lastReview = Date.now();
  return item;
}

// Get items due for review (nextReview <= now)
function getDueItems(log) {
  const now = Date.now();
  // Group by item key
  const items = {};
  log.forEach(entry => {
    if (entry.type !== 'attempt') return;
    const key = `${entry.lessonSlug}|${entry.questionIndex}`;
    if (!items[key]) {
      items[key] = {
        lessonSlug: entry.lessonSlug,
        questionIndex: entry.questionIndex,
        reps: 0,
        easiness: 2.5,
        interval: 0,
        nextReview: 0,
        lastReview: 0,
        lastResultCorrect: null
      };
    }
    const item = items[key];
    // Update based on this attempt (we'll process in order)
    // We'll rebuild from scratch each time for simplicity
  });
  // Instead of incremental, let's reprocess the entire log for each item
  // Simpler: for each item, simulate the sequence of attempts
  const itemAttempts = {};
  log.forEach(entry => {
    if (entry.type !== 'attempt') return;
    const key = `${entry.lessonSlug}|${entry.questionIndex}`;
    if (!itemAttempts[key]) itemAttempts[key] = [];
    itemAttempts[key].push(entry);
  });
  const due = [];
  for (const key in itemAttempts) {
    const attempts = itemAttempts[key];
    let item = {
      lessonSlug: attempts[0].lessonSlug,
      questionIndex: parseInt(attempts[0].questionIndex, 10),
      reps: 0,
      easiness: 2.5,
      interval: 0,
      nextReview: 0,
      lastReview: 0,
      lastResultCorrect: null
    };
    attempts.forEach(attempt => {
      item = updateItem(item, attempt.correct ? 5 : 1);
    });
    if (item.nextReview <= now) {
      due.push(item);
    }
  }
  return due;
}

// Get a random due item (or null)
function getRandomDueItem(log) {
  const due = getDueItems(log);
  if (due.length === 0) return null;
  return due[Math.floor(Math.random() * due.length)];
}

// Export for use in other modules
window.acfSpacedRep = {
  getDueItems,
  getRandomDueItem,
  updateItem,
  initItem
};