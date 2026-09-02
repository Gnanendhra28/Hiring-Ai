import asyncio
import signal
from app.core.logging import logger
from app.infrastructure.workers.pipeline_worker import PipelineWorker

async def main():
    logger.info("[WorkerDaemon] Starting Hiring AI asynchronous pipeline worker daemon...")
    worker = PipelineWorker()
    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("[WorkerDaemon] Termination signal received. Stopping worker daemon...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            pass

    logger.info("[WorkerDaemon] Worker daemon online and listening for events.")
    await stop_event.wait()
    logger.info("[WorkerDaemon] Worker daemon gracefully shutdown.")

if __name__ == "__main__":
    asyncio.run(main())
