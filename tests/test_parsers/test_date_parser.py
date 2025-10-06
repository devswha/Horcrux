"""
DateParser 테스트
"""
import pytest
from datetime import datetime, timedelta
from parsers.date_parser import DateParser


@pytest.fixture
def parser():
    return DateParser()


def test_parse_today(parser):
    """오늘 파싱"""
    result = parser.parse("오늘")
    expected = datetime.now().strftime("%Y-%m-%d")
    assert result == expected


def test_parse_yesterday(parser):
    """어제 파싱"""
    result = parser.parse("어제")
    expected = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    assert result == expected


def test_parse_days_ago(parser):
    """N일 전 파싱"""
    result = parser.parse("3일 전")
    expected = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    assert result == expected


def test_parse_days_later(parser):
    """N일 후 파싱"""
    result = parser.parse("2일 후")
    expected = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    assert result == expected


def test_extract_from_sentence(parser):
    """문장에서 날짜 추출"""
    result = parser.extract_date_from_sentence("어제 5시간 잤어")
    expected = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    assert result == expected
