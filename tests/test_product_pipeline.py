import pytest

from app.product_pipeline import ProductPipeline, ProductPipelineError


def draft(store):
    return store.create({
        "title": "Customer Interview Kit",
        "problem": "Independent creators struggle to validate which products customers need.",
        "audience": "Independent creators and small digital-product businesses",
        "solution": "A guided interview and evidence-capture toolkit for validating product demand.",
        "description": "A practical toolkit with interview prompts, scoring rubrics, evidence logs, and a validation worksheet.",
        "format": "template",
        "proposed_price_cents": 900,
    })


def test_product_pipeline_requires_validation_before_owner_approval():
    store = ProductPipeline(":memory:")
    product = draft(store)
    with pytest.raises(ProductPipelineError, match="validation"):
        store.decide(product["id"], "APPROVED_FOR_LISTING")


def test_product_pipeline_approves_only_when_every_check_passes():
    store = ProductPipeline(":memory:")
    product = draft(store)
    checks = [
        {"name": "problem_evidence", "passed": True, "evidence": "Three customer interviews recorded"},
        {"name": "prototype_test", "passed": True, "evidence": "Prototype task test completed"},
        {"name": "delivery_test", "passed": True, "evidence": "Download package opened and checked"},
    ]
    store.record_validation(product["id"], checks, "Evidence collected from interviews and prototype tests.")
    result = store.decide(product["id"], "APPROVED_FOR_LISTING")
    assert result["status"] == "APPROVED_FOR_LISTING"


def test_product_pipeline_rejects_failed_validation():
    store = ProductPipeline(":memory:")
    product = draft(store)
    checks = [
        {"name": "problem_evidence", "passed": True, "evidence": "Interviews recorded"},
        {"name": "prototype_test", "passed": False, "evidence": "Core workflow failed"},
        {"name": "delivery_test", "passed": True, "evidence": "Package opened"},
    ]
    store.record_validation(product["id"], checks, "One critical test failed and needs repair.")
    with pytest.raises(ProductPipelineError, match="failed validation"):
        store.decide(product["id"], "APPROVED_FOR_LISTING")


def test_product_pipeline_rejects_missing_evidence():
    store = ProductPipeline(":memory:")
    with pytest.raises(ProductPipelineError):
        store.create({"title": "Bad", "problem": "too short"})
