import pytest

from app.internal.entities import Role
from app.internal.services import ResumeService
from app.pkg.errors import Forbidden, NotFound, PayloadTooLarge, ValidationFailed
from tests.fixtures.factories import UserFactory
from tests.fixtures.fakes import FakeResumeRepo, FakeStorage, FakeUserRepo

PDF = b"%PDF-1.4\nbody"


@pytest.fixture
def env():
    users = FakeUserRepo()
    owner = users.add(UserFactory(id=None, username="owner", email="o@x.com"))
    other = users.add(UserFactory(id=None, username="other", email="x@x.com"))
    expert = users.add(UserFactory(id=None, username="exp", email="e@x.com", role=Role.EXPERT))
    admin = users.add(UserFactory(id=None, username="adm", email="a@x.com", role=Role.ADMIN))
    resumes, storage = FakeResumeRepo(users), FakeStorage()
    svc = ResumeService(resumes, storage, max_upload_bytes=100)
    return svc, resumes, storage, owner, other, expert, admin


def test_upload_stores_and_hides_nothing_sensitive(env):
    svc, resumes, storage, owner, *_ = env
    r = svc.upload(owner, "cv.pdf", [PDF])
    assert r.file_size == len(PDF) and r.mime_type == "application/pdf"
    assert r.storage_key.endswith(".pdf") and storage.exists(r.storage_key)


def test_upload_rejects_non_pdf_and_stores_nothing(env):
    svc, _, storage, owner, *_ = env
    with pytest.raises(ValidationFailed):
        svc.upload(owner, "cv.pdf", [b"<html>not a pdf</html>"])
    assert storage.files == {}


def test_upload_too_large(env):
    svc, _, storage, owner, *_ = env
    with pytest.raises(PayloadTooLarge):
        svc.upload(owner, "cv.pdf", [PDF, b"x" * 200])
    assert storage.files == {}


def test_upload_db_failure_removes_stored_file(env):
    svc, resumes, storage, owner, *_ = env
    resumes.fail_on_add = True
    with pytest.raises(RuntimeError):
        svc.upload(owner, "cv.pdf", [PDF])
    assert storage.files == {}


def test_download_permissions(env):
    svc, _, _, owner, other, expert, admin = env
    r = svc.upload(owner, "cv.pdf", [PDF])
    for ok in (owner, expert, admin):
        _, chunks = svc.download(ok, r.id)
        assert b"".join(chunks) == PDF
    with pytest.raises(Forbidden):
        svc.download(other, r.id)
    with pytest.raises(NotFound):
        svc.download(owner, 999)


def test_download_missing_file(env):
    svc, _, storage, owner, *_ = env
    r = svc.upload(owner, "cv.pdf", [PDF])
    storage.files.clear()
    with pytest.raises(NotFound):
        svc.download(owner, r.id)


def test_delete_permissions(env):
    svc, resumes, storage, owner, other, expert, admin = env
    r = svc.upload(owner, "cv.pdf", [PDF])
    for denied in (other, expert):
        with pytest.raises(Forbidden):
            svc.delete(denied, r.id)
    svc.delete(owner, r.id)
    assert resumes.count() == 0 and storage.files == {}
    r2 = svc.upload(owner, "cv.pdf", [PDF])
    svc.delete(admin, r2.id)
    with pytest.raises(NotFound):
        svc.delete(admin, r2.id)


def test_list_mine_and_expert_listing(env):
    svc, _, _, owner, other, expert, admin = env
    svc.upload(owner, "a.pdf", [PDF])
    svc.upload(other, "b.pdf", [PDF])
    assert len(svc.list_mine(owner)) == 1
    assert len(svc.list_for_experts(expert, 0, 50)) == 2
    assert len(svc.list_for_experts(admin, 1, 50)) == 1
    with pytest.raises(Forbidden):
        svc.list_for_experts(owner, 0, 50)
