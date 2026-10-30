from app.ml.preprocess import clean_text


def test_notebook_example():
    out = clean_text(
        "I've been to São Paulo, and it isn't the kind of city you'd forget — "
        "it's full of life, color, and chaos! 😊✨"
    )
    assert out == (
        "i have been to sao paulo and it is not the kind of city you would forget "
        "it is full of life color and chaos"
    )


def test_numbers_and_currency():
    assert clean_text("Man wins $1,500 and 50% off") == "man win 1500 dollar and 50 percent off"


def test_special_abbreviations():
    assert "unitedstates" in clean_text("U.S. senate passes bill")


def test_us_and_has_not_mangled():
    assert clean_text("give us what he has").split()[-1] == "has"
    assert "us" in clean_text("give us a break").split()


def test_empty_after_cleaning():
    assert clean_text("😊✨") == ""
