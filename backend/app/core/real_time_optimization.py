"""
Real-time Support Optimization for 5/5 Rating
Advanced WebSocket management, real-time caching, and performance optimization
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import redis.asyncio as redis
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid

logger = logging.getLogger(__name__)

@dataclass
class WebSocketSession:
    """WebSocket session management"""
    session_id: str
    lead_id: Optional[str]
    user_id: Optional[str]
    connected_at: datetime
    last_activity: datetime
    message_count: int = 0
    is_active: bool = True

@dataclass
class RealTimeMetrics:
    """Real-time performance metrics"""
    active_sessions: int
    messages_per_second: float
    avg_response_time: float
    cache_hit_rate: float
    error_rate: float
    timestamp: datetime

class RealTimeOptimizer:
    """Advanced real-time optimization system"""
    
    def __init__(self, redis_client: redis.Redis, db_session: Session):
        self.redis = redis_client
        self.db = db_session
        
        # Real-time data structures
        self.active_sessions: Dict[str, WebSocketSession] = {}
        self.session_metrics: List[RealTimeMetrics] = []
        self.message_queue: asyncio.Queue = asyncio.Queue()
        
        # Performance tracking
        self.message_times: List[float] = []
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Real-time cache keys
        self.CACHE_KEYS = {
            'lead_data': 'rt:lead:{lead_id}',
            'conversation': 'rt:conv:{session_id}',
            'nyc_data': 'rt:nyc:{zip_code}',
            'lead_score': 'rt:score:{lead_id}',
            'market_data': 'rt:market:{borough}',
        }
        
        # Start background tasks
        asyncio.create_task(self._process_message_queue())
        asyncio.create_task(self._cleanup_inactive_sessions())
        asyncio.create_task(self._update_metrics())
    
    async def register_session(self, session_id: str, lead_id: Optional[str] = None, user_id: Optional[str] = None):
        """Register a new WebSocket session"""
        session = WebSocketSession(
            session_id=session_id,
            lead_id=lead_id,
            user_id=user_id,
            connected_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        self.active_sessions[session_id] = session
        
        # Cache session data in Redis
        await self.redis.setex(
            f"rt:session:{session_id}",
            3600,  # 1 hour TTL
            json.dumps(asdict(session), default=str)
        )
        
        logger.info(f"Registered WebSocket session: {session_id}")
    
    async def unregister_session(self, session_id: str):
        """Unregister a WebSocket session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            await self.redis.delete(f"rt:session:{session_id}")
            logger.info(f"Unregistered WebSocket session: {session_id}")
    
    async def update_session_activity(self, session_id: str):
        """Update session activity timestamp"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].last_activity = datetime.now()
            self.active_sessions[session_id].message_count += 1
    
    async def get_lead_data_realtime(self, lead_id: str) -> Dict[str, Any]:
        """Get lead data with real-time caching"""
        cache_key = self.CACHE_KEYS['lead_data'].format(lead_id=lead_id)
        
        # Try cache first
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            self.cache_hits += 1
            return json.loads(cached_data)
        
        # Fetch from database
        start_time = time.time()
        lead_data = await self._fetch_lead_from_db(lead_id)
        query_time = time.time() - start_time
        
        # Cache for 5 minutes
        await self.redis.setex(
            cache_key,
            300,
            json.dumps(lead_data, default=str)
        )
        
        self.cache_misses += 1
        logger.debug(f"Lead data fetched from DB in {query_time:.3f}s")
        
        return lead_data
    
    async def get_conversation_realtime(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation data with real-time caching"""
        cache_key = self.CACHE_KEYS['conversation'].format(session_id=session_id)
        
        # Try cache first
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            self.cache_hits += 1
            return json.loads(cached_data)
        
        # Fetch from database
        start_time = time.time()
        conversation = await self._fetch_conversation_from_db(session_id)
        query_time = time.time() - start_time
        
        # Cache for 2 minutes
        await self.redis.setex(
            cache_key,
            120,
            json.dumps(conversation, default=str)
        )
        
        self.cache_misses += 1
        logger.debug(f"Conversation fetched from DB in {query_time:.3f}s")
        
        return conversation
    
    async def get_nyc_data_realtime(self, zip_code: str) -> Dict[str, Any]:
        """Get NYC data with real-time caching"""
        cache_key = self.CACHE_KEYS['nyc_data'].format(zip_code=zip_code)
        
        # Try cache first
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            self.cache_hits += 1
            return json.loads(cached_data)
        
        # Fetch from database
        start_time = time.time()
        nyc_data = await self._fetch_nyc_data_from_db(zip_code)
        query_time = time.time() - start_time
        
        # Cache for 1 hour (NYC data is relatively static)
        await self.redis.setex(
            cache_key,
            3600,
            json.dumps(nyc_data, default=str)
        )
        
        self.cache_misses += 1
        logger.debug(f"NYC data fetched from DB in {query_time:.3f}s")
        
        return nyc_data
    
    async def calculate_lead_score_realtime(self, lead_id: str) -> Dict[str, Any]:
        """Calculate lead score with real-time optimization"""
        cache_key = self.CACHE_KEYS['lead_score'].format(lead_id=lead_id)
        
        # Try cache first
        cached_score = await self.redis.get(cache_key)
        if cached_score:
            self.cache_hits += 1
            return json.loads(cached_score)
        
        # Calculate score
        start_time = time.time()
        score_data = await self._calculate_lead_score(lead_id)
        calculation_time = time.time() - start_time
        
        # Cache for 10 minutes
        await self.redis.setex(
            cache_key,
            600,
            json.dumps(score_data, default=str)
        )
        
        self.cache_misses += 1
        logger.debug(f"Lead score calculated in {calculation_time:.3f}s")
        
        return score_data
    
    async def broadcast_to_sessions(self, message: Dict[str, Any], target_sessions: Optional[List[str]] = None):
        """Broadcast message to WebSocket sessions"""
        if target_sessions is None:
            target_sessions = list(self.active_sessions.keys())
        
        for session_id in target_sessions:
            if session_id in self.active_sessions:
                await self.message_queue.put({
                    'session_id': session_id,
                    'message': message,
                    'timestamp': time.time()
                })
    
    async def _process_message_queue(self):
        """Process WebSocket message queue"""
        while True:
            try:
                message_data = await self.message_queue.get()
                await self._send_websocket_message(
                    message_data['session_id'],
                    message_data['message']
                )
                self.message_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing message queue: {e}")
    
    async def _send_websocket_message(self, session_id: str, message: Dict[str, Any]):
        """Send message via WebSocket (placeholder for actual implementation)"""
        # This would integrate with your WebSocket implementation
        logger.debug(f"Sending message to session {session_id}: {message}")
    
    async def _cleanup_inactive_sessions(self):
        """Clean up inactive WebSocket sessions"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                current_time = datetime.now()
                inactive_sessions = []
                
                for session_id, session in self.active_sessions.items():
                    if (current_time - session.last_activity).seconds > 300:  # 5 minutes
                        inactive_sessions.append(session_id)
                
                for session_id in inactive_sessions:
                    await self.unregister_session(session_id)
                
                if inactive_sessions:
                    logger.info(f"Cleaned up {len(inactive_sessions)} inactive sessions")
                
            except Exception as e:
                logger.error(f"Error cleaning up sessions: {e}")
    
    async def _update_metrics(self):
        """Update real-time metrics"""
        while True:
            try:
                await asyncio.sleep(30)  # Update every 30 seconds
                
                # Calculate metrics
                active_sessions = len(self.active_sessions)
                messages_per_second = len(self.message_times) / 30 if self.message_times else 0
                avg_response_time = sum(self.message_times) / len(self.message_times) if self.message_times else 0
                cache_hit_rate = self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
                
                metrics = RealTimeMetrics(
                    active_sessions=active_sessions,
                    messages_per_second=messages_per_second,
                    avg_response_time=avg_response_time,
                    cache_hit_rate=cache_hit_rate,
                    error_rate=0.0,  # Would need to track errors
                    timestamp=datetime.now()
                )
                
                self.session_metrics.append(metrics)
                
                # Keep only last 100 metrics
                if len(self.session_metrics) > 100:
                    self.session_metrics = self.session_metrics[-100:]
                
                # Cache metrics in Redis
                await self.redis.setex(
                    'rt:metrics',
                    60,
                    json.dumps(asdict(metrics), default=str)
                )
                
                # Reset counters
                self.message_times = []
                self.cache_hits = 0
                self.cache_misses = 0
                
            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
    
    async def _fetch_lead_from_db(self, lead_id: str) -> Dict[str, Any]:
        """Fetch lead data from database"""
        result = self.db.execute(text("""
            SELECT l.*, nzc.solar_potential_score, nzc.conversion_rate
            FROM leads l
            LEFT JOIN nyc_zip_codes nzc ON l.zip_code = nzc.zip_code
            WHERE l.id = :lead_id
        """), {'lead_id': lead_id})
        
        row = result.fetchone()
        if row:
            return dict(row._mapping)
        return {}
    
    async def _fetch_conversation_from_db(self, session_id: str) -> List[Dict[str, Any]]:
        """Fetch conversation data from database"""
        result = self.db.execute(text("""
            SELECT * FROM lead_conversations
            WHERE session_id = :session_id
            ORDER BY created_at DESC
            LIMIT 50
        """), {'session_id': session_id})
        
        return [dict(row._mapping) for row in result.fetchall()]
    
    async def _fetch_nyc_data_from_db(self, zip_code: str) -> Dict[str, Any]:
        """Fetch NYC data from database"""
        result = self.db.execute(text("""
            SELECT * FROM nyc_zip_codes
            WHERE zip_code = :zip_code
        """), {'zip_code': zip_code})
        
        row = result.fetchone()
        if row:
            return dict(row._mapping)
        return {}
    
    async def _calculate_lead_score(self, lead_id: str) -> Dict[str, Any]:
        """Calculate lead score with real-time optimization"""
        # This would implement the actual lead scoring logic
        # For now, return a placeholder
        return {
            'lead_id': lead_id,
            'score': 75,
            'quality': 'warm',
            'factors': ['high_electric_bill', 'good_solar_potential'],
            'calculated_at': datetime.now().isoformat()
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get real-time performance summary"""
        if not self.session_metrics:
            return {}
        
        recent_metrics = self.session_metrics[-10:]  # Last 10 measurements
        
        return {
            'active_sessions': len(self.active_sessions),
            'avg_messages_per_second': sum(m.messages_per_second for m in recent_metrics) / len(recent_metrics),
            'avg_response_time': sum(m.avg_response_time for m in recent_metrics) / len(recent_metrics),
            'avg_cache_hit_rate': sum(m.cache_hit_rate for m in recent_metrics) / len(recent_metrics),
            'total_messages_processed': len(self.message_times),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
        }

# Global real-time optimizer instance
realtime_optimizer: Optional[RealTimeOptimizer] = None

def initialize_realtime_optimizer(redis_client: redis.Redis, db_session: Session):
    """Initialize the real-time optimizer"""
    global realtime_optimizer
    realtime_optimizer = RealTimeOptimizer(redis_client, db_session)
    return realtime_optimizer

def get_realtime_optimizer() -> Optional[RealTimeOptimizer]:
    """Get the real-time optimizer instance"""
    return realtime_optimizer
