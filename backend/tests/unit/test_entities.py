from app.internal.entities import Role
from tests.fixtures.factories import ResumeFactory, UserFactory


def test_candidate_cannot_review():
    assert not UserFactory(role=Role.CANDIDATE).can_review_resumes()


def test_expert_and_admin_can_review():
    assert UserFactory(role=Role.EXPERT).can_review_resumes()
    assert UserFactory(role=Role.ADMIN).can_review_resumes()


def test_delete_rules():
    owner = UserFactory(id=1)
    other = UserFactory(id=2)
    admin = UserFactory(id=3, role=Role.ADMIN)
    expert = UserFactory(id=4, role=Role.EXPERT)
    resume = ResumeFactory(user_id=1)
    assert owner.can_delete(resume)
    assert admin.can_delete(resume)
    assert not other.can_delete(resume)
    assert not expert.can_delete(resume)


def test_download_rules():
    resume = ResumeFactory(user_id=1)
    assert UserFactory(id=1).can_download(resume)
    assert UserFactory(id=2, role=Role.EXPERT).can_download(resume)
    assert UserFactory(id=3, role=Role.ADMIN).can_download(resume)
    assert not UserFactory(id=2).can_download(resume)
