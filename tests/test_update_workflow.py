from pathlib import Path


def test_update_workflow_has_concurrency_guard():
    workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "update.yml"
    content = workflow_path.read_text()

    assert "concurrency:" in content
    assert "group: hn-daily-update-main" in content
    assert "cancel-in-progress: false" in content


def test_update_workflow_has_rebase_push_retry():
    workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "update.yml"
    content = workflow_path.read_text()

    assert "for attempt in 1 2 3; do" in content
    assert "git fetch origin main" in content
    assert "git rebase origin/main" in content
    assert "git push origin HEAD:main" in content
