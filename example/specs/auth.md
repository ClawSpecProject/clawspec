# Authentication

## Entities

A **User** has a name, email, and password. Email addresses must be unique across all users.

## Rules

- Passwords are never stored in plain text
- Login sessions expire after 24 hours
- Attempting to register with an existing email is rejected with a clear error

## Constraints

- Use Firebase Auth for all authentication
- Store user profile data (name) in a Firestore `users` collection
- Protect all non-auth pages with a route guard

## User Stories

### Sign Up
A new user provides their name, email, and password to create an account.
The password must be at least 8 characters.
On success, they are directed to the task dashboard.
If the email is already taken, an error message is shown.

**Acceptance criteria:**
- Submitting the form with valid data creates a Firebase Auth user and a Firestore user document
- Submitting with an existing email shows "Email already in use"
- Submitting with a password under 8 characters shows a validation error
- After successful signup, the browser is on `/tasks`

### Log In
A user enters their email and password.
On success, they are taken to the task dashboard.
If the credentials are wrong, an error message is shown.

**Acceptance criteria:**
- Valid credentials redirect to `/tasks`
- Invalid credentials show "Invalid email or password"
- The auth token is persisted so refreshing the page stays logged in

### Log Out
A logged-in user clicks a logout button in the navigation bar.
They are returned to the login page.

**Acceptance criteria:**
- After logout, visiting `/tasks` redirects to `/login`
