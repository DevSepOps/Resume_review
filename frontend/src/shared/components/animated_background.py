"""Twinkling particle background (adapted from the animated_login prototype).

Fixes versus the prototype: a single ``update()`` per tick, a ``while`` loop with a
cancellation flag instead of recursion, a bounded particle count and positions scaled to
the page size. Start with ``page.run_task(background.run)`` and call ``stop()`` to end it.
"""
from __future__ import annotations

import asyncio
import random
from typing import List, Optional

import flet as ft

DEFAULT_PARTICLES = 24
TICK_SECONDS = 0.3
COLORS = ("#4C8DFF", "#FFFFFF")


class Particle(ft.Container):
    def __init__(self, rng: random.Random, width: float, height: float) -> None:
        color = rng.choice(COLORS)
        super().__init__(
            width=3, height=3, shape=ft.BoxShape.CIRCLE, bgcolor=color, opacity=0,
            shadow=ft.BoxShadow(spread_radius=4, blur_radius=24, color=color),
        )
        self._rng = rng
        self.ticks_left = rng.randint(1, 4)
        self.relocate(width, height)
        self.animate_opacity = ft.Animation(rng.randrange(500, 900, 100), ft.AnimationCurve.EASE)

    def relocate(self, width: float, height: float) -> None:
        self.left = self._rng.uniform(0, max(width, 1))
        self.top = self._rng.uniform(0, max(height, 1))

    def step(self, width: float, height: float) -> None:
        """Advance one tick: toggle visibility when due; move only while invisible."""
        self.ticks_left -= 1
        if self.ticks_left > 0:
            return
        self.ticks_left = self._rng.randint(2, 5)
        if self.opacity:
            self.opacity = 0
        else:
            self.relocate(width, height)
            self.opacity = 1


class ParticleBackground(ft.Stack):
    def __init__(self, count: int = DEFAULT_PARTICLES, width: float = 1280,
                 height: float = 800, seed: Optional[int] = None) -> None:
        self._rng = random.Random(seed)
        self.area_width = width
        self.area_height = height
        self.particles: List[Particle] = [Particle(self._rng, width, height) for _ in range(count)]
        super().__init__(controls=list(self.particles), expand=True)
        self._stopped = False

    def resize(self, width: float, height: float) -> None:
        """Rescale to a new page size; particles get fresh positions."""
        self.area_width, self.area_height = width, height
        for particle in self.particles:
            particle.relocate(width, height)

    def step(self) -> None:
        for particle in self.particles:
            particle.step(self.area_width, self.area_height)

    def stop(self) -> None:
        self._stopped = True

    async def run(self) -> None:
        """Animation loop; exits when stop() is called or the control is gone."""
        self._stopped = False
        while not self._stopped:
            self.step()
            try:
                self.update()
            except Exception:  # control detached / session closed
                break
            await asyncio.sleep(TICK_SECONDS)
