import argparse
import logging
import sys
from pathlib import Path

from src.config.settings import AppConfig
from src.container import Container

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("AutoBotApp")


def main() -> None:
    parser = argparse.ArgumentParser(description="Facebook Auto-Comment/Reply Bot (Clean Architecture)")
    parser.add_argument(
        "--flow",
        choices=["a", "b"],
        default="a",
        help="Flow to run: 'a' for Post Comment, 'b' for Thread Reply",
    )
    parser.add_argument(
        "--config",
        default="configs/settings.yaml",
        help="Path to settings YAML file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without making actual inputs",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    config = AppConfig.load_from_yaml(config_path)
    if args.dry_run:
        from dataclasses import replace
        config = replace(config, dry_run=True)

    from src.infrastructure.input.fail_safe import default_fail_safe, EmergencyStopException

    logger.info("Initializing AutoBot Container (Flow: %s, DryRun: %s)...", args.flow.upper(), config.dry_run)
    logger.info("Emergency Fail-Safe is ACTIVE: Press [ESC] at any time to abort immediately.")

    container = Container(config=config)

    try:
        with default_fail_safe:
            if args.flow == "a":
                logger.info("Starting Flow A (Comment Feed)...")
                use_case = container.create_feed_comment_use_case()
                result = use_case.execute_step()
                logger.info("Flow A step execution finished. Success: %s", result)
            else:
                logger.info("Starting Flow B (Reply Thread)...")
                use_case = container.create_thread_reply_use_case()
                result = use_case.execute_step(post_context_text="Mẫu bài viết thảo luận...")
                logger.info("Flow B step execution finished. Success: %s", result)
    except EmergencyStopException:
        logger.warning("[EMERGENCY STOP] Kill switch activated by user (ESC pressed or mouse in corner). Exiting gracefully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
