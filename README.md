# Adaptive Practice Service

A small FastAPI service that runs an adaptive practice session. The learner gets one question at a time, and the
difficulty level moves up or down with their answers. The task description is in [`TASK.md`](TASK.md).

## Install, run, test

You need Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync                                                    # install dependencies (incl. dev: pytest, httpx)
uv run uvicorn app.main:create_app --factory --reload      # run the service on http://127.0.0.1:8000
uv run pytest                                              # run the tests
```

Interactive API docs are at http://127.0.0.1:8000/docs once the service is running.

The question bank is loaded from `data/questions.json` at startup. To use a different file, set the
`QUESTIONS_PATH` environment variable. An invalid file stops the service from starting with a clear error
instead of failing later.

### Quick example

```bash
curl -X POST localhost:8000/sessions                       # {"session_id": "...", "level": 5}
curl localhost:8000/sessions/<id>/question                 # q17, attempt 1
curl -X POST localhost:8000/sessions/<id>/answers \
     -H "content-type: application/json" \
     -d '{"question_id": "q17", "answer": "32"}'
curl localhost:8000/sessions/<id>/results
```

## Project layout

```
app/
  domain/            pure rules, no web code
    config.py        START_LEVEL, MIN/MAX_LEVEL, SESSION_LENGTH
    models.py        Question (validated) and Session (state)
    selector.py      choosing the next question
    engine.py        applying an answer: level and retry rules, ending the session
    exceptions.py    the expected errors
  bank.py            loading and validating questions.json, indexing by level
  store.py           in-memory session store
  service.py         uses the engine for each endpoint; builds responses
  schemas.py         request and response shapes
  api/               FastAPI routes, dependencies, error handlers
  main.py            app factory
tests/               selector, engine, bank and API tests
```

The rules live in `app/domain` and don't depend on FastAPI. They are tested directly, without HTTP. The API
layer only translates requests and errors.

## API

| Method | Path | Notes |
|---|---|---|
| `POST` | `/sessions` | `201` → `{session_id, level}` |
| `GET` | `/sessions/{id}/question` | current question; `attempt` is 1 or 2; never includes the correct answer |
| `POST` | `/sessions/{id}/answers` | body `{question_id, answer}` → `{correct, retry_open, level, session_finished, ...}` |
| `GET` | `/sessions/{id}/results` | `{questions_finished, correct_first_attempt, correct_on_retry, final_level, session_finished}` |

Errors return `{"error": "<code>", "message": "<sentence>"}`:

| Situation | Status | `error` |
|---|---|---|
| Unknown session | 404 | `session_not_found` |
| Answer to a question that isn't the current one | 409 | `question_not_current` |
| Answer after the session has ended | 409 | `session_finished` |
| Answer that isn't one of the options (no attempt used) | 422 | `invalid_option` |
| Malformed body (missing field, wrong type, not JSON) | 422 | `invalid_request` |

## Decisions where the rules were open

- **Question after the session ends.** `GET /question` returns `200` with
  `{"session_finished": true, "question_id": null, "message": "..."}`. Ending the session is a normal state,
  not an error. Clients can check `session_finished` on every question response, because normal questions
  carry `session_finished: false`.
- **Status codes.** `409 Conflict` covers both "not the current question" and "session ended": the request is
  well formed but conflicts with the session's state. `422` covers an answer outside the options.
- **Order of checks** on an answer: session exists → session not ended → question is current → answer is
  an option. The client always gets the most basic problem first. A rejected request never changes the
  session.
- **Unknown `question_id`** (not in the bank at all) gets the same `409 question_not_current`. From the
  client's point of view it is simply not the current question.
- **Exact comparison.** Answers are compared as exact strings, as the task says, with no trimming or case
  folding. `" 32"` is not one of the options, so it gets a `422` and uses no attempt.
- **`retry_open`** is `true` only right after a wrong first attempt. After the second attempt it is `false`,
  whatever the result.
- **"Lowest id"** compares ids naturally (`q2` < `q10`), not as plain text. With the given zero-padded ids
  both give the same order.
- **Results mid-session.** `GET /results` works at any time and shows progress so far. `final_level` is
  the current level, and `session_finished` says whether it is final.
- **Extra fields.** Answer responses also include `question_finished` and `questions_finished`, so a
  client doesn't need extra calls.
- **Bank validation.** At startup the service rejects:
  - duplicate ids
  - duplicate options
  - a `correct_answer` that isn't an option
  - difficulty outside 1–10
  - fewer than two options
  - ids shorter than 3 characters
- **Storage.** Sessions are kept in memory, per process, as the task allows. They are lost on restart.
- **Session ids** look like `abc123`: three lowercase letters, then three digits, drawn with `secrets` so
  they are hard to guess. That is about 17.6 million possible ids, so repeats can happen. The store never
  overwrites: it rejects an id already in use, and the service draws a fresh one. It gives up with an error
  after 100 attempts, which only happens if the id space is nearly full.

## What I would improve with more time
- **Session lifecycle**: expire idle sessions and cap how many sessions are kept in memory.
- **Auth**: link sessions to a learner, so one learner can't read or answer another's session.
- **Configuration**: make the session length, start level and level range settings instead of constants.
- **Observability**: structured logging of answers and level changes, and a health endpoint.


## How I Used AI

- **Project Structure** – Discussed different approaches and chose a structure that keeps the code organized and easy to extend.
- **Visualization** – Created a diagram of the full flow, from creating a session to answering all 10 questions, to make the whole process easier to understand.
- **Writing Tests** – Sped up test writing by generating test cases with multiple agents, then reviewed and adjusted them to cover the important scenarios.
- **Code Clean-Up** – Got suggestions for better naming, readability and overall code quality.
- **Postman Testing** – Organized requests into Postman collections and folders so the API can be tested end to end.
- **Code Generation** – Got help with parts of the code where I was stuck, then adapted it to fit the project.
- **Bug Fixing** – Used AI to track down the causes of bugs and work out fixes.

All AI-generated code and suggestions were reviewed, tested and adjusted by me before being included.
