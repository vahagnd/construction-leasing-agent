import subprocess
import json
import sys

class Client:
    def __init__(self, server_script="server.py"):
        self.server_script = server_script
        self.process = None
        self.request_id = 0

    def start(self):
        self.process = subprocess.Popen(
            [sys.executable, self.server_script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Initialize server
        response = self.send_request({
            "jsonrpc": "2.0",
            "id": self.next_id(),
            "method": "initialize",
            "params": {}
        })
        return response

    def next_id(self):
        self.request_id += 1
        return self.request_id

    def send_request(self, request):
        if not self.process:
            raise RuntimeError("Server not started")

        request_json = json.dumps(request, ensure_ascii=False)
        self.process.stdin.write(request_json + "\n")
        self.process.stdin.flush()

        response_line = self.process.stdout.readline()
        if not response_line:
            stderr_output = self.process.stderr.read()
            raise RuntimeError(f"Server error: {stderr_output}")

        return json.loads(response_line.strip())

    def list_tools(self):
        request = {
            "jsonrpc": "2.0",
            "id": self.next_id(),
            "method": "tools/list"
        }
        return self.send_request(request)

    def call_tool(self, name, arguments):
        request = {
            "jsonrpc": "2.0",
            "id": self.next_id(),
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments
            }
        }
        return self.send_request(request)

    def close(self):
        if self.process:
            self.process.stdin.close()
            self.process.terminate()
            self.process.wait()

def test():
    client = Client()

    try:
        print("Starting server...")
        init_response = client.start()
        print(f"Init: {init_response}")

        print("\nListing tools...")
        tools_response = client.list_tools()
        print(f"Tools: {json.dumps(tools_response, ensure_ascii=False, indent=2)}")

        sample_contract = """
        Договор лизинга №123/2024
        Между ООО "СтройТех" (Лизингодатель) и ИП Иванов А.И. (Лизингополучатель)
        заключен настоящий договор лизинга 15 марта 2024 года.
        Предмет лизинга: Экскаватор JCB JS220LC
        Стоимость: 3,500,000 рублей
        """

        print("\nExtracting information...")
        extract_response = client.call_tool("extract_information", {
            "contract_text": sample_contract
        })
        print(f"Extract: {json.dumps(extract_response, ensure_ascii=False, indent=2)}")

        if "result" in extract_response:
            contract_info = extract_response["result"]["content"][0]["text"]

            print("\nClassifying contract...")
            classify_response = client.call_tool("classify_contract", {
                "product_description": contract_info
            })
            print(f"Classify: {json.dumps(classify_response, ensure_ascii=False, indent=2)}")

            print("\nSaving contract...")
            save_response = client.call_tool("save_leasing_info", {
                "contract_info": contract_info
            })
            print(f"Save: {json.dumps(save_response, ensure_ascii=False, indent=2)}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        client.close()

if __name__ == "__main__":
    test()