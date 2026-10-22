import asyncio
import json
import os
import secrets
import string
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8000"))
GAME_PAGE = Path(__file__).parent / "tic-tac-toe" / "index.html"
ROOMS = {}
WINNING_LINES = (
	(0, 1, 2), (3, 4, 5), (6, 7, 8),
	(0, 3, 6), (1, 4, 7), (2, 5, 8),
	(0, 4, 8), (2, 4, 6),
)


def room_view(room):
	return {
		"board": room["board"],
		"turn": room["turn"],
		"winner": room["winner"],
		"draw": room["draw"],
		"joined": room["joined"],
		"round": room["round"],
	}

def decode_json_object(body):
	data = json.loads(body or b"{}")
	if not isinstance(data, dict):
		raise ValueError("Expected a JSON object")
	return data



def create_room():
	remove_expired_rooms()
	alphabet = string.ascii_uppercase + string.digits
	while True:
		code = "".join(secrets.choice(alphabet) for _ in range(6))
		if code not in ROOMS:
			break
	ROOMS[code] = {
		"board": [""] * 9,
		"turn": "X",
		"winner": None,
		"draw": False,
		"joined": False,
		"round": 0,
		"created": time.monotonic(),
	}
	return code, ROOMS[code]


def remove_expired_rooms():
	cutoff = time.monotonic() - 12 * 60 * 60
	for code in [code for code, room in ROOMS.items() if room["created"] < cutoff]:
		ROOMS.pop(code, None)


def winning_line(board):
	for line in WINNING_LINES:
		if board[line[0]] and all(board[index] == board[line[0]] for index in line):
			return line
	return ()


def apply_room_move(room, player, index):
	if player not in ("X", "O"):
		return "Invalid player mark"
	if type(index) is not int or not 0 <= index < 9:
		return "Choose a board square from 1 to 9"
	if room["winner"] or room["draw"]:
		return "This round is already over"
	if player != room["turn"]:
		return "It is the other player's turn"
	if room["board"][index]:
		return "That square is already taken"

	room["board"][index] = player
	if winning_line(room["board"]):
		room["winner"] = player
	elif all(room["board"]):
		room["draw"] = True
	else:
		room["turn"] = "O" if player == "X" else "X"
	return None


def reset_room(room):
	room.update({
		"board": [""] * 9,
		"turn": "X",
		"winner": None,
		"draw": False,
		"round": room["round"] + 1,
	})


async def write_response(writer, status, body, content_type="application/json; charset=utf-8"):
	if isinstance(body, str):
		body = body.encode("utf-8")
	reason = {200: "OK", 400: "Bad Request", 404: "Not Found", 409: "Conflict", 500: "Internal Server Error"}.get(status, "OK")
	headers = (
		f"HTTP/1.1 {status} {reason}\r\n"
		f"Content-Type: {content_type}\r\n"
		f"Content-Length: {len(body)}\r\n"
		"Cache-Control: no-store\r\n"
		"Connection: close\r\n\r\n"
	).encode("ascii")
	writer.write(headers + body)
	await writer.drain()


async def respond_json(writer, status, data):
	await write_response(writer, status, json.dumps(data, separators=(",", ":")))


async def handle_client(reader, writer):
	try:
		remove_expired_rooms()
		request_line = await reader.readline()
		if not request_line:
			return
		parts = request_line.decode("ascii", errors="replace").strip().split()
		if len(parts) != 3:
			await respond_json(writer, 400, {"error": "Malformed request"})
			return
		method, request_target, _version = parts
		headers = {}
		while True:
			line = await reader.readline()
			if line in (b"\r\n", b"\n", b""):
				break
			name, separator, value = line.decode("iso-8859-1").partition(":")
			if separator:
				headers[name.strip().lower()] = value.strip()

		content_length = int(headers.get("content-length", "0"))
		if content_length > 16_384:
			await respond_json(writer, 400, {"error": "Request is too large"})
			return
		body = await reader.readexactly(content_length) if content_length else b""
		url = urlsplit(request_target)
		query = parse_qs(url.query)

		if method == "GET" and url.path in ("/", "/index.html"):
			await write_response(writer, 200, GAME_PAGE.read_bytes(), "text/html; charset=utf-8")
		elif method == "POST" and url.path == "/api/rooms":
			code, room = create_room()
			await respond_json(writer, 200, {"code": code, "player": "X", "room": room_view(room)})
		elif method == "POST" and url.path == "/api/rooms/join":
			data = decode_json_object(body)
			code = str(data.get("code", "")).strip().upper()
			room = ROOMS.get(code)
			if room is None:
				await respond_json(writer, 404, {"error": "Room not found. Check the code and try again."})
			elif room["joined"]:
				await respond_json(writer, 409, {"error": "That room already has two players."})
			else:
				room["joined"] = True
				await respond_json(writer, 200, {"code": code, "player": "O", "room": room_view(room)})
		elif method == "GET" and url.path == "/api/rooms/state":
			code = query.get("code", [""])[0].strip().upper()
			room = ROOMS.get(code)
			if room is None:
				await respond_json(writer, 404, {"error": "Room not found. It may have expired."})
			else:
				await respond_json(writer, 200, {"room": room_view(room)})
		elif method == "POST" and url.path == "/api/rooms/move":
			data = decode_json_object(body)
			room = ROOMS.get(str(data.get("code", "")).strip().upper())
			if room is None:
				await respond_json(writer, 404, {"error": "Room not found. It may have expired."})
			else:
				error = apply_room_move(room, data.get("player"), data.get("index"))
				if error:
					await respond_json(writer, 409, {"error": error, "room": room_view(room)})
				else:
					await respond_json(writer, 200, {"room": room_view(room)})
		elif method == "POST" and url.path == "/api/rooms/reset":
			data = decode_json_object(body)
			room = ROOMS.get(str(data.get("code", "")).strip().upper())
			if room is None:
				await respond_json(writer, 404, {"error": "Room not found. It may have expired."})
			else:
				reset_room(room)
				await respond_json(writer, 200, {"room": room_view(room)})
		else:
			await respond_json(writer, 404, {"error": "Not found"})
	except (json.JSONDecodeError, UnicodeDecodeError, ValueError, asyncio.IncompleteReadError):
		await respond_json(writer, 400, {"error": "Invalid request"})
	except (ConnectionError, BrokenPipeError):
		pass
	finally:
		writer.close()
		try:
			await writer.wait_closed()
		except ConnectionError:
			pass


async def serve():
	server = await asyncio.start_server(handle_client, HOST, PORT, limit=32_768)
	print(f"Tic Tac Toe is running at http://localhost:{PORT}", flush=True)
	print("For LAN play, share this computer's local IP address and port with the other player.", flush=True)
	async with server:
		await server.serve_forever()


def main():
	try:
		asyncio.run(serve())
	except KeyboardInterrupt:
		print("\nGame server stopped.")


if __name__ == "__main__":
	main()