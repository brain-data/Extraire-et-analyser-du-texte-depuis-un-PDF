import time
# Capture the start time immediately
start_time = time.perf_counter()

import os
import re
import cProfile
from pdfminer.high_level import extract_pages  # type: ignore
from pdfminer.layout import LTTextContainer, LAParams  # type: ignore

# ---------------------------
# PDF Extraction and Text Cleaning
# ---------------------------
def raw_extract_from_pdf(pdf_path):
    """
    Extract raw text from a PDF by concatenating all text blocks.
    Iterates over each page and collects text from LTTextContainer elements.
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"The file '{pdf_path}' was not found. Check the path.")

    laparams = LAParams(
        all_texts=True,
        detect_vertical=False,
        word_margin=0.1,
        char_margin=1.0,
        line_margin=0.5,
        boxes_flow=0.5
    )

    full_text = []
    for page_layout in extract_pages(pdf_path, laparams=laparams):
        page_str = []
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                page_str.append(element.get_text())
        page_text = " ".join(page_str)
        if page_text.strip():
            full_text.append(page_text.strip())
    return "\n".join(full_text)

def final_clean_text(text):
    """
    Cleans the extracted text by:
      1) Removing blocks starting with 'Figure X:' that include 'Placeholder'
      2) Removing lines that contain only digits (page numbers)
      3) Removing isolated page numbers between newlines
      4) Replacing multiple spaces with a single space
    """
    text = re.sub(r"Figure\s*\d+:\s*.*?Placeholder.*?\d*", "", text)
    text = re.sub(r"(?m)^\s*\d+\s*$", "", text)
    text = re.sub(r"(?<=\n)\d+(?=\n)", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ---------------------------
# Occurrence Counting Functions
# ---------------------------
PUNCT_REGEX = re.compile(r"[,!?;:()\"]")
_pattern_cache = {}

def build_pattern(word: str) -> re.Pattern:
    """
    Builds a regex pattern for the given word.
    For complex words (with spaces, apostrophes, or longer than 5 characters),
    it ensures the word is matched as a whole.
    For short words, it avoids matching them as substrings.
    The compiled pattern is cached for reuse.
    """
    word_lower = word.lower().strip("'\"")
    if word_lower in _pattern_cache:
        return _pattern_cache[word_lower]
    if " " in word_lower or "'" in word_lower or len(word_lower) > 5:
        pat_str = rf"(?<![a-z0-9]){re.escape(word_lower)}(?![a-z0-9])"
    else:
        pat_str = rf"(?<![a-z0-9'])(?:{re.escape(word_lower)})(?:['\"_]{{2,}})?(?![a-z0-9'])"
    pattern = re.compile(pat_str)
    _pattern_cache[word_lower] = pattern
    return pattern

def count_occurrences_with_pattern(word_pattern: re.Pattern, text: str) -> int:
    """
    Counts the occurrences of a compiled regex pattern in the text.
    The text is converted to lowercase and punctuation is replaced with spaces.
    """
    text_lower = text.lower()
    text_lower = PUNCT_REGEX.sub(" ", text_lower)
    matches = word_pattern.findall(text_lower)
    return len(matches)

def count_occurrences_in_text(word: str, text: str) -> int:
    """
    Convenience function: builds the pattern for the given word and returns its occurrence count.
    """
    word_pattern = build_pattern(word)
    return count_occurrences_with_pattern(word_pattern, text)

# ---------------------------
# Unit Tests
# ---------------------------
def test_large_text():
    """
    Runs tests to verify the occurrence counting functions work correctly.
    """
    text = """Georges is my name and I like python. Oh ! your name is georges? And you like Python!
    Yes is is true, I like PYTHON
    and my name is GEORGES"""
    assert 3 == count_occurrences_in_text("Georges", text)
    assert 3 == count_occurrences_in_text("GEORGES", text)
    assert 3 == count_occurrences_in_text("georges", text)
    assert 0 == count_occurrences_in_text("george", text)
    assert 3 == count_occurrences_in_text("python", text)
    assert 3 == count_occurrences_in_text("PYTHON", text)
    assert 2 == count_occurrences_in_text("I", text)
    assert 0 == count_occurrences_in_text("n", text)
    assert 1 == count_occurrences_in_text("true", text)
    # Ensure that "maley" is not matched within "O'maley"
    assert 0 == count_occurrences_in_text("maley", "John O'maley is my friend")

    text = """The quick brown fox jump over the lazy dog.The quick brown fox jump over the lazy dog.""" * 500
    text += """The quick brown fox jump over the lazy dog.The quick brown Georges jump over the lazy dog."""
    text += """esrf sqfdg sfdglkj sdflgh sdflgjdsqrgl """ * 4000
    text += """The quick brown fox jump over the lazy dog.The quick brown fox jump over the lazy python."""
    text += """The quick brown fox jump over the lazy dog.The quick brown fox jump over the lazy dog.""" * 500
    text += """The quick brown fox jump over the lazy dog.The quick brown Georges jump over the lazy dog."""
    text += """esrf sqfdg sfdglkj sdflgh sdflgjdsqrgl """ * 4000
    text += """The quick brown fox jump over the lazy dog.The quick brown fox jump over the lazy python."""
    text += """The quick brown fox jump over the lazy dog.The quick brown fox jump over the lazy dog.""" * 500
    text += """The quick brown fox jump over the lazy dog.The quick brown Georges jump over the lazy dog."""
    text += """esrf sqfdg sfdglkj sdflgh sdflgjdsqrgl """ * 4000
    text += """The quick brown fox jump over the lazy dog.The quick brown fox jump over the lazy python."""
    text += """The quick brown fox jump over the true lazy dog.The quick brown fox jump over the lazy dog."""
    text += """The quick brown fox jump over the lazy dog.The quick brown fox jump over the lazy dog.""" * 500
    text += """ I vsfgsdfg sfdg sdfg sdgh sgh I sfdgsdf"""
    text += """The quick brown fox jump over the lazy dog.The quick brown fox jump over the lazy dog.""" * 500

    assert 3 == count_occurrences_in_text("Georges", text)
    assert 3 == count_occurrences_in_text("GEORGES", text)
    assert 3 == count_occurrences_in_text("georges", text)
    assert 0 == count_occurrences_in_text("george", text)
    assert 3 == count_occurrences_in_text("python", text)
    assert 3 == count_occurrences_in_text("PYTHON", text)
    assert 2 == count_occurrences_in_text("I", text)
    assert 0 == count_occurrences_in_text("n", text)
    assert 1 == count_occurrences_in_text("true", text)
    assert 1 == count_occurrences_in_text(
        "'reflexion mirror'", "I am a senior citizen and I live in the Fun-Plex 'Reflexion Mirror' in Sopchoppy, Florida"
    )
    assert 1 == count_occurrences_in_text(
        "reflexion mirror", "I am a senior citizen and I live in the Fun-Plex (Reflexion Mirror) in Sopchoppy, Florida"
    )
    assert 1 == count_occurrences_in_text("reflexion mirror", "Reflexion Mirror\" in Sopchoppy, Florida")
    assert 1 == count_occurrences_in_text(
        "reflexion mirror", "I am a senior citizen and I live in the Fun-Plex «Reflexion Mirror» in Sopchoppy, Florida"
    )
    assert 1 == count_occurrences_in_text(
        "reflexion mirror",
        "I am a senior citizen and I live in the Fun-Plex \u201cReflexion Mirror\u201d in Sopchoppy, Florida"
    )
    assert 1 == count_occurrences_in_text(
        "legitimate", "who is approved by OILS is completely legitimate: their employees are of legal working age"
    )
    assert 0 == count_occurrences_in_text(
        "legitimate their", "who is approved by OILS is completely legitimate: their employees are of legal working age"
    )
    assert 1 == count_occurrences_in_text(
        "get back to me", "I hope you will consider this proposal, and get back to me as soon as possible"
    )
    assert 1 == count_occurrences_in_text(
        "skin-care", "enable Delavigne and its subsidiaries to create a skin-care monopoly"
    )
    assert 1 == count_occurrences_in_text(
        "skin-care monopoly", "enable Delavigne and its subsidiaries to create a skin-care monopoly"
    )
    assert 0 == count_occurrences_in_text(
        "skin-care monopoly in the US", "enable Delavigne and its subsidiaries to create a skin-care monopoly"
    )
    assert 1 == count_occurrences_in_text("get back to me", "When you know:get back to me")
    assert 1 == count_occurrences_in_text(
        "don't be left", """emergency alarm warning.
Don't be left unprotected. Order your SSSS3000 today!"""
    )
    assert 1 == count_occurrences_in_text(
        "don", """emergency alarm warning.
Don't be left unprotected. Order your don SSSS3000 today!"""
    )
    assert 1 == count_occurrences_in_text("take that as a 'yes'", "Do I have to take that as a 'yes'?")
    assert 1 == count_occurrences_in_text("don't take that as a 'yes'", "I don't take that as a 'yes'?")
    assert 1 == count_occurrences_in_text("take that as a 'yes'", "I don't take that as a 'yes'?")
    assert 1 == count_occurrences_in_text("don't", "I don't take that as a 'yes'?")
    assert 1 == count_occurrences_in_text("attaching my c.v. to this e-mail", "I am attaching my c.v. to this e-mail.")
    assert 1 == count_occurrences_in_text("Linguist", "'''Linguist Specialist Found Dead on Laboratory Floor'''")
    assert 1 == count_occurrences_in_text(
        "Linguist Specialist", "'''Linguist Specialist Found Dead on Laboratory Floor'''"
    )
    assert 1 == count_occurrences_in_text(
        "Laboratory Floor", "'''Linguist Specialist Found Dead on Laboratory Floor'''"
    )
    assert 1 == count_occurrences_in_text("Floor", "'''Linguist Specialist Found Dead on Laboratory Floor'''")
    assert 1 == count_occurrences_in_text("Floor", "''Linguist Specialist Found Dead on Laboratory Floor''")
    assert 1 == count_occurrences_in_text("Floor", "__Linguist Specialist Found Dead on Laboratory Floor__")
    assert 1 == count_occurrences_in_text("Floor", "'''''Linguist Specialist Found Dead on Laboratory Floor'''''")
    assert 1 == count_occurrences_in_text("Linguist", "'''Linguist Specialist Found Dead on Laboratory Floor'''")
    assert 1 == count_occurrences_in_text("Linguist", "''Linguist Specialist Found Dead on Laboratory Floor''")
    assert 1 == count_occurrences_in_text("Linguist", "__Linguist Specialist Found Dead on Laboratory Floor__")
    assert 1 == count_occurrences_in_text("Linguist", "'''''Linguist Specialist Found Dead on Laboratory Floor'''''")


# ---------------------------
# Profiling Test
# ---------------------------
def doit():
    # SAMPLE_TEXT_FOR_BENCH is defined at module level when the script is imported.
    i = 0
    for _ in range(400):
        i += count_occurrences_in_text("word", SAMPLE_TEXT_FOR_BENCH)
        i += count_occurrences_in_text("suggestion", SAMPLE_TEXT_FOR_BENCH)
        i += count_occurrences_in_text("help", SAMPLE_TEXT_FOR_BENCH)
        i += count_occurrences_in_text("heavily", SAMPLE_TEXT_FOR_BENCH)
        i += count_occurrences_in_text("witfull", SAMPLE_TEXT_FOR_BENCH)
        i += count_occurrences_in_text("dog", SAMPLE_TEXT_FOR_BENCH)
        i += count_occurrences_in_text("almost", SAMPLE_TEXT_FOR_BENCH)
        i += count_occurrences_in_text("insulin", SAMPLE_TEXT_FOR_BENCH)
        i += count_occurrences_in_text("attaching", SAMPLE_TEXT_FOR_BENCH)
        i += count_occurrences_in_text("asma", SAMPLE_TEXT_FOR_BENCH)
        i += count_occurrences_in_text("neither", SAMPLE_TEXT_FOR_BENCH)
        i += count_occurrences_in_text("green", SAMPLE_TEXT_FOR_BENCH)
        i += count_occurrences_in_text("parabole", SAMPLE_TEXT_FOR_BENCH)
    return i

def test_profile():
    with cProfile.Profile() as pr:
        assert doit() == 2000
        pr.print_stats()

# ---------------------------
# Main Execution Block
# ---------------------------
if __name__ == "__main__":
    # Prompt the user for the PDF file path
    user_path = input("Please enter the path to your PDF file: ").strip()
    if os.path.isfile(user_path):
        PDF_PATH = user_path
        extracted_raw = raw_extract_from_pdf(PDF_PATH)
        SAMPLE_TEXT_FOR_BENCH = final_clean_text(extracted_raw)
    else:
        print("File not found. Exiting.")
        exit(1)

    test_profile()
    test_large_text()
    print("All good for your partial tests!")
    end_time = time.perf_counter()
    print(f"Total execution time: {end_time - start_time:.6f} seconds")
