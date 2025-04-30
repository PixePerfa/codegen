"""Event bus for communication between components in the integrated CI/CD flow."""

import logging
import threading
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Set

from shared.models import Event, EventType

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class EventBus:
    """Event bus for communication between components.

    This class implements a simple publish-subscribe pattern for event-driven
    communication between components in the CI/CD flow.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Create a singleton instance of the event bus."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EventBus, cls).__new__(cls)
                cls._instance._subscribers = defaultdict(set)
                cls._instance._event_history = []
                cls._instance._max_history = 100
            return cls._instance

    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Subscribe to events of a specific type.

        Args:
            event_type: Type of events to subscribe to
            callback: Function to call when an event of this type is published
        """
        with self._lock:
            self._subscribers[event_type].add(callback)
            logger.debug(f"Subscribed to {event_type} events")

    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Unsubscribe from events of a specific type.

        Args:
            event_type: Type of events to unsubscribe from
            callback: Function to remove from subscribers
        """
        with self._lock:
            if event_type in self._subscribers and callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from {event_type} events")

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers.

        Args:
            event: Event to publish
        """
        with self._lock:
            # Add event to history
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

            # Notify subscribers
            subscribers = self._subscribers.get(event.type, set())
            logger.info(f"Publishing {event.type} event to {len(subscribers)} subscribers")

        # Call subscribers outside the lock to avoid deadlocks
        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event subscriber: {e}")

    def get_event_history(self, event_type: Optional[EventType] = None, limit: int = 10) -> List[Event]:
        """Get recent events from history.

        Args:
            event_type: Optional filter for event type
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        with self._lock:
            if event_type:
                events = [e for e in self._event_history if e.type == event_type]
            else:
                events = self._event_history.copy()
            
            # Return most recent events first
            return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]

    def clear_history(self) -> None:
        """Clear event history."""
        with self._lock:
            self._event_history = []
            logger.info("Event history cleared")

    @property
    def subscriber_count(self) -> Dict[EventType, int]:
        """Get the number of subscribers for each event type.

        Returns:
            Dictionary mapping event types to subscriber counts
        """
        with self._lock:
            return {event_type: len(subscribers) for event_type, subscribers in self._subscribers.items()}


# Global event bus instance
event_bus = EventBus()