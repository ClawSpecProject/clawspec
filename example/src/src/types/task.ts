import { Timestamp } from "firebase/firestore";

export type TaskStatus = "todo" | "in_progress" | "done";

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  creatorId: string;
  assigneeId?: string;
  createdAt: Timestamp;
  updatedAt: Timestamp;
}

export interface CreateTaskInput {
  title: string;
  description?: string;
  assigneeId?: string;
}

export interface UpdateTaskInput {
  title?: string;
  description?: string;
  status?: TaskStatus;
  assigneeId?: string | null;
}
