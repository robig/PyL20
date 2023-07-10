import json
import websockets
import logging
import asyncio

logger = logging.getLogger(__name__)

class Ws:

    # list of connected sockets:
    clients=[]

    device_status = None

    request_callback = None
    port = 5000

    async def send_to_clients(self, obj):
        msg = json.dumps(obj, indent=2)
        for c in self.clients:
            logger.info("sending to client: %s", msg)
            try:
                await c.send(msg)
            except websockets.exceptions.ConnectionClosed:
                logger.error("Cannot send to client - connection closed")



    async def ws_handler(self, websocket, path):
        self.clients.append(websocket)
        
        status = "unknown"
        if self.device_status.get("connected"):
            status = self.device_status.get("connected")
        await websocket.send(f"{{\"status\": \"{status}\"}}")
        while websocket.open:
            try:
                data = await websocket.recv()
                logger.info(f"Data received: {data}")
                try:
                    json_data = json.loads(data)
                    #await ws_process_request(json_data)
                    if self.request_callback:
                        await self.request_callback(json_data)
                    else:
                        logger.error("No callback!")
                except ValueError:
                    logger.info("Ignoring invalid request (invalid json)")
                #reply = f"{{\"message\": \"Data recieved: {data}!\"}}"
                #await websocket.send(reply)
            except websockets.exceptions.ConnectionClosed:
                logger.debug("Client disconnected.  Do cleanup")
                break             

        self.clients.remove(websocket)

    def set_port(self, port : int):
        self.port = port

    def set_callback(self, callback):
        self.request_callback = callback

    def set_device_status_obj(self, obj):
        self.device_status = obj

    #def __init__(self, args: argparse.Namespace, callback):
    #    self.request_callback = callback
    #    self.port = int(args.port)
    
    async def run(self):
        async with websockets.serve(self.ws_handler, "", self.port):
            await asyncio.Future()  # run forever