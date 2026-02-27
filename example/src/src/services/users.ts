import { doc, getDoc, collection, getDocs } from "firebase/firestore";
import { db } from "@/lib/firebase";
import { UserProfile } from "@/types/user";

/**
 * Fetches a single user profile document from the Firestore `users` collection.
 * Returns null if the user document does not exist.
 */
export async function getUserProfile(
  uid: string
): Promise<UserProfile | null> {
  const userDocRef = doc(db, "users", uid);
  const userSnapshot = await getDoc(userDocRef);

  if (!userSnapshot.exists()) {
    return null;
  }

  const data = userSnapshot.data();

  return {
    uid: userSnapshot.id,
    name: data.name,
    email: data.email,
  } as UserProfile;
}

/**
 * Fetches all user profiles from the Firestore `users` collection.
 * Used to populate the assignee dropdown when creating or editing tasks.
 */
export async function getAllUsers(): Promise<UserProfile[]> {
  const usersCollectionRef = collection(db, "users");
  const usersSnapshot = await getDocs(usersCollectionRef);

  const users: UserProfile[] = usersSnapshot.docs.map((docSnapshot) => {
    const data = docSnapshot.data();
    return {
      uid: docSnapshot.id,
      name: data.name,
      email: data.email,
    } as UserProfile;
  });

  return users;
}
