from src.fetcher import fetch_current_rankings


def test_fetcher_returns_list():
    data = fetch_current_rankings()
    assert isinstance(data, list)
    # If sample data exists, check structure of first item
    if data:
        first = data[0]
        assert 'artist' in first and 'song' in first and 'points' in first
