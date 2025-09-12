import socket
import threading
import time
import json

class LabVIEWServerDevice:
    """
    TCP Server with duplicate detection and JSON handling
    """
    
    def __init__(self, host='localhost', port=9999, buffer_size=1024):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.server_socket = None
        self.connection = None
        self.connected = False
        self.listening = False
        self.server_thread = None
        self.last_received_parameters = ""
        self.last_sent_parameters = ""
        self.last_data_hash = None  # Track duplicate data
        self.message_count = 0
        self.unique_message_count = 0
        
    def start_server(self):
        """Start the TCP server to listen for LabVIEW connections"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            self.listening = True
            
            print(f"✅ Server listening on {self.host}:{self.port}")
            
            self.server_thread = threading.Thread(target=self._server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def _server_loop(self):
        """Main server loop - handles LabVIEW connections"""
        while self.listening:
            try:
                print("🔄 Waiting for LabVIEW connection...")
                conn, addr = self.server_socket.accept()
                self.connection = conn
                self.connected = True
                print(f"🔌 LabVIEW connected from {addr}")
                
                self._handle_connection(conn)
                
            except Exception as e:
                if self.listening:
                    print(f"⚠️ Server error: {e}")
                break
    
    def _handle_connection(self, conn):
        """Handle commands from LabVIEW with duplicate detection"""
        try:
            while self.connected and self.listening:
                data = conn.recv(self.buffer_size)
                if not data:
                    break
                    
                raw_message = data.decode("utf-8").strip()
                self.message_count += 1
                
                # Check for duplicates
                current_hash = hash(raw_message)
                is_duplicate = (current_hash == self.last_data_hash)
                
                if not is_duplicate:
                    self.unique_message_count += 1
                    self.last_data_hash = current_hash
                    self.last_received_parameters = raw_message
                    
                    print(f"📨 Message #{self.message_count} (Unique #{self.unique_message_count}): {raw_message[:100]}...")
                    
                    # Process the new message
                    response = self._process_message(raw_message)
                    if response:
                        self.last_sent_parameters = response
                        print(f"📤 Response sent: {response}")
                else:
                    # Just acknowledge duplicate without processing
                    print(f"🔄 Duplicate message #{self.message_count} (ignoring)")
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
        finally:
            conn.close()
            self.connected = False
            print("🔌 LabVIEW disconnected")
    
    def _process_message(self, message):
        """Process new (non-duplicate) messages"""
        try:
            # Try to parse as JSON first
            data = json.loads(message.strip())
            return self._process_json_data(data)
        except json.JSONDecodeError:
            # Not JSON, just echo back
            return f"ECHO: {message}"
    
    def _process_json_data(self, data):
        """Process JSON data from LabVIEW"""
        input_val = data.get("Input", 0)
        output_val = data.get("Output", 0)
        string_output = data.get("StringOutput", "")
        
        # Process the data and create response
        processed_input = input_val * 2  # Example processing
        processed_output = output_val + 10  # Example processing
        
        response_data = {
            "ProcessedInput": processed_input,
            "ProcessedOutput": processed_output,
            "Status": "OK",
            "Timestamp": int(time.time()),
            "Echo": string_output
        }
        
        return json.dumps(response_data)
    
    def get_message_stats(self):
        """Get statistics about messages received"""
        return {
            "total_messages": self.message_count,
            "unique_messages": self.unique_message_count,
            "duplicate_messages": self.message_count - self.unique_message_count
        }
    
    def stop_server(self):
        """Stop the TCP server"""
        self.listening = False
        self.connected = False
        
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
                
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
                
        print("🛑 Server stopped")
    
    def is_connected(self):
        return self.connected
    
    def is_listening(self):
        return self.listening
    
    def get_last_received_parameters(self):
        return self.last_received_parameters
    
    def get_last_sent_command(self):
        return self.last_sent_parameters
    
    def _get_dict_from_last_received_parameters(self) -> dict:
        """Convert last command JSON to dict"""
        try:
            data = json.loads(self.last_received_parameters.rstrip("\\n").strip())
            return data
        except:
            return None
        
    def read_value_from_labview(self, value_type="command"):
        """Read a value/command from LabVIEW"""
        if not self.connected or not self.connection:
            print("❌ Not connected to LabVIEW")
            return None
        
        try:
            data = self._get_dict_from_last_received_parameters()
            entry = data.get(value_type, None) if data else None
            if entry is not None:
                print(f"📥 Read from LabVIEW: {entry}")
                return entry
            else:
                print(f"⚠️ No 'Entry' found in last command, data was: {data}")
            
        except Exception as e:
            print(f"❌ Failed to read from LabVIEW: {e}")
            self.connected = False
            return None
        
    def _send_to_labview(self, text: str) -> bool:
        """Low-level: send a newline-terminated UTF-8 message to LabVIEW."""
        if not self.connected or not self.connection:
            print("❌ Not connected to LabVIEW")
            return False
        try:
            if not text.endswith("\n"):
                text += "\n"
            self.connection.sendall(text.encode("utf-8"))
            self.last_sent_parameters = text.rstrip("\n")
            print(f"📤 Sent to LabVIEW: {self.last_sent_parameters}")
            return True
        except Exception as e:
            print(f"❌ Failed to send to LabVIEW: {e}")
            self.connected = False
            return False
        
    def send_json_to_labview(self, data: dict) -> bool:
        """Send a JSON message to LabVIEW."""
        try:
            json_text = json.dumps(data)
            return self._send_to_labview(json_text)
        except Exception as e:
            print(f"❌ send_json_to_labview failed: {e}")
            return False
        
    def write_value_to_labview(self, value_type: str, value: float, merge_last_command: bool = True) -> bool:
        """
        Inverse of read_value_from_labview:
        Sends a JSON message to LabVIEW where `value_type` is set to `value`.

        If merge_last_command=True, start from the last received JSON (if any)
        and overwrite/append the given key; otherwise send a minimal dict.
        """
        try:
            payload = {}
            if merge_last_command:
                # reuse previous JSON if available
                base = self._get_dict_from_last_received_parameters()
                if isinstance(base, dict):
                    payload.update(base)
            payload[value_type] = value

            return self._send_to_labview(json.dumps(payload))
        except Exception as e:
            print(f"❌ write_value_to_labview failed: {e}")
            return False
    
def main():
    server = LabVIEWServerDevice(host='localhost', port=9999)
    if server.start_server():
        try:
            while True:
                time.sleep(1)
                server.write_value_to_labview("Input", 42)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down server...")
            server.stop_server()
    else:
        print("❌ Could not start LabVIEW server.")

if __name__ == "__main__":
    main()