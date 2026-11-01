// Google sign-in through Firebase. Firebase only proves who the person is: the ID token goes to the API, which returns
// a normal BrandGuard session, so nothing else in the app talks to Firebase.
import type { Auth } from "firebase/auth";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || "",
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "",
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || "",
};

export const firebaseConfigured = Boolean(firebaseConfig.apiKey && firebaseConfig.authDomain && firebaseConfig.projectId);

type FirebaseAuth = { auth: Auth; sdk: typeof import("firebase/auth") };
let ready: FirebaseAuth | null = null;
let pending: Promise<FirebaseAuth> | null = null;

/** Load the SDK before the click. A browser only allows a popup opened directly by a click, so nothing can be awaited
 *  between the click and signInWithPopup: call this as soon as the Google button is shown. */
export function loadFirebase(): Promise<FirebaseAuth> {
  pending ??= Promise.all([import("firebase/app"), import("firebase/auth")]).then(([appSdk, sdk]) => {
    const app = appSdk.getApps()[0] ?? appSdk.initializeApp(firebaseConfig);
    ready = { auth: sdk.getAuth(app), sdk };
    return ready;
  });
  return pending;
}

const MESSAGES: Record<string, string> = {
  "auth/popup-blocked": "Your browser blocked the Google sign-in window. Allow pop-ups for this site and try again.",
  "auth/unauthorized-domain": "Google sign-in isn't allowed on this domain yet. Add it in Firebase under Authentication > Settings > Authorized domains.",
  "auth/operation-not-allowed": "Google sign-in is switched off in Firebase. Turn it on under Authentication > Sign-in method.",
  "auth/network-request-failed": "Couldn't reach Google. Check your connection and try again.",
};

/** Show the Google account picker and return a Firebase ID token, or null if the person closed it. */
export async function signInWithGooglePopup(): Promise<string | null> {
  const { auth, sdk } = ready ?? (await loadFirebase()); // already loaded in the normal case, so the popup is allowed
  const provider = new sdk.GoogleAuthProvider();
  provider.setCustomParameters({ prompt: "select_account" });
  try {
    const result = await sdk.signInWithPopup(auth, provider);
    const idToken = await result.user.getIdToken();
    await sdk.signOut(auth); // BrandGuard keeps its own session; don't leave a second one behind
    return idToken;
  } catch (e: unknown) {
    const code = (e as { code?: string }).code ?? "";
    if (code === "auth/popup-closed-by-user" || code === "auth/cancelled-popup-request") return null;
    throw new Error(MESSAGES[code] ?? "Google sign-in failed. Please try again.");
  }
}
