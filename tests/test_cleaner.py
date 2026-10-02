from datetime import datetime

from data_ingestion.cleaner import clean_review_text, extract_review_metadata


def test_clean_review_text_edge_cases():
    # 1. Test filtering thresholds
    assert clean_review_text('good') is None
    assert clean_review_text(None) is None

    # 2. HTML tags must go, before any length check
    html_input = '<b>Great phone!</b> Battery life is absolutely amazing on this device.'
    assert clean_review_text(html_input) == 'Great phone! Battery life is absolutely amazing on this device.'


def test_extract_review_metadata_mappings():
    # Keep your test data scoped inside the test function
    sample_review = {
        'text': 'Battery life is terrible but the camera is absolutely stunning on this phone.',
        'rating': '4',
        'reviewer': 'Rahul',
        'date': '08 4, 2014',
        'verified': True
    }

    result = extract_review_metadata(sample_review)

    # Verify the structure and structural type transformations
    assert isinstance(result, dict)
    assert result['rating'] == 4.0                  # Verifies string -> float conversion
    assert result['reviewer_name'] == 'Rahul'
    assert isinstance(result['review_date'], datetime) # Verifies string -> datetime object
    assert result['verified_purchase'] is True


class TestQuestionMarksArePreservedInReviewText:
    """
    clean_review_text must leave '?' alone, at every run length.

    Measured against the real corpora:

      Amazon reviewText, 1,128,437 rows
        1 '?'  36,630     2 '?'     993     3 '?'    736
        4 '?'    162     5 '?'      61     6 '?'     17  ... up to 22
        Every one of the 1,013 runs of 3+ was verified by hand to be
        ordinary reviewer emphasis, and 100% were followed by whitespace or
        punctuation rather than '('.

      Dataset-SA Review + Summary, 205,052 rows
        Runs of 3+ appear in exactly 2 rows.

    So a run-length threshold would delete 1,013 legitimate emphasis marks
    from Amazon review text while repairing 2 rows. Net negative.

    The '??????' in Dataset-SA is in product_name, not review text:
        50,424 product_name rows carry it, versus 2 Review/Summary rows.
    Damaging there is a product-name concern and belongs in its own
    cleaner, where a noun phrase cannot legitimately contain '?'.
    """

    def test_single_question_mark_survives(self):
        raw = 'Is this worth the extra money for a phone?'
        assert clean_review_text(raw) == raw

    def test_question_mark_inside_sentence_survives(self):
        raw = 'Battery life? No. The camera is genuinely excellent overall.'
        assert clean_review_text(raw) == raw

    def test_leading_question_mark_survives(self):
        raw = '?Would this work with my existing desk setup here'
        assert clean_review_text(raw) == raw

    def test_double_question_mark_survives(self):
        raw = 'Does the build quality actually feel premium?? I doubt it.'
        assert clean_review_text(raw) == raw

    def test_emphasis_run_of_three_survives(self):
        """Real Amazon review: 'What's not to like???' — emphasis, not damage."""
        raw = "What's not to like??? I love the fit too, best I've tried."
        assert clean_review_text(raw) == raw

    def test_emphasis_run_of_five_survives(self):
        """Real Amazon review: 'ARE YOU KIDDING ME?????' — anger, not damage."""
        raw = "Look at other options. But for $2.50!!! ARE YOU KIDDING ME????? Terrible."
        assert clean_review_text(raw) == raw

    def test_long_emphasis_run_survives(self):
        """Real Amazon review with a 22-char run."""
        raw = "THIS CASE DOES NOT FIT THE GALAXY S4 AT ALL?????????????????????? Buy elsewhere."
        assert clean_review_text(raw) == raw

    def test_question_mark_survives_alongside_html_removal(self):
        """HTML is stripped; the '?' inside the sentence is not collateral."""
        raw = '<p>Is it worth $40?????</p><br/>Build quality is fine overall.'
        assert clean_review_text(raw) == 'Is it worth $40?????Build quality is fine overall.'


class TestLengthThresholdInteraction:
    def test_short_review_returns_none(self):
        assert clean_review_text('good') is None

    def test_exactly_at_threshold_is_kept(self):
        assert clean_review_text('x' * 20) == 'x' * 20

    def test_one_below_threshold_is_dropped(self):
        assert clean_review_text('x' * 19) is None