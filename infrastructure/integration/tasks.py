"""
Celery background tasks.
Infrastructure Layer - Integration Package
"""

from celery import current_task
from infrastructure.integration.celery_app import celery_app
from infrastructure.integration.gemini_client import gemini_client
from infrastructure.integration.message_queue import notification_service, analytics_service
from data_access.repositories.usuario_repository import UsuarioRepository
from data_access.repositories.desempenho_repository import DesempenhoRepository
from data_access.external_services.content_provider import notification_api
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any

@celery_app.task(bind=True, max_retries=3)
def send_email(self, recipient: str, subject: str, content: str, template: str = None):
    """
    Send email notification task.
    
    Args:
        recipient: Email recipient
        subject: Email subject
        content: Email content
        template: Email template name
    """
    try:
        # Use async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            notification_api.send_email_notification(recipient, subject, content, template)
        )
        
        loop.close()
        
        if result.get('status') == 'sent':
            return {
                'status': 'success',
                'message_id': result.get('message_id'),
                'recipient': recipient
            }
        else:
            raise Exception(f"Email sending failed: {result.get('error', 'Unknown error')}")
            
    except Exception as exc:
        print(f"Email task failed: {exc}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        
        return {
            'status': 'failed',
            'error': str(exc),
            'recipient': recipient
        }

@celery_app.task(bind=True, max_retries=2)
def generate_recommendations(self, user_id: int):
    """
    Generate AI recommendations for a user.
    
    Args:
        user_id: User ID to generate recommendations for
    """
    try:
        from business.ai.recommendation_engine import RecommendationEngine
        
        # Use async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        recommendation_engine = RecommendationEngine()
        result = loop.run_until_complete(
            recommendation_engine.generate_personalized_recommendations(user_id)
        )
        
        loop.close()
        
        if result.get('success'):
            # Store recommendations in cache or database
            # For now, just return the result
            return {
                'status': 'success',
                'user_id': user_id,
                'recommendations_count': len(result.get('structured_recommendations', {}).get('content_recommendations', [])),
                'generated_at': datetime.utcnow().isoformat()
            }
        else:
            raise Exception(f"Recommendation generation failed: {result.get('error')}")
            
    except Exception as exc:
        print(f"Recommendation generation task failed: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300 * (2 ** self.request.retries), exc=exc)
        
        return {
            'status': 'failed',
            'error': str(exc),
            'user_id': user_id
        }

@celery_app.task
def process_analytics(data: Dict[str, Any]):
    """
    Process analytics data in background.
    
    Args:
        data: Analytics data to process
    """
    try:
        # Use async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Track the analytics event
        loop.run_until_complete(
            analytics_service.track_event(
                data.get('event_type'),
                data.get('user_id'),
                data.get('event_data', {})
            )
        )
        
        loop.close()
        
        return {
            'status': 'success',
            'event_type': data.get('event_type'),
            'processed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        print(f"Analytics processing task failed: {exc}")
        return {
            'status': 'failed',
            'error': str(exc)
        }

@celery_app.task
def generate_daily_recommendations():
    """
    Generate daily recommendations for all active users.
    Scheduled task that runs daily.
    """
    try:
        usuario_repository = UsuarioRepository()
        
        # Use async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Get active users (users who have been active in the last 7 days)
        active_users = loop.run_until_complete(
            usuario_repository.get_active_users(days=7)
        )
        
        loop.close()
        
        # Queue recommendation generation for each active user
        recommendation_tasks = []
        for user in active_users:
            task = generate_recommendations.delay(user.id)
            recommendation_tasks.append(task.id)
        
        return {
            'status': 'success',
            'active_users_count': len(active_users),
            'recommendation_tasks': recommendation_tasks,
            'generated_at': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        print(f"Daily recommendations task failed: {exc}")
        return {
            'status': 'failed',
            'error': str(exc)
        }

@celery_app.task
def process_daily_analytics():
    """
    Process daily analytics and generate insights.
    Scheduled task that runs hourly.
    """
    try:
        desempenho_repository = DesempenhoRepository()
        
        # Use async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Get top performers for the day
        top_performers = loop.run_until_complete(
            desempenho_repository.get_top_performers(limit=10, metric="progress")
        )
        
        loop.close()
        
        # Process analytics data
        analytics_data = {
            'date': datetime.utcnow().date().isoformat(),
            'top_performers_count': len(top_performers),
            'processed_at': datetime.utcnow().isoformat()
        }
        
        # Store or send analytics summary
        # For now, just log it
        print(f"Daily analytics processed: {analytics_data}")
        
        return {
            'status': 'success',
            'analytics': analytics_data
        }
        
    except Exception as exc:
        print(f"Daily analytics task failed: {exc}")
        return {
            'status': 'failed',
            'error': str(exc)
        }

@celery_app.task
def cleanup_old_data():
    """
    Clean up old data from the system.
    Scheduled task that runs weekly.
    """
    try:
        # Use async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Clean up old analytics events
        loop.run_until_complete(
            analytics_service.process_analytics()
        )
        
        loop.close()
        
        # Additional cleanup logic can be added here
        # - Old temporary files
        # - Expired sessions
        # - Old logs
        
        return {
            'status': 'success',
            'cleaned_at': datetime.utcnow().isoformat(),
            'cleanup_type': 'weekly'
        }
        
    except Exception as exc:
        print(f"Cleanup task failed: {exc}")
        return {
            'status': 'failed',
            'error': str(exc)
        }

@celery_app.task
def send_learning_reminders():
    """
    Send learning reminders to inactive users.
    Scheduled task that runs twice daily.
    """
    try:
        usuario_repository = UsuarioRepository()
        
        # Use async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Get users who haven't been active in the last 3 days
        cutoff_date = datetime.utcnow() - timedelta(days=3)
        
        # This would need a more sophisticated query to find inactive users
        # For now, we'll use a simple approach
        all_users = loop.run_until_complete(
            usuario_repository.get_all(limit=1000)
        )
        
        loop.close()
        
        # Queue reminder emails
        reminder_tasks = []
        for user in all_users[:10]:  # Limit to 10 for demo
            # Send learning reminder
            task = send_email.delay(
                user.email,
                "Continue sua jornada de aprendizado! 📚",
                f"Olá {user.nome}, notamos que você não acessa a plataforma há alguns dias. "
                f"Que tal continuar seus estudos hoje?",
                "learning_reminder"
            )
            reminder_tasks.append(task.id)
        
        return {
            'status': 'success',
            'reminders_sent': len(reminder_tasks),
            'reminder_tasks': reminder_tasks,
            'sent_at': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        print(f"Learning reminders task failed: {exc}")
        return {
            'status': 'failed',
            'error': str(exc)
        }

@celery_app.task(bind=True)
def analyze_content_with_ai(self, content: str, content_type: str):
    """
    Analyze content using AI in background.
    
    Args:
        content: Content to analyze
        content_type: Type of content
    """
    try:
        # Use async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            gemini_client.analyze_learning_content(content, content_type)
        )
        
        loop.close()
        
        return {
            'status': 'success',
            'analysis': result,
            'analyzed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        print(f"Content analysis task failed: {exc}")
        return {
            'status': 'failed',
            'error': str(exc)
        }

@celery_app.task
def batch_process_user_progress(user_progress_data: List[Dict]):
    """
    Process multiple user progress updates in batch.
    
    Args:
        user_progress_data: List of progress update data
    """
    try:
        from business.learning.content_delivery import ContentDelivery
        content_delivery = ContentDelivery()
        
        # Use async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        results = []
        for progress_data in user_progress_data:
            result = loop.run_until_complete(
                content_delivery.update_content_progress(
                    progress_data['user_id'],
                    progress_data['conteudo_id'],
                    progress_data['progresso'],
                    progress_data.get('nota'),
                    progress_data.get('tempo_estudo')
                )
            )
            results.append(result)
        
        loop.close()
        
        successful_updates = len([r for r in results if r.get('success')])
        
        return {
            'status': 'success',
            'total_updates': len(user_progress_data),
            'successful_updates': successful_updates,
            'failed_updates': len(user_progress_data) - successful_updates,
            'processed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        print(f"Batch progress processing task failed: {exc}")
        return {
            'status': 'failed',
            'error': str(exc)
        }

# Task monitoring and health check
@celery_app.task
def health_check():
    """
    Health check task for monitoring.
    """
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'worker_id': current_task.request.id
    }

