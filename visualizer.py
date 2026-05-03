import colorsys
import random
import pygame
from world import World
from genome import Genome, Gene
from cell import Cell
from simulation import ANCESTOR_GENOME

WINDOW_W = 1200
WINDOW_H = 720
WORLD_PX = 720          # left square: world view
PANEL_X = WORLD_PX
PANEL_W = WINDOW_W - WORLD_PX
SCALE = WORLD_PX / 200  # pixels per grid unit

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

_color_cache: dict = {}


def _lineage_color(lineage_id: int) -> tuple:
    if lineage_id not in _color_cache:
        hue = (lineage_id * 137.508) % 360
        r, g, b = colorsys.hsv_to_rgb(hue / 360.0, 0.75, 0.95)
        _color_cache[lineage_id] = (int(r * 255), int(g * 255), int(b * 255))
    return _color_cache[lineage_id]


class Visualizer:
    def __init__(self, seed: int = 42, speed: int = 1, max_ticks: int = 0):
        self.seed = seed
        self.speed = speed
        self.max_ticks = max_ticks

        self.world: World | None = None
        self.cells: list = []
        self.tick = 0

        self.pop_history: list[int] = []
        self.pred_history: list[int] = []

        self.peak_pop = 0
        self.all_lineages: set = set()
        self.most_complex_genome = None
        self.predation_evolved = False

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("DigitalGenesis")
        clock = pygame.time.Clock()

        font_sm = pygame.font.SysFont("Consolas", 13)
        font_md = pygame.font.SysFont("Consolas", 16)
        font_lg = pygame.font.SysFont("Consolas", 21, bold=True)

        random.seed(self.seed)
        Cell._next_id = 0
        self.world = World(seed=self.seed)
        ancestor = Cell(
            (100, 100),
            Genome([Gene(g.type, g.value) for g in ANCESTOR_GENOME.genes]),
        )
        self.cells = [ancestor]

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            if not running:
                break

            for _ in range(self.speed):
                if not self.cells:
                    running = False
                    break
                if self.max_ticks > 0 and self.tick >= self.max_ticks:
                    running = False
                    break
                self._sim_tick()

            self._render(screen, font_sm, font_md, font_lg)
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        self._print_summary()

    # ------------------------------------------------------------------ #

    def _sim_tick(self):
        self.world.tick(len(self.cells))
        random.shuffle(self.cells)

        new_children = []
        for cell in self.cells:
            if cell.alive:
                child = cell.tick(self.world, self.cells)
                if child is not None:
                    new_children.append(child)

        self.cells = [c for c in self.cells if c.alive] + new_children
        self.tick += 1

        n = len(self.cells)
        preds = sum(1 for c in self.cells if c.genome.get_trait("DIET_CELL") > 0)

        if n > self.peak_pop:
            self.peak_pop = n

        for c in self.cells:
            self.all_lineages.add(c.lineage_id)
            if self.most_complex_genome is None or len(c.genome) > len(self.most_complex_genome):
                self.most_complex_genome = c.genome
            if c.genome.get_trait("DIET_CELL") > 0:
                self.predation_evolved = True

        self.pop_history.append(n)
        self.pred_history.append(preds)
        if len(self.pop_history) > POP_HISTORY_LEN:
            self.pop_history.pop(0)
            self.pred_history.pop(0)

    # ------------------------------------------------------------------ #

    def _render(self, screen, font_sm, font_md, font_lg):
        screen.fill(C_BG)
        self._draw_world(screen)
        self._draw_panel(screen, font_sm, font_md, font_lg)

    def _draw_world(self, screen):
        for cell in self.cells:
            x, y = cell.position
            px = int(x * SCALE)
            py = int(y * SCALE)
            size = max(0.3, cell.genome.get_trait("SIZE"))
            radius = max(1, round(size * 1.8))
            pygame.draw.circle(screen, _lineage_color(cell.lineage_id), (px, py), radius)

    def _draw_panel(self, screen, font_sm, font_md, font_lg):
        panel_rect = pygame.Rect(PANEL_X, 0, PANEL_W, WINDOW_H)
        pygame.draw.rect(screen, C_PANEL_BG, panel_rect)
        pygame.draw.line(screen, C_DIVIDER, (PANEL_X, 0), (PANEL_X, WINDOW_H), 1)

        n = len(self.cells)
        preds = sum(1 for c in self.cells if c.genome.get_trait("DIET_CELL") > 0)
        lineages_now = len(set(c.lineage_id for c in self.cells)) if self.cells else 0
        avg_genes = (sum(len(c.genome) for c in self.cells) / n) if n else 0.0
        avg_energy = (sum(c.energy for c in self.cells) / n) if n else 0.0
        pred_pct = f" ({preds / n * 100:.0f}%)" if n else ""

        px0 = PANEL_X + 14
        y = 14

        hdr = font_lg.render("DIGITAL GENESIS", True, C_HEADER)
        screen.blit(hdr, (px0, y))
        y += 32

        rows = [
            ("Tick",           f"{self.tick:,}"),
            ("Population",     f"{n:,}"),
            ("Peak pop",       f"{self.peak_pop:,}"),
            ("Lineages (live)",f"{lineages_now:,}"),
            ("Lineages (ever)",f"{len(self.all_lineages):,}"),
            ("Predators",      f"{preds:,}{pred_pct}"),
            ("Avg genome len", f"{avg_genes:.2f}"),
            ("Avg energy",     f"{avg_energy:.1f}"),
        ]

        col1 = px0
        col2 = px0 + 155
        row_h = 22
        for label, value in rows:
            screen.blit(font_md.render(label + ":", True, C_LABEL),  (col1, y))
            screen.blit(font_md.render(value,       True, C_TEXT),   (col2, y))
            y += row_h

        # --- separator ---
        y += 6
        pygame.draw.line(screen, C_DIVIDER, (px0, y), (WINDOW_W - 14, y))
        y += 14

        # --- population graph ---
        screen.blit(font_sm.render("Population (green) / Predators (red)", True, C_LABEL), (px0, y))
        y += 16

        graph_w = PANEL_W - 28
        graph_h = 170
        graph_rect = pygame.Rect(px0, y, graph_w, graph_h)
        pygame.draw.rect(screen, C_GRAPH_BG, graph_rect)
        pygame.draw.rect(screen, C_DIVIDER, graph_rect, 1)

        if len(self.pop_history) >= 2:
            max_val = max(max(self.pop_history), 1)
            hist_len = len(self.pop_history)

            def to_graph_pt(i, val):
                gx = px0 + round(i / (hist_len - 1) * (graph_w - 2)) + 1
                gy = y + graph_h - 2 - round(val / max_val * (graph_h - 4))
                return gx, gy

            pop_pts  = [to_graph_pt(i, v) for i, v in enumerate(self.pop_history)]
            pred_pts = [to_graph_pt(i, v) for i, v in enumerate(self.pred_history)]
            pygame.draw.lines(screen, C_POP_LINE,  False, pop_pts,  1)
            pygame.draw.lines(screen, C_PRED_LINE, False, pred_pts, 1)

        y += graph_h + 12

        # --- most complex genome ever ---
        if self.most_complex_genome:
            mc_text = f"Most complex genome: {len(self.most_complex_genome)} genes"
            screen.blit(font_sm.render(mc_text, True, C_LABEL), (px0, y))
            y += 16
            # show gene type breakdown in two columns
            types = {}
            for g in self.most_complex_genome.genes:
                types[g.type] = types.get(g.type, 0) + 1
            parts = [f"{t[0]}{t[1:3].lower()}:{cnt}" for t, cnt in sorted(types.items())]
            detail = "  ".join(parts)
            screen.blit(font_sm.render(detail, True, (90, 100, 118)), (px0, y))
            y += 16

        # --- footer ---
        speed_text = f"--speed {self.speed}   --seed {self.seed}"
        if self.predation_evolved:
            speed_text += "   [predation ACTIVE]"
        screen.blit(font_sm.render(speed_text, True, (75, 85, 105)), (px0, WINDOW_H - 20))

    # ------------------------------------------------------------------ #

    def _print_summary(self):
        print()
        print("=" * 58)
        print("SIMULATION ENDED")
        print(f"  Total ticks run:        {self.tick:,}")
        print(f"  Peak population:        {self.peak_pop:,}")
        print(f"  Lineages ever existed:  {len(self.all_lineages):,}")
        print(f"  Predation evolved:      {'YES' if self.predation_evolved else 'NO'}")
        if self.most_complex_genome is not None:
            g = self.most_complex_genome
            print(f"  Most complex genome:    {len(g)} genes")
            for gene in g.genes:
                print(f"    {gene.type:<26} {gene.value:.3f}")
        print("=" * 58)
