"""Unit tests for PDF prose-quality heuristics."""

from assertpy import assert_that

from rag.core.text_quality import is_prose_text

_PROSE = (
    "NewsAnalyticalToolkit is an online natural language processing platform "
    "to analyze news. The system extracts topics and sentiment from articles "
    "published by national outlets during special elections."
)

_FIGURE_JUNK = (
    "1.0 - 0.8 - 0.4 - ó 0.6 - 02 - 0.0 SadnessDisgustAngerFearJoy "
    '6h o*("< cyeoe5 ayo By ArticleBy Site .. . . óz- + OP co p '
    "ThPKPmbaWlly 530 abcO+ FlveThirlyEight cbsO ABC cnnO+ ces"
)

_LDA_CHROME = (
    "Intertopic Distance Map (via multidimensional scaling) Top-10 Most "
    "Relevant Terms for Topic 3 (7.6% of tokens) PC1 i Marginal topic "
    "distribution gianforte Jacob quis[ greg_gianforte special_election "
    "body_slammed misdemeanor_assault altercation reporter- 200400600 "
    "greg_gianforte_win special_election_day body_slammed_reporter"
)

_STUTTER = (
    "538 abc cbJ - cnn - fox O 1 0 A O titititititi `) 06 i ii ii o°' "
    "ci) 000 \\ o°o°'ti°titititi>ti°'lytiooooooodod°eeee m v 0 0.10 "
    "PositiveNegative coverage of news outlets across the plotted topic"
)

_DEDICATION = "To my love, Persia To my parents, who always suspected I’d end up here iii"

_UNICODE_FIG = (
    "0.0 0.2 0.4 0.6 0.8 1.0 False/uni00A0Positive/uni00A0Rate 0.0 0.2 "
    "0.4 0.6 0.8 1.0True/uni00A0Positive/uni00A0Rate ROC curve dump"
)


def test_is_prose_text__paper_abstract__true() -> None:
    assert_that(is_prose_text(text=_PROSE)).is_true()


def test_is_prose_text__emotion_chart__false() -> None:
    assert_that(is_prose_text(text=_FIGURE_JUNK)).is_false()


def test_is_prose_text__ldavis_chrome__false() -> None:
    assert_that(is_prose_text(text=_LDA_CHROME)).is_false()


def test_is_prose_text__stutter_glyphs__false() -> None:
    assert_that(is_prose_text(text=_STUTTER)).is_false()


def test_is_prose_text__dedication__false() -> None:
    assert_that(is_prose_text(text=_DEDICATION)).is_false()


def test_is_prose_text__unicode_figure__false() -> None:
    assert_that(is_prose_text(text=_UNICODE_FIG)).is_false()


def test_is_prose_text__few_real_words__false() -> None:
    text = "alpha beta gamma delta " + ("1 " * 80)
    assert_that(is_prose_text(text=text)).is_false()


def test_is_prose_text__symbol_salad_ratio__false() -> None:
    prose = (
        "This paper presents a method for detecting driver nodes in "
        "directed biological networks using controllability theory. "
    )
    salad = " ".join(["naïve°x"] * 20)
    assert_that(is_prose_text(text=prose + salad)).is_false()


def test_is_prose_text__sparse_single_letters__false() -> None:
    words = "neural network models trained using accuracy precision recall fscore values "
    singles = " ".join(["a"] * 25)
    assert_that(is_prose_text(text=words + singles)).is_false()
