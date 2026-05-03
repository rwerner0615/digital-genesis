"""DigitalGenesis v2 — composed-body visualizer."""
import colorsys
import math
import random
import pygame

from world import World, GRID_SIZE, HARD_POPULATION_CAP
from dna import ANCESTOR
from cell import Cell, build_cell_index
from simulation import _population_guardian

WINDOW_W = 1200
WINDOW_H = 720
WORLD_PX = 720
PANEL_X  = WORLD_PX
PANEL_W  = WINDOW_W - WORLD_PX
SCALE    = WORLD_PX / GRID_SIZE   # 3.6 px per grid unit

POP_HISTORY_LEN = 500

C_BG        = (12,  14,  20)
C_PANEL_BG  = (18,  20,  30)
C_DIVIDER   = (45,  50,  70)
C_TEXT      = (195, 210, 220)
C_LABEL     = (120, 135, 155)
C_HEADER    = (255, 255, 255)
C_GRAPH_BG  = (8,   10,  16)
C_POP_LINE  = (70,  200, 110)
C_PRED_LINE = (210, 70,  70)

# 8 angular slots (degrees clockwise from right).
# shell → outer ring; body_mass → body radius (both handled separately).
_SLOT_ANGLES: dict[str, int] = {
    'spike':          0,
    'tentacle':      36,
    'mouth_cell':    72,
    'mouth_nutrient': 108,
    'flagellum':     180,
    'fin':           216,
    'eye':           270,
    'plate':         324,
}

_color_cache: dict = {}


def _lineage_color(lineage_id: int) -> tuple:
    if lineage_id not in _color_cache:
        hue = (lineage_id * 137.508) % 360
        r, g, b = colorsys.hsv_to_rgb(hue / 360.0, 0.75, 0.95)
        _color_cache[lineage_id] = (int(r * 255), int(g * 255), int(b * 255))
    return _color_cache[lineage_id]


def _cell_color(cell) -> tuple:
    ph = cell.phenotype
    if ph.color_override is not None:
        h1, h2 = ph.color_override
        r, g, b = colorsys.hsv_to_rgb(h1 / 12.0, 0.5 + (h2 % 6) / 12.0, 0.9)
        return (int(r * 255), int(g * 255), int(b * 255))
    return _lineage_color(cell.lineage_id)


# ── composed-body renderer ─────────────────────────────────────────────────────

def _draw_cell(surf: pygame.Surface, cell, scale: float) -> None:
    cx = round(cell.position[0] * scale)
    cy = round(cell.position[1] * scale)
    ph  = cell.phenotype
    bp  = ph.body_parts
    sym = ph.symmetric_parts
    color = _cell_color(cell)

    # body_mass (slot 9) → enlarges the core circle
    body_r = max(2, round(ph.stats['size'] * 1.5))

    # shell (slot 10) → outer protective ring drawn first
    if 'shell' in bp:
        pygame.draw.circle(surf, color, (cx, cy), body_r + 2 + bp['shell'], 1)

    pygame.draw.circle(surf, color, (cx, cy), body_r)

    # 8 angular slots
    for part_type, slot_angle in _SLOT_ANGLES.items():
        count = bp.get(part_type, 0)
        if not count:
            continue
        _draw_part(surf, cx, cy, body_r, slot_angle, part_type, count, color)
        if part_type in sym:                         # KLK mirror
            _draw_part(surf, cx, cy, body_r, (slot_angle + 180) % 360,
                       part_type, count, color)


def _draw_part(surf, cx: int, cy: int, body_r: int,
               base_angle: int, part_type: str, count: int, color: tuple) -> None:
    n      = min(count, 4)
    spread = (n - 1) * 14          # ±14° per extra copy
    for i in range(n):
        a = base_angle if n == 1 else base_angle - spread / 2 + i * spread / (n - 1)
        _draw_single(surf, cx, cy, body_r, math.radians(a), part_type, color)


def _draw_single(surf, cx: int, cy: int, body_r: int,
                 rad: float, part_type: str, color: tuple) -> None:
    cr = math.cos(rad)
    sr = math.sin(rad)

    if part_type == 'spike':
        tip = (round(cx + cr * (body_r + 5)), round(cy + sr * (body_r + 5)))
        perp = rad + math.pi / 2
        bd   = body_r + 1
        b1 = (round(cx + cr * bd - math.cos(perp) * 2),
               round(cy + sr * bd - math.sin(perp) * 2))
        b2 = (round(cx + cr * bd + math.cos(perp) * 2),
               round(cy + sr * bd + math.sin(perp) * 2))
        pygame.draw.polygon(surf, color, [tip, b1, b2])

    elif part_type == 'plate':
        pts = [
            (round(cx + math.cos(rad + math.radians(-25 + j * 10)) * (body_r + 2)),
             round(cy + math.sin(rad + math.radians(-25 + j * 10)) * (body_r + 2)))
            for j in range(6)
        ]
        pygame.draw.lines(surf, color, False, pts, 2)

    elif part_type == 'eye':
        ex = round(cx + cr * (body_r + 2))
        ey = round(cy + sr * (body_r + 2))
        pygame.draw.circle(surf, (230, 230, 230), (ex, ey), 2)
        pygame.draw.circle(surf, (10,  10,  20),  (ex, ey), 1)

    elif part_type == 'flagellum':
        x0, y0 = cx + cr * body_r, cy + sr * body_r
        perp   = rad + math.pi / 2
        pts    = [(round(x0), round(y0))]
        for seg in range(3):
            sign = 1 if seg % 2 == 0 else -1
            x0 += cr * 2 + math.cos(perp) * sign * 1.5
            y0 += sr * 2 + math.sin(perp) * sign * 1.5
            pts.append((round(x0), round(y0)))
        pygame.draw.lines(surf, color, False, pts, 1)

    elif part_type == 'mouth_nutrient':
        pygame.draw.circle(surf, (50, 200, 80),
                           (round(cx + cr * (body_r + 2)),
                            round(cy + sr * (body_r + 2))), 2)

    elif part_type == 'mouth_cell':
        pygame.draw.circle(surf, (210, 55, 55),
                           (round(cx + cr * (body_r + 2)),
                            round(cy + sr * (body_r + 2))), 2)

    elif part_type == 'tentacle':
        t_dist = body_r + 7
        tx, ty = round(cx + cr * t_dist), round(cy + sr * t_dist)
        pygame.draw.line(surf, color,
                         (round(cx + cr * body_r), round(cy + sr * body_r)),
                         (tx, ty), 1)
        pygame.draw.circle(surf, color, (tx, ty), 2)

    elif part_type == 'fin':
        fx, fy  = cx + cr * (body_r + 1), cy + sr * (body_r + 1)
        tip     = (round(cx + cr * (body_r + 4)), round(cy + sr * (body_r + 4)))
        perp    = rad + math.pi / 2
        pygame.draw.line(surf, color,
                         (round(fx + math.cos(perp) * 1.5), round(fy + math.sin(perp) * 1.5)),
                         tip, 1)
        pygame.draw.line(surf, color,
                         (round(fx - math.cos(perp) * 1.5), round(fy - math.sin(perp) * 1.5)),
                         tip, 1)


# ── Visualizer class ──────────────────────────────────────────────────────────

class Visualizer:
    def __init__(self, seed: int = 42, speed: int = 1, max_ticks: int = 0):
        self.seed      = seed
        self.speed     = speed
        self.max_ticks = max_ticks

        self.world: World | None = None
        self.cells: list         = []
        self.tick                = 0

        self.pop_history:  list[int] = []
        self.pred_history: list[int] = []
        self.all_lineages: set       = set()

        self.peak_pop           = 0
        self.most_complex_cell  = None
        self.predation_evolved  = False

    # ── main loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        pygame.init()
        screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("DigitalGenesis v2")
        clock = pygame.time.Clock()

        font_sm = pygame.font.SysFont("Consolas", 13)
        font_md = pygame.font.SysFont("Consolas", 16)
        font_lg = pygame.font.SysFont("Consolas", 21, bold=True)

        random.seed(self.seed)
        Cell._next_id = 0
        self.world = World(seed=self.seed)
        ancestor   = Cell((100, 100), ANCESTOR)
        self.cells = [ancestor]
        self.all_lineages.add(ancestor.lineage_id)

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            if not running:
                break

            for _ in range(self.speed):
                if self.max_ticks > 0 and self.tick >= self.max_ticks:
                    running = False
                    break
                if not self.cells:
                    running = False
                    break
                self._sim_tick()

            self._render(screen, font_sm, font_md, font_lg)
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        self._print_summary()

    # ── simulation tick ───────────────────────────────────────────────────────

    def _sim_tick(self) -> None:
        self.world.tick(len(self.cells))

        cell_index = build_cell_index(self.cells)
        random.shuffle(self.cells)

        new_children: list = []
        for cell in self.cells:
            if cell.alive:
                new_children.extend(cell.tick(self.world, cell_index))

        self.cells = [c for c in self.cells if c.alive] + new_children

        for c in new_children:
            self.all_lineages.add(c.lineage_id)

        if 0 < len(self.cells) < 5:
            self.cells = _population_guardian(self.cells)
            for c in self.cells:
                self.all_lineages.add(c.lineage_id)

        if len(self.cells) > HARD_POPULATION_CAP:
            random.shuffle(self.cells)
            self.cells = self.cells[:HARD_POPULATION_CAP]

        self.tick += 1
        n = len(self.cells)
        if n > self.peak_pop:
            self.peak_pop = n

        preds = 0
        for c in self.cells:
            if c.phenotype.stats['cell_eat'] > 0:
                preds += 1
                self.predation_evolved = True
            if (self.most_complex_cell is None or
                    len(c.dna) > len(self.most_complex_cell.dna)):
                self.most_complex_cell = c

        self.pop_history.append(n)
        self.pred_history.append(preds)
        if len(self.pop_history) > POP_HISTORY_LEN:
            self.pop_history.pop(0)
            self.pred_history.pop(0)

    # ── rendering ─────────────────────────────────────────────────────────────

    def _render(self, screen, font_sm, font_md, font_lg) -> None:
        screen.fill(C_BG)
        self._draw_world(screen)
        self._draw_panel(screen, font_sm, font_md, font_lg)

    def _draw_world(self, screen) -> None:
        for cell in self.cells:
            _draw_cell(screen, cell, SCALE)

    def _draw_panel(self, screen, font_sm, font_md, font_lg) -> None:
        pygame.draw.rect(screen, C_PANEL_BG, pygame.Rect(PANEL_X, 0, PANEL_W, WINDOW_H))
        pygame.draw.line(screen, C_DIVIDER, (PANEL_X, 0), (PANEL_X, WINDOW_H), 1)

        n       = len(self.cells)
        preds   = sum(1 for c in self.cells if c.phenotype.stats['cell_eat'] > 0)
        live_lin = len(set(c.lineage_id for c in self.cells)) if self.cells else 0
        avg_dna  = (sum(len(c.dna) for c in self.cells) / n) if n else 0.0
        avg_e    = (sum(c.energy    for c in self.cells) / n) if n else 0.0
        pred_pct = f" ({preds / n * 100:.0f}%)" if n else ""

        px0 = PANEL_X + 14
        y   = 14

        screen.blit(font_lg.render("DIGITAL GENESIS", True, C_HEADER), (px0, y))
        y += 32

        col2  = px0 + 155
        row_h = 22
        for label, value in [
            ("Tick",             f"{self.tick:,}"),
            ("Population",       f"{n:,}"),
            ("Peak pop",         f"{self.peak_pop:,}"),
            ("Lineages (live)",  f"{live_lin:,}"),
            ("Lineages (ever)",  f"{len(self.all_lineages):,}"),
            ("Predators",        f"{preds:,}{pred_pct}"),
            ("Avg DNA length",   f"{avg_dna:.1f}"),
            ("Avg energy",       f"{avg_e:.1f}"),
        ]:
            screen.blit(font_md.render(label + ":", True, C_LABEL), (px0, y))
            screen.blit(font_md.render(value,       True, C_TEXT),  (col2, y))
            y += row_h

        y += 6
        pygame.draw.line(screen, C_DIVIDER, (px0, y), (WINDOW_W - 14, y))
        y += 14

        screen.blit(font_sm.render("Population (green) / Predators (red)", True, C_LABEL),
                    (px0, y))
        y += 16

        graph_w = PANEL_W - 28
        graph_h = 170
        graph_rect = pygame.Rect(px0, y, graph_w, graph_h)
        pygame.draw.rect(screen, C_GRAPH_BG,  graph_rect)
        pygame.draw.rect(screen, C_DIVIDER,   graph_rect, 1)

        if len(self.pop_history) >= 2:
            max_val  = max(max(self.pop_history), 1)
            hist_len = len(self.pop_history)

            def _pt(i, v):
                gx = px0 + round(i / (hist_len - 1) * (graph_w - 2)) + 1
                gy = y + graph_h - 2 - round(v / max_val * (graph_h - 4))
                return gx, gy

            pygame.draw.lines(screen, C_POP_LINE,  False,
                              [_pt(i, v) for i, v in enumerate(self.pop_history)],  1)
            pygame.draw.lines(screen, C_PRED_LINE, False,
                              [_pt(i, v) for i, v in enumerate(self.pred_history)], 1)

        y += graph_h + 12

        if self.most_complex_cell is not None:
            mc = self.most_complex_cell
            screen.blit(font_sm.render(f"Longest genome: {len(mc.dna)} letters",
                                       True, C_LABEL), (px0, y))
            y += 16
            bp_str = "  ".join(
                f"{pt[:3]}:{cnt}" for pt, cnt in sorted(mc.phenotype.body_parts.items()) if cnt)
            if bp_str:
                screen.blit(font_sm.render(bp_str, True, (90, 100, 118)), (px0, y))
            y += 16

        footer = f"--speed {self.speed}   --seed {self.seed}"
        if self.predation_evolved:
            footer += "   [predation ACTIVE]"
        screen.blit(font_sm.render(footer, True, (75, 85, 105)), (px0, WINDOW_H - 20))

    def _print_summary(self) -> None:
        print()
        print("=" * 58)
        print("SIMULATION ENDED")
        print(f"  Total ticks run:        {self.tick:,}")
        print(f"  Peak population:        {self.peak_pop:,}")
        print(f"  Lineages ever existed:  {len(self.all_lineages):,}")
        print(f"  Predation evolved:      {'YES' if self.predation_evolved else 'NO'}")
        if self.most_complex_cell is not None:
            c = self.most_complex_cell
            print(f"  Longest genome:         {len(c.dna)} letters")
            for pt, cnt in sorted(c.phenotype.body_parts.items()):
                if cnt:
                    print(f"    {pt:<20} x{cnt}")
        print("=" * 58)
