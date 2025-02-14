from arnelify_broker import ArnelifyBroker
import json

def main() -> int:
  broker = ArnelifyBroker()
  
  def setMessageAction(ctx: dict) -> dict:
    res: dict = {}
    res["params"] = ctx["params"]
    res["params"]["success"] = "Welcome to Arnelify Broker"
    return res
  
  def setCodeAction(ctx: dict) -> dict:
    res: dict = {}
    res["params"] = ctx["params"]
    res["params"]["code"] = 200
    return broker.call("second.welcome", res["params"])
  
  broker.subscribe("second.welcome", setMessageAction)
  broker.subscribe("first.welcome", setCodeAction)

  ctx: dict = {}
  ctx["params"] = {
    "code": 0,
    "success": ""
  }

  res: dict = broker.call("first.welcome", ctx["params"])
  print(res)

if __name__ == "__main__":
  main()