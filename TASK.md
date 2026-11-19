# Adaptive Practice Service

## Overview

Our product helps people prepare for aptitude tests. A learner practises in a session, and the difficulty of each question adapts to how well they are doing: it goes up when they answer correctly and down when they struggle.

Your task is to build a small backend service that runs such a practice session.

Expected effort is about 3 to 4 hours. Please do not spend much more than that. If you run out of time, write down in your README what you would do next. That is a perfectly good outcome.

## Stack

1. Python 3.11 or newer
2. FastAPI
3. pytest for tests

Anything else is your choice. Storage can be in memory, SQLite or anything you like.

## Question bank

The file `questions.json` holds 30 questions. Each question has:

1. `id`: unique id, for example `q07`
2. `difficulty`: a whole number from 1 (easiest) to 10 (hardest)
3. `text`: the question
4. `options`: the possible answers
5. `correct_answer`: the right option

Load the questions from this file when the service starts. Note that not every difficulty level has the same number of questions. Answers are always strings, compared exactly.

## How a session works

1. A new session starts at level 5.
2. The level belongs to the session. It only changes by the answer rules below, never to match the difficulty of the question served.
3. The service always serves one question at a time, the "current question". It is chosen as soon as the previous question is finished (or when the session starts), and it stays the current question until it is finished.
4. Choosing the next question:
   1. Pick a question the learner has not been served yet in this session, at the current level.
   2. If there is none at that level, use the closest level that still has one. If two levels are equally close, use the lower one.
   3. Within a level, pick the question with the lowest id.
5. Answering:
   1. Correct on the first attempt: the question is finished and the level goes up by 1.
   2. Wrong on the first attempt: the learner gets one retry on the same question. The level does not change yet.
   3. Correct on the retry: the question is finished and the level stays the same.
   4. Wrong on the retry: the question is finished and the level goes down by 1.
6. The level never goes below 1 or above 10.
7. A session ends when 10 questions are finished, or when there are no unserved questions left. Your code should handle both, even though the bank you were given has more than 10 questions.

### Example

A learner answers the first three questions correctly on the first attempt:

1. Level 5, so the first question is `q17` (level 5, lowest id). Correct, the level becomes 6.
2. Level 6 has no questions. Levels 5 and 7 are equally close, so the lower one wins: `q18`. Correct, the level becomes 7.
3. Level 7, so the next question is `q21`. Correct, the level becomes 8.

## API

All request and response bodies are JSON. The shapes below are a guide. You may add fields, but please keep the ones listed.

### Start a session

`POST /sessions`

Response:

```json
{ "session_id": "abc123", "level": 5 }
```

### Get the current question

`GET /sessions/{session_id}/question`

Response:

```json
{
  "question_id": "q17",
  "text": "What comes next: 8, 14, 20, 26, ?",
  "options": ["29", "32", "33", "34"],
  "difficulty": 5,
  "attempt": 1
}
```

1. Never return the correct answer here.
2. Calling this again before answering returns the same question.
3. During a retry, the same question comes back with `"attempt": 2`.
4. When the session has ended, return a response that makes this clear (your choice how).

### Answer the current question

`POST /sessions/{session_id}/answers`

Request:

```json
{ "question_id": "q17", "answer": "32" }
```

Response:

```json
{ "correct": true, "retry_open": false, "level": 6, "session_finished": false }
```

### Results

`GET /sessions/{session_id}/results`

Response:

```json
{ "questions_finished": 10, "correct_first_attempt": 6, "correct_on_retry": 2, "final_level": 7, "session_finished": true }
```

## Errors

Return sensible HTTP status codes with a short message, at least for:

1. An unknown session
2. An answer to a question that is not the current question
3. An answer after the session has ended
4. An answer that is not one of the question's options. This does not use up an attempt.

## What to hand in

1. Your code, as a zip or a link to a git repository
2. Tests for the rules above. We care most about the level and retry rules.
3. A short README with:
   1. How to install, run the service and run the tests
   2. Any decisions you made where the rules above were not clear to you
   3. What you would improve with more time

## What we look at

1. Correctness: the rules above behave exactly as described
2. Edge cases: what happens at the limits and on unexpected input
3. Tests
4. Code that is easy to read and easy to change

There is no trick and no single right structure. Keep it simple.

## Using AI tools

You may use AI assistants and any other resources. Please mention in your README where you used them, and make sure you understand every part of your code.

## Unclear rules

If a rule above is unclear to you, make a reasonable choice and write it down in your README.
