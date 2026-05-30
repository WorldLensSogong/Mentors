import importlib

debate_router = importlib.import_module("features.debate.router")
debate_topic_resolver = importlib.import_module("features.debate.topic_resolver")
market_data_collector = importlib.import_module("core.market_data.collector")
market_data_finnhub = importlib.import_module("core.market_data.finnhub")
market_data_models = importlib.import_module("core.market_data.models")
market_data_naver_finance = importlib.import_module("core.market_data.naver_finance")
market_data_repository = importlib.import_module("core.market_data.repository")


def test_market_data_resolver_treats_unknown_company_as_stock_candidate() -> None:
    entity = market_data_models.MarketEntity(
        kind="stock",
        symbol="PLTR",
        name="팔란티어",
        name_en="Palantir",
        aliases=["palantir", "pltr"],
    )
    match = market_data_repository.MarketEntityMatch(
        entity=entity,
        matched_text="팔란티어",
        score=100,
    )

    resolution = debate_topic_resolver._to_resolution("팔란티어 전망", match)

    assert resolution.topic_type == "stock"
    assert resolution.topic == "팔란티어 주식 투자 전망"
    assert debate_router._news_queries(resolution.topic)[0] == "팔란티어"


def test_market_data_resolver_treats_unknown_related_stocks_as_theme() -> None:
    entity = market_data_models.MarketEntity(
        kind="theme",
        symbol="SPACE_TECH",
        name="우주테크",
        aliases=["우주항공", "항공우주"],
    )
    match = market_data_repository.MarketEntityMatch(
        entity=entity,
        matched_text="우주테크",
        score=100,
    )

    resolution = debate_topic_resolver._to_resolution("앞으로 우주테크 관련주의 전망", match)

    assert resolution.topic_type == "theme"
    assert resolution.topic == "우주테크 관련주 전망"
    assert debate_router._news_queries(resolution.topic)[0] == "우주테크 관련주 전망"


def test_market_news_item_unique_constraint_is_scoped_to_entity() -> None:
    constraints = {
        constraint.name: tuple(constraint.columns.keys())
        for constraint in market_data_models.MarketNewsItem.__table__.constraints
    }

    assert constraints["uq_market_news_items_entity_url"] == ("entity_id", "url")
    assert all(columns != ("url",) for columns in constraints.values())


def test_stock_theme_labels_are_not_used_as_primary_match_names() -> None:
    stock = market_data_models.MarketEntity(
        kind="stock",
        symbol="PLTR",
        name="팔란티어",
        name_en="Palantir",
        aliases=["palantir", "pltr"],
        themes=["AI", "방산"],
    )
    theme = market_data_models.MarketEntity(
        kind="theme",
        symbol="AI",
        name="AI",
        aliases=["인공지능"],
        themes=["AI", "AI 반도체"],
    )

    stock_match = market_data_repository._score_entity_match(stock, "AI 전망", ["AI"])
    theme_match = market_data_repository._score_entity_match(theme, "AI 전망", ["AI"])

    assert stock_match is None
    assert theme_match is not None
    assert theme_match.entity.kind == "theme"


def test_topic_discovery_queries_keep_unknown_company_name_first() -> None:
    queries = market_data_collector._topic_discovery_queries("nvidia 전망")

    assert queries[0] == "nvidia"
    assert "전망" not in queries


def test_topic_discovery_queries_strip_korean_particle_from_latin_name() -> None:
    queries = market_data_collector._topic_discovery_queries("openai의 오너리스크")

    assert queries == ["openai"]


def test_topic_discovery_queries_do_not_use_aliases_as_api_search_terms() -> None:
    queries = market_data_collector._topic_discovery_queries("엔비디아 전망")

    assert "NVDA" not in queries
    assert queries == ["엔비디아"]


def test_global_stock_korean_aliases_are_matchable_after_cache_seed() -> None:
    entity = market_data_models.MarketEntity(
        kind="stock",
        symbol="NVDA",
        name="NVIDIA Corp",
        name_en="NVIDIA Corp",
        aliases=["NVDA", "NVIDIA Corp", "엔비디아"],
    )

    match = market_data_repository._score_entity_match(entity, "엔비디아 전망", ["엔비디아"])

    assert match is not None
    assert match.entity.symbol == "NVDA"


def test_naver_finance_parser_extracts_korean_stock_candidates() -> None:
    payload = {
        "items": [
            [
                ["삼성전자", "005930", "KOSPI"],
                {"name": "삼성전자우", "code": "005935", "market": "KOSPI"},
            ]
        ]
    }

    stocks = market_data_naver_finance._parse_stocks(payload)

    assert stocks[0].code == "005930"
    assert stocks[0].name == "삼성전자"
    assert stocks[0].market == "KOSPI"
    assert stocks[1].code == "005935"

async def test_discover_entity_from_topic_upserts_external_stock(monkeypatch) -> None:
    upsert_calls = []

    class FakeFinnhubClient:
        async def search_companies(self, query: str, *, limit: int = 5):
            assert query == "nvidia"
            return [
                market_data_finnhub.FinnhubCompany(
                    symbol="NVDA",
                    display_symbol="NVDA",
                    description="NVIDIA Corp",
                    kind="Common Stock",
                )
            ]

        async def get_company_profile(self, symbol: str):
            assert symbol == "NVDA"
            return market_data_finnhub.FinnhubCompanyProfile(
                symbol="NVDA",
                name="NVIDIA Corp",
                exchange="NASDAQ",
                industry="Semiconductors",
                country="US",
            )

        async def get_company_news(self, symbol: str, *, limit: int = 5):
            return []

    async def fake_upsert_entity(db, **kwargs):
        upsert_calls.append(kwargs)
        return market_data_models.MarketEntity(
            kind=kwargs["kind"],
            symbol=kwargs["symbol"],
            name=kwargs["name"],
            name_en=kwargs["name_en"],
            exchange=kwargs.get("exchange"),
            industry=kwargs["industry"],
            aliases=kwargs["aliases"],
            themes=kwargs["themes"],
            source=kwargs["source"],
            confidence=kwargs["confidence"],
        )

    monkeypatch.setattr(market_data_collector, "upsert_entity", fake_upsert_entity)
    monkeypatch.setattr(market_data_collector.settings, "market_data_discovery_enabled", True)

    entity = await market_data_collector.discover_entity_from_topic(
        object(),
        "nvidia 전망",
        client=FakeFinnhubClient(),
    )

    assert entity is not None
    assert entity.kind == "stock"
    assert entity.symbol == "NVDA"
    assert entity.source == "finnhub"
    assert "NVIDIA Corp" in entity.aliases
    assert "엔비디아" in entity.aliases
    assert "Semiconductors" in entity.themes
    assert any(
        call["kind"] == "theme"
        and call["symbol"] == "INDUSTRY_SEMICONDUCTORS"
        and call["source"] == "finnhub_profile"
        for call in upsert_calls
    )


async def test_discover_entity_from_topic_uses_korean_stock_search_first(monkeypatch) -> None:
    class FakeKoreanClient:
        async def search_stocks(self, query: str, *, limit: int = 5):
            assert query == "삼성전자"
            return [
                market_data_naver_finance.NaverFinanceStock(
                    code="005930",
                    name="삼성전자",
                    market="KOSPI",
                )
            ]

    class FakeFinnhubClient:
        async def search_companies(self, query: str, *, limit: int = 5):
            raise AssertionError("Finnhub should not be called when Korean search matches")

        async def get_company_profile(self, symbol: str):
            raise AssertionError("Finnhub should not be called when Korean search matches")

        async def get_company_news(self, symbol: str, *, limit: int = 5):
            raise AssertionError("Finnhub should not be called when Korean search matches")

    async def fake_upsert_entity(db, **kwargs):
        return market_data_models.MarketEntity(
            kind=kwargs["kind"],
            symbol=kwargs["symbol"],
            name=kwargs["name"],
            name_en=kwargs["name_en"],
            exchange=kwargs.get("exchange"),
            sector=kwargs.get("sector"),
            aliases=kwargs["aliases"],
            themes=kwargs["themes"],
            source=kwargs["source"],
            confidence=kwargs["confidence"],
        )

    monkeypatch.setattr(market_data_collector, "upsert_entity", fake_upsert_entity)
    monkeypatch.setattr(market_data_collector.settings, "market_data_discovery_enabled", True)

    entity = await market_data_collector.discover_entity_from_topic(
        object(),
        "삼성전자 전망",
        client=FakeFinnhubClient(),
        korean_client=FakeKoreanClient(),
    )

    assert entity is not None
    assert entity.kind == "stock"
    assert entity.symbol == "005930"
    assert entity.name == "삼성전자"
    assert entity.exchange == "KOSPI"
    assert entity.source == "naver_finance"
