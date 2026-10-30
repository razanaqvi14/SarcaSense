"""Examples of what the cleaning pipeline does to text.
See docs/ml/VIVA_GUIDE.md, Appendix D for how to run it."""
from app.ml.preprocess import clean_text
for s in ["Trump's tariffs hit farmers", "The company's CEO resigned", "He's late again", "It's not what you think", "Man's best friend isn't a dog",
          "Man wins $1,500 and 50% off", "No means NO!!!", "WOW. Great job.", "Don't you dare"]:
    print(f"{s!r:45} -> {clean_text(s)!r}")
