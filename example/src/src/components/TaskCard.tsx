"use client";

import Link from "next/link";
import { Task, TaskStatus } from "@/types/task";

interface TaskCardProps {
  task: Task;
  /** Display name of the assigned user, or undefined/null if unassigned. */
  assigneeName?: string | null;
}

/**
 * Maps a TaskStatus value to its human-readable label.
 */
function getStatusLabel(status: TaskStatus): string {
  switch (status) {
    case "todo":
      return "To Do";
    case "in_progress":
      return "In Progress";
    case "done":
      return "Done";
    default:
      return status;
  }
}

/**
 * Returns the CSS class name for a status badge based on the task status.
 * - Grey for todo
 * - Blue for in_progress
 * - Green for done
 */
function getStatusBadgeClass(status: TaskStatus): string {
  switch (status) {
    case "todo":
      return "badge-todo";
    case "in_progress":
      return "badge-in-progress";
    case "done":
      return "badge-done";
    default:
      return "badge-todo";
  }
}

/**
 * Formats a Firestore Timestamp (or compatible object) into a readable date string.
 * Falls back to "—" if the timestamp is missing or invalid.
 */
function formatDate(timestamp: { toDate?: () => Date } | undefined | null): string {
  if (!timestamp || typeof timestamp.toDate !== "function") {
    return "—";
  }

  try {
    const date = timestamp.toDate();
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return "—";
  }
}

/**
 * Card component for displaying a single task in the list view.
 *
 * Shows:
 * - Task title
 * - Status badge (color-coded: grey for todo, blue for in_progress, green for done)
 * - Assignee name (or "Unassigned")
 * - Formatted creation date
 *
 * The entire card is clickable and links to /tasks/[id].
 */
export default function TaskCard({ task, assigneeName }: TaskCardProps) {
  return (
    <Link
      href={`/tasks/${task.id}`}
      className="card block p-4 transition-shadow hover:shadow-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
    >
      <div className="flex items-start justify-between gap-3">
        {/* Left section: title and meta info */}
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold text-gray-900">
            {task.title}
          </h3>

          <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500">
            {/* Assignee */}
            <span className="flex items-center gap-1">
              <svg
                className="h-3.5 w-3.5 text-gray-400"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"
                />
              </svg>
              {assigneeName || "Unassigned"}
            </span>

            {/* Creation date */}
            <span className="flex items-center gap-1">
              <svg
                className="h-3.5 w-3.5 text-gray-400"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5"
                />
              </svg>
              {formatDate(task.createdAt)}
            </span>
          </div>
        </div>

        {/* Right section: status badge */}
        <span className={getStatusBadgeClass(task.status)}>
          {getStatusLabel(task.status)}
        </span>
      </div>
    </Link>
  );
}
