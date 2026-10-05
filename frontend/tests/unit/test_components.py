import os

from shared.components.animated_background import ParticleBackground
from shared.components.animated_nav import AnimatedNav, MAX_WIDTH, NavEntry, nav_width
from shared.components.downloader import purge_downloads, remove_download, stage_download


def test_nav_width_is_responsive():
    assert nav_width(None) == MAX_WIDTH and nav_width(1920) == MAX_WIDTH
    assert nav_width(360) == 360 - 32 and nav_width(100) == 200


def test_nav_marks_active_and_dispatches_selection():
    picked = []
    entries = [NavEntry("a", "A", "home", "/a"), NavEntry("b", "B", "home", "/b")]
    nav = AnimatedNav(entries, "b", picked.append, page_width=400)
    assert nav.width == 368
    assert [i.active for i in nav.items] == [False, True]
    assert nav.items[1]._label.opacity == 1 and nav.items[0]._label.opacity == 0
    nav.items[0].on_click(None)
    assert picked == [entries[0]]
    assert all(i.ink and i.tooltip for i in nav.items)
    nav.set_page_width(2000)
    assert nav.width == MAX_WIDTH


def test_particles_bounded_and_scaled():
    bg = ParticleBackground(width=500, height=300, seed=1)
    assert len(bg.particles) == 24
    assert all(0 <= p.left <= 500 and 0 <= p.top <= 300 for p in bg.particles)
    bg.resize(100, 100)
    assert all(0 <= p.left <= 100 and 0 <= p.top <= 100 for p in bg.particles)
    for _ in range(10):
        bg.step()
    assert any(p.opacity == 1 for p in bg.particles)


def test_particle_loop_stops(event_loop=None):
    import asyncio
    bg = ParticleBackground(count=3, seed=2)

    async def go():
        task = asyncio.ensure_future(bg.run())
        await asyncio.sleep(0)  # first update() raises on a detached control -> loop exits cleanly
        await asyncio.wait_for(task, 2)

    asyncio.run(go())
    bg.stop()
    assert bg._stopped


def test_download_staging_roundtrip(tmp_path):
    d = str(tmp_path / "dl")
    token = stage_download(d, "../x y.pdf", b"data")
    files = os.listdir(os.path.join(d, token))
    assert files == ["y.pdf"] or files == ["x_y.pdf"] or len(files) == 1
    assert len(token) == 32
    remove_download(d, token)
    assert not os.path.exists(os.path.join(d, token))
    stage_download(d, "a.pdf", b"1")
    purge_downloads(d)
    assert not os.path.exists(d)


def test_download_path_should_be_root_relative_not_page_url():
    # Regression: Flet's page.url is the websocket URL (ws://...), which a browser tab
    # cannot open; the link must be resolved by the browser against the page origin.
    from shared.components.downloader import download_path

    url = download_path("/app/assets/downloads", "ab" * 16, "my cv.pdf")

    assert url == "/downloads/" + "ab" * 16 + "/my%20cv.pdf"
    assert "://" not in url
