// Example headlines for the "Try one" list. They were written for this demo (none are copied from
// the training data) and each was checked against the deployed model before being added: satirical
// ones score >= 0.88 sarcastic, straight-news ones <= 0.18. They are NOT a benchmark: the model is
// noticeably less reliable on plain wire-style news than on these (see docs/ml/VIVA_GUIDE.md).

const SARCASTIC = [
  "Nation's coworkers agree meeting could have been an email",
  "Study finds majority of people who skip breakfast are skipping breakfast",
  "Man who said he would be right back leaves party for fourth consecutive hour",
  "Report: Office plant only employee to receive recognition this quarter",
  "Local dad unanimously elected to explain how the grill works",
  "Experts warn that weekend will end on schedule again this week",
  "Area man bravely announces he is going to bed early tonight",
  "Nation relieved to learn that someone else will fix the printer",
  "Man confident he can assemble furniture without reading instructions",
  "Study: Five minutes of exercise enough to justify entire day of rest",
  "Man who forgot password again calls it a learning experience",
  "Nation's grandmothers agree you look thin and should eat more",
  "Area couple finally agree on restaurant after two hours of discussion",
  "Report: Everyone in meeting waiting for someone else to speak first",
  "Local teen discovers three more hours of the afternoon online",
];

const NOT_SARCASTIC = [
  "Democrats unveil plan to lower prescription drug costs",
  "Governors call for federal help after hurricane damage",
  "Teachers union backs proposal to raise education funding",
  "Lawmakers debate new rules for social media companies",
  "Climate activists rally outside state capitol",
  "Federal judge halts rule on immigration detention",
  "Mayor proposes affordable housing plan for downtown",
  "Advocates urge Congress to expand mental health funding",
  "Poll shows voters divided over healthcare proposal",
  "Lawmakers reach deal to avoid government shutdown",
  "World leaders pledge new climate commitments at summit",
  "Lawmakers split over how to tackle student debt",
  "Women make historic gains in state legislatures",
  "Storm brings heavy rain and flooding to coastal towns",
  "Union and management reach agreement after weeks of talks",
];

function shuffled(list) {
  const a = [...list];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// `count` random headlines, always a mix of both kinds (2 + 3 or 3 + 2), in random order.
export function pickSamples(count = 5) {
  const sarcasticCount = Math.random() < 0.5 ? Math.floor(count / 2) : Math.ceil(count / 2);
  return shuffled([
    ...shuffled(SARCASTIC).slice(0, sarcasticCount),
    ...shuffled(NOT_SARCASTIC).slice(0, count - sarcasticCount),
  ]);
}
