import {
  collection,
  doc,
  addDoc,
  getDoc,
  getDocs,
  updateDoc,
  deleteDoc,
  query,
  where,
  orderBy,
  serverTimestamp,
  Timestamp,
} from "firebase/firestore";
import { db } from "@/lib/firebase";
import { Task, CreateTaskInput, UpdateTaskInput, TaskStatus } from "@/types/task";

const TASKS_COLLECTION = "tasks";

export interface TaskFilters {
  status?: TaskStatus;
  assigneeId?: string;
}

/**
 * Creates a new task in the Firestore `tasks` collection.
 * Automatically sets status to 'todo' and applies server-side timestamps
 * for both createdAt and updatedAt.
 */
export async function createTask(
  input: CreateTaskInput,
  creatorId: string
): Promise<Task> {
  const taskData: Record<string, unknown> = {
    title: input.title,
    status: "todo" as TaskStatus,
    creatorId,
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
  };

  if (input.description !== undefined && input.description !== "") {
    taskData.description = input.description;
  }

  if (input.assigneeId !== undefined && input.assigneeId !== "") {
    taskData.assigneeId = input.assigneeId;
  }

  const tasksCollectionRef = collection(db, TASKS_COLLECTION);
  const docRef = await addDoc(tasksCollectionRef, taskData);

  // Fetch the created document to return the full Task with server timestamps
  const createdDoc = await getDoc(docRef);
  const data = createdDoc.data()!;

  return {
    id: docRef.id,
    title: data.title,
    description: data.description,
    status: data.status,
    creatorId: data.creatorId,
    assigneeId: data.assigneeId,
    createdAt: data.createdAt as Timestamp,
    updatedAt: data.updatedAt as Timestamp,
  } as Task;
}

/**
 * Fetches a single task by its document ID from the Firestore `tasks` collection.
 * Returns null if the task does not exist.
 */
export async function getTask(id: string): Promise<Task | null> {
  const taskDocRef = doc(db, TASKS_COLLECTION, id);
  const taskSnapshot = await getDoc(taskDocRef);

  if (!taskSnapshot.exists()) {
    return null;
  }

  const data = taskSnapshot.data();

  return {
    id: taskSnapshot.id,
    title: data.title,
    description: data.description,
    status: data.status,
    creatorId: data.creatorId,
    assigneeId: data.assigneeId,
    createdAt: data.createdAt as Timestamp,
    updatedAt: data.updatedAt as Timestamp,
  } as Task;
}

/**
 * Fetches tasks from the Firestore `tasks` collection with optional
 * server-side filtering by status and/or assigneeId.
 * Results are always ordered by createdAt descending (newest first).
 *
 * All filtering is done via Firestore where() clauses (server-side),
 * not client-side, per the project constraints.
 */
export async function getTasks(filters?: TaskFilters): Promise<Task[]> {
  const tasksCollectionRef = collection(db, TASKS_COLLECTION);
  const queryConstraints = [];

  if (filters?.status) {
    queryConstraints.push(where("status", "==", filters.status));
  }

  if (filters?.assigneeId) {
    queryConstraints.push(where("assigneeId", "==", filters.assigneeId));
  }

  queryConstraints.push(orderBy("createdAt", "desc"));

  const tasksQuery = query(tasksCollectionRef, ...queryConstraints);
  const tasksSnapshot = await getDocs(tasksQuery);

  const tasks: Task[] = tasksSnapshot.docs.map((docSnapshot) => {
    const data = docSnapshot.data();
    return {
      id: docSnapshot.id,
      title: data.title,
      description: data.description,
      status: data.status,
      creatorId: data.creatorId,
      assigneeId: data.assigneeId,
      createdAt: data.createdAt as Timestamp,
      updatedAt: data.updatedAt as Timestamp,
    } as Task;
  });

  return tasks;
}

/**
 * Updates an existing task document in Firestore by merging the provided fields.
 * Automatically sets updatedAt to the current server timestamp.
 */
export async function updateTask(
  id: string,
  updates: UpdateTaskInput
): Promise<void> {
  const taskDocRef = doc(db, TASKS_COLLECTION, id);

  const updateData: Record<string, unknown> = {
    updatedAt: serverTimestamp(),
  };

  if (updates.title !== undefined) {
    updateData.title = updates.title;
  }

  if (updates.description !== undefined) {
    updateData.description = updates.description;
  }

  if (updates.status !== undefined) {
    updateData.status = updates.status;
  }

  if (updates.assigneeId !== undefined) {
    // Allow setting assigneeId to null to unassign
    updateData.assigneeId = updates.assigneeId === null ? null : updates.assigneeId;
  }

  await updateDoc(taskDocRef, updateData);
}

/**
 * Permanently deletes a task document from the Firestore `tasks` collection.
 */
export async function deleteTask(id: string): Promise<void> {
  const taskDocRef = doc(db, TASKS_COLLECTION, id);
  await deleteDoc(taskDocRef);
}
