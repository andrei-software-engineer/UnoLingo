# UnoLingo

#### Ceban Andrei, FAF-211

## Application Suitability
The following system is suitable for the following reasons:

* The Learning Session Service is essential and flexible as it manages core functionalities like matching users with native speakers or tutors, handling conversation sessions (text, voice, or video), and providing real-time feedback during language practice (such as pronunciation correction, vocabulary tips, or grammar suggestions).

* Growing Demand for Language Learning: With increasing globalization, the need to learn new languages for travel, work, or personal growth has surged. Online learning platforms have become a preferred method for language acquisition due to their flexibility and accessibility.

* Real-time Interactions are Critical: Language learning thrives on conversation and immediate feedback. Unlike traditional self-paced apps, this platform offers real-time interactions with native speakers, which provides an immersive learning experience essential for mastering speaking and listening skills.

* Convenience and Accessibility: The app connects learners and native speakers from different regions, offering users the ability to practice anytime and anywhere. This is especially valuable in regions where access to in-person language tutors is limited.

## Service boundaries

1. Client - Is a service which interacts with the system by making requests to the Gateway.
2. Gateway Service - The entry point to the system, handling WebSocket connections and routing requests to the Simulation Service and User Service.
3. Service Discovery - Is responsible for maintaining a registry of services and their instances, that way all services can communicate between them.
   or UserService based on the required functionality.
4. User Service - Is responsible for handling user registration, authentification, data management.
5. Simulation Service - Implements the game logic, real-time requests and updates.

![image](assets/svd.pn)

## Technology Stack

1. Client
    * React.js framework.
2. Gateway Service
    * Node.js
    * WebSocket Library: Starlett (ASGI) - for asynchronous operations and real-time features.
3. User Service
    * Programming language - Python / Flask, to manage user actions
    * Database - Sqlite
4. Simulation Service
    * Programming language - Python / Flask
    * Database - Sqlite
    * Redis - For caching ongoing sessions and handling real-time interactions.


## Communication Patterns 

1. RESTful APIs:
    * HTTP communication between external clients and services.

2. gRPC:
    * Communication between services and service discovery.

3. WebSocket:
    * For real-time, bi-directional communication.

## Data Management Design
### User Service:
#### Endpoints:

### 1. Register a New User

- **Endpoint**: `/gateway/register`
- **Method**: `POST`
- **Rate Limiting**: Max 10 requests per minute per IP
- **Description**: Registers a new user with the authentication service.

**Request Body**:
```json
{
    "username": "Teacher",
    "password": "123456"
}
```

- Responses:

- ** 201 Created: User registered successfully.
- ** 429 Too Many Requests: Rate limit exceeded.
- ** 504 Gateway Timeout: Request to the auth service timed out.
- ** 500 Internal Server Error: Service discovery or auth service failure.

### 2. Login and Issue JWT Token

- **Endpoint**: `/gateway/login`
- **Method**: `POST`
- **Description**: Authenticates a user and issues a JWT token.

**Request Body**:
```json
{
    "username": "Teacher",
    "password": "123456"
}
```

- Responses:

200 OK: Login successful, token issued.
401 Unauthorized: Incorrect credentials.
500 Internal Server Error: Service discovery or auth service failure.

### 3. Validate JWT Token

- **Endpoint**: `/gateway/validate_token`
- **Method**: `GET`
- **Description**: Validates a JWT token with the authentication service.

**Headers**:
- `Authorization`: Bearer token

**Responses**:
- `200 OK`: Token is valid.
- `401 Unauthorized`: Token is invalid or missing.
- `500 Internal Server Error`: Service discovery or auth service failure.



### 4. Get User Information by ID

- **Endpoint**: `/gateway/user/:id`
- **Method**: `GET`
- **Description**: Retrieves user information by user ID.

**Parameters**:
- `id`: User ID to retrieve information for

**Responses**:
- `200 OK`: User information retrieved.
- `404 Not Found`: User not found.
- `500 Internal Server Error`: Service discovery or auth service failure.


### 5. Get All Users

- **Endpoint**: `/gateway/users`
- **Method**: `GET`
- **Description**: Retrieves information for all users.

**Responses**:
- `200 OK`: List of users.
- `500 Internal Server Error`: Service discovery or auth service failure.

---

### 6. Gateway Status

- **Endpoint**: `/status`
- **Method**: `GET`
- **Description**: Retrieves the status of the gateway and authentication service.

**Responses**:
- `200 OK`: Returns status of the gateway and auth service.
- `500 Internal Server Error`: Failed to retrieve service status.


### Chat Service:
#### Endpoints:

### 1. Create Room

- **Endpoint**: `/socket.io/createRoom`
- **Method**: `SocketIO Event`
- **Description**: Creates a new chat room.

**Request Data**:
```json
{
    "room": "string"  // Name of the room to create
}
```

**Responses**:
- Room "{room_name}" created.: Indicates the room has been created successfully.
- Room "{room_name}" already exists.: The specified room name is already in use.

### 2. Join Room

- **Endpoint:** `/socket.io/joinRoom`  
- **Method:** SocketIO Event  
- **Description:** Joins an existing chat room.

### Request Data:

```json
{
    "token": "string",  // JWT token for authentication
    "room": "string"    // Name of the room to join
}
```

**Responses**:
- Joined room: {room_name} as {username}: Indicates successful joining of the room.
- Invalid token. You cannot join the room.: Token validation failed.
- Room "{room_name}" does not exist.: The specified room does not exist.


### 3. Leave Room

- **Endpoint**: `/socket.io/leaveRoom`
- **Method**: SocketIO Event
- **Description**: Leaves a chat room.

#### Request Data:

```json
{
    "room": "string"  // Name of the room to leave
}
```

**Responses**:
- You left room: {room_name}: Indicates successful exit from the room.


### 4. Get Rooms

- **Endpoint**: `/socket.io/getRooms`
- **Method**: SocketIO Event
- **Description**: Fetches the list of available chat rooms.

**Responses**:
- List of room names : Sent back to the user, containing the names of all available chat rooms.


### 5. Get Room Messages

- **Endpoint**: `/socket.io/getRoomMessages`
- **Method**: SocketIO Event
- **Description**: Retrieves messages from a specific chat room.

#### Request Data:

```json
{
    "room": "string"  // Name of the room to fetch messages from
}
```

**Responses**:
- List of messages from the specified room, formatted as "{username}: {message}".


### 6. Delete Room

- **Endpoint**: `/socket.io/deleteRoom`
- **Method**: SocketIO Event
- **Description**: Deletes a chat room.

#### Request Data:

```json
{
    "room": "string"  // Name of the room to delete
}
```

**Responses**:
- Room "{room_name}" deleted.: Indicates successful deletion of the room.

### 7. Send Message

- **Endpoint**: `/socket.io/message`
- **Method**: SocketIO Event
- **Description**: Sends a message to a chat room.

#### Request Data:

```json
{
    "token": "string",  // JWT token for authentication
    "room": "string",    // Name of the room to send the message to
    "message": "string"  // The message content
}
```

**Responses**:
- Invalid token. You cannot send messages.: Token validation failed.
- You are not in this room.: User is not in the specified room.


## Running the Application with Docker

To run the application using Docker, follow these steps:

### Prerequisites

- Ensure you have Docker installed on your machine. You can download it from [Docker's official website](https://www.docker.com/get-started).

### Setup

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone <repository-url>
   cd <repository-directory>

2. ** Navigate to the project directory where the docker-compose.yml file is located.

### Running the Services

To build and run the services using Docker Compose, use the following command:

```bash
docker-compose up --build
```

This command will:

- **Build the images** for the `api-gateway`, `auth_service`, `chat_service`,  `discovery_service` and `redis`.
- **Start all services** defined in the `docker-compose.yml` file.


## Accessing the Services

Once the containers are up and running, you can access the services at the following URLs:

- **API Gateway:** [http://localhost:3000](http://localhost:3000)
- **Auth Service:** [http://localhost:5003](http://localhost:5003)
- **Chat Service:** [http://localhost:5005](http://localhost:5005)
- **Service Discovery:** [http://localhost:8080](http://localhost:8080)


## Stopping the Services

To stop the running services, you can either:

1. Press `Ctrl + C` in the terminal where Docker Compose is running, or
2. Run the following command:

   ```bash
   docker-compose down

   
## Deployment & Scaling

* Deployment: Each microservice, including Authentication , will be containerized with Docker. Docker Compose will handle the network setup, enabling communication between services via their names and creating separate environments for each service.

* Scaling: Horizontal scaling will be implemented to deploy additional instances of the Flashcards service during peak usage times. This approach will distribute the load across multiple instances, enhancing performance and optimizing resource utilization.
