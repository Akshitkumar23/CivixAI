# CivixAI

This is a Next.js project for CivixAI, an application to help users find government schemes they are eligible for.

## Getting Started

First, install the dependencies:
```bash
npm install
```

Next, run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Docker (Two Services)

This app runs with a Next.js web service + a FastAPI ML microservice.

1. Create `.env` from the template:
```bash
copy .env.example .env
```

2. Start the stack:
```bash
docker-compose up --build
```

- Web: `http://localhost:3000`
- ML service: `http://localhost:8001`
