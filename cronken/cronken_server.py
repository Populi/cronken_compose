import asyncio
import signal
import os
from typing import Any

from cronken import Cronken

test_jobs = {
    "minutely": {
        "cron_args": {
            "cronstring": "* * * * *"
        },
        "job_args": {
            "cmd": "echo 'minutely job'",
            "lock": True,
            "ttl": 10
        }
    }
}


REQUIRED_CONFIGS = ["redis_info"]
ALL_CONFIGS = {
    "namespace": "{cronken}",
    "log_level": "DEBUG",
    "heartbeat_cadence": 30,
    "output_cadence": 5,
    "max_finalized_output_lines": 10,
    "perjob_results_limit": 1000,
    "general_results_limit": 10000,
    "output_buffer_size": 1024,
    "pubsub_timeout": 30,
    "job_shell": "/bin/bash"
}
ALL_CONFIGS.update({k: None for k in REQUIRED_CONFIGS})


def get_config_value(prefix: str, key: str, default: Any):
    env_value = os.environ.get(f"{prefix}_{key.upper()}", None)
    if env_value is None and default is None:
        raise Exception(f"Required env var '{prefix}_{key.upper()}' not set")

    # Cast env_value to the correct type, if it exists
    if env_value is not None:
        if key == "redis_info":
            # Special processing for the redis node(s) to convert from "foo:1234,bar:5678" to structured data
            env_value = [
                {"host": node.split(":")[0], "port": int(node.split(":")[1])}
                for node in env_value.split(",")
            ]
        elif isinstance(default, bool):
            # bools in Python are instances of both bool and int, so this check needs to be before the>
            env_value = env_value.lower() == "true"
        elif isinstance(default, int):
            env_value = int(env_value)

    return env_value if env_value is not None else default


def get_config(prefix: str, defaults: dict) -> dict:
    return {k: get_config_value(prefix, k, defaults[k]) for k in defaults}


# Adapted from https://github.com/Populi/cronken/blob/master/example_server.py
async def main():
    loop = asyncio.get_running_loop()
    cronken = Cronken(**get_config("CRONKEN", ALL_CONFIGS))

    async def graceful_shutdown(sig: signal.Signals):
        cronken.logger.error(f"Received signal {sig}, gracefully shutting down...")
        await cronken.cleanup()
        cronken.logger.error("Finished cleanup")

    # Jobs persist in redis and are automatically loaded on cronken startup
    cronken.logger.info("Starting cronken...")
    cronken_lifetime = await cronken.start()
    # Schedule cleanup on SIGINT
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(graceful_shutdown(sig)))
    num_jobs = await cronken.num_jobs()
    if not num_jobs:
        # Load a default job in if there aren't already jobs defined
        cronken.logger.info("Setting jobs...")
        await cronken.set_jobs(test_jobs)
        # Now that we've overwritten the jobs, reload them
        cronken.logger.info("Reloading jobs...")
        await cronken.reload_jobs()
    cronken.logger.info("Running...")
    await cronken_lifetime


if __name__ == '__main__':
    asyncio.run(main())
