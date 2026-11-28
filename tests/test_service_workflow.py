import pytest

from app.service_workflow import ServiceWorkflowError, WebsiteServiceWorkflow


def create_request(workflow):
    fingerprint = workflow.fingerprint("203.0.113.70", "service-secret-" + "q" * 40)
    return workflow.create_request(
        "Local Shop", "https://shop.example", "owner@shop.example",
        "AI Website", fingerprint,
        {"AI Website", "AI Front Desk", "Property Video Walkthroughs"},
    )


def test_website_service_requires_explicit_contact_and_https():
    workflow = WebsiteServiceWorkflow(":memory:")
    fp = workflow.fingerprint("203.0.113.71", "service-secret-" + "r" * 40)
    with pytest.raises(ServiceWorkflowError):
        workflow.create_request("Local Shop", "http://shop.example", "owner@shop.example",
                                "AI Website", fp, {"AI Website"})


def test_customer_must_approve_proposal_before_paid_delivery():
    workflow = WebsiteServiceWorkflow(":memory:")
    request = create_request(workflow)
    workflow.record_audit(request["id"], {"findings": ["Missing page title"]})
    workflow.record_proposal(request["id"], {
        "package": "AI Website", "total_upfront_usd": 499,
        "body": "A fixed-price website proposal for Local Shop.",
    })
    item, token = workflow.issue_customer_approval(request["id"])
    assert item["status"] == "AWAITING_CUSTOMER_APPROVAL"
    with pytest.raises(ServiceWorkflowError, match="customer approval"):
        workflow.update_delivery(request["id"], "IN_PROGRESS", payment_sale_id="sale-1")
    accepted = workflow.customer_decide(token, "ACCEPTED")
    assert accepted["status"] == "CUSTOMER_APPROVED"
    with pytest.raises(ServiceWorkflowError, match="verified Gumroad"):
        workflow.update_delivery(request["id"], "IN_PROGRESS")
    started = workflow.update_delivery(request["id"], "IN_PROGRESS", payment_sale_id="sale-1")
    assert started["status"] == "IN_PROGRESS"
    delivered = workflow.update_delivery(
        request["id"], "DELIVERED", "Completed the agreed site build and tested the contact form.",
        "https://deliverables.example/site", "sale-1",
    )
    assert delivered["status"] == "DELIVERED"
    assert delivered["payment_sale_id"] == "sale-1"


def test_customer_approval_link_is_single_use():
    workflow = WebsiteServiceWorkflow(":memory:")
    request = create_request(workflow)
    workflow.record_audit(request["id"], {"findings": []})
    workflow.record_proposal(request["id"], {"body": "Proposal body."})
    _, token = workflow.issue_customer_approval(request["id"])
    workflow.customer_decide(token, "DECLINED")
    with pytest.raises(LookupError):
        workflow.get_public_approval(token)


def test_website_service_intake_rate_limit():
    workflow = WebsiteServiceWorkflow(":memory:")
    fp = workflow.fingerprint("203.0.113.72", "service-secret-" + "s" * 40)
    for _ in range(3):
        workflow.create_request("Local Shop", "https://shop.example", "owner@shop.example",
                                "AI Website", fp, {"AI Website"})
    with pytest.raises(ServiceWorkflowError, match="limit"):
        workflow.create_request("Local Shop", "https://shop.example", "owner@shop.example",
                                "AI Website", fp, {"AI Website"})
