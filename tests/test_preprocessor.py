from app.preprocessor import preprocess

def test_removes_html_tags():
    result = preprocess("<b>Hello</b> <p>world</p>")
    assert "<b>" not in result
    assert "Hello" in result

def test_collapses_spaces():
    result = preprocess("hello    world")
    assert "  " not in result

def test_collapses_newlines():
    result = preprocess("line1\n\n\n\n\nline2")
    assert "\n\n\n" not in result

def test_empty_string():
    assert preprocess("") == ""

def test_plain_text_unchanged():
    result = preprocess("Hello world this is a test.")
    assert "Hello world" in result