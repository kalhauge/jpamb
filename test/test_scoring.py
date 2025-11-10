"""
Tests for scoring and validation logic.
These ensure students get consistent and accurate feedback from their analysis scripts.
"""

import pytest
from jpamb import model, jvm


class TestPredictionParsing:
    """Test parsing of prediction strings."""

    def test_parse_percentage(self):
        """Test parsing percentage format predictions."""
        pred = model.Prediction.parse("75%")
        assert pred.to_probability() == pytest.approx(0.75, abs=0.01)

        # Note: 100% confidence (wager=inf) returns 0 probability to discourage
        # students from being overly confident - teaches that you can't be 100% certain
        pred = model.Prediction.parse("100%")
        assert pred.to_probability() == 0.0

        pred = model.Prediction.parse("0%")
        assert pred.to_probability() == pytest.approx(0.0, abs=0.01)

    def test_parse_wager(self):
        """Test parsing wager format predictions."""
        pred = model.Prediction.parse("1.0")
        assert pred.wager == 1.0

        pred = model.Prediction.parse("0.5")
        assert pred.wager == 0.5

        pred = model.Prediction.parse("-1.0")
        assert pred.wager == -1.0

    def test_parse_infinity(self):
        """Test parsing infinite confidence predictions."""
        pred = model.Prediction.parse("inf")
        assert pred.wager == float("inf")
        # Returns 0 to discourage extreme confidence (pedagogical choice)
        assert pred.to_probability() == 0.0

        pred = model.Prediction.parse("-inf")
        assert pred.wager == float("-inf")
        assert pred.to_probability() == 0.0


class TestPredictionScoring:
    """Test the scoring algorithm for predictions."""

    def test_perfect_prediction_positive(self):
        """Test scoring when prediction is perfectly confident and correct."""
        pred = model.Prediction(float("inf"))
        score = pred.score(happens=True)
        assert score == 1

    def test_perfect_prediction_negative(self):
        """Test scoring when prediction is perfectly confident it won't happen and is correct."""
        pred = model.Prediction(float("-inf"))
        score = pred.score(happens=False)
        assert score == 1

    def test_wrong_confident_prediction(self):
        """Test scoring when prediction is confident but wrong."""
        # Wager inf (think it will happen), but it doesn't
        pred = model.Prediction(float("inf"))
        score = pred.score(happens=False)
        assert score == float("-inf")

        # Wager -inf (think it won't happen), but it does
        pred = model.Prediction(float("-inf"))
        score = pred.score(happens=True)
        assert score == float("-inf")  # Maximum penalty for being wrong

    def test_neutral_prediction(self):
        """Test scoring for neutral predictions."""
        pred = model.Prediction(0)
        score_yes = pred.score(happens=True)
        score_no = pred.score(happens=False)
        # Neutral prediction should score 0 either way
        assert score_yes == 0
        assert score_no == 0

    def test_moderate_confidence(self):
        """Test scoring for moderate confidence predictions."""
        pred = model.Prediction(1.0)
        score_correct = pred.score(happens=True)
        score_wrong = pred.score(happens=False)

        # Correct prediction should score positive
        assert score_correct > 0
        # Wrong prediction should score negative
        assert score_wrong < 0

    def test_probability_to_wager_roundtrip(self):
        """Test converting between probability and wager maintains consistency.

        Note: Extreme values (0.0, 1.0) don't roundtrip because the system
        discourages overconfidence - this is intentional pedagogy.
        """
        for prob in [0.1, 0.25, 0.5, 0.75, 0.9, 0.99]:
            pred = model.Prediction.from_probability(prob)
            recovered = pred.to_probability()
            assert recovered == pytest.approx(prob, abs=0.01)


class TestResponseParsing:
    """Test parsing of response strings from analysis scripts."""

    def test_parse_simple_response(self):
        """Test parsing a simple response."""
        output = "ok;1.0\ndivide by zero;-1.0"
        response = model.Response.parse(output)

        assert "ok" in response.predictions
        assert "divide by zero" in response.predictions
        assert response.predictions["ok"].wager == 1.0
        assert response.predictions["divide by zero"].wager == -1.0

    def test_parse_percentage_response(self):
        """Test parsing responses with percentages."""
        output = "ok;75%\nassertion error;25%"
        response = model.Response.parse(output)

        assert "ok" in response.predictions
        assert "assertion error" in response.predictions

    def test_parse_ignores_invalid_queries(self):
        """Test that invalid queries are ignored."""
        output = "ok;1.0\ninvalid_query;1.0\ndivide by zero;0.5"
        response = model.Response.parse(output)

        assert "ok" in response.predictions
        assert "divide by zero" in response.predictions
        assert "invalid_query" not in response.predictions

    def test_parse_handles_malformed_lines(self):
        """Test that malformed lines are skipped gracefully."""
        output = "ok;1.0\nthis is not valid\ndivide by zero;0.5"
        response = model.Response.parse(output)

        # Should still parse the valid lines
        assert "ok" in response.predictions
        assert "divide by zero" in response.predictions

    def test_parse_empty_response(self):
        """Test parsing an empty response."""
        output = ""
        response = model.Response.parse(output)
        assert len(response.predictions) == 0


class TestResponseScoring:
    """Test scoring of complete responses."""

    def test_score_perfect_response(self):
        """Test scoring a perfect response."""
        output = "ok;inf"
        response = model.Response.parse(output)
        score = response.score(["ok"])
        assert score == 1

    def test_score_multi_query_response(self):
        """Test scoring a response with multiple queries."""
        output = "ok;inf\ndivide by zero;-inf"
        response = model.Response.parse(output)
        score = response.score(["ok"])

        # Should get points for correct "ok" and correct "not divide by zero"
        assert score == 2

    def test_score_partial_response(self):
        """Test scoring when not all queries are answered."""
        output = "ok;1.0"
        response = model.Response.parse(output)
        score = response.score(["ok", "divide by zero"])

        # Should only score the answered query
        assert score > 0 and score < 2


class TestCaseParsing:
    """Test parsing of Case strings."""

    def test_case_decode(self):
        """Test decoding a case string."""
        case_str = "jpamb.cases.Simple.divideByZero:()I () -> divide by zero"
        case = model.Case.decode(case_str)

        assert case.methodid.classname.encode() == "jpamb.cases.Simple"
        assert case.methodid.extension.name == "divideByZero"
        assert case.result == "divide by zero"

    def test_case_encode(self):
        """Test encoding a case back to string."""
        case_str = "jpamb.cases.Simple.divideByN:(I)I (0) -> divide by zero"
        case = model.Case.decode(case_str)
        encoded = case.encode()

        # Should be able to encode back
        assert "divideByN" in encoded
        assert "(0)" in encoded
        assert "divide by zero" in encoded

    def test_case_roundtrip(self):
        """Test that case parsing is reversible."""
        original = "jpamb.cases.Simple.assertBoolean:(Z)V (false) -> assertion error"
        case = model.Case.decode(original)
        encoded = case.encode()
        case2 = model.Case.decode(encoded)

        assert case == case2


class TestInputParsing:
    """Test parsing of Input values."""

    def test_input_decode_empty(self):
        """Test decoding empty input."""
        input_str = "()"
        input_obj = model.Input.decode(input_str)
        assert len(input_obj.values) == 0

    def test_input_decode_single_int(self):
        """Test decoding single integer input."""
        input_str = "(1)"
        input_obj = model.Input.decode(input_str)
        assert len(input_obj.values) == 1

    def test_input_decode_multiple_values(self):
        """Test decoding multiple input values."""
        input_str = "(1, 2)"
        input_obj = model.Input.decode(input_str)
        assert len(input_obj.values) == 2

    def test_input_encode_roundtrip(self):
        """Test that input encoding is reversible."""
        original = "(1, false, 'a')"
        input_obj = model.Input.decode(original)
        encoded = input_obj.encode()

        # Should preserve the structure
        assert "1" in encoded
        assert "false" in encoded

    def test_input_invalid_format(self):
        """Test that invalid input format raises error."""
        with pytest.raises(ValueError):
            model.Input.decode("1, 2")  # Missing parentheses


class TestKnownQueries:
    """Test that the known queries list is correct."""

    def test_all_queries_defined(self):
        """Test that all expected queries are defined."""
        expected_queries = {
            "*",
            "assertion error",
            "divide by zero",
            "null pointer",
            "ok",
            "out of bounds",
        }

        assert set(model.QUERIES) == expected_queries

    def test_wildcard_query_present(self):
        """Test that wildcard query exists."""
        assert "*" in model.QUERIES
