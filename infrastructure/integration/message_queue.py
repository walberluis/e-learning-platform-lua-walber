"""
Message Queue integration for asynchronous processing.
Infrastructure Layer - Integration Package
"""

import asyncio
import json
from typing import Dict, Callable, Optional, Any
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class MessageQueue:
    """
    Simple in-memory message queue implementation.
    In production, this would be replaced with Redis, RabbitMQ, or similar.
    """
    
    def __init__(self):
        self.queues: Dict[str, list] = {}
        self.subscribers: Dict[str, list] = {}
        self.processing = False
    
    async def publish(self, queue_name: str, message: Dict[str, Any]) -> bool:
        """
        Publish a message to a queue.
        
        Args:
            queue_name: Name of the queue
            message: Message data to publish
            
        Returns:
            True if message was published successfully
        """
        try:
            if queue_name not in self.queues:
                self.queues[queue_name] = []
            
            # Add timestamp and unique ID to message
            enriched_message = {
                "id": f"{queue_name}_{datetime.utcnow().timestamp()}",
                "timestamp": datetime.utcnow().isoformat(),
                "data": message
            }
            
            self.queues[queue_name].append(enriched_message)
            
            # Notify subscribers
            await self._notify_subscribers(queue_name, enriched_message)
            
            return True
            
        except Exception as e:
            print(f"Error publishing message to {queue_name}: {e}")
            return False
    
    async def subscribe(self, queue_name: str, callback: Callable) -> bool:
        """
        Subscribe to a queue with a callback function.
        
        Args:
            queue_name: Name of the queue to subscribe to
            callback: Function to call when message is received
            
        Returns:
            True if subscription was successful
        """
        try:
            if queue_name not in self.subscribers:
                self.subscribers[queue_name] = []
            
            self.subscribers[queue_name].append(callback)
            return True
            
        except Exception as e:
            print(f"Error subscribing to {queue_name}: {e}")
            return False
    
    async def consume(self, queue_name: str, max_messages: int = 10) -> list:
        """
        Consume messages from a queue.
        
        Args:
            queue_name: Name of the queue
            max_messages: Maximum number of messages to consume
            
        Returns:
            List of consumed messages
        """
        if queue_name not in self.queues:
            return []
        
        messages = self.queues[queue_name][:max_messages]
        self.queues[queue_name] = self.queues[queue_name][max_messages:]
        
        return messages
    
    async def _notify_subscribers(self, queue_name: str, message: Dict) -> None:
        """Notify all subscribers of a queue about new message."""
        if queue_name in self.subscribers:
            for callback in self.subscribers[queue_name]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    print(f"Error in subscriber callback: {e}")
    
    def get_queue_stats(self) -> Dict[str, Dict]:
        """Get statistics about all queues."""
        stats = {}
        for queue_name, messages in self.queues.items():
            stats[queue_name] = {
                "message_count": len(messages),
                "subscriber_count": len(self.subscribers.get(queue_name, [])),
                "oldest_message": messages[0]["timestamp"] if messages else None,
                "newest_message": messages[-1]["timestamp"] if messages else None
            }
        return stats

class NotificationService:
    """
    Notification service for sending various types of notifications.
    Uses message queue for asynchronous processing.
    """
    
    def __init__(self, message_queue: MessageQueue):
        self.message_queue = message_queue
        self.notification_types = {
            "learning_reminder": self._send_learning_reminder,
            "progress_update": self._send_progress_update,
            "recommendation_ready": self._send_recommendation_notification,
            "course_completion": self._send_completion_notification
        }
    
    async def send_notification(self, notification_type: str, recipient: str, data: Dict) -> bool:
        """
        Send a notification through the message queue.
        
        Args:
            notification_type: Type of notification
            recipient: Recipient identifier (email, user_id, etc.)
            data: Notification data
            
        Returns:
            True if notification was queued successfully
        """
        notification_message = {
            "type": notification_type,
            "recipient": recipient,
            "data": data,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return await self.message_queue.publish("notifications", notification_message)
    
    async def process_notifications(self) -> None:
        """Process pending notifications from the queue."""
        notifications = await self.message_queue.consume("notifications", max_messages=50)
        
        for notification in notifications:
            try:
                notification_data = notification["data"]
                notification_type = notification_data["type"]
                
                if notification_type in self.notification_types:
                    await self.notification_types[notification_type](notification_data)
                else:
                    print(f"Unknown notification type: {notification_type}")
                    
            except Exception as e:
                print(f"Error processing notification: {e}")
    
    async def _send_learning_reminder(self, data: Dict) -> None:
        """Send learning reminder notification."""
        print(f"Learning reminder sent to {data['recipient']}: {data['data'].get('message', 'Time to continue learning!')}")
    
    async def _send_progress_update(self, data: Dict) -> None:
        """Send progress update notification."""
        progress = data['data'].get('progress', 0)
        print(f"Progress update sent to {data['recipient']}: {progress}% completed")
    
    async def _send_recommendation_notification(self, data: Dict) -> None:
        """Send recommendation ready notification."""
        print(f"New recommendations available for {data['recipient']}")
    
    async def _send_completion_notification(self, data: Dict) -> None:
        """Send course completion notification."""
        course = data['data'].get('course_name', 'Unknown Course')
        print(f"Congratulations! {data['recipient']} completed {course}")

class AnalyticsService:
    """
    Analytics service for tracking user behavior and system metrics.
    Uses message queue for real-time analytics processing.
    """
    
    def __init__(self, message_queue: MessageQueue):
        self.message_queue = message_queue
        self.metrics = {
            "user_actions": 0,
            "content_views": 0,
            "recommendations_generated": 0,
            "chatbot_interactions": 0
        }
    
    async def track_event(self, event_type: str, user_id: Optional[int], data: Dict) -> bool:
        """
        Track an analytics event.
        
        Args:
            event_type: Type of event to track
            user_id: User ID (if applicable)
            data: Event data
            
        Returns:
            True if event was tracked successfully
        """
        event_message = {
            "event_type": event_type,
            "user_id": user_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Update local metrics
        if event_type in self.metrics:
            self.metrics[event_type] += 1
        
        return await self.message_queue.publish("analytics", event_message)
    
    async def process_analytics(self) -> None:
        """Process analytics events from the queue."""
        events = await self.message_queue.consume("analytics", max_messages=100)
        
        for event in events:
            try:
                event_data = event["data"]
                # In production, this would store to analytics database
                print(f"Analytics: {event_data['event_type']} by user {event_data.get('user_id', 'anonymous')}")
                
            except Exception as e:
                print(f"Error processing analytics event: {e}")
    
    def get_metrics(self) -> Dict[str, int]:
        """Get current metrics."""
        return self.metrics.copy()

# Global instances
message_queue = MessageQueue()
notification_service = NotificationService(message_queue)
analytics_service = AnalyticsService(message_queue)

