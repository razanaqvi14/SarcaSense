// The five example headlines shown under the text box. They are fixed (the same for every visitor).
// Written for this demo, none copied from the training data, and each was checked against the
// deployed model: the satirical ones score >= 0.98 sarcastic, the straight-news ones <= 0.07.
// They are NOT a benchmark: the model is noticeably less reliable on plain wire-style news than on
// these (see docs/ml/VIVA_GUIDE.md).
export const SAMPLES = [
  "Nation's coworkers agree meeting could have been an email",
  "Lawmakers reach deal to avoid government shutdown",
  "Man who said he would be right back leaves party for fourth consecutive hour",
  "Governors call for federal help after hurricane damage",
  "Area man bravely announces he is going to bed early tonight",
];
