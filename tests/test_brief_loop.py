from app.llm import FakeClient
from app.pipeline import MAX_ROUNDS, brief_loop

REPORT = {
    "id": 7,
    "name": "Marco Diaz",
    "station": "GND",
    "wind_knots": 27,
    "temp_c": 4,
    "fuel_pct": 98,
    "note": "Pad camera 3 feed froze.",
    "verdict": "no_go",
    "violations": [
        {
            "reading": "wind_knots",
            "value": 27,
            "message": "Wind 27 kt exceeds the limit of 25 kt or less",
        }
    ],
}
ANALYSIS = {"subsystem": "ground_systems", "severity": "high", "brief_by_minutes": 5}
GOOD_DRAFT = "NO-GO: wind 27 kt exceeds the 25 kt limit. GND reports pad camera 3 froze."
NO = {"approved": False, "feedback": "MENTION THE WIND VALUE"}
YES = {"approved": True, "feedback": "Good."}


async def test_loop_stops_after_three_rounds_if_never_approved():
    fake = FakeClient({"draft": [GOOD_DRAFT] * 5, "review": [NO] * 5})
    result, steps = await brief_loop(fake, REPORT, ANALYSIS)
    assert MAX_ROUNDS == 3
    assert result["briefing_rounds"] == 3
    assert result["reviewer_approved"] is False
    assert result["review_feedback"] == "MENTION THE WIND VALUE"
    assert [s["name"] for s in steps] == [
        "draft_1", "review_1", "draft_2", "review_2", "draft_3", "review_3",
    ]  # fmt: skip
    assert len(fake.calls) == 6


async def test_loop_stops_as_soon_as_the_reviewer_approves():
    fake = FakeClient({"draft": [GOOD_DRAFT], "review": [YES]})
    result, steps = await brief_loop(fake, REPORT, ANALYSIS)
    assert result == {
        "briefing": GOOD_DRAFT,
        "briefing_rounds": 1,
        "reviewer_approved": True,
        "review_feedback": "Good.",
        "warnings": [],
    }
    assert len(steps) == 2


async def test_reviewer_feedback_goes_into_the_next_draft():
    fake = FakeClient({"draft": ["NO-GO: draft one.", GOOD_DRAFT], "review": [NO, YES]})
    result, _ = await brief_loop(fake, REPORT, ANALYSIS)
    drafts = [c for c in fake.calls if c["step"] == "draft"]
    assert "MENTION THE WIND VALUE" not in drafts[0]["user"]
    assert "MENTION THE WIND VALUE" in drafts[1]["user"]
    assert "NO-GO: draft one." in drafts[1]["user"]  # the reviewer's target is visible too
    assert result["briefing"] == GOOD_DRAFT
    assert result["briefing_rounds"] == 2


async def test_reviewer_sees_the_draft():
    fake = FakeClient({"draft": [GOOD_DRAFT], "review": [YES]})
    await brief_loop(fake, REPORT, ANALYSIS)
    review = next(c for c in fake.calls if c["step"] == "review")
    assert GOOD_DRAFT in review["user"]


async def test_briefing_that_contradicts_the_code_verdict_gets_a_warning():
    fake = FakeClient({"draft": ["GO: all good."], "review": [YES]})
    result, _ = await brief_loop(fake, REPORT, ANALYSIS)
    assert result["warnings"] == ["Briefing does not open with the code verdict NO-GO."]


async def test_failed_draft_falls_back_to_a_code_written_briefing():
    fake = FakeClient({"draft": [RuntimeError("down")]})
    result, steps = await brief_loop(fake, REPORT, ANALYSIS)
    assert result["briefing"].startswith("NO-GO: Wind 27 kt exceeds the limit of 25 kt or less.")
    assert result["reviewer_approved"] is False
    assert "Briefing could not be drafted" in result["warnings"][0]
    assert [s["name"] for s in steps] == ["draft_1"]
    assert steps[0]["status"] == "error"


async def test_failed_review_counts_as_not_approved():
    fake = FakeClient({"draft": [GOOD_DRAFT] * 3, "review": [RuntimeError("x"), YES]})
    result, steps = await brief_loop(fake, REPORT, ANALYSIS)
    assert result["briefing_rounds"] == 2
    assert steps[1]["status"] == "error"
