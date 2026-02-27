# Task Manager

A task management app where teams can create, assign, and track work items.

## Tech Stack

- Next.js with TypeScript
- Firebase Auth and Firestore
- Tailwind CSS

## Entities

### User
A person who uses the app. Has a name, email (unique), and password.

### Task
A work item with a title, optional description, and status (to do, in progress, or done).
A task is created by one user and can be assigned to another user.
Tasks track when they were created and last updated.
