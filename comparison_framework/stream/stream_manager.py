"""
WebSocket Connection and Session Management for JSS Streaming
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)


class WebSocketConnection:
	"""Represents a single WebSocket connection"""

	def __init__(self, websocket: WebSocket, client_id: str):
		self.websocket = websocket
		self.client_id = client_id
		self.connected_at = datetime.now()
		self.is_active = True
		self.subscribed_sessions: Set[str] = set()

	async def send_message(self, message: dict):
		"""Send message to this connection"""
		try:
			if self.is_active:
				await self.websocket.send_text(json.dumps(message))
		except Exception as e:
			logger.error(f'Error sending message to {self.client_id}: {e}')
			self.is_active = False
			raise  # Re-raise to let caller know the connection failed

	async def close(self):
		"""Close the connection"""
		try:
			if self.is_active:
				await self.websocket.close()
		except Exception as e:
			logger.error(f'Error closing connection {self.client_id}: {e}')
		finally:
			self.is_active = False


class StreamSession:
	"""Represents a JSS execution session that can be streamed to multiple clients"""

	def __init__(self, session_id: str, request_data: dict):
		self.session_id = session_id
		self.request_data = request_data
		self.created_at = datetime.now()
		self.status = 'initializing'  # initializing, running, completed, failed
		self.progress = 0.0
		self.current_episode = 0
		self.total_episodes = 0
		self.results = {}
		self.error_message = None
		self.subscribers: Set[str] = set()  # Client IDs subscribed to this session

	def to_dict(self) -> dict:
		"""Convert session to dictionary for JSON serialization"""
		return {'session_id': self.session_id, 'status': self.status, 'progress': self.progress, 'current_episode': self.current_episode, 'total_episodes': self.total_episodes, 'created_at': self.created_at.isoformat(), 'request_data': self.request_data, 'error_message': self.error_message, 'subscriber_count': len(self.subscribers)}


class StreamManager:
	"""Manages WebSocket connections and streaming sessions"""

	def __init__(self):
		self.connections: Dict[str, WebSocketConnection] = {}
		self.sessions: Dict[str, StreamSession] = {}
		self._lock = asyncio.Lock()

	async def connect_client(self, websocket: WebSocket) -> str:
		"""Add a new WebSocket connection"""
		await websocket.accept()
		client_id = str(uuid.uuid4())

		connection = WebSocketConnection(websocket, client_id)

		async with self._lock:
			self.connections[client_id] = connection

		logger.info(f'Client {client_id} connected. Total connections: {len(self.connections)}')

		# Send welcome message
		await connection.send_message({'type': 'connection_established', 'client_id': client_id, 'timestamp': datetime.now().isoformat()})

		return client_id

	async def disconnect_client(self, client_id: str):
		"""Remove a WebSocket connection"""
		async with self._lock:
			if client_id in self.connections:
				connection = self.connections[client_id]

				# Unsubscribe from all sessions
				for session_id in connection.subscribed_sessions.copy():
					await self.unsubscribe_from_session(client_id, session_id)

				# Close and remove connection
				await connection.close()
				del self.connections[client_id]

				logger.info(f'Client {client_id} disconnected. Total connections: {len(self.connections)}')

	async def create_session(self, request_data: dict) -> str:
		"""Create a new streaming session"""
		session_id = str(uuid.uuid4())

		session = StreamSession(session_id, request_data)
		session.total_episodes = request_data.get('num_episodes', 10)

		async with self._lock:
			self.sessions[session_id] = session

		logger.info(f'Created session {session_id}')

		# Broadcast session creation to all connected clients
		await self.broadcast_to_all({'type': 'session_created', 'session': session.to_dict(), 'timestamp': datetime.now().isoformat()})

		return session_id

	async def subscribe_to_session(self, client_id: str, session_id: str) -> bool:
		"""Subscribe a client to a session"""
		async with self._lock:
			if client_id not in self.connections or session_id not in self.sessions:
				return False

			connection = self.connections[client_id]
			session = self.sessions[session_id]

			connection.subscribed_sessions.add(session_id)
			session.subscribers.add(client_id)

			logger.info(f'Client {client_id} subscribed to session {session_id}')

		# Send current session state to the newly subscribed client
		await self.connections[client_id].send_message({'type': 'session_subscribed', 'session': session.to_dict(), 'timestamp': datetime.now().isoformat()})

		return True

	async def unsubscribe_from_session(self, client_id: str, session_id: str):
		"""Unsubscribe a client from a session"""
		async with self._lock:
			if client_id in self.connections and session_id in self.sessions:
				connection = self.connections[client_id]
				session = self.sessions[session_id]

				connection.subscribed_sessions.discard(session_id)
				session.subscribers.discard(client_id)

				logger.info(f'Client {client_id} unsubscribed from session {session_id}')

	async def update_session_status(self, session_id: str, status: str, **kwargs):
		"""Update session status and notify subscribers"""
		async with self._lock:
			if session_id not in self.sessions:
				return

			session = self.sessions[session_id]
			session.status = status

			# Update additional fields
			for key, value in kwargs.items():
				if hasattr(session, key):
					setattr(session, key, value)

		# Notify subscribers
		message = {'type': 'session_status_update', 'session_id': session_id, 'status': status, 'session': session.to_dict(), 'timestamp': datetime.now().isoformat()}

		await self.broadcast_to_session_subscribers(session_id, message)

	async def send_episode_start(self, session_id: str, episode: int, agent_name: str):
		"""Send episode start event"""
		message = {'type': 'episode_start', 'session_id': session_id, 'episode': episode, 'agent_name': agent_name, 'timestamp': datetime.now().isoformat()}

		await self.broadcast_to_session_subscribers(session_id, message)

	async def send_episode_progress(self, session_id: str, episode: int, agent_name: str, step: int, action: int, reward: float, makespan: float = None):
		"""Send episode progress event"""
		message = {'type': 'episode_progress', 'session_id': session_id, 'episode': episode, 'agent_name': agent_name, 'step': step, 'action': action, 'reward': reward, 'makespan': makespan, 'timestamp': datetime.now().isoformat()}

		await self.broadcast_to_session_subscribers(session_id, message)

	async def send_episode_complete(self, session_id: str, episode: int, agent_name: str, makespan: float, total_reward: float, execution_time: float):
		"""Send episode completion event"""
		message = {'type': 'episode_complete', 'session_id': session_id, 'episode': episode, 'agent_name': agent_name, 'makespan': makespan, 'total_reward': total_reward, 'execution_time': execution_time, 'timestamp': datetime.now().isoformat()}

		# Update session progress
		async with self._lock:
			if session_id in self.sessions:
				session = self.sessions[session_id]
				session.current_episode = episode
				session.progress = episode / session.total_episodes if session.total_episodes > 0 else 0

		await self.broadcast_to_session_subscribers(session_id, message)

	async def send_comparison_progress(self, session_id: str, completed_agents: int, total_agents: int, current_agent: str = None):
		"""Send overall comparison progress"""
		message = {'type': 'comparison_progress', 'session_id': session_id, 'completed_agents': completed_agents, 'total_agents': total_agents, 'current_agent': current_agent, 'progress': completed_agents / total_agents if total_agents > 0 else 0, 'timestamp': datetime.now().isoformat()}

		await self.broadcast_to_session_subscribers(session_id, message)

	async def send_comparison_complete(self, session_id: str, results: dict):
		"""Send comparison completion event"""
		async with self._lock:
			if session_id in self.sessions:
				session = self.sessions[session_id]
				session.results = results
				session.status = 'completed'
				session.progress = 1.0

		message = {'type': 'comparison_complete', 'session_id': session_id, 'results': results, 'timestamp': datetime.now().isoformat()}

		await self.broadcast_to_session_subscribers(session_id, message)

	async def send_error(self, session_id: str, error_message: str, error_details: dict = None):
		"""Send error event"""
		async with self._lock:
			if session_id in self.sessions:
				session = self.sessions[session_id]
				session.status = 'failed'
				session.error_message = error_message

		message = {'type': 'error', 'session_id': session_id, 'error_message': error_message, 'error_details': error_details or {}, 'timestamp': datetime.now().isoformat()}

		await self.broadcast_to_session_subscribers(session_id, message)

	async def broadcast_to_session_subscribers(self, session_id: str, message: dict):
		"""Broadcast message to all subscribers of a session"""
		async with self._lock:
			if session_id not in self.sessions:
				return

			session = self.sessions[session_id]
			subscriber_ids = session.subscribers.copy()

		# Send to each subscriber
		for client_id in subscriber_ids:
			if client_id in self.connections:
				connection = self.connections[client_id]
				await connection.send_message(message)

	async def broadcast_to_all(self, message: dict):
		"""Broadcast message to all connected clients"""
		async with self._lock:
			connection_list = list(self.connections.values())

		for connection in connection_list:
			await connection.send_message(message)

	async def send_to_client(self, client_id: str, message: dict):
		"""Send message to a specific client"""
		async with self._lock:
			if client_id in self.connections:
				connection = self.connections[client_id]
				try:
					await connection.send_message(message)
				except Exception as e:
					logger.warning(f'Failed to send message to client {client_id}: {e}')
					# Mark connection as inactive and remove it
					connection.is_active = False
					# Clean up the failed connection
					await self._cleanup_failed_connection(client_id)

	async def _cleanup_failed_connection(self, client_id: str):
		"""Clean up a failed connection"""
		try:
			if client_id in self.connections:
				connection = self.connections[client_id]

				# Unsubscribe from all sessions
				for session_id in connection.subscribed_sessions.copy():
					await self.unsubscribe_from_session(client_id, session_id)

				# Remove connection
				del self.connections[client_id]
				logger.info(f'Cleaned up failed connection {client_id}')
		except Exception as e:
			logger.error(f'Error cleaning up connection {client_id}: {e}')

	def get_session_info(self, session_id: str) -> Optional[dict]:
		"""Get session information"""
		if session_id in self.sessions:
			return self.sessions[session_id].to_dict()
		return None

	def get_all_sessions(self) -> List[dict]:
		"""Get information about all sessions"""
		return [session.to_dict() for session in self.sessions.values()]

	def get_connection_count(self) -> int:
		"""Get number of active connections"""
		return len(self.connections)

	async def cleanup_inactive_connections(self):
		"""Remove inactive connections"""
		inactive_clients = []

		async with self._lock:
			for client_id, connection in self.connections.items():
				if not connection.is_active:
					inactive_clients.append(client_id)

		for client_id in inactive_clients:
			await self.disconnect_client(client_id)

	async def handle_client_message(self, client_id: str, message: dict):
		"""Handle incoming message from client"""
		message_type = message.get('type')

		if message_type == 'subscribe':
			session_id = message.get('session_id')
			if session_id:
				success = await self.subscribe_to_session(client_id, session_id)
				await self.send_to_client(client_id, {'type': 'subscribe_response', 'success': success, 'session_id': session_id})

		elif message_type == 'unsubscribe':
			session_id = message.get('session_id')
			if session_id:
				await self.unsubscribe_from_session(client_id, session_id)
				await self.send_to_client(client_id, {'type': 'unsubscribe_response', 'session_id': session_id})

		elif message_type == 'get_sessions':
			sessions = self.get_all_sessions()
			await self.send_to_client(client_id, {'type': 'sessions_list', 'sessions': sessions})

		elif message_type == 'ping':
			await self.send_to_client(client_id, {'type': 'pong', 'timestamp': datetime.now().isoformat()})


# Global stream manager instance
stream_manager = StreamManager()
