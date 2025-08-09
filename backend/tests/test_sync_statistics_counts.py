import pytest

from core.sync.sync_worker import SyncStatistics


def test_sync_statistics_issue_counts():
    stats = SyncStatistics()
    stats.add_project_result('P1', 'Success', 1.0, issues_count=5, issues_created=2, issues_updated=3)
    stats.add_project_result('P2', 'Success', 2.0, issues_count=2, issues_created=1, issues_updated=1)
    stats.add_project_result('P3', 'Failed', 0.5, issues_count=0, issues_created=0, issues_updated=0, error='err')

    assert stats.total_issues == 7
    assert stats.total_created == 3
    assert stats.total_updated == 4
    assert stats.project_created['P1'] == 2
    assert stats.project_updated['P1'] == 3
    assert stats.failed_projects == 1
    assert stats.errors['P3'] == 'err'
