# Tasks

## Entities

A **Task** belongs to the user who created it and can optionally be assigned to any user.
Tasks have a status: to do (default), in progress, or done.

## Rules

- Only logged-in users can view or manage tasks
- Any user can create a task (they become the creator)
- Any user can change a task's status or reassign it
- Only the creator of a task can delete it
- The task list shows newest tasks first

## Constraints

- Store tasks in a Firestore `tasks` collection
- Use Firestore queries for filtering (not client-side)
- Task status is stored as a string enum: `todo`, `in_progress`, `done`

## User Stories

### Create a Task
A user fills in a title and optional description, and optionally picks someone to assign it to.
The task is created with status "to do".

**Acceptance criteria:**
- A task with just a title can be created successfully
- The new task appears at the top of the task list
- The creator is automatically set to the current user
- Assignee dropdown shows all users in the system

### Browse Tasks
A user sees all tasks in a list showing title, status, assignee, and creation date.
They can filter by status or by assignee.

**Acceptance criteria:**
- All tasks are visible to all logged-in users
- Filtering by "in progress" shows only in-progress tasks
- Filtering by assignee shows only tasks assigned to that person
- Clearing filters shows all tasks again
- Tasks are ordered newest first

### View and Edit a Task
A user clicks on a task to see its full details.
They can edit the title, description, status, and assignee.
A save button commits the changes.

**Acceptance criteria:**
- All task fields are displayed and editable
- Changing the status and saving persists the change
- Navigating back to the list shows the updated task

### Delete a Task
The task creator sees a delete button on the task detail view.
Deleting removes the task permanently. Other users do not see the delete button.

**Acceptance criteria:**
- The delete button is only visible to the task creator
- Clicking delete removes the task from Firestore
- After deletion, the user is redirected to the task list
- The deleted task no longer appears in the list
