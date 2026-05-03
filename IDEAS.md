# DigitalGenesis — Ideas Backlog

## Tier 1: Core Identity (the project isn't real without these)

1. **DNA-style genome (THE BIG ONE)** — Replace the current gene-list system 
   with a letter-string genome (pool of A–K, codons of 2–4 letters). The sim 
   reads the string, chops it into chunks, each chunk maps to an action. 
   Nothing hardcoded. Mutations swap/insert/delete/duplicate letters. This 
   is the v2 rebuild and the heart of the project.

2. **Different-looking creatures** — Cells render as actual shapes/sprites 
   based on their genome, not dots. Body parts emerge from genes. A creature 
   with high SIZE looks bigger; one with sense genes has eye-spots; 
   predators look different from prey. Visual diversity = visceral demo.

3. **Food moves** — Nutrients aren't static tiles. Food is its own simple 
   organism (algae? plankton?) that drifts, multiplies, and can be hunted. 
   Creates real chase dynamics instead of "stand on tile, absorb."

## Tier 2: Ecosystem Depth (turns the sim into a world)

4. **Terrain / biomes** — Water, mountains, forests, deserts. Different 
   regions select for different traits. Migration becomes meaningful.

5. **Day/night cycle** — Predators hunt at night, prey forage by day. 
   Forces evolution of vision, sleep, behavioral specialization.

6. **Weather and seasons** — Winter kills the weak. Periodic pressure 
   accelerates evolution and prevents stagnation.

7. **Mass extinction events** — Periodic disasters wipe regions. Forces 
   genetic diversity to actually matter for survival.

8. **Migration** — Cells follow seasonal food patterns. Emerges naturally 
   from seasons + terrain.

## Tier 3: Emergent Behaviors (the wow moments)

9. **Pheromone trails** — Cells leave smells behind. Other cells can 
   follow or avoid. Foundation for every social behavior below.

10. **Pack behavior** — Cells flock together for defense. Emerges from 
    pheromones + selection pressure.

11. **Sexual reproduction as evolved trait** — Not hardcoded. Mutation 
    invents it, selection rewards it.

12. **Symbiosis** — Two cell types help each other survive. Emerges 
    from co-evolution.

13. **Parasites** — Small cells live inside bigger cells. Whole new 
    evolutionary game.

14. **Camouflage** — Cells match background color. Co-evolves with 
    predator vision.

15. **Memory** — Cells remember where food was. Beginnings of 
    intelligence.

16. **Generational memory / instincts** — Behaviors passed via genome. 
    Long-term cultural evolution.

## Tier 4: Advanced (v3+, real research territory)

17. **Signaling / proto-speech** — Cells emit signals other cells react 
    to. Communication evolves.

18. **Tool use** — Cells can pick up and carry resources.

19. **Diseases** — Spread between cells. Pathogen-host evolutionary 
    arms race.

20. **Aging mechanics** — Old cells slower but smarter. Trade-offs 
    create new strategies.

21. **Territory marking** — Cells claim space. Foundation for 
    cooperation/conflict.

22. **Sleep** — Cells need rest, vulnerable while sleeping. Tradeoff 
    with foraging time.

23. **Fire / destruction events** — Localized chaos that creates 
    evolutionary pressure.

## Rules for Myself

- Lock v1 before touching ANY of this.
- One idea per branch. Never tweak two systems at once.
- Write the spec before coding. No vibe building from this list.
- Add to IDEAS.md instead of building when I get a new idea mid-flight.
- "Done" means the success criteria are met. No moving the goalposts.