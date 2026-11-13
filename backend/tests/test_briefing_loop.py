from app.briefing import MAX_ROUNDS, draft_and_review, verdict_warning
from app.llm.fake import FakeClient
from tests.helpers import tracer

FACTS = {"verdict": "no_go", "violations": ["wind 27 kt exceeds max 25 kt"], "station": "GND"}
NO = {"approved": False, "feedback": "MENTION THE WIND VALUE"}
YES = {"approved": True, "feedback": ""}


async def test_loop_stops_at_three_rounds():
    llm = FakeClient({"draft": ["d1", "d2", "d3", "d4"], "review": [NO, NO, NO, NO]})
    t = tracer()
    rounds = await draft_and_review(llm, t, "m", "m", FACTS)
    assert MAX_ROUNDS == 3
    assert len(rounds) == 3
    assert [s["step"] for s in t.steps] == [
        "draft_1",
        "review_1",
        "draft_2",
        "review_2",
        "draft_3",
        "review_3",
    ]
    assert not rounds[-1].approved


async def test_loop_stops_early_when_reviewer_approves():
    llm = FakeClient({"draft": ["d1"], "review": [YES]})
    rounds = await draft_and_review(llm, tracer(), "m", "m", FACTS)
    assert len(rounds) == 1 and rounds[0].approved


async def test_reviewer_feedback_goes_into_the_next_draft():
    llm = FakeClient({"draft": ["d1", "d2"], "review": [NO, YES]})
    await draft_and_review(llm, tracer(), "m", "m", FACTS)
    drafts = [c for c in llm.calls if c["step"] == "draft"]
    assert "MENTION THE WIND VALUE" not in drafts[0]["prompt"]
    assert "MENTION THE WIND VALUE" in drafts[1]["prompt"]
    assert "d1" in drafts[1]["prompt"]  # the previous draft is shown too


async def test_invalid_review_counts_as_not_approved():
    llm = FakeClient({"draft": ["d1", "d2"], "review": ["garbage", YES]})
    rounds = await draft_and_review(llm, tracer(), "m", "m", FACTS)
    assert len(rounds) == 2 and not rounds[0].approved


def test_briefing_that_contradicts_the_code_verdict_is_caught():
    assert verdict_warning("GO for launch, all nominal.", "no_go")
    assert verdict_warning("No-Go: wind 27 kt over the 25 kt limit.", "no_go") is None
    assert verdict_warning("GO. Camera 3 froze, recovered.", "go") is None
    assert verdict_warning("NO-GO recommended.", "go")
