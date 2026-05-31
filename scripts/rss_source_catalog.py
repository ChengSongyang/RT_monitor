"""RSS source catalog for radiotherapy AI monitoring."""

RSS_SOURCES = [
    {
        "id": "arxiv-radiotherapy-ai",
        "name": "arXiv 放疗 + AI",
        "short_name": "arXiv RT+AI",
        "kind": "preprint",
        "kind_label": "预印本",
        "source": "arXiv",
        "source_type": "rss",
        "category": "paper",
        "feed_url": "https://export.arxiv.org/api/query?search_query=all:radiotherapy+AND+all:%22artificial+intelligence%22&start=0&max_results=50&sortBy=submittedDate&sortOrder=descending",
        "homepage": "https://arxiv.org/",
        "enabled": True,
        "trust_level": "medium",
        "collection_method": "rss",
        "description": "arXiv preprints matching radiotherapy and artificial intelligence terms.",
        "base_score": 75,
        "tags": ["radiotherapy", "artificial-intelligence", "preprint"],
    },
    {
        "id": "ijrobp-red-journal",
        "name": "International Journal of Radiation Oncology•Biology•Physics",
        "short_name": "Red Journal",
        "kind": "journal",
        "kind_label": "期刊",
        "source": "ScienceDirect",
        "source_type": "rss",
        "category": "paper",
        "feed_url": "https://rss.sciencedirect.com/publication/science/03603016",
        "homepage": "https://www.redjournal.org/",
        "enabled": True,
        "trust_level": "high",
        "collection_method": "rss",
        "description": "RSS feed for International Journal of Radiation Oncology•Biology•Physics articles.",
        "base_score": 90,
        "tags": ["radiation-oncology", "journal", "red-journal"],
    },
    {
        "id": "radonc-green-journal",
        "name": "Radiotherapy and Oncology",
        "short_name": "Green Journal",
        "kind": "journal",
        "kind_label": "期刊",
        "source": "ScienceDirect",
        "source_type": "rss",
        "category": "paper",
        "feed_url": "https://rss.sciencedirect.com/publication/science/01678140",
        "homepage": "https://www.thegreenjournal.com/",
        "enabled": True,
        "trust_level": "high",
        "collection_method": "rss",
        "description": "RSS feed for Radiotherapy and Oncology articles.",
        "base_score": 90,
        "tags": ["radiotherapy", "oncology", "journal", "green-journal"],
    },
]


def enabled_rss_sources():
    """Return enabled RSS source definitions."""
    return [source for source in RSS_SOURCES if source["enabled"]]


def get_rss_source(source_id):
    """Return an RSS source definition by id."""
    for source in RSS_SOURCES:
        if source["id"] == source_id:
            return source
    return None
