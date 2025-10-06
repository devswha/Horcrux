"""
NumberParser 테스트
"""
import pytest
from parsers.number_parser import NumberParser


@pytest.fixture
def parser():
    return NumberParser()


def test_parse_hours(parser):
    """시간 파싱"""
    assert parser.parse_hours("5시간") == 5.0
    assert parser.parse_hours("7.5시간") == 7.5
    assert parser.parse_hours("반시간") == 0.5


def test_parse_minutes(parser):
    """분 파싱"""
    assert parser.parse_minutes("30분") == 30
    assert parser.parse_minutes("반시간") == 30
    assert parser.parse_minutes("45분") == 45


def test_parse_grams(parser):
    """그램 파싱"""
    assert parser.parse_grams("100g") == 100.0
    assert parser.parse_grams("150그램") == 150.0


def test_parse_weight(parser):
    """체중 파싱"""
    assert parser.parse_weight("70kg") == 70.0
    assert parser.parse_weight("65.5키로") == 65.5
