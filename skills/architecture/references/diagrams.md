# Architecture Diagram Templates

Ready-to-use Mermaid diagram templates for architecture documentation.

## C4 Model Diagrams

### Level 1: System Context

Shows system and external actors/systems.

```mermaid
graph TB
    subgraph External
        User[👤 User]
        Admin[👤 Admin]
        ExtAPI[External API]
    end

    subgraph "System Boundary"
        System[🖥️ Your System]
    end

    User -->|Uses| System
    Admin -->|Manages| System
    System -->|Calls| ExtAPI
```

**Template:**
```
graph TB
    subgraph External
        Actor1[👤 Actor Name]
        ExtSystem[External System]
    end

    subgraph "System Boundary"
        System[🖥️ System Name]
    end

    Actor1 -->|Action| System
    System -->|Action| ExtSystem
```

---

### Level 2: Container Diagram

Shows deployable units within the system.

```mermaid
graph TB
    subgraph "Your System"
        WebApp[🌐 Web App<br/>React]
        API[⚙️ API Server<br/>Go]
        Worker[⚙️ Background Worker<br/>Go]
        DB[(📦 Database<br/>PostgreSQL)]
        Cache[(📦 Cache<br/>Redis)]
        Queue[📨 Message Queue<br/>Redis Streams]
    end

    WebApp -->|HTTPS/JSON| API
    API -->|SQL| DB
    API -->|Read/Write| Cache
    API -->|Publish| Queue
    Worker -->|Subscribe| Queue
    Worker -->|SQL| DB
```

---

### Level 3: Component Diagram

Shows components within a container.

```mermaid
graph TB
    subgraph "API Server"
        Router[Router]
        AuthMW[Auth Middleware]

        subgraph Controllers
            UserCtrl[User Controller]
            OrderCtrl[Order Controller]
        end

        subgraph Services
            UserSvc[User Service]
            OrderSvc[Order Service]
        end

        subgraph Repositories
            UserRepo[User Repository]
            OrderRepo[Order Repository]
        end
    end

    Router --> AuthMW
    AuthMW --> UserCtrl & OrderCtrl
    UserCtrl --> UserSvc
    OrderCtrl --> OrderSvc
    UserSvc --> UserRepo
    OrderSvc --> OrderRepo
    UserRepo & OrderRepo --> DB[(Database)]
```

---

## Sequence Diagrams

### Basic Request Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant G as Gateway
    participant S as Service
    participant D as Database

    C->>G: HTTP Request
    G->>G: Validate Token
    G->>S: Forward Request
    S->>D: Query
    D-->>S: Results
    S-->>G: Response
    G-->>C: HTTP Response
```

### With Error Handling

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Service
    participant D as Database

    C->>S: Create Order
    S->>D: Check Inventory

    alt Inventory Available
        D-->>S: OK
        S->>D: Save Order
        D-->>S: Saved
        S-->>C: 201 Created
    else Out of Stock
        D-->>S: Insufficient
        S-->>C: 400 Bad Request
    end
```

### Async with Events

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Order Service
    participant E as Event Bus
    participant N as Notification Service
    participant P as Payment Service

    C->>S: Create Order
    S->>S: Validate Order
    S->>E: Publish OrderCreated
    S-->>C: 202 Accepted

    par Parallel Processing
        E->>N: OrderCreated Event
        N->>N: Send Email
    and
        E->>P: OrderCreated Event
        P->>P: Process Payment
        P->>E: Publish PaymentCompleted
    end
```

---

## Data Flow Diagrams

### Simple Flow

```mermaid
flowchart LR
    A[Input] --> B[Process]
    B --> C[Output]
    B --> D[(Storage)]
```

### Complex Flow with Decisions

```mermaid
flowchart TB
    Start([Request]) --> Validate{Valid?}

    Validate -->|Yes| Auth{Authenticated?}
    Validate -->|No| Error1[400 Bad Request]

    Auth -->|Yes| Process[Process Request]
    Auth -->|No| Error2[401 Unauthorized]

    Process --> Cache{In Cache?}
    Cache -->|Yes| Return[Return Cached]
    Cache -->|No| DB[(Query DB)]

    DB --> Store[Update Cache]
    Store --> Return

    Return --> End([Response])
    Error1 --> End
    Error2 --> End
```

---

## State Diagrams

### Order State Machine

```mermaid
stateDiagram-v2
    [*] --> Pending: Create Order

    Pending --> Confirmed: Confirm Payment
    Pending --> Cancelled: Cancel

    Confirmed --> Processing: Start Processing
    Confirmed --> Cancelled: Cancel

    Processing --> Shipped: Ship
    Processing --> Cancelled: Cancel

    Shipped --> Delivered: Deliver
    Shipped --> Returned: Return

    Delivered --> Returned: Return
    Delivered --> [*]: Complete

    Returned --> Refunded: Process Refund
    Refunded --> [*]

    Cancelled --> [*]
```

---

## Entity Relationship Diagrams

### Basic ERD

```mermaid
erDiagram
    USER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_ITEM : contains
    PRODUCT ||--o{ ORDER_ITEM : "ordered in"

    USER {
        uuid id PK
        string email UK
        string name
        timestamp created_at
    }

    ORDER {
        uuid id PK
        uuid user_id FK
        decimal total
        string status
        timestamp created_at
    }

    ORDER_ITEM {
        uuid id PK
        uuid order_id FK
        uuid product_id FK
        int quantity
        decimal price
    }

    PRODUCT {
        uuid id PK
        string name
        decimal price
        int stock
    }
```

### Multi-Tenant ERD

```mermaid
erDiagram
    TENANT ||--o{ USER : has
    TENANT ||--o{ PROJECT : owns
    PROJECT ||--o{ TASK : contains
    USER ||--o{ TASK : assigned

    TENANT {
        uuid id PK
        string name
        string plan
    }

    USER {
        uuid id PK
        uuid tenant_id FK
        string email
        string role
    }

    PROJECT {
        uuid id PK
        uuid tenant_id FK
        string name
    }

    TASK {
        uuid id PK
        uuid tenant_id FK
        uuid project_id FK
        uuid assignee_id FK
        string title
    }
```

---

## Deployment Diagrams

### Kubernetes Deployment

```mermaid
graph TB
    subgraph "Kubernetes Cluster"
        subgraph "Ingress"
            IG[Ingress Controller]
        end

        subgraph "Services"
            subgraph "API Deployment"
                API1[API Pod 1]
                API2[API Pod 2]
                API3[API Pod 3]
            end

            subgraph "Worker Deployment"
                W1[Worker Pod 1]
                W2[Worker Pod 2]
            end
        end

        subgraph "Data"
            PG[(PostgreSQL)]
            Redis[(Redis)]
        end
    end

    Internet --> IG
    IG --> API1 & API2 & API3
    API1 & API2 & API3 --> PG & Redis
    W1 & W2 --> PG & Redis
```

### Cloud Architecture

```mermaid
graph TB
    subgraph "AWS"
        subgraph "Public"
            ALB[Application Load Balancer]
            CF[CloudFront CDN]
        end

        subgraph "Private"
            subgraph "ECS Cluster"
                API[API Service]
                Worker[Worker Service]
            end

            RDS[(RDS PostgreSQL)]
            ElastiCache[(ElastiCache Redis)]
            S3[(S3 Bucket)]
        end
    end

    Users --> CF
    CF --> ALB
    ALB --> API
    API --> RDS & ElastiCache & S3
    Worker --> RDS & ElastiCache
```

---

## Microservices Diagrams

### Service Communication

```mermaid
graph LR
    subgraph "API Gateway"
        GW[Gateway]
    end

    subgraph "Services"
        US[User Service]
        OS[Order Service]
        PS[Payment Service]
        NS[Notification Service]
    end

    subgraph "Infrastructure"
        MQ[Message Queue]
        SD[Service Discovery]
    end

    GW --> US & OS
    OS --> PS
    OS --> MQ
    MQ --> NS
    US & OS & PS & NS --> SD
```

### Event-Driven Services

```mermaid
graph TB
    subgraph "Producers"
        OS[Order Service]
        PS[Payment Service]
    end

    subgraph "Event Bus (Kafka)"
        OT[orders topic]
        PT[payments topic]
    end

    subgraph "Consumers"
        NS[Notification Service]
        AS[Analytics Service]
        IS[Inventory Service]
    end

    OS -->|OrderCreated| OT
    PS -->|PaymentProcessed| PT

    OT --> NS & AS & IS
    PT --> NS & AS
```

---

## Class Diagrams (Domain Model)

### Domain Entities

```mermaid
classDiagram
    class Order {
        +String id
        +String customerId
        +OrderStatus status
        +List~OrderItem~ items
        +Money total
        +addItem(product, quantity)
        +removeItem(itemId)
        +calculateTotal()
        +submit()
        +cancel()
    }

    class OrderItem {
        +String id
        +String productId
        +int quantity
        +Money unitPrice
        +Money subtotal()
    }

    class Money {
        +Decimal amount
        +String currency
        +add(Money)
        +subtract(Money)
    }

    class OrderStatus {
        <<enumeration>>
        DRAFT
        SUBMITTED
        CONFIRMED
        SHIPPED
        DELIVERED
        CANCELLED
    }

    Order "1" --> "*" OrderItem
    Order --> OrderStatus
    OrderItem --> Money
    Order --> Money
```

---

## Quick Copy Templates

### Minimal System Diagram
```
graph TB
    Client --> API --> DB[(Database)]
```

### Basic Layers
```
graph TB
    UI[Presentation] --> App[Application] --> Domain --> Infra[Infrastructure]
```

### Request/Response
```
sequenceDiagram
    Client->>Server: Request
    Server-->>Client: Response
```

### Simple State
```
stateDiagram-v2
    [*] --> State1
    State1 --> State2
    State2 --> [*]
```

### Basic ERD
```
erDiagram
    A ||--o{ B : has
    A { id PK }
    B { id PK, a_id FK }
```
