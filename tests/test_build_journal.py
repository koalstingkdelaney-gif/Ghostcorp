from app.build_journal import BuildJournal


def test_journal_publishes_only_allowlisted_fields_and_deduplicates(tmp_path):
    journal = BuildJournal(str(tmp_path / "journal.db"))
    event = {"event_key":"commit:abc123","category":"milestone",
             "title":"Queue foundation added",
             "summary":"Added division-scoped durable task queue.",
             "state":"implemented","commit_ref":"abc123"}
    assert journal.publish(event) == "published"
    assert journal.publish(event) == "duplicate"
    result = journal.list_public()
    assert len(result["entries"]) == 1
    assert "event_key" not in result["entries"][0]


def test_journal_rejects_unverified_states(tmp_path):
    journal = BuildJournal(str(tmp_path / "journal.db"))
    event = {"event_key":"commit:def456","category":"release",
             "title":"Claim live","summary":"Not actually deployed.",
             "state":"live"}
    try:
        journal.publish(event)
        assert False, "invalid state should be rejected"
    except ValueError:
        pass
