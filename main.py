import argparse


def main():
    parser = argparse.ArgumentParser(
        description="DigitalGenesis — open-ended evolution simulator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--headless", action="store_true",
                        help="run without Pygame visualization")
    parser.add_argument("--speed", type=int, default=1, metavar="N",
                        help="ticks simulated per rendered frame (1=normal, 50=fast)")
    parser.add_argument("--seed", type=int, default=42,
                        help="random seed")
    parser.add_argument("--ticks", type=int, default=0,
                        help="stop after N ticks (0 = run until window closed)")
    parser.add_argument("--interval", type=int, default=50,
                        help="headless: print stats every N ticks")
    args = parser.parse_args()

    if args.headless:
        from simulation import run
        run(
            seed=args.seed,
            max_ticks=args.ticks if args.ticks > 0 else 100_000,
            print_interval=args.interval,
        )
    else:
        from visualizer import Visualizer
        vis = Visualizer(seed=args.seed, speed=args.speed, max_ticks=args.ticks)
        vis.run()


if __name__ == "__main__":
    main()
