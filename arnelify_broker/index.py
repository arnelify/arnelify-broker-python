import cffi
import json
import os

from concurrent.futures import Future

class ArnelifyBroker:
  def __init__(self):
    srcDir: str = os.walk(os.path.abspath('venv/lib64'))
    libPaths: list[str] = []
    for root, dirs, files in srcDir:
      for file in files:
        if file.startswith('arnelify-broker') and file.endswith('.so'):
          libPaths.append(os.path.join(root, file))

    self.ffi = cffi.FFI()
    self.lib = self.ffi.dlopen(libPaths[0])

    self.ffi.cdef("""
      typedef const char* cSerialized;
      typedef const char* cDeserialized;

      void broker_create();
      const char* broker_deserialize(cSerialized);
      void broker_destroy();
      void broker_free(cDeserialized);
      const char* broker_get_datetime();
      const char* broker_get_uuid();
      const char* broker_serialize(cDeserialized);
    """)

    self.actions: dict = {}
    self.req: dict = {}
    self.res: dict = {}
    self.lib.broker_create()
    
  def callback(self, message: str, isError: bool) -> None:
    if isError:
      print(message)
      return
    
    print(message)

  def consumer(self, topic: str, onMessage: callable) -> None:
    self.req[topic] = onMessage

  def deserialize(self, message: str) -> dict:
    cMessage = self.ffi.new("char[]", message.encode('utf-8'))
    cDeserialized = self.lib.broker_deserialize(cMessage)
    deserialized = self.ffi.string(cDeserialized).decode('utf-8')
    self.lib.broker_free(cDeserialized)
    json_: dict = {}

    try: 
      json_ = json.loads(deserialized)
    except json.JSONDecodeError as err:
      self.callback(f"[ArnelifyBroker FFI]: Python error: The Message must be a valid JSON.", True)
      exit(1)

    return json_

  def handler(self, topic: str, ctx: dict) -> dict:
    ctx["receivedAt"] = self.getDateTime()
    action: callable = self.actions[topic]
    res: dict = {
      "content": action(ctx),
      "createdAt": ctx["createdAt"],
      "receivedAt": self.getDateTime(),
      "topic": ctx["topic"],
      "uuid": ctx["uuid"],
    }

    return res
  
  def producer(self, topic: str, message: str) -> None:
    onMessage: callable = self.req[topic]
    onMessage(message)

  def receive(self, res: dict) -> None:
    uuid: str = res["uuid"]
    resolve: callable = self.res[uuid]
    del self.res[uuid]
    resolve(res["content"])

  def send(self, topic: str, params: dict, producer: callable) -> dict:
    future = Future()

    uuid: str = self.getUuId()
    def resolve(res: dict) -> None:
      future.set_result(res)

    self.res[uuid] = resolve
    ctx: dict = {
      "topic": topic,
      "createdAt": self.getDateTime(),
      "params": params,
      "uuid": uuid
    }

    message: str = self.serialize(ctx)
    producer(message)
    return future.result()

  def serialize(self, ctx: dict) -> str:
    cCtx: str = json.dumps(ctx)
    cDeserialized = self.ffi.new("char[]", cCtx.encode('utf-8'))
    cSerialized = self.lib.broker_serialize(cDeserialized)
    message: str = self.ffi.string(cSerialized).decode('utf-8')
    self.lib.broker_free(cSerialized)
    return message

  def call(self, topic: str, params: dict) -> dict:
    def callback(message: str) -> None:
      self.producer(topic + ":req", message)

    return self.send(topic, params, callback)

  def getDateTime(self) -> str:
    cDateTime = self.lib.broker_get_datetime()
    datetime: str = self.ffi.string(cDateTime).decode('utf-8')
    self.lib.broker_free(cDateTime)
    return datetime
  
  def getUuId(self) -> str:
    cUuId = self.lib.broker_get_uuid()
    uuid: str = self.ffi.string(cUuId).decode('utf-8')
    self.lib.broker_free(cUuId)
    return uuid

  def setAction(self, topic: str, action: callable) -> None:
    self.actions[topic] = action

  def subscribe(self, topic: str, action: callable) -> None:
    self.setAction(topic, action)

    def onResponse(message: str) -> None:
      res: dict = self.deserialize(message)
      self.receive(res)

    self.consumer(topic + ":res", onResponse)

    def onRequest(message: str) -> None:
      ctx: dict = self.deserialize(message)
      topic: str = ctx["topic"]
      res: dict = self.handler(topic, ctx)
      serialized: str = self.serialize(res)
      self.producer(topic + ":res", serialized)

    self.consumer(topic + ":req", onRequest)