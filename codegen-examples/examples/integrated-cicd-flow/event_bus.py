"""Event bus for the integrated CI/CD flow."""

import asyncio
import logging
from typing import Callable, Dict, List, Optional

from models import Event, EventType

logger = logging.getLogger(__name__)


class EventBus:
    """Simple event bus for communication between components."""

    def __init__(self):
        """Initialize the event bus."""
        self.subscribers: Dict[EventType, List[Callable]] = {}
        self.event_queue = asyncio.Queue()
        self.running = False

    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """Subscribe to an event type.

        Args:
            event_type: The type of event to subscribe to
            callback: The function to call when the event occurs
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        logger.info(f"Subscribed to {event_type}")

    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """Unsubscribe from an event type.

        Args:
            event_type: The type of event to unsubscribe from
            callback: The function to remove from the subscribers
        """
        if event_type in self.subscribers and callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
            logger.info(f"Unsubscribed from {event_type}")

    async def publish(self, event: Event) -> None:
        """Publish an event to the bus.

        Args:
            event: The event to publish
        """
        await self.event_queue.put(event)
        logger.info(f"Published event: {event.type}")

    async def start(self) -> None:
        """Start the event bus."""
        self.running = True
        logger.info("Event bus started")
        while self.running:
            try:
                event = await self.event_queue.get()
                await self._process_event(event)
                self.event_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    async def stop(self) -> None:
        """Stop the event bus."""
        self.running = False
        logger.info("Event bus stopped")

    async def _process_event(self, event: Event) -> None:
        """Process an event by calling all subscribers.

        Args:
            event: The event to process
        """
        if event.type in self.subscribers:
            for callback in self.subscribers[event.type]:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Error in subscriber callback: {e}")


# Global event bus instance
event_bus = EventBus()