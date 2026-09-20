from types import SimpleNamespace

from app.services.typesense import TypesenseService


class FakeDocuments:
    def __init__(self):
        self.search_parameters = None

    def search(self, parameters):
        self.search_parameters = parameters
        return {"found": 0, "hits": []}


def test_search_applies_format_filter_and_sorting():
    documents = FakeDocuments()
    service = TypesenseService.__new__(TypesenseService)
    service.settings = SimpleNamespace(typesense_collection="documents")
    service.client = SimpleNamespace(
        collections={
            "documents": SimpleNamespace(documents=documents),
        }
    )
    service.ensure_collection = dict

    service.search(
        "contrat",
        format_filter="google-doc",
        sort_by="updated_at",
        sort_order="desc",
    )

    assert documents.search_parameters["filter_by"] == "format:=`google-doc`"
    assert documents.search_parameters["sort_by"] == "updated_at:desc"


def test_search_keeps_relevance_when_no_sorting_is_requested():
    documents = FakeDocuments()
    service = TypesenseService.__new__(TypesenseService)
    service.settings = SimpleNamespace(typesense_collection="documents")
    service.client = SimpleNamespace(
        collections={
            "documents": SimpleNamespace(documents=documents),
        }
    )
    service.ensure_collection = dict

    service.search("contrat")

    assert "filter_by" not in documents.search_parameters
    assert "sort_by" not in documents.search_parameters
