# Real-Time Bid War System

## Prerequisites

### Install Python
Ensure you have Python 3.7 or higher installed. Check with:
```bash
python3 --version  # or
python --version
```

### Install pip
Make sure you have pip installed. It usually comes with Python.

### Install Required Libraries
Run the following command in your terminal:
```bash
pip install websockets aiortc opencv-python av
```

- **websockets**: For WebSocket communication (bid transmissions).
- **aiortc**: For WebRTC (live video streaming).
- **opencv-python**: For video capture and processing.
- **av**: For audio/video encoding/decoding with WebRTC.

### Install FFmpeg
FFmpeg is required for WebRTC video encoding/decoding. Install it based on your OS:

- **Windows**: Download from the [official website](https://ffmpeg.org/) or use a package manager like Chocolatey. Ensure `ffmpeg.exe` and `ffprobe.exe` are in your system's PATH.
- **macOS**: Run:
  ```bash
  brew install ffmpeg
  ```
- **Linux (Debian/Ubuntu)**: Run:
  ```bash
  sudo apt-get install ffmpeg
  ```

### Generate SSL Certificates
The system uses SSL for secure WebSockets. Generate self-signed certificates using OpenSSL:
```bash
openssl req -newkey rsa:2048 -nodes -keyout ssl_key.pem -x509 -days 365 -out ssl_cert.pem
```
Answer the prompts. Use `localhost` for testing in the **Common Name (CN)** field. Place `ssl_cert.pem` and `ssl_key.pem` in the same directory as your Python scripts.

## Setup & Execution

### Create the Required Files
Create the following Python files in the same directory:

- `server.py`
- `client.py`
- `video_stream.py`
- `signaling_server.py`
- `video_client.py`

Copy the corresponding code into each file and save them.

### Running the System

1. **Run the Signaling Server** (for WebRTC connection negotiation):
   ```bash
   python signaling_server.py
   ```
   Keep this running in a separate terminal.

2. **Run the Auction Server** (handles bids and auction state):
   ```bash
   python server.py
   ```
   Keep this running in another terminal.

3. **Run the Video Stream (Host)**:
   ```bash
   python video_stream.py
   ```
   The host's video stream needs an offer before starting. First, run the video client, copy the offer given by the client, and paste it into the video stream to provide an answer.

4. **Run the Video Client (Viewer)**:
   ```bash
   python video_client.py
   ```
   Copy the offer generated and use it in the video stream.

5. **Run the Auction Client(s) (Bidders)**:
   ```bash
   python client.py
   ```
   Run this command in multiple terminal windows to simulate multiple bidders.

## Important Considerations

- **SSL Errors**: Since self-signed certificates are used, SSL errors might appear. The client code includes:
  ```python
  ssl_context.check_hostname = False
  ssl_context.verify_mode = ssl.CERT_NONE
  ```
  This bypasses SSL verification for testing but should NOT be used in production.

- **Firewall**: Ensure your firewall isn't blocking ports **8765** and **8766**.

- **Camera Access**: If using a real camera (`USE_FAKE_CAMERA = False` in `video_stream.py`), ensure the script has camera access permissions.

- **WebRTC Offer/Answer Exchange**: The offer from the client must reach the server, and the answer from the server must reach the client. This system uses a basic in-memory mechanism.

- **Execution Order**:
  1. Start the **Signaling Server** first.
  2. Start the **Auction Server**.
  3. Start the **Video Stream**.
  4. Start the **Video Client**.
  5. Start the **Auction Clients** (bidders).

## Usage Commands

### Auction Client Commands:

- `bid <amount>`: Places a bid.
- `host_request`: Requests to become the auction host.
- `message <content>`: Sends a message to all clients.
- `quit`: Disconnects from the server.

---

This guide ensures you can set up and run the real-time bid war system efficiently. Happy bidding! 🚀
